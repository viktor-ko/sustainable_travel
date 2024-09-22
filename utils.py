import streamlit as st
import pandas as pd
import altair as alt
import numpy as np
import json
import os
import math

# Custom CSS to hide the links to other pages in the sidebar
hide_page_links_style = """
    <style>
        [data-testid="stSidebarNav"] {
            display: none;
        }
    </style>
"""

# Load the trip and coordinates data and clean up the column names
trip_data = pd.read_csv('data/trips_data.csv')
trip_data.columns = trip_data.columns.str.strip()
coordinates_data = pd.read_csv('data/coordinates.csv')
coordinates_data.columns = coordinates_data.columns.str.strip()

# Normalize city pairs in trip data
def normalize_city_pair(city1, city2):
    return '-'.join(sorted([city1, city2]))

trip_data['route'] = trip_data.apply(lambda row: normalize_city_pair(row['City_1'], row['City_2']), axis=1)

# Get unique cities for the select boxes
cities = coordinates_data['city'].unique()

# Function to create the base map with all cities
def create_base_map():
    # Load TopoJSON of Europe
    europe = alt.topo_feature('https://dmws.hkvservices.nl/dataportal/data.asmx/read?database=vega&key=europe', 'europe')
    base = alt.Chart(europe).mark_geoshape(
        fill='lightgray',
        stroke='white',
        strokeWidth = 0.5
    ).project(
        'mercator',
        scale=700,
        center=[11, 49],
        # rotate=[5, 0, 0]
    ).properties(
        height=500
    ).encode(
        tooltip=alt.value('')  # Suppress default tooltip by setting to an empty string
    )
    # Add cities
    points = alt.Chart(coordinates_data).mark_circle(
        color='#FF6F61',
        size=150,
        opacity=0.9
    ).project(
        'mercator',
        scale=700,
        center=[11, 49],
        # rotate=[5, 0, 0]
    ).encode(
        longitude='longitude:Q',
        latitude='latitude:Q',
        tooltip=['city:N']
    )
    return base + points

# calculate the center (mean lat/lon) and scale based on point spread
def get_projection_params(cities):
    # Get longitude and latitude values
    lons = [city['lon'] for city in cities]
    lats = [city['lat'] for city in cities]

    # Calculate the center as the mean of the coordinates
    center_lon = (sum(lons) / len(lons)) + 2
    center_lat = sum(lats) / len(lats)

    # Calculate the spread of the points (difference between max and min coordinates)
    lon_range = max(lons) - min(lons)
    lat_range = max(lats) - min(lats)

    # Factor in the latitude difference less because distances shrink closer to the poles
    weighted_lat_range = lat_range * math.cos(math.radians(center_lat))

    # Use the larger of the two ranges to determine the scale, adding a buffer to prevent extremes
    max_range = max(lon_range, weighted_lat_range)

    # Adjust the scale based on the range; larger range -> smaller scale (zoom out)
    scale_factor = 300 / (max_range ** 0.7)

    # Set bounds for the scale to prevent extreme zoom-in/zoom-out
    min_scale = 400  # Minimum zoom level (for large ranges)
    max_scale = 2500  # Maximum zoom level (for small ranges)

    final_scale = min(max(scale_factor * 25, min_scale), max_scale)

    # Debugging: print calculated values
    # print(f"Center: {[center_lon, center_lat]}, Scale: {final_scale}")

    return {
        'center': [center_lon, center_lat],
        'scale': final_scale
    }

# Load GeoJSON route between cities for train
def load_geojson_route(from_city, to_city):

    # Replace spaces with underscores for city names
    from_city = from_city.replace(" ", "_")
    to_city = to_city.replace(" ", "_")

    # Special case: always check if "Luxembourg_City" comes first
    if "Luxembourg_City" in [from_city, to_city]:
        luxembourg_first_file_name = f"Luxembourg_City_{from_city if from_city != 'Luxembourg_City' else to_city}.geojson"
        luxembourg_first_file_path = os.path.join('geojson_files', luxembourg_first_file_name)

        if os.path.exists(luxembourg_first_file_path):
            with open(luxembourg_first_file_path, 'r') as f:
                geojson_data = json.load(f)
            return geojson_data

    sorted_cities = sorted([from_city, to_city])
    file_name = f"{sorted_cities[0]}_{sorted_cities[1]}.geojson"
    file_path = os.path.join('geojson_files', file_name)

    # Load GeoJSON file
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            geojson_data = json.load(f)
        return geojson_data
    else:
        st.warning(f"No GeoJSON route found for {from_city} to {to_city}")
        return None

def double_duration(duration_str):
    hours, minutes = map(int, duration_str.split(':'))
    total_minutes = (hours * 60 + minutes) * 2
    doubled_hours = total_minutes // 60
    doubled_minutes = total_minutes % 60
    return f"{doubled_hours}:{doubled_minutes:02d}"

#convert duration to "hours:minutes" string
def duration_to_str(duration_str):
    hours, minutes = map(int, duration_str.split(':'))
    return f"{hours:02}:{minutes:02}"

#convert duration to minutes
def duration_to_minutes(duration_str):
    hours, minutes = map(int, duration_str.split(':'))
    return hours * 60 + minutes

# Determine dynamic tick intervals for bar charts
def calculate_tick_values(min_value, max_value):
    range_span = max_value - min_value
    if range_span <= 180:
        step = 30  # 30-minute intervals for <3h journeys
    elif range_span <= 360:
          step = 60  # 1-hour intervals for 3-6h journeys
    elif range_span <= 720:
          step = 120  # 2-hour intervals for 6-12h journeys
    elif range_span <= 1440:
        step = 240  # 4-hour intervals for 12-24h journeys
    else:
        step = 480  # 8-hour intervals for >24h journeys
    return [0] + np.arange(step, max_value + step, step).tolist()  # Include 0 as the starting point
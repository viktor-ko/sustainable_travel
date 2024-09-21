import streamlit as st
import pandas as pd
import altair as alt
import json
import os

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
        stroke='white'
    ).project(
        'mercator'
    ).properties(
        width=1500,
        height=1000
    ).encode(
        tooltip=alt.value('')  # Suppress default tooltip by setting to an empty string
    )
    # Add cities
    points = alt.Chart(coordinates_data).mark_circle(color='#fc9272', size=50).encode(
        longitude='longitude:Q',
        latitude='latitude:Q',
        tooltip=['city:N']
    )
    return base + points

# Load GeoJSON route between cities for train
def load_geojson_route(from_city, to_city):
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
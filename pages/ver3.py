import streamlit as st
import pandas as pd
import altair as alt
import numpy as np
import os
import json

# Set the app layout to "wide" mode
st.set_page_config(layout="wide")

from vega_datasets import data

# Load the world map data
source = alt.topo_feature(data.world_110m.url, 'countries')

cities = [
    {'city': 'Riga', 'lon': 24.10589, 'lat': 56.946},
    {'city': 'Lisbon', 'lon': -9.13333, 'lat': 38.71667},
]


# Helper function to calculate the center (mean lat/lon) and scale based on point spread
def get_projection_params(cities):
    # Get longitude and latitude values
    lons = [city['lon'] for city in cities]
    lats = [city['lat'] for city in cities]

    # Calculate the center based on the average of the cities' coordinates
    avg_lon = (cities[0]['lon'] + cities[1]['lon']) / 2
    avg_lat = (cities[0]['lat'] + cities[1]['lat']) / 2

    # Calculate the distance between the two cities for scale
    lon_range = abs(cities[0]['lon'] - cities[1]['lon'])
    lat_range = abs(cities[0]['lat'] - cities[1]['lat'])
    max_range = max(lon_range, lat_range)

    # Adjust the scale based on the range; larger range -> smaller scale (zoom out)
    scale_factor = 800 / max_range

    # Debugging: print calculated values
    print(f"Center: {[avg_lon, avg_lat]}, Scale: {scale_factor}")

    return {
        'center': [avg_lon, avg_lat],
        'scale': scale_factor * 25  # Scaling for Altair's projection scale
    }

# Get projection parameters based on the city points
projection_params = get_projection_params(cities)

# Convert cities data to an Altair chart layer
cities_layer = alt.Chart(alt.Data(values=cities)).mark_circle(size=100, color='red').encode(
    longitude='lon:Q',
    latitude='lat:Q',
    tooltip=['city:N']
).project(
    type='mercator',
    scale=projection_params['scale'],  # Dynamic scale
    center=projection_params['center']  # Dynamic center
)

# Create a map with projection focused on Europe
map_layer = alt.Chart(source).mark_geoshape(
    stroke='white',
    strokeWidth=0.5
).encode(
    color=alt.value('lightgray'),
    tooltip=alt.value('')
).project(
    type='mercator',  # Mercator projection is common for world maps
    scale=projection_params['scale'],  # Dynamic scale
    center=projection_params['center']  # Dynamic center
).properties(
    width=800,
    height=450
)

final_map = map_layer + cities_layer

col1, col2 = st.columns([1, 2])
with col2:
    st.altair_chart(final_map, use_container_width=True)

# st.title("Ver 3")

# Initialize session state to keep track of sidebar collapse state
# if 'sidebar_collapsed' not in st.session_state:
#     st.session_state.sidebar_collapsed = False
#
# # Function to toggle sidebar collapse state
# def toggle_sidebar():
#     st.session_state.sidebar_collapsed = True  # Collapse sidebar when search is clicked
#
# def show_sidebar():
#     st.session_state.sidebar_collapsed = False  # Show sidebar again
#
# # Sidebar content
# st.sidebar.title("Custom Sidebar")
# st.sidebar.write("Sidebar with additional options.")
#
# # Main interface
# with st.sidebar:
#     from_city = st.selectbox('From', ['City A', 'City B', 'City C'], index=None, placeholder="Select a departure city")
#     to_city_options = [city for city in ['City A', 'City B', 'City C'] if city != from_city]
#     to_city = st.selectbox('To', to_city_options, index=None, placeholder="Select a destination city")
#
#     col_left, col_right = st.columns([0.4, 0.5], gap='medium')
#     with col_left:
#         num_people = st.number_input('People:', min_value=1, max_value=10, value=1)
#     with col_right:
#         round_trip = st.checkbox('Round Trip')
#
#     # Button to trigger search and collapse the sidebar
#     search_clicked = st.button('Search', on_click=toggle_sidebar)
#
# # Button to show sidebar again
# if st.session_state.sidebar_collapsed:
#     st.button("Show Sidebar", on_click=show_sidebar)
#
# # Apply the collapse CSS if the sidebar is collapsed
# if st.session_state.sidebar_collapsed:
#     st.markdown("""
#         <style>
#             [data-testid="stSidebar"] {
#                 display: none;
#             }
#         </style>
#     """, unsafe_allow_html=True)
#
# # Display search information
# if search_clicked:
#     st.write(f"Searching from {from_city} to {to_city} for {num_people} people.")

import streamlit as st
import pandas as pd
import altair as alt

# Load the trip and coordinates data
trip_data = pd.read_csv('data/trips_data.csv')
coordinates_data = pd.read_csv('data/coordinates.csv')

# Strip any leading or trailing spaces from column names
coordinates_data.columns = coordinates_data.columns.str.strip()
trip_data.columns = trip_data.columns.str.strip()

# Normalize city pairs in trip data
def normalize_city_pair(city1, city2):
    return '-'.join(sorted([city1, city2]))

trip_data['route'] = trip_data.apply(lambda row: normalize_city_pair(row['City_1'], row['City_2']), axis=1)

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

# Get unique cities for the select boxes
cities = coordinates_data['city'].unique()

# Set Streamlit page configuration to wide mode
st.set_page_config(layout="wide")

# Title of the app
st.title('Sustainable Travel Planner')

# Create two columns for layout
col1, col2 = st.columns([1, 2])

with col1:
    # Input fields for "From" and "To" with selectbox and placeholder
    from_city = st.selectbox('From', cities, index=None, placeholder="Select a departure city")

    # Dynamically update the 'To' options based on the selected 'From' city
    to_city_options = [city for city in cities if city != from_city]
    to_city = st.selectbox('To', to_city_options, index=None, placeholder="Select a destination city")

    # Button to trigger search
    search_clicked = st.button('Search')

    # Travel Data
    st.subheader('Travel Plan Details')
    if search_clicked and from_city and to_city:
        route = normalize_city_pair(from_city, to_city)
        travel_details = trip_data[trip_data['route'] == route]
        if not travel_details.empty:
            travel_info = travel_details.iloc[0]
            hours, minutes = travel_info['Duration_train'].split(':')[:2]
            st.write(f"Traveling from {from_city} to {to_city} will take {hours} h {minutes} min by train.")
            # st.write(f"Train CO2 emissions: {travel_info['Train_CO2_kg']} kg")
            # st.write(f"Plane CO2 emissions: {travel_info['Plane_CO2_kg']} kg")

            # Create bar chart
            emissions_data = pd.DataFrame({
                'Mode': ['Train', 'Plane'],
                'CO2_kg': [travel_info['Train_CO2_kg'], travel_info['Plane_CO2_kg']]
            })
            # alt.ColorScheme('basic', ['#f00', '#0f0', '#00f', '#ff0', '#f0f', '#0ff'])
            emissions_chart = alt.Chart(emissions_data).mark_bar().encode(
                x=alt.X('CO2_kg', title='CO2 (kg)'),
                y=alt.Y('Mode', title=None),
                color=alt.Color('Mode', legend=None).scale(scheme="redyellowgreen")
            ).properties(
                title='CO2 Emissions'
            )
            st.altair_chart(emissions_chart, use_container_width=True)
        else:
            st.write(f"No travel data available for the route from {from_city} to {to_city}.")
    elif search_clicked:
        st.write('Please select both "From" and "To" cities.')

with col2:
    # Display the base map with all cities
    map_with_cities = create_base_map()

    # If search button is clicked and both cities are selected, highlight the "From" and "To" cities
    if search_clicked and from_city and to_city:
        # Filter the DataFrame for the selected cities
        from_city_data = coordinates_data[coordinates_data['city'] == from_city].iloc[0]
        to_city_data = coordinates_data[coordinates_data['city'] == to_city].iloc[0]

        # Add the Plane_CO2_kg and Train_CO2_kg to to_city_data for the tooltip
        to_city_data = to_city_data.append(pd.Series({
            'Plane_CO2_kg': travel_info['Plane_CO2_kg'],
            'Train_CO2_kg': travel_info['Train_CO2_kg']
        }))

        # Highlight the "From" and "To" cities
        from_point = alt.Chart(pd.DataFrame([from_city_data])).mark_circle(color='green', size=200).encode(
            longitude='longitude:Q',
            latitude='latitude:Q',
            tooltip=['city:N']
        )

        to_point_plane = alt.Chart(pd.DataFrame([to_city_data])).mark_circle(color='red', size=travel_info['Plane_CO2_kg']*10).encode(
            longitude='longitude:Q',
            latitude='latitude:Q',
            tooltip=['city:N', 'Plane_CO2_kg:Q']
        )

        to_point_train = alt.Chart(pd.DataFrame([to_city_data])).mark_circle(color='green', size=travel_info['Train_CO2_kg']*10).encode(
            longitude='longitude:Q',
            latitude='latitude:Q',
            tooltip=['city:N', 'Train_CO2_kg:Q']
        )

        # Combine the map with highlighted cities
        map_with_cities += from_point + to_point_plane + to_point_train

    # Display the map
    st.altair_chart(map_with_cities, use_container_width=True)
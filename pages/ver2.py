import streamlit as st
import pandas as pd
import altair as alt

from utils import cities, trip_data, coordinates_data, normalize_city_pair, double_duration, \
    create_base_map, duration_to_str, duration_to_minutes, calculate_tick_values, get_projection_params, load_geojson_lines, \
    load_geojson_points, generate_curved_arc, calculate_transfers

# Set Streamlit page configuration to wide mode
st.set_page_config(layout="wide")

# custom padding
st.markdown("""
    <style>
    .block-container {padding-top: 0 !important;}
    </style>
    """, unsafe_allow_html=True
)

# Custom CSS to hide the sidebar
hide_sidebar_style = """
    <style>
        [data-testid="stSidebar"] {
            display: none;
        }
    </style>
"""
# Inject the CSS into the app
st.markdown(hide_sidebar_style, unsafe_allow_html=True)

title, disclaimer = st.columns([0.95, 0.05], vertical_alignment="bottom")
with title:
    st.title('Sustainable Travel Planner')
with disclaimer:
    with st.popover("❔", help="Disclaimer"):
        st.markdown(
 '''
This tool is a prototype and may contain bugs or data errors. 
Travel duration and carbon emissions here are estimates based on route averages and may actually vary depending on the day, time and exact route.
''')

search, maps, charts = st.columns([0.28, 0.5, 0.33])

with search:
    from_city = st.selectbox('From', cities, index=None, placeholder="Departure city")

    # Dynamically update the 'To' options based on the selected 'From' city
    to_city_options = [city for city in cities if city != from_city]
    to_city = st.selectbox('To', to_city_options, index=None, placeholder="Destination city")
    cl1, cl2 = st.columns([0.48, 0.52], gap = 'small', vertical_alignment="bottom")
    with cl1:
        num_people = st.number_input('People:', min_value=1, max_value=10, value=1)
    with cl2:
        round_trip = st.toggle('Round Trip')

    # Button to trigger search
    search_clicked = st.button('Search')

    # Calculate the number of transfers based on points in GeoJSON data
    geojson_data_points = load_geojson_points(from_city, to_city)

    if search_clicked and geojson_data_points:
        transfers = calculate_transfers(geojson_data_points)
        st.metric(label="Train Transfers:", value=transfers)

with charts:

    #Travel Data
    if search_clicked and from_city and to_city:
        route = normalize_city_pair(from_city, to_city)
        travel_details = trip_data[trip_data['route'] == route]
        if not travel_details.empty:
            travel_info = travel_details.iloc[0]

            # Check if plane duration is available
            if pd.isna(travel_info['Duration_plane_total']) or pd.isna(travel_info['Plane_CO2_kg']):
                # Show a warning message
                st.write("Cities are too close, no flights available.")
                # Set default values for the chart if plane data is not available
                plane_duration = "N/A"
                plane_co2 = 0
            else:
                plane_duration = travel_info['Duration_plane_total']
                plane_co2 = round(travel_info['Plane_CO2_kg'], 1)

            train_duration = travel_info['Duration_train']
            train_co2 = round(travel_info['Train_CO2_kg'], 1)

            # Adjust CO2 emissions based on the number of people
            train_co2 *= num_people
            plane_co2 *= num_people

            # Double the values if round trip is selected
            if round_trip:
                train_duration = double_duration(train_duration)
                train_co2 *= 2
                if plane_duration != "N/A":
                    plane_duration = double_duration(plane_duration)
                plane_co2 *= 2

            # Prepare the data for the duration bar chart
            duration_data = pd.DataFrame({
                'Mode': ['🚂', '✈️'],
                'Duration': [
                    duration_to_str(train_duration),
                    plane_duration
                ],
                'Duration_minutes': [
                    duration_to_minutes(train_duration),
                    duration_to_minutes(plane_duration) if plane_duration != "N/A" else 0
                ]
            })

            # Calculate dynamic tick values
            max_duration = duration_data['Duration_minutes'].max()
            tick_values = calculate_tick_values(0, max_duration)

            #Label expression for the x-axis of duration chart
            labelExpr = '''
                (datum.value % 60 == 0) ?
                    format(datum.value / 60, "d") : 
                    format(floor(datum.value / 60), "d") + ".5"
            '''

            colors = ['indianred', 'forestgreen']

            # Create the duration bar chart
            duration_chart = alt.Chart(duration_data).mark_bar().encode(
                x=alt.X('Mode', title=None, axis=alt.Axis(labelFontSize=15, labelAngle=0)),
                y=alt.Y('Duration_minutes:Q', title=None,
                        axis=alt.Axis(values=tick_values, labelExpr=labelExpr)),
                tooltip=[alt.Tooltip('Duration', title='Duration'), alt.Tooltip('Mode', title='Mode')],
                color=alt.Color('Mode', legend=None).scale(range=colors),
            ).properties(
                title='Travel Duration'
            )

            # Add data labels to the duration chart
            duration_labels = alt.Chart(duration_data).mark_text(
                align='center',
                baseline='middle',
                color='white',
                size=14,
                dy= 15
            ).encode(
                x=alt.X('Mode', title=None),
                y=alt.Y('Duration_minutes:Q'),
                text=alt.Text('Duration'),
                tooltip = alt.value('')
            )

            # Combine bar chart with labels
            duration_combined_chart = duration_chart + duration_labels

            # Create emissions bar chart
            emissions_data = pd.DataFrame({
                'Mode': ['🚂', '✈️'],
                'CO2_kg': [train_co2, plane_co2]
            })

            emissions_chart = alt.Chart(emissions_data).mark_bar().encode(
                y=alt.Y('CO2_kg', title=None, axis=alt.Axis(orient='right')),
                x=alt.X('Mode', title=None, axis=alt.Axis(labelFontSize=15, labelAngle=0)),
                color=alt.Color('Mode', legend=None).scale(
                    range=colors
                )
            ).properties(
                title='Carbon Emissions'
            )

            # Add data labels to the emissions chart
            emissions_labels = alt.Chart(emissions_data).mark_text(
                align='center',
                baseline='middle',
                color='white',
                size=14,
                dy=15
            ).encode(
                x=alt.X('Mode', title=None),
                y=alt.Y('CO2_kg'),
                tooltip = alt.value('')
            ).transform_calculate(
                label="round(datum.CO2_kg) + ' kg'" # Concatenate "kg" to the CO2 value
            ).encode(
                text=alt.Text('label:N')  # Use the calculated label field
            )

            # Combine bar chart with labels
            emissions_combined_chart = emissions_chart + emissions_labels

            #Display charts
            col1, col2 = st.columns(2, gap='medium')
            with col1:
                st.altair_chart(duration_combined_chart, use_container_width=True)
            with col2:
                st.altair_chart(emissions_combined_chart, use_container_width=True)

            # Add note below chart
            note = "<p style='font-family: monospace; font-size: small;'>Plane duration includes +3h for getting to/from the airport, security check and boarding</p>"
            note_round = "<p style='font-family: monospace; font-size: small;'>Plane duration includes +6h for getting to/from the airport, security check and boarding</p>"
            if round_trip:
                st.markdown(note_round, unsafe_allow_html=True)
            else:
                st.markdown(note, unsafe_allow_html=True)

        else:
            st.write(f"No travel data available for the route from {from_city} to {to_city}.")
    elif search_clicked:
        st.warning('Please select both "From" and "To" cities.')

with maps:
    # If search button is not clicked, display the base map with all cities
    if not search_clicked:
        map_with_all_cities = create_base_map(from_city, to_city)
        st.altair_chart(map_with_all_cities, use_container_width=True)

    # If search button is clicked and both cities are selected, highlight the "From" and "To" cities
    if search_clicked and from_city and to_city:
        # Filter the DataFrame for the selected cities
        filtered_points = coordinates_data[coordinates_data['city'].isin([from_city, to_city])]

        from_city_data = filtered_points[filtered_points['city'] == from_city].iloc[0]
        to_city_data = filtered_points[filtered_points['city'] == to_city].iloc[0]

        # Add Plane_CO2_kg and Train_CO2_kg to to_city_data for the tooltip
        to_city_data['Plane_CO2_kg'] = plane_co2
        to_city_data['Train_CO2_kg'] = train_co2

        # Convert to_city_data to a DataFrame for Altair
        from_city_df = pd.DataFrame([from_city_data])
        to_city_df = pd.DataFrame([to_city_data])

        # Get dynamic projection parameters based on the selected cities
        cities = [{'city': from_city, 'lon': from_city_data['longitude'], 'lat': from_city_data['latitude']},
                  {'city': to_city, 'lon': to_city_data['longitude'], 'lat': to_city_data['latitude']}]

        projection_params = get_projection_params(cities)

        # create the route map with 2 cities
        europe = alt.topo_feature('https://raw.githubusercontent.com/leakyMirror/map-of-europe/refs/heads/master/TopoJSON/europe.topojson', 'europe')
        base = alt.Chart(europe).mark_geoshape(
            fill='lightgray',
            stroke='white',
            strokeWidth=0.5
        ).project(
            'mercator',
            scale=projection_params['scale'],
            center=projection_params['center'],
            rotate=[5, 0, 0]
        ).properties(
            height=500
        ).encode(
            tooltip=alt.value('')  # Suppress default tooltip by setting to an empty string
        )

        from_point = alt.Chart(from_city_df).mark_circle(
            color='#FF6F61',
            size=300,
            opacity=0.9
        ).project(
            'mercator',
            scale=projection_params['scale'],
            center=projection_params['center'],
            rotate=[5, 0, 0]
        ).transform_calculate(
            tooltip_text='"From: " + datum.city'
        ).encode(
            longitude='longitude:Q',
            latitude='latitude:Q',
            tooltip=alt.Tooltip('tooltip_text:N')
        )

        to_point = alt.Chart(to_city_df).mark_circle(
            color='#FF6F61',
            size=300,
            opacity = 0.9
        ).project(
            'mercator',
            scale=projection_params['scale'],
            center=projection_params['center'],
            rotate=[5, 0, 0]
        ).transform_calculate(
            tooltip_text='"To: " + datum.city'
        ).encode(
            longitude='longitude:Q',
            latitude='latitude:Q',
            tooltip=alt.Tooltip('tooltip_text:N')
        )

        # Load GeoJSON data for both lines and points
        geojson_lines_data = load_geojson_lines(from_city, to_city)
        geojson_points_data = load_geojson_points(from_city, to_city)

        # Extract coordinates from GeoJSON for the train route
        line_coordinates = geojson_lines_data['features'][0]['geometry']['coordinates']

        # Prepare tooltip information directly in DataFrame for Altair
        tooltip_data = pd.DataFrame({
            'type': ['LineString'],
            'coordinates': [line_coordinates],
            'route_type': [f"Train from {from_city} to {to_city}"],
            'Train_CO2_kg': [f"{train_co2} kg"],
            'Duration_train': [train_duration]
        })

        # draw train route on the map
        train_route = alt.Chart(alt.Data(values=[tooltip_data.to_dict(orient='records')[0]])).mark_geoshape(
            fill=None,
            stroke='forestgreen',
            strokeWidth=train_co2 / 15,
            opacity=0.7
        ).project(
            'mercator',
            scale=projection_params['scale'],
            center=projection_params['center'],
            rotate=[5, 0, 0]
        ).encode(
            tooltip=[
                alt.Tooltip('route_type:N', title='Route'),
                alt.Tooltip('Train_CO2_kg:N', title='CO2'),
                alt.Tooltip('Duration_train:N', title='Duration'),
            ]
        )

        # Generate the arc line for the plane route if plane data are available
        if pd.isna(travel_info['Duration_plane_total']) or pd.isna(travel_info['Plane_CO2_kg']):
            plane_route = alt.Chart(pd.DataFrame()).mark_geoshape()  # Empty placeholder if plane data is missing
        else:
            from_coords = [from_city_data['longitude'], from_city_data['latitude']]
            to_coords = [to_city_data['longitude'], to_city_data['latitude']]
            arc_points = generate_curved_arc(from_coords, to_coords)

            # Add custom tooltip text to the data
            arc_data = {
                'type': 'LineString',
                'coordinates': arc_points,
                'route_type': f"Plane from {from_city} to {to_city}",
                'Plane_CO2_kg': f"{plane_co2} kg",
                'Duration_plane_total': plane_duration
            }

            plane_route = alt.Chart(alt.Data(values=[arc_data])).mark_geoshape(
                fill=None,
                stroke='indianred',
                strokeWidth=plane_co2/15,
            ).project(
                'mercator',
                scale=projection_params['scale'],
                center=projection_params['center'],
                rotate=[5, 0, 0]
            ).encode(
                tooltip=[alt.Tooltip('route_type:N', title='Route'),
                         alt.Tooltip('Plane_CO2_kg:N', title='CO2'),
                         alt.Tooltip('Duration_plane_total:N', title='Duration')]
            )

        # Combine the layers in the correct order
        map_with_selected_cities = base + plane_route + train_route + from_point + to_point

        # Display the map
        st.altair_chart(map_with_selected_cities, use_container_width=True)

expander = st.expander("Calculation Methodology and Data Sources")
expander.write('''
Emissions data for all travel routes was obtained using the [Travel CO2 API](https://travelco2.com/documentation). 
According to their [methodology](https://travelco2.com/met/Methodology-Report-for-Travel-and-Climate-Version-4.pdf), the following CO2 emission factors are used:  
- **Train** - **24** g CO2e per passenger-km  
- **Plane** - **127** g CO2e per passenger-km (Economy scheduled flight).

Information about the average flight times between airports was collected from the [AeroDataBox API](https://aerodatabox.com/).

**Important Note Regarding Plane Data**: Both sources calculate flight routes as a straight line between two cities, not considering possible transfers. 
Therefore, in reality, actual plane travel times and emissions will be higher for cities without direct flight connection.
''')
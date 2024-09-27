import streamlit as st
import pandas as pd
import altair as alt

from utils import cities, trip_data, coordinates_data, normalize_city_pair, double_duration, \
    create_base_map, duration_to_minutes, calculate_tick_values, get_projection_params, load_geojson_lines, \
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

            new_duration_data = pd.DataFrame({
                'Mode': ['Train', 'Plane'],
                'Duration_minutes': [duration_to_minutes(train_duration),
                                     duration_to_minutes(plane_duration) if plane_duration != "N/A" else 0],
                'Duration': [train_duration, plane_duration]
            })

            # Calculate dynamic tick values
            max_duration = new_duration_data['Duration_minutes'].max()
            tick_values = calculate_tick_values(0, max_duration)

            #Label expression for the x-axis of duration chart
            labelExpr = '''
                (datum.value % 60 == 0) ?
                    format(datum.value / 60, "d") : 
                    format(floor(datum.value / 60), "d") + ".5"
            '''

            colors = ['indianred', 'forestgreen']

            #bullet chart for train & plane travel time
            train_bar = alt.Chart(new_duration_data).transform_filter(
                alt.datum.Mode == 'Train'
            ).mark_bar().encode(
                y=alt.Y('Mode:N', title=None, axis=None),
                x=alt.X('Duration_minutes:Q', title=None,
                        axis=alt.Axis(values=tick_values, labelExpr=labelExpr)),
                tooltip=[alt.Tooltip('Duration', title='Train Duration')],
                color=alt.value('forestgreen')  # Set the color for the train bar
            ).properties(
                title='Train & Plane Duration'
            )

            # Create a thick tick for plane travel time
            plane_tick = alt.Chart(new_duration_data).transform_filter(
                alt.datum.Mode == 'Plane'
            ).mark_tick(
                thickness=10,  # Adjust the thickness of the tick
                size=40,  # Control the height of the tick
                color='indianred'  # Set the color for the plane tick
            ).encode(
                x=alt.X('Duration_minutes:Q', title=None),
                tooltip=[alt.Tooltip('Duration', title='Plane Duration')]
            )

            # Layer the train bar and plane tick
            new_chart = alt.layer(
                train_bar,
                plane_tick
            )

            # Display the chart in Streamlit
            st.altair_chart(new_chart, use_container_width=True)

            # Add note below chart
            note = "<p style='font-family: monospace; font-size: small;'>Plane duration includes +3h for getting to/from the airport, security check and boarding</p>"
            note_round = "<p style='font-family: monospace; font-size: small;'>Plane duration includes +6h for getting to/from the airport, security check and boarding</p>"
            if round_trip:
                st.markdown(note_round, unsafe_allow_html=True)
            else:
                st.markdown(note, unsafe_allow_html=True)

            # Create emissions bar chart
            data = pd.DataFrame({
                'Mode': ['🚂', '✈️'],
                'CO2_kg': [train_co2, plane_co2]
            })

            circle_chart = alt.Chart(data).mark_circle().encode(
                x=alt.X('Mode:N', title=None, axis=alt.Axis(labelAngle=0, labelFontSize=15)),
                y=alt.value(50),
                size=alt.Size('CO2_kg:Q', scale=alt.Scale(range=[0, 10000]), legend=None),
                tooltip=['Mode:N', 'CO2_kg:Q'],
                color=alt.Color('Mode', legend=None).scale(
                    range=colors
                )
            ).properties(
                height=200,
                title='Carbon Emissions'
        )
            # Add data labels inside the circles
            labels = alt.Chart(data).mark_text(
                align='center',
                baseline='middle',
                color='white',
                fontSize=20
            ).transform_calculate(
                label="round(datum.CO2_kg) + ' kg'"
            ).encode(
                x=alt.X('Mode:N', title=None),  # Same x-axis as circles
                y=alt.value(50),  # Keep labels aligned horizontally, matching circle position
                text=alt.Text('label:N'),
                tooltip=alt.value('')  # Disable tooltip on the text layer
            )

            # Combine the circles and labels into a single chart
            final_chart = (circle_chart + labels).properties(
                height=200
            ).configure_axis(
                grid=False,
                title=None
            )

            st.altair_chart(final_chart, use_container_width=True)

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
        europe = alt.topo_feature('https://dmws.hkvservices.nl/dataportal/data.asmx/read?database=vega&key=europe', 'europe')
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

        # train route transfer points
        train_stops = alt.Chart(alt.Data(values=geojson_points_data['features'])).mark_circle(
            color='mediumseagreen',
            size=100,
            opacity=0.7
        ).project(
            'mercator',
            scale=projection_params['scale'],
            center=projection_params['center'],
            rotate=[5, 0, 0]
        ).encode(
            longitude='geometry.coordinates[0]:Q',
            latitude='geometry.coordinates[1]:Q',
            tooltip=alt.Tooltip('properties.stop_name:N')
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
        map_with_selected_cities = base + plane_route + train_route + train_stops + from_point + to_point

        # Display the map
        st.altair_chart(map_with_selected_cities, use_container_width=True)

expander = st.expander("Calculation Methodology and Data Sources")
expander.write('''
Emissions data for all travel routes was obtained using the [Travel CO2 API](https://travelco2.com/documentation). 
According to their [methodology](https://travelco2.com/met/Methodology-Report-for-Travel-and-Climate-Version-4.pdf), CO2 emissions are estimated as follows:  
- **Train**: **24** g CO2e per passenger-km  
- **Plane**: **127** g CO2e per passenger-km (for an Economy scheduled flight, which is the default option).

Information about the average flight times between airports was collected from the [AeroDataBox API](https://aerodatabox.com/).

**Important Note Regarding Plane Data**: Both sources calculate flight routes as a straight line between two cities, not considering possible transfers. 
Therefore, in reality, actual plane travel times and emissions will be higher for cities without direct flight connection.
''')
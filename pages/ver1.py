import streamlit as st
import pandas as pd
import altair as alt
from utils import hide_page_links_style, cities, trip_data, coordinates_data, normalize_city_pair, double_duration, \
    create_base_map, load_geojson_route, duration_to_str, duration_to_minutes, calculate_tick_values, \
    get_projection_params

# Set Streamlit page configuration to wide mode
st.set_page_config(layout="wide")

# Inject the CSS into the app
st.markdown(hide_page_links_style, unsafe_allow_html=True)

# custom padding
st.markdown("""
    <style>
    .block-container {padding-top: 0 !important;}
    </style>
    """, unsafe_allow_html=True
)

#default sidebar width (narrow)
st.markdown("""
    <style>
        section[data-testid="stSidebar"] {
            width: 244px !important;
        }
    </style>
    """, unsafe_allow_html=True,
)

col_left, col_right = st.columns([0.9, 0.1], vertical_alignment="bottom")
with col_left:
    st.title('Sustainable Travel Planner')
with col_right:
    with st.popover("❔", help="This app helps you compare the CO2 emissions and travel duration between train and plane for your trip."):
        st.markdown(
 '''The data is for demonstration purposes only and may not be accurate for real-world travel planning.
 The CO2 emissions are based on average values and may vary depending on the specific circumstances of the trip.
 Please use this app as a reference and other sources for accurate travel information.  ''')

with st.sidebar:
    from_city = st.selectbox('From', cities, index=None, placeholder="Departure city")

    # Dynamically update the 'To' options based on the selected 'From' city
    to_city_options = [city for city in cities if city != from_city]
    to_city = st.selectbox('To', to_city_options, index=None, placeholder="Destination city")
    num_people = st.number_input('People:', min_value=1, max_value=10, value=1)
    round_trip = st.toggle('Round Trip')

    # Button to trigger search
    search_clicked = st.button('Search')

    # Display note below the button if clicked
    if search_clicked:
        note = "<p style='font-family: monospace; font-size: small;'>3h added to plane travel time for getting to/from the airport and waiting times</p>"
        st.markdown(note, unsafe_allow_html=True)

#Columns width based on search button state
if not search_clicked:
    col1, col2 = st.columns([0.95, 0.05])  # Map takes most of the screen before search
else:
    col1, col2 = st.columns([2, 1])  # Map takes 2/3 after search is clicked

with col2:

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
                plane_co2 = travel_info['Plane_CO2_kg']

            train_duration = travel_info['Duration_train']
            train_co2 = travel_info['Train_CO2_kg']

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

            # Create the duration bar chart
            duration_chart = alt.Chart(duration_data).mark_bar().encode(
                y=alt.Y('Mode', title=None, axis=alt.Axis(labelFontSize=13)),
                x=alt.X('Duration_minutes:Q', title='Duration (hours)',
                        axis=alt.Axis(values=tick_values, labelExpr=labelExpr)),
                color=alt.Color('Mode', legend=None).scale(scheme="redyellowgreen"),
                tooltip=[alt.Tooltip('Duration', title='Duration'), alt.Tooltip('Mode', title='Mode')]
            ).properties(
                title='Travel Duration'
            )

            # Add data labels to the duration chart
            duration_labels = alt.Chart(duration_data).mark_text(
                align='right',
                baseline='middle',
                color='black',
                dx= -5
            ).encode(
                y=alt.Y('Mode', title=None),
                x=alt.X('Duration_minutes:Q'),
                text=alt.Text('Duration'),
                tooltip = alt.value('')
            )

            # Combine bar chart with labels
            duration_combined_chart = duration_chart + duration_labels
            st.altair_chart(duration_combined_chart, use_container_width=True)

            # Create emissions bar chart
            emissions_data = pd.DataFrame({
                'Mode': ['🚂', '✈️'],
                'CO2_kg': [train_co2, plane_co2]
            })
            # alt.ColorScheme('basic', ['#f00', '#0f0', '#00f', '#ff0', '#f0f', '#0ff'])
            emissions_chart = alt.Chart(emissions_data).mark_bar().encode(
                x=alt.X('CO2_kg', title='CO2 (kg)'),
                y=alt.Y('Mode', title=None, axis=alt.Axis(labelFontSize=13)),
                color=alt.Color('Mode', legend=None).scale(scheme="redyellowgreen")
            ).properties(
                title='CO2 Emissions'
            )

            # Add data labels to the emissions chart
            emissions_labels = alt.Chart(emissions_data).mark_text(
                align='right',
                baseline='middle',
                color='black',
                dx= -5
            ).encode(
                y=alt.Y('Mode', title=None),
                x=alt.X('CO2_kg'),
                text=alt.Text('CO2_kg:Q', format='.1f'),
                tooltip = alt.value('')
            )

            # Combine bar chart with labels
            emissions_combined_chart = emissions_chart + emissions_labels
            st.altair_chart(emissions_combined_chart, use_container_width=True)

        else:
            st.write(f"No travel data available for the route from {from_city} to {to_city}.")
    elif search_clicked:
        st.write('Please select both "From" and "To" cities.')

with col1:
    # If search button is not clicked, display the base map with all cities
    if not search_clicked:
        map_with_all_cities = create_base_map()
        st.altair_chart(map_with_all_cities, use_container_width=True)

    # If search button is clicked and both cities are selected, highlight the "From" and "To" cities
    if search_clicked and from_city and to_city:
        # Filter the DataFrame for the selected cities
        filtered_points = coordinates_data[coordinates_data['city'].isin([from_city, to_city])]

        from_city_data = filtered_points[filtered_points['city'] == from_city].iloc[0]
        to_city_data = filtered_points[filtered_points['city'] == to_city].iloc[0]

        # Add Plane_CO2_kg and Train_CO2_kg to to_city_data for the tooltip
        to_city_data['Plane_CO2_kg'] = round(plane_co2)
        to_city_data['Train_CO2_kg'] = round(train_co2)

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
            color='#9C27B0',
            size=200
        ).project(
            'mercator',
            scale=projection_params['scale'],
            center=projection_params['center'],
            rotate=[5, 0, 0]
        ).encode(
            longitude='longitude:Q',
            latitude='latitude:Q',
            tooltip=['city:N']
        )

        if 'Plane_CO2_kg' in to_city_data and not pd.isna(to_city_data['Plane_CO2_kg']):
            to_point_plane = alt.Chart(to_city_df).mark_circle(
                color='red',
                size=plane_co2*10
            ).project(
                'mercator',
                scale=projection_params['scale'],
                center=projection_params['center'],
                rotate=[5, 0, 0]
            ).encode(
                longitude='longitude:Q',
                latitude='latitude:Q',
                tooltip=['city:N', 'Plane_CO2_kg:Q']
            )
        else:
            to_point_plane = alt.Chart(pd.DataFrame()).mark_circle(size=0)  #Invisible point to handle missing data

        to_point_train = alt.Chart(to_city_df).mark_circle(
            color='green',
            size=train_co2*10
        ).project(
            'mercator',
            scale=projection_params['scale'],
            center=projection_params['center'],
            rotate=[5, 0, 0]
        ).encode(
            longitude='longitude:Q',
            latitude='latitude:Q',
            tooltip=['city:N', 'Train_CO2_kg:Q']
        )
        # draw train route on the map
        def create_route_layer(geojson_data):
            route_layer = alt.Chart(alt.Data(values=geojson_data['features'])).mark_geoshape(
                fill=None,
                stroke='blue',
                strokeWidth=1
            ).project(
                'mercator',
                scale=projection_params['scale'],
                center=projection_params['center'],
                rotate=[5, 0, 0]
            ).encode(
                tooltip=alt.value(f"Train: {from_city} to {to_city}")
            )
            return route_layer

        geojson_data = load_geojson_route(from_city, to_city)
        if geojson_data:
            route_layer = create_route_layer(geojson_data)

        # Combine the map with highlighted cities
        map_with_selected_cities = base + from_point + to_point_plane + to_point_train + route_layer

        # Display the map
        st.altair_chart(map_with_selected_cities, use_container_width=True)

expander = st.expander("How emissions are calculated?")
expander.write('''
    Note on methodology, calculations, limitations
''')

# with tab2:
#     # Create two columns for layout
#     col1, col2 = st.columns([1, 2])
#
#     with col1:
#         # Input fields for "From" and "To" with selectbox and placeholder
#         from_city = st.selectbox('From', coordinates_data['city'].unique(), index=None,
#                                  placeholder="Select a departure city", key="from_tab2")
#
#         # Dynamically update the 'To' options based on the selected 'From' city
#         to_city = st.selectbox('To', [city for city in coordinates_data['city'].unique() if city != from_city],
#                                index=None, placeholder="Select a destination city", key="to_tab2")
#
#         col_left, col_right = st.columns([0.4, 0.5], gap = 'medium', vertical_alignment="bottom")
#         #Number of people selectbox
#         with col_left:
#             num_people = st.number_input('People:', min_value=1, max_value=10, value=1, key='num_people_tab2')
#         #Round Trip toggle
#         with col_right:
#             round_trip = st.toggle('Round Trip', key='round_trip_tab2')
#
#         # Button to trigger search
#         search_clicked = st.button('Search', key='tab2_search')
#
#         # Travel Data
#         st.subheader('Travel Plan Details')
#         if search_clicked and from_city and to_city:
#             route = normalize_city_pair(from_city, to_city)
#             travel_details = trip_data[trip_data['route'] == route]
#             note = "<p style='font-family: monospace; font-size: small;'> Please note that duration time for a plane includes trip to/from airport and waiting time.</p>"
#             st.markdown(note, unsafe_allow_html=True)
#             if not travel_details.empty:
#                 travel_info = travel_details.iloc[0]
#
#                 # Adjust CO2 emissions based on the number of people
#                 travel_info['Train_CO2_kg'] *= num_people
#                 travel_info['Plane_CO2_kg'] *= num_people
#
#                 # Double the values if round trip is selected
#                 if round_trip:
#                     travel_info['Duration_train'] = double_duration(travel_info['Duration_train'])
#                     travel_info['Duration_plane'] = double_duration(travel_info['Duration_plane'])
#                     travel_info['Train_CO2_kg'] *= 2
#                     travel_info['Plane_CO2_kg'] *= 2
#
#                 # Convert duration to minutes
#                 def duration_to_min(duration_str):
#                     hours, minutes = map(int, duration_str.split(':'))
#                     return hours * 60 + minutes
#
#                 # Prepare the data for the duration bar chart (in this version plane duration includes trip to/from airport and waiting time)
#                 duration_data = pd.DataFrame({
#                     'Mode': ['Train', 'Plane'],
#                     'Duration': [
#                         duration_to_min(travel_info['Duration_train']),
#                         duration_to_min(travel_info['Duration_plane_total'])
#                     ],
#                     'Duration_str': [travel_info['Duration_train'], travel_info['Duration_plane_total']]
#                 })
#
#                 # Create the duration bar chart
#                 # duration_chart = alt.Chart(duration_data).mark_bar().encode(
#                 #     y=alt.Y('Mode', title=None),
#                 #     x=alt.X('Duration:Q', title='Duration (hours)',
#                 #         axis=alt.Axis(labelExpr='round(datum.value / 60)')),
#                 #     color=alt.Color('Mode', legend=None).scale(scheme="redyellowgreen"),
#                 #     tooltip=[alt.Tooltip('Mode', title='Mode'), alt.Tooltip('Duration_str', title='Duration')]
#                 # ).properties(
#                 #     title='Travel Duration'
#                 # )
#                 # st.altair_chart(duration_chart, use_container_width=True)
#
#                 # # Add the text note below the chart
#                 # note = """
#                 # <p style='font-family: monospace; font-size: small; margin: 0; padding: 0;'>
#                 #     Please note that duration time for a plane includes trip to/from airport and waiting time.
#                 # </p>
#                 # """
#                 # st.markdown(note, unsafe_allow_html=True)
#
#                 # Create emissions bar chart
#                 emissions_data = pd.DataFrame({
#                     'Mode': ['Train', 'Plane'],
#                     'CO2_kg': [travel_info['Train_CO2_kg'], travel_info['Plane_CO2_kg']]
#                 })
#
#                 # Combine duration and emissions data
#                 combined_data = pd.concat([
#                     duration_data.melt(id_vars='Mode', value_vars=['Duration']).rename(
#                         columns={'value': 'Value', 'variable': 'Metric'}),
#                     emissions_data.melt(id_vars='Mode', value_vars=['CO2_kg']).rename(
#                         columns={'value': 'Value', 'variable': 'Metric'})
#                 ])
#
#                 # Convert values to hours and tons
#                 # combined_data['Value'] = combined_data.apply(
#                 #     lambda row: round(row['Value'] / 60, 2) if row['Metric'] == 'Duration' else round(
#                 #         row['Value'] * 1000, 0),
#                 #     axis=1
#                 # )
#
#                 # Adjust values for butterfly chart: CO2 emissions as negative
#                 combined_data['Adjusted_Value'] = combined_data.apply(
#                     lambda row: -row['Value'] if row['Metric'] == 'CO2_kg' else row['Value'], axis=1)
#
#                 # Define max values for scaling
#                 max_value = max(combined_data['Adjusted_Value'].abs())
#
#                 # Create the butterfly (back-to-back) chart
#                 butterfly_chart = alt.Chart(combined_data).mark_bar().encode(
#                     y=alt.Y('Mode:N', title=None, axis=alt.Axis(grid=False)),
#                     x=alt.X('Adjusted_Value:Q', title='Value', axis=alt.Axis(
#                         grid=False,
#                         format='.0f',
#                         labelExpr = "datum.value < 0 ? -datum.value : datum.value"  # Custom label formatting
#                     ), scale=alt.Scale(domain=[-max_value, max_value])),
#                     color=alt.Color('Metric:N',
#                                     scale=alt.Scale(domain=['Duration', 'CO2_kg'], range=['#1f77b4', '#ff7f0e']),
#                                     legend=None),
#                     tooltip=[
#                         alt.Tooltip('Metric:N', title='Metric'),
#                         alt.Tooltip('Value:Q', title='Value', format='.0f')
#                     ]
#                 ).properties(
#                     title='Travel Duration and CO2 Emissions by Mode'
#                 ).configure_axis(
#                     grid=False
#                 ).configure_view(
#                     strokeWidth=0
#                 )
#
#                 # Display chart using Streamlit
#                 st.altair_chart(butterfly_chart, use_container_width=True)
#
#                 # alt.ColorScheme('basic', ['#f00', '#0f0', '#00f', '#ff0', '#f0f', '#0ff'])
#                 # emissions_chart = alt.Chart(emissions_data).mark_bar().encode(
#                 #     x=alt.X('CO2_kg', title='CO2 (kg)'),
#                 #     y=alt.Y('Mode', title=None),
#                 #     color=alt.Color('Mode', legend=None).scale(scheme="redyellowgreen")
#                 # ).properties(
#                 #     title='CO2 Emissions'
#                 # )
#                 # st.altair_chart(emissions_chart, use_container_width=True)
#             else:
#                 st.write(f"No travel data available for the route from {from_city} to {to_city}.")
#         elif search_clicked:
#             st.write('Please select both "From" and "To" cities.')
#
#     with col2:
#         # Display the base map with all cities
#         map_with_cities = create_base_map()
#
#         # If search button is clicked and both cities are selected, highlight the "From" and "To" cities
#         if search_clicked and from_city and to_city:
#             # Filter the DataFrame for the selected cities
#             from_city_data = coordinates_data[coordinates_data['city'] == from_city].iloc[0]
#             to_city_data = coordinates_data[coordinates_data['city'] == to_city].iloc[0]
#
#             # Add the Plane_CO2_kg and Train_CO2_kg to to_city_data for the tooltip
#             to_city_data = to_city_data.append(pd.Series({
#                 'Plane_CO2_kg': travel_info['Plane_CO2_kg'],
#                 'Train_CO2_kg': travel_info['Train_CO2_kg']
#             }))
#
#             # Highlight the "From" and "To" cities
#             from_point = alt.Chart(pd.DataFrame([from_city_data])).mark_circle(color='green', size=200).encode(
#                 longitude='longitude:Q',
#                 latitude='latitude:Q',
#                 tooltip=['city:N']
#             )
#
#             to_point_plane = alt.Chart(pd.DataFrame([to_city_data])).mark_circle(color='red', size=travel_info['Plane_CO2_kg']*10).encode(
#                 longitude='longitude:Q',
#                 latitude='latitude:Q',
#                 tooltip=['city:N', 'Plane_CO2_kg:Q']
#             )
#
#             to_point_train = alt.Chart(pd.DataFrame([to_city_data])).mark_circle(color='green', size=travel_info['Train_CO2_kg']*10).encode(
#                 longitude='longitude:Q',
#                 latitude='latitude:Q',
#                 tooltip=['city:N', 'Train_CO2_kg:Q']
#             )
#
#             # Combine the map with highlighted cities
#             map_with_cities += from_point + to_point_plane + to_point_train
#
#         # Display the map
#         st.altair_chart(map_with_cities, use_container_width=True)
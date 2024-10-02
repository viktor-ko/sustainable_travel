# Sustainable Travel Planner

This project is a web application that helps users compare the carbon emissions and travel duration between train and plane for their trips. The application is built using [Streamlit](https://streamlit.io/), data visualisations are made in [Vega-Altair](https://altair-viz.github.io/).

## Features

- Compare carbon emissions and travel duration between train and plane.
- Visualize travel routes on a map.
- Support for round trips and multiple passengers.
- Dynamic updates based on selected cities.

## Scope and Limitations

Route planning is limited to 29 European cities:
-	Amsterdam
-	Berlin
-	Bern
-	Bilbao
-	Bratislava
-	Brussels
-	Bucharest
-	Budapest
-	Copenhagen
-	Dresden
-	Istanbul
-	Lisbon
-	Ljubljana
-	London
-	Luxembourg City
-	Madrid
-	Munich
-	Oslo
-	Paris
-	Prague
-	Riga
-	Rome
-	Sofia
-	Stockholm
-	Tallinn
-	Vienna
-	Vilnius
-	Warsaw
-	Zagreb

## Project Structure

- `streamlit_app.py`: Main application file.
- `data_gathering.ipynb`: Jupyter notebook with scripts for data processing
- `data/`: Directory containing the CSV files for trips and coordinates data.
- `geojson_files/`: Directory containing GeoJSON files for routes between cities.

## Data

- `data/trips_data.csv`: Contains trip data, including city pairs, travel durations, and CO2 emissions.
- `data/coordinates.csv`: Contains coordinates data for cities.

### Data Flow

1. **Loading Data**:
   - The trip and coordinates data are loaded from CSV files into Pandas DataFrames.
   - Column names are stripped of any leading or trailing spaces.

2. **Normalizing Data**:
   - City pairs in the trip data are normalized using the `normalize_city_pair` function.

3. **Creating Maps**:
   - The base map is created using the `create_base_map` function, which includes city points.
   - GeoJSON routes are loaded using the `load_geojson_route` function to draw routes on the map.

4. **User Interaction**:
   - Users select departure and destination cities, number of people, and whether the trip is a round trip.
   - Travel details are displayed, including duration and CO2 emissions for both train and plane.
   - Dynamic charts are created using Vega-Altair to visualize travel duration and CO2 emissions.

5. **Dynamic Updates**:
   - The app dynamically updates the 'To' city options based on the selected 'From' city.
   - Travel details and maps are updated based on user input.

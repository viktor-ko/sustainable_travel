# Sustainable Travel Planner
https://github.com/user-attachments/assets/63a85799-c62c-4095-b6a0-bca5c5cd7959

This project is part of a [Cartography MSc.](https://cartographymaster.eu/) thesis "Maps for sustainable business travel advice", conducted by Viktor Kochkin at the University of Twente (October 2024).

Sustainable Travel Planner helps users compare train and plane carbon emissions and travel duration. The application is built using [Streamlit](https://streamlit.io/), map and charts are created in [Vega-Altair](https://altair-viz.github.io/).

For user testing, three versions of the sustainable travel planner were created with different data visualisations:
- [Version 1](https://sustainable-travel.streamlit.app/ver1)
- [Version 2](https://sustainable-travel.streamlit.app/ver2)
- [Version 3](https://sustainable-travel.streamlit.app/ver3)

## Features

- Compare carbon emissions and travel duration between train and plane.
- Visualize travel routes on a map.
- Support for round trips and multiple passengers.
- Dynamic updates based on selected cities.

## Project Structure
```sh
└── sustainable_travel/
    ├── data
    │   ├── coordinates.csv #Coordinates of 29 cities for the map
    │   └── trips_data.csv  #Plane and train travel time and emissions data for 406 city pairs
    ├── geojson_files
    │   ├── lines #Train routes lines
    │   └── points #Train routes transfer points
    ├── pages
    │   ├── ver1.py    #Prototype version 1
    │   ├── ver2.py    #Prototype version 2
    │   └── ver3.py    #Prototype version 3
    ├── data_gathering.ipynb   #Data preparation scripts in jupyter notebook
    ├── streamlit_app.py    #Main Streamlit page
    └── utils.py        #Functions used across all prototype versions
```

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

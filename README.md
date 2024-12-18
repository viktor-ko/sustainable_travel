# Sustainable Travel Planner
https://github.com/user-attachments/assets/63a85799-c62c-4095-b6a0-bca5c5cd7959

[Sustainable Travel Planner](https://sustainable-travel.streamlit.app/) helps users compare train and plane carbon emissions and travel duration. The application is built using [Streamlit](https://streamlit.io/), map and charts are created in [Vega-Altair](https://altair-viz.github.io/).

Three versions of the sustainable travel planner with different data visualisations were created for user testing:
- [Version 1](https://sustainable-travel.streamlit.app/ver1): horizontal bar charts
- [Version 2](https://sustainable-travel.streamlit.app/ver2): vertical bar charts
- [Version 3](https://sustainable-travel.streamlit.app/ver3): bullet chart and proportion area circles

This tool is part of a [Cartography MSc.](https://cartographymaster.eu/) thesis "[Maps for sustainable business travel advice](https://cartographymaster.eu/wp-content/theses/2024_Kochkin_Thesis.pdf)" ([Poster](https://cartographymaster.eu/wp-content/theses/2024_Kochkin_Poster.pdf), [Presentation](https://cartographymaster.eu/wp-content/theses/2024_Kochkin_Presentation.pdf)), conducted by Viktor Kochkin at the [ITC, University of Twente](https://www.itc.nl).

## Features

- Compare carbon emissions and travel duration between train and plane.
- Visualize travel routes on a map.
- Support for round trips and multiple passengers.
- Dynamic updates based on selected cities.

## Project Structure
```sh
└── sustainable_travel/
    ├── streamlit_app.py    #Streamlit app main script
    ├── utils.py        #Functions for data loading, normalization, and map creation
    ├── data_gathering.ipynb   #Data preparation scripts in jupyter notebook
    ├── data
    │   ├── coordinates.csv #Coordinates of 29 cities for the map
    │   └── trips_data.csv  #Plane and train travel time and emissions data for 406 city pairs
    ├── geojson_files
    │   ├── lines  #Train routes polylines
    │   └── points #Train routes transfer points
    └── pages # Different prototype versions for user testing
        ├── ver1.py
        ├── ver2.py
        └── ver3.py
```

## Scope and Limitations

<details>
<summary>Route planning is limited to 29 European cities:</summary>
-	Amsterdam <br>
-	Bern <br>
-	Bilbao <br>
-	Bratislava <br>
-	Brussels <br>
-	Bucharest <br>
-	Budapest <br>
-	Copenhagen <br>
-	Dresden <br>
-	Istanbul <br>
-	Lisbon <br>
-	Ljubljana <br>
-	London <br>
-	Luxembourg City <br>
-	Madrid <br>
-	Munich <br>
-	Oslo <br>
-	Paris <br>
-	Prague <br>
-	Riga <br>
-	Rome <br>
-	Sofia <br>
-	Stockholm <br>
-	Tallinn <br>
-	Vienna <br>
-	Vilnius <br>
-	Warsaw <br>
-	Zagreb <br>
</details>




## Data Flow

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

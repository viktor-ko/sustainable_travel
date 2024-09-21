import streamlit as st
import pandas as pd
import altair as alt
import numpy as np
import os
import json

# Set the app layout to "wide" mode
st.set_page_config(layout="wide")

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

st.title("Ver 2")
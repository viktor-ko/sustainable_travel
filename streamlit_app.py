# Routing Page
import streamlit as st
import os
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
st.write(os.getcwd())
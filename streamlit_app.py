# streamlit_app.py - Main entry point
import streamlit as st
from page import app_mixing_p_and_id  # we rename import safely for Python

st.set_page_config(layout="wide", page_title="Rig Simulation")

# Sidebar manual menu
menu = ["Home", "Mixing Area"]
choice = st.sidebar.selectbox("Navigation", menu)

if choice == "Home":
    st.title("Rig Simulation Dashboard")
    st.write("Welcome to the Rig Simulation.")
    st.write("Use the sidebar to navigate between pages.")
elif choice == "Mixing Area":
    # Run your mixing page code
    app_mixing_p_and_id.run()

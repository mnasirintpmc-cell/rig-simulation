# streamlit_app.py
import streamlit as st
import importlib.util
import sys
import os

st.set_page_config(layout="wide", page_title="Rig Simulation")

# ===================== MANUAL IMPORT OF FILE WITH & =====================
page_file = os.path.join("page", "app_mixing_p&id.py")
spec = importlib.util.spec_from_file_location("app_mixing", page_file)
app_mixing = importlib.util.module_from_spec(spec)
sys.modules["app_mixing"] = app_mixing
spec.loader.exec_module(app_mixing)

# ===================== SIDEBAR NAVIGATION =====================
menu = ["Home", "Mixing Area"]
choice = st.sidebar.selectbox("Navigation", menu)

if choice == "Home":
    st.title("Rig Simulation Dashboard")
    st.write("Welcome to the Rig Simulation.")
    st.write("Use the sidebar to navigate between pages.")
elif choice == "Mixing Area":
    app_mixing.run()  # run the mixing page

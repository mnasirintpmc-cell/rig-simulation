# streamlit_app.py
import streamlit as st
import importlib.util
import sys
import os

st.set_page_config(layout="wide", page_title="Rig Simulation")

# ===================== LOAD PAGE =====================
page_file = os.path.join("page", "app_mixing_p&id.py")
spec = importlib.util.spec_from_file_location("app_mixing", page_file)
app_mixing = importlib.util.module_from_spec(spec)
sys.modules["app_mixing"] = app_mixing
spec.loader.exec_module(app_mixing)

# ===================== SIDEBAR MENU =====================
menu = ["Home", "Mixing Area"]
choice = st.sidebar.selectbox("Navigation", menu)

# Initialize session state for valves
if "valve_states" not in st.session_state:
    # Load valves from JSON
    import json
    with open(os.path.join("data","valves_mixing.json")) as f:
        valves_json = json.load(f)
    st.session_state.valve_states = {tag: False for tag in valves_json}

if choice == "Home":
    st.title("Rig Simulation Dashboard")
    st.write("Welcome to the Rig Simulation.")
    st.write("Select 'Mixing Area' from the sidebar to control valves.")

elif choice == "Mixing Area":
    # ===================== VALVE CONTROLS =====================
    st.sidebar.header("Valve Controls")
    for v_tag in st.session_state.valve_states:
        state = st.session_state.valve_states[v_tag]
        label = f"{'OPEN' if state else 'CLOSED'} {v_tag}"
        if st.sidebar.button(label, key=f"valve_{v_tag}"):
            st.session_state.valve_states[v_tag] = not state
            st.experimental_rerun()  # Rerun safely from main app

    # ===================== RENDER PAGE =====================
    app_mixing.run(st.session_state.valve_states)

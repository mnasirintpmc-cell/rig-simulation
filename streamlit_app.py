import streamlit as st
from page import app_mixing_p_and_id

st.set_page_config(
    page_title="Rig Simulation Dashboard",
    layout="wide",
)


# ---- INIT SESSION ----
if "valve_states" not in st.session_state:
    st.session_state.valve_states = {}


# ---- SIDEBAR (VALVE CONTROL) ----
st.sidebar.title("Valve Control Panel")

# Import valve names from JSON
import json
with open("data/valves_mixing.json") as f:
    valves_json = json.load(f)

for v in valves_json.keys():
    if v not in st.session_state.valve_states:
        st.session_state.valve_states[v] = False

    st.session_state.valve_states[v] = st.sidebar.toggle(
        v,
        value=st.session_state.valve_states[v]
    )


# ---- MAIN PAGE (P&ID VISUAL OUTPUT) ----
app_mixing_p_and_id.run(st.session_state.valve_states)

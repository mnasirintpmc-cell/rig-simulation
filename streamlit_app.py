import streamlit as st
import pandas as pd
import json
import os
from PIL import Image, ImageDraw

st.set_page_config("Rig Simulation", "🏭", layout="wide")

# =========================================================
# PANELS
# =========================================================
PANELS = {
    "mixing": {
        "name": "Gas Mixing Panel",
        "valves": "data/valves_mixing.json",
        "pipes": "data/pipes_mixing.json",
        "image": "assets/p&id_mixing.png",
    },
    "supply": {
        "name": "Pressure Supply Panel",
        "valves": "data/valves_pressure_in.json",
        "pipes": "data/pipes_pressure_in.json",
        "image": "assets/p&id_pressure_in.png",
    },
    "dgs": {
        "name": "DGS Panel",
        "valves": "data/valves_dgs.json",
        "pipes": "data/pipes_dgs.json",
        "image": "assets/p&id_dgs.png",
    },
    "return": {
        "name": "Pressure Return Panel",
        "valves": "data/valves_pressure_return.json",
        "pipes": "data/pipes_pressure_return.json",
        "image": "assets/p&id_pressure_return.png",
    },
    "seal": {
        "name": "Separation Seal Panel",
        "valves": "data/valves_separation_seal.json",
        "pipes": "data/pipes_separation_seal.json",
        "image": "assets/p&id_separation_seal.png",
    },
}

# =========================================================
# SESSION STATE
# =========================================================
if "csv" not in st.session_state:
    st.session_state.csv = None
if "csv_loaded" not in st.session_state:
    st.session_state.csv_loaded = False
if "step" not in st.session_state:
    st.session_state.step = 0
if "panel" not in st.session_state:
    st.session_state.panel = "mixing"
if "valve_states" not in st.session_state:
    st.session_state.valve_states = {}
if "pressure_state" not in st.session_state:
    st.session_state.pressure_state = {
        "cell": False,
        "nde": False,
        "de": False,
        "bp_nde": False,
        "bp_de": False,
    }

# =========================================================
# HELPERS
# =========================================================
def load_json(path):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}

def csv_val(row, key):
    return float(row[key]) if key in row else 0.0

# =========================================================
# APPLY STEP (FINAL AUTHORITATIVE LOGIC)
# =========================================================
def apply_step(row):
    vs = st.session_state.valve_states
    vs.clear()

    # -------------------------------
    # CELL PRESSURE SELECTION
    # -------------------------------
    cell_p = csv_val(row, "TST_CellPresDemand")

    v108 = v106 = v107 = False
    if cell_p > 0:
        if cell_p <= 10:
            v108 = True
        elif cell_p <= 100:
            v106 = True
        else:
            v107 = True

    if v108: vs["V-108"] = True
    if v106: vs["V-106"] = True
    if v107:

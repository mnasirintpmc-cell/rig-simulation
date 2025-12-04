# mixing_page.py - Plug-and-play Mixing System
import streamlit as st
from PIL import Image, ImageDraw
import json
import os

st.set_page_config(layout="wide", page_title="Rig Simulation - Mixing")

# ===================== DYNAMIC FILE FINDER =====================
def find_file(filename, folders=["assets", "data", "."]):
    for f in folders:
        path = os.path.join(f, filename)
        if os.path.exists(path):
            return path
    return None

# ===================== FILE PATHS =====================
SYSTEM_NAME = "Mixing Area"
PRESSURE_SOURCES = []  # Optional: list of pipe tags with pressure, e.g., ["P1", "P5"]

PID_FILE = find_file("p&id_mixing.png")
VALVES_FILE = find_file("valves_mixing.json", ["data", "."])
PIPES_FILE = find_file("pipes_mixing.json", ["data", "."])

# Check files
if not all([PID_FILE, VALVES_FILE, PIPES_FILE]):
    st.error("❌ Missing required files! Check assets/data folders.")
    st.stop()

# ===================== LOAD JSON =====================
def load_json(file):
    try:
        with open(file) as f:
            data = json.load(f)
            return data
    except Exception as e:
        st.error(f"Error loading {file}: {e}")
        return {} if "valves" in file else []

valves = load_json(VALVES_FILE)
pipes = load_json(PIPES_FILE)

# ===================== SESSION STATE =====================
if "valve_states" not in st.session_state:
    st.session_state.valve_states = {tag: False for tag in valves}
if "selected_pipe" not in st.session_state:
    st.session_state.selected_pipe = None

# =================

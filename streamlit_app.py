# streamlit_app.py
# FULL RIG SIMULATION WITH P&ID + CSV SEQUENCE

import streamlit as st
import pandas as pd
import json
import os
import time
from PIL import Image, ImageDraw

# ===============================
# PAGE CONFIG
# ===============================
st.set_page_config(
    page_title="Rig Simulation Platform",
    page_icon="🏭",
    layout="wide"
)

# ===============================
# SESSION STATE
# ===============================
if "current_system" not in st.session_state:
    st.session_state.current_system = "home"

if "valve_states" not in st.session_state:
    st.session_state.valve_states = {}

if "df" not in st.session_state:
    st.session_state.df = None
if "step" not in st.session_state:
    st.session_state.step = 0
if "playing" not in st.session_state:
    st.session_state.playing = False
if "last_tick" not in st.session_state:
    st.session_state.last_tick = time.time()

# ===============================
# SYSTEM FILES (RESTORED)
# ===============================
SYSTEMS = {
    "mixing": {
        "name": "Mixing System",
        "valves": "data/valves_mixing.json",
        "pipes": "data/pipes_mixing.json",
        "image": "assets/p&id_mixing.png"
    },
    "supply": {
        "name": "Pressure Supply",
        "valves": "data/valves_pressure_in.json",
        "pipes": "data/pipes_pressure_in.json",
        "image": "assets/p&id_pressure_in.png"
    },
    "dgs": {
        "name": "DGS System",
        "valves": "data/valves_dgs.json",
        "pipes": "data/pipes_dgs.json",
        "image": "assets/p&id_dgs.png"
    },
    "return": {
        "name": "Pressure Return",
        "valves": "data/valves_pressure_return.json",
        "pipes": "data/pipes_pressure_return.json",
        "image": "assets/p&id_pressure_return.png"
    },
    "seal": {
        "name": "Separation Seal",
        "valves": "data/valves_separation_seal.json",
        "pipes": "data/pipes_separation_seal.json",
        "image": "assets/p&id_separation_seal.png"
    }
}

# ===============================
# CSV → VALVE MAP
# ===============================
CSV_VALVE_MAP = {
    "TST_CellPresDemand": "V_CELL",
    "TST_InterPresDemand": "V_INTER",
    "TST_InterBPDemand_DE": "V_BP_DE",
    "TST_InterBPDemand_NDE": "V_BP_NDE",
    "TST_GasInjectionDemand": "V_GAS",
}

# ===============================
# LOAD FUNCTIONS
# ===============================
def load_json(path, default):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return default


def load_csv(upload):
    return pd.read_csv(upload, sep=";")


def advance_step():
    df = st.session_state.df
    step = st.session_state.step

    duration = float(df.iloc[step]["TST_StepDuration"])
    elapsed = time.time() - st.session_state.last_tick

    if elapsed >= max(duration, 0.1):
        st.session_state.step += 1
        st.session_state.last_tick = time.time()
        if st.session_state.step >= len(df):
            st.session_state.step = len(df) - 1
            st.session_state.playing = False


def apply_csv_to_valves(valves, row):
    for csv_col, valve in CSV_VALVE_MAP.items():
        if valve in valves:
            st.session_state.valve_states[valve] = float(row[csv_col]) > 0


def get_pipe_active(pipe_idx, valves, pipes):
    pipe_num = pipe_idx + 1
    for v, data in valves.items():
        if st.session_state.valve_states.get(v, False):
            if pipe_num in data.get("connected_pipes", []):
                return True
    return False


def render_pid(image_path, valves, pipes):
    if not os.path.exists(image_path):
        img = Image.new("RGB", (900, 600), (40, 40, 60))
    else:
        img = Image.open(image_path).convert("RGBA")

    draw = ImageDraw.Draw(img)

    for i, pipe in enumerate(pipes):
        active = get_pipe_active(i, valves, pipes)
        color = (0, 255, 0) if active else (60, 60, 90)
        width = 6 if active else 4
        draw.line(
            [(pipe["x1"], pipe["y1"]), (pipe["x2"], pipe["y2"])],
            fill=color,
            width=width
        )

    for tag, v in valves.items():
        x, y = v["x"], v["y"]
        open_ = st.session_state.valve_states.get(tag, False)
        color = (0, 255, 0) if open_ else (255, 0, 0)
        draw.ellipse([x-7, y-7, x+7, y+7], fill=color, outline="white", width=2)
        draw.text((x+10, y-10), tag, fill="white")

    return img.convert("RGB")

# ===============================
# SIDEBAR
# ===============================
with st.sidebar:
    st.title("🏭 Rig Control")

    if st.button("🏠 Home"):
        st.session_state.current_system = "home"

    st.markdown("---")
    csv = st.file_uploader("Upload CSV", type=["csv"])
    if csv:
        st.session_state.df = load_csv(csv)
        st.session_state.step = 0
        st.session_state.last_tick = time.time()
        st.success("CSV loaded")

    if st.session_state.df is not None:
        if st.button("▶ Play" if not st.session_state.playing else "⏸ Pause"):
            st.session_state.playing = not st.session_state.playing
            st.session_state.last_tick = time.time()

# ===============================
# HOME
# ===============================
if st.session_state.current_system == "home":
    st.title("🏭 Rig Simulation – Home")
    cols = st.columns(len(SYSTEMS))
    for i, (k, v) in enumerate(SYSTEMS.items()):
        with cols[i]:
            if st.button(v["name"], use_container_width=True):
                st.session_state.current_system = k
    st.stop()

# ===============================
# SYSTEM PAGE
# ===============================
system = st.session_state.current_system
cfg = SYSTEMS[system]

valves = load_json(cfg["valves"], {})
pipes = load_json(cfg["pipes"], [])

for v in valves:
    st.session_state.valve_states.setdefault(v, False)

if st.session_state.df is not None:
    if st.session_state.playing:
        advance_step()
        time.sleep(0.05)
        st.rerun()

    row = st.session_state.df.iloc[st.session_state.step]
    apply_csv_to_valves(valves, row)

st.title(cfg["name"])
img = render_pid(cfg["image"], valves, pipes)
st.image(img, use_container_width=True, caption="Green = Flow | Red = Closed Valve")

with st.expander("🔍 CSV Step Data"):
    if st.session_state.df is not None:
        st.write(row)

import streamlit as st
import pandas as pd
import json
import os
import time
from PIL import Image, ImageDraw

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="Rig Simulation Platform",
    page_icon="🏭",
    layout="wide"
)

# =========================================================
# SESSION STATE
# =========================================================
if "page" not in st.session_state:
    st.session_state.page = "home"

if "valve_states" not in st.session_state:
    st.session_state.valve_states = {}

if "csv" not in st.session_state:
    st.session_state.csv = None

if "step" not in st.session_state:
    st.session_state.step = 0

if "playing" not in st.session_state:
    st.session_state.playing = False

if "last_tick" not in st.session_state:
    st.session_state.last_tick = time.time()

# =========================================================
# SYSTEM DEFINITIONS
# =========================================================
SYSTEMS = {
    "mixing": {
        "name": "🔧 Mixing System",
        "valves": "data/valves_mixing.json",
        "pipes": "data/pipes_mixing.json",
        "image": "assets/p&id_mixing.png",
    },
    "supply": {
        "name": "⚡ Pressure Supply",
        "valves": "data/valves_pressure_in.json",
        "pipes": "data/pipes_pressure_in.json",
        "image": "assets/p&id_pressure_in.png",
    },
    "dgs": {
        "name": "🎮 DGS System",
        "valves": "data/valves_dgs.json",
        "pipes": "data/pipes_dgs.json",
        "image": "assets/p&id_dgs.png",
    },
    "return": {
        "name": "🔄 Pressure Return",
        "valves": "data/valves_pressure_return.json",
        "pipes": "data/pipes_pressure_return.json",
        "image": "assets/p&id_pressure_return.png",
    },
    "seal": {
        "name": "🔒 Separation Seal",
        "valves": "data/valves_separation_seal.json",
        "pipes": "data/pipes_separation_seal.json",
        "image": "assets/p&id_separation_seal.png",
    },
}

# =========================================================
# VALVE ALIGNMENT (NUMERIC TAGS)
# =========================================================
VALVE_ROLE_MAP = {
    "CELL_PRESSURE": "101",
    "INTER_PRESSURE": "201",
    "BP_DE": "301",
    "BP_NDE": "302",
    "GAS_INJECTION": "401",
}

CSV_ROLE_MAP = {
    "TST_CellPresDemand": "CELL_PRESSURE",
    "TST_InterPresDemand": "INTER_PRESSURE",
    "TST_InterBPDemand_DE": "BP_DE",
    "TST_InterBPDemand_NDE": "BP_NDE",
    "TST_GasInjectionDemand": "GAS_INJECTION",
}

# =========================================================
# UTILITY FUNCTIONS
# =========================================================
def load_json(path):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {} if "valves" in path else []


def load_csv(upload):
    return pd.read_csv(upload, sep=";")


def advance_step():
    df = st.session_state.csv
    duration = float(df.iloc[st.session_state.step]["TST_StepDuration"])
    elapsed = time.time() - st.session_state.last_tick

    if elapsed >= max(duration, 0.1):
        st.session_state.step += 1
        st.session_state.last_tick = time.time()

        if st.session_state.step >= len(df):
            st.session_state.step = len(df) - 1
            st.session_state.playing = False


def apply_csv_to_valves(valves, row):
    for csv_col, role in CSV_ROLE_MAP.items():
        valve_tag = VALVE_ROLE_MAP.get(role)

        if valve_tag in valves:
            st.session_state.valve_states[valve_tag] = float(row[csv_col]) > 0


def pipe_active(pipe_idx, valves):
    pipe_no = pipe_idx + 1

    for tag, data in valves.items():
        if st.session_state.valve_states.get(tag, False):
            if pipe_no in data.get("connected_pipes", []):
                return True

    return False


def render_pid(image_path, valves, pipes):
    if os.path.exists(image_path):
        img = Image.open(image_path).convert("RGBA")
    else:
        img = Image.new("RGBA", (900, 600), (40, 40, 60))

    draw = ImageDraw.Draw(img)

    for i, pipe in enumerate(pipes):
        active = pipe_active(i, valves)
        color = (0, 255, 0) if active else (70, 70, 100)
        width = 6 if active else 4

        draw.line(
            [(pipe["x1"], pipe["y1"]), (pipe["x2"], pipe["y2"])],
            fill=color,
            width=width,
        )

    for tag, valve in valves.items():
        x, y = valve["x"], valve["y"]
        open_ = st.session_state.valve_states.get(tag, False)
        color = (0, 255, 0) if open_ else (255, 0, 0)

        draw.ellipse(
            [x - 7, y - 7, x + 7, y + 7],
            fill=color,
            outline="white",
            width=2,
        )

        draw.text((x + 10, y - 10), tag, fill="white")

    return img.convert("RGB")

# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.title("🏭 Rig Control")

    if st.button("🏠 Home"):
        st.session_state.page = "home"

    st.markdown("---")

    csv_file = st.file_uploader("Upload CSV Test Sequence", type=["csv"])

    if csv_file:
        st.session_state.csv = load_csv(csv_file)
        st.session_state.step = 0
        st.session_state.playing = False
        st.session_state.last_tick = time.time()
        st.success("CSV Loaded")

    if st.session_state.csv is not None:
        st.markdown("---")

        if st.button("▶ Play" if not st.session_state.playing else "⏸ Pause"):
            st.session_state.playing = not st.session_state.playing
            st.session_state.last_tick = time.time()

# =========================================================
# HOME PAGE
# =========================================================
if st.session_state.page == "home":
    st.title("🏭 Rig Simulation – Home")

    cols = st.columns(len(SYSTEMS))

    for i, (key, system) in enumerate(SYSTEMS.items()):
        with cols[i]:
            if st.button(system["name"], use_container_width=True):
                st.session_state.page = key

    st.info("Select a system. CSV simulation drives valve behaviour.")
    st.stop()

# =========================================================
# SYSTEM PAGE
# =========================================================
system_key = st.session_state.page
config = SYSTEMS[system_key]

valves = load_json(config["valves"])
pipes = load_json(config["pipes"])

for tag in valves:
    st.session_state.valve_states.setdefault(tag, False)

if st.session_state.csv is not None:
    if st.session_state.playing:
        advance_step()
        time.sleep(0.05)
        st.rerun()

    row = st.session_state.csv.iloc[st.session_state.step]
    apply_csv_to_valves(valves, row)

st.title(config["name"])

image = render_pid(config["image"], valves, pipes)
st.image(image, use_container_width=True, caption="Green = Flow | Red = Closed Valve")

with st.expander("🔍 CSV Step Data"):
    if st.session_state.csv is not None:
        st.write(row)

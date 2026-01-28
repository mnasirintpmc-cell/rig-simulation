import streamlit as st
import pandas as pd
import json
import os
from PIL import Image, ImageDraw

st.set_page_config("Rig Simulation", "🏭", layout="wide")

# =========================================================
# PANELS (ALL PRESENT)
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
# SESSION STATE (GLOBAL, NOT PER PANEL)
# =========================================================
if "csv" not in st.session_state:
    st.session_state.csv = None
if "step" not in st.session_state:
    st.session_state.step = 0
if "panel" not in st.session_state:
    st.session_state.panel = "mixing"
if "valve_states" not in st.session_state:
    st.session_state.valve_states = {}
if "flow_state" not in st.session_state:
    st.session_state.flow_state = {"cell": False, "nde": False, "de": False}

# =========================================================
# HELPERS
# =========================================================
def load_json(path):
    with open(path) as f:
        return json.load(f)

def csv_val(row, key):
    return float(row[key]) if key in row else 0.0

# =========================================================
# STEP → VALVES (SUPPLY + MIXING)
# =========================================================
def apply_step(row):
    st.session_state.valve_states.clear()
    fs = {"cell": False, "nde": False, "de": False}

    # ---- MIXING ----
    if csv_val(row, "TST_GasInjectionDemand") > 0:
        st.session_state.valve_states["MIXING_ON"] = True

    # ---- PRESSURE SUPPLY ----
    if csv_val(row, "TST_CellPresDemand") > 0:
        fs["cell"] = True
    if csv_val(row, "TST_InterBPDemand_NDE") > 0:
        fs["nde"] = True
    if csv_val(row, "TST_InterBPDemand_DE") > 0:
        fs["de"] = True

    st.session_state.flow_state = fs

    # ---- DGS ----
    if fs["nde"]:
        st.session_state.valve_states["V-202"] = True
    if fs["de"]:
        st.session_state.valve_states["V-210"] = True

# =========================================================
# PIPE ACTIVE
# =========================================================
def pipe_active(panel, pipe_idx, valves):
    pipe_no = pipe_idx + 1
    for tag, data in valves.items():
        if st.session_state.valve_states.get(tag, False):
            key = next((k for k in data if k.startswith("pipes")), None)
            if key and pipe_no in data[key]:
                return True
    return False

# =========================================================
# RENDER
# =========================================================
def render(panel):
    cfg = PANELS[panel]
    img = Image.open(cfg["image"]).convert("RGBA")
    draw = ImageDraw.Draw(img)

    valves = load_json(cfg["valves"])
    pipes = load_json(cfg["pipes"])

    for i, p in enumerate(pipes):
        active = pipe_active(panel, i, valves)
        draw.line(
            [(p["x1"], p["y1"]), (p["x2"], p["y2"])],
            fill=(0,255,0) if active else (80,80,100),
            width=6 if active else 4
        )

    for tag, v in valves.items():
        open_ = st.session_state.valve_states.get(tag, False)
        draw.ellipse(
            [v["x"]-7, v["y"]-7, v["x"]+7, v["y"]+7],
            fill=(0,255,0) if open_ else (255,0,0),
            outline="white"
        )
        draw.text((v["x"]+10, v["y"]-10), tag, fill="white")

    return img

# =========================================================
# SIDEBAR (GLOBAL CSV + STEP)
# =========================================================
with st.sidebar:
    st.title("🏭 Rig Control")

    st.session_state.panel = st.selectbox(
        "Select Panel",
        list(PANELS.keys()),
        format_func=lambda k: PANELS[k]["name"]
    )

    csv_file = st.file_uploader("Upload Test CSV", type=["csv"])
    if csv_file:
        st.session_state.csv = pd.read_csv(csv_file, sep=";")
        st.session_state.step = 0
        st.success("CSV loaded")

    if st.session_state.csv is not None:
        if st.button("⏭ Next Step"):
            st.session_state.step += 1
            if st.session_state.step >= len(st.session_state.csv):
                st.session_state.step = len(st.session_state.csv) - 1
            st.rerun()

# =========================================================
# MAIN
# =========================================================
if st.session_state.csv is not None:
    row = st.session_state.csv.iloc[st.session_state.step]
    apply_step(row)

st.title(PANELS[st.session_state.panel]["name"])
st.image(render(st.session_state.panel), use_container_width=True)

if st.session_state.csv is not None:
    st.markdown("### ⏱ Step Status")
    st.write(f"Row {st.session_state.step + 1} / {len(st.session_state.csv)}")
    st.write(row)

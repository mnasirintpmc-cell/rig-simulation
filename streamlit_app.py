import streamlit as st
import pandas as pd
import json
import os
from PIL import Image, ImageDraw

st.set_page_config("Rig Simulation", "🏭", layout="wide")

PANELS = {
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
}

# =========================================================
# SESSION STATE
# =========================================================
if "panel" not in st.session_state:
    st.session_state.panel = "supply"

if "csv" not in st.session_state:
    st.session_state.csv = None

if "step" not in st.session_state:
    st.session_state.step = 0

if "valve_states" not in st.session_state:
    st.session_state.valve_states = {}

if "flow_state" not in st.session_state:
    st.session_state.flow_state = {
        "cell": False,
        "nde": False,
        "de": False,
    }

# =========================================================
# HELPERS
# =========================================================
def load_json(path):
    with open(path) as f:
        return json.load(f)

def csv_val(row, key):
    return float(row[key]) if key in row else 0.0

# =========================================================
# SUPPLY → FLOW STATE
# =========================================================
def update_flow_from_supply(valves):
    fs = {"cell": False, "nde": False, "de": False}

    for tag, open_ in st.session_state.valve_states.items():
        if not open_:
            continue

        if tag in ["V-402", "V-404", "V-408"]:
            fs["cell"] = True
        if tag == "V-112":
            fs["nde"] = True
        if tag == "V-113":
            fs["de"] = True

    st.session_state.flow_state = fs

# =========================================================
# FLOW STATE → DGS + RETURN
# =========================================================
def propagate_flow():
    fs = st.session_state.flow_state

    # DGS
    if fs["nde"]:
        st.session_state.valve_states["V-112_IN"] = True
        st.session_state.valve_states["V-112_OUT"] = True
    if fs["de"]:
        st.session_state.valve_states["V-113_IN"] = True
        st.session_state.valve_states["V-113_OUT"] = True

    # RETURN
    st.session_state.valve_states["V-202"] = fs["nde"]
    st.session_state.valve_states["V-210"] = fs["de"]

# =========================================================
# APPLY CSV STEP
# =========================================================
def apply_step(row):
    # RESET
    for k in st.session_state.valve_states:
        st.session_state.valve_states[k] = False

    # SUPPLY LOGIC
    if csv_val(row, "TST_CellPresDemand") > 0:
        st.session_state.valve_states["V-402"] = True

    if csv_val(row, "TST_InterBPDemand_NDE") > 0:
        st.session_state.valve_states["V-112"] = True

    if csv_val(row, "TST_InterBPDemand_DE") > 0:
        st.session_state.valve_states["V-113"] = True

    update_flow_from_supply(None)
    propagate_flow()

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
        active = False
        for tag, data in valves.items():
            if st.session_state.valve_states.get(tag, False):
                key = next((k for k in data if k.startswith("pipes")), None)
                if key and (i + 1) in data[key]:
                    active = True
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
# UI
# =========================================================
with st.sidebar:
    st.session_state.panel = st.selectbox(
        "Select Panel", list(PANELS.keys()),
        format_func=lambda k: PANELS[k]["name"]
    )

    csv_file = st.file_uploader("Upload Pressure CSV", type=["csv"])
    if csv_file:
        st.session_state.csv = pd.read_csv(csv_file, sep=";")
        st.session_state.step = 0
        st.success("CSV loaded")

    if st.button("⏭ Next Step") and st.session_state.csv is not None:
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

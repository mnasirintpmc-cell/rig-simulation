import streamlit as st
import pandas as pd
import json
import os
import time
from PIL import Image, ImageDraw

st.set_page_config("Rig Simulation", "🏭", layout="wide")

# =========================================================
# PANELS
# =========================================================
PANELS = {
    "mixing": {
        "name": "Gas Mixing Panel",
        "valves": "data/valves_mixing.json",
        "image": "assets/p&id_mixing.png",
    },
    "supply": {
        "name": "Pressure Supply Panel",
        "valves": "data/valves_pressure_in.json",
        "image": "assets/p&id_pressure_in.png",
    },
    "dgs": {
        "name": "DGS Panel",
        "valves": "data/valves_dgs.json",
        "image": "assets/p&id_dgs.png",
    },
    "return": {
        "name": "Pressure Return Panel",
        "valves": "data/valves_pressure_return.json",
        "image": "assets/p&id_pressure_return.png",
    },
    "seal": {
        "name": "Separation Seal Panel",
        "valves": "data/valves_separation_seal.json",
        "image": "assets/p&id_separation_seal.png",
    },
}

# =========================================================
# SESSION STATE
# =========================================================
if "csv" not in st.session_state:
    st.session_state.csv = None
if "csv_id" not in st.session_state:
    st.session_state.csv_id = None
if "step" not in st.session_state:
    st.session_state.step = 0
if "panel" not in st.session_state:
    st.session_state.panel = "mixing"
if "valve_states" not in st.session_state:
    st.session_state.valve_states = {}
if "playing" not in st.session_state:
    st.session_state.playing = False
if "next_time" not in st.session_state:
    st.session_state.next_time = None

# =========================================================
# HELPERS
# =========================================================
def load_json(path):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}

def csv_val(row, key):
    return float(row[key]) if key in row and pd.notna(row[key]) else 0.0

def is_seal_csv(df):
    return "TST_SepSealControlTyp" in df.columns

# =========================================================
# DGS LOGIC (WORKING BASELINE)
# =========================================================
def apply_dgs_step(row):
    vs = st.session_state.valve_states
    vs.clear()

    cell_p = csv_val(row, "TST_CellPresDemand")

    if cell_p > 0:
        if cell_p <= 10:
            vs["V-108"] = True
        elif cell_p <= 100:
            vs["V-107"] = True
        else:
            vs["V-106"] = True

    inter_source = (
        csv_val(row, "TST_InterBPDemand_NDE") > 0
        or csv_val(row, "TST_InterBPDemand_DE") > 0
    )

    if inter_source:
        vs["V-110"] = True
        vs["V-109"] = True

    nde = csv_val(row, "TST_InterBPDemand_NDE") > 0
    de  = csv_val(row, "TST_InterBPDemand_DE") > 0

    if nde: vs["V-112"] = True
    if de:  vs["V-113"] = True

    gas = csv_val(row, "TST_GasInjectionDemand") > 0

    if gas:
        vs["V-206"] = True
        vs["V-207"] = True
        vs["V-115"] = True
        vs["V-116"] = True
    else:
        if nde:
            vs["V-115"] = True
            vs["V-204"] = True
        if de:
            vs["V-116"] = True
            vs["V-208"] = True

    if cell_p > 0: vs["cell"] = True
    if nde: vs["NDE in"] = True
    if de:  vs["DE in"] = True

# =========================================================
# SEPARATION SEAL LOGIC (SIMPLIFIED)
# =========================================================
def apply_seal_step(row):
    vs = st.session_state.valve_states
    vs.clear()

    flow = max(
        csv_val(row, "TST_SepSealFlwSet1"),
        csv_val(row, "TST_SepSealFlwSet2")
    )

    pressure = max(
        csv_val(row, "TST_SepSealPSet1"),
        csv_val(row, "TST_SepSealPSet2")
    )

    # Pressure supply
    if pressure > 0:
        if pressure <= 10:
            vs["V-108"] = True
        elif pressure <= 100:
            vs["V-107"] = True
        else:
            vs["V-106"] = True

    # Main seal paths
    if flow > 0 or pressure > 0:
        vs["V-212"] = True
        vs["V-213"] = True
        vs["V-214"] = True
        vs["V-215"] = True

    # High flow boosters
    if flow > 500:
        vs["V-216"] = True
        vs["V-217"] = True

# =========================================================
# RENDER (VALVES ONLY)
# =========================================================
def render(panel):
    cfg = PANELS[panel]
    img = Image.open(cfg["image"]).convert("RGBA")
    draw = ImageDraw.Draw(img)

    valves = load_json(cfg["valves"])

    for tag, v in valves.items():
        open_ = st.session_state.valve_states.get(tag, False)
        draw.ellipse(
            [v["x"] - 7, v["y"] - 7, v["x"] + 7, v["y"] + 7],
            fill=(0, 255, 0) if open_ else (255, 0, 0),
            outline="white",
        )
        draw.text((v["x"] + 10, v["y"] - 10), tag, fill="white")

    return img

# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.title("🏭 Rig Control")

    st.session_state.panel = st.selectbox(
        "Select Panel",
        list(PANELS.keys()),
        format_func=lambda k: PANELS[k]["name"],
    )

    uploaded = st.file_uploader("Upload Test CSV", type=["csv"])
    if uploaded:
        cid = (uploaded.name, uploaded.size)
        if cid != st.session_state.csv_id:
            st.session_state.csv = pd.read_csv(uploaded, sep=";")
            st.session_state.csv_id = cid
            st.session_state.step = 0
            st.session_state.playing = False
            st.session_state.next_time = None

    if st.session_state.csv is not None:
        col1, col2 = st.columns(2)
        if col1.button("▶ Play"):
            st.session_state.playing = True
            st.session_state.next_time = None
        if col2.button("⏸ Pause"):
            st.session_state.playing = False

        col3, col4 = st.columns(2)
        if col3.button("⏮ Previous"):
            st.session_state.step = max(0, st.session_state.step - 1)
        if col4.button("⏭ Next"):
            st.session_state.step = min(
                len(st.session_state.csv) - 1,
                st.session_state.step + 1
            )

# =========================================================
# AUTO STEP ADVANCE (CSV DURATION ONLY)
# =========================================================
if st.session_state.playing and st.session_state.csv is not None:
    row = st.session_state.csv.iloc[st.session_state.step]

    duration = csv_val(row, "TST_StepDuration")
    if duration <= 0:
        duration = 1

    if st.session_state.next_time is None:
        st.session_state.next_time = time.time() + duration

    if time.time() >= st.session_state.next_time:
        if st.session_state.step < len(st.session_state.csv) - 1:
            st.session_state.step += 1
            next_row = st.session_state.csv.iloc[st.session_state.step]
            st.session_state.next_time = time.time() + csv_val(
                next_row, "TST_StepDuration"
            )
        else:
            st.session_state.playing = False

    st.rerun()

# =========================================================
# MAIN
# =========================================================
if st.session_state.csv is not None:
    row = st.session_state.csv.iloc[st.session_state.step]
    if is_seal_csv(st.session_state.csv):
        apply_seal_step(row)
    else:
        apply_dgs_step(row)

st.title(PANELS[st.session_state.panel]["name"])
st.image(render(st.session_state.panel), use_container_width=True)

if st.session_state.csv is not None:
    st.markdown("### ⏱ Step Status")
    st.write(f"Step {st.session_state.step + 1} / {len(st.session_state.csv)}")
    st.write(row)


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
if "step_start_time" not in st.session_state:
    st.session_state.step_start_time = None

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
# DGS LOGIC (UNCHANGED)
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
# SEPARATION SEAL LOGIC (UNCHANGED)
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

    if pressure > 0:
        if pressure <= 10:
            vs["V-108"] = True
        elif pressure <= 100:
            vs["V-107"] = True
        else:
            vs["V-106"] = True

    if flow > 0 or pressure > 0:
        vs["V-212"] = True
        vs["V-213"] = True
        vs["V-214"] = True
        vs["V-215"] = True

    if flow > 500:
        vs["V-216"] = True
        vs["V-217"] = True

# =========================================================
# RENDER (UNCHANGED)
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
    if uploaded is not None:
        cid = (uploaded.name, uploaded.size)
        if cid != st.session_state.csv_id:
            st.session_state.csv = pd.read_csv(uploaded, sep=";")
            st.session_state.csv_id = cid
            st.session_state.step = 0
            st.session_state.playing = False
            st.session_state.step_start_time = None

    if st.session_state.csv is not None:
        c1, c2 = st.columns(2)
        if c1.button("⏮ Previous Step"):
            st.session_state.step = max(0, st.session_state.step - 1)
            st.session_state.playing = False
            st.session_state.step_start_time = None
            st.rerun()

        if c2.button("⏭ Next Step"):
            st.session_state.step = min(
                len(st.session_state.csv) - 1,
                st.session_state.step + 1
            )
            st.session_state.playing = False
            st.session_state.step_start_time = None
            st.rerun()

        c3, c4 = st.columns(2)
        if c3.button("▶ Play"):
            st.session_state.playing = True
            st.session_state.step_start_time = None
            st.rerun()

        if c4.button("⏸ Pause"):
            st.session_state.playing = False
            st.session_state.step_start_time = None
            st.rerun()

# =========================================================
# AUTO REFRESH CLOCK (THIS IS THE KEY FIX)
# =========================================================
if st.session_state.playing:
    st.autorefresh(interval=500, key="play_clock")

# =========================================================
# AUTO STEP ADVANCE (CSV TST_StepDuration ONLY)
# =========================================================
if st.session_state.playing and st.session_state.csv is not None:
    row = st.session_state.csv.iloc[st.session_state.step]
    duration = csv_val(row, "TST_StepDuration")

    if duration <= 0:
        duration = 1

    if st.session_state.step_start_time is None:
        st.session_state.step_start_time = time.time()

    if time.time() - st.session_state.step_start_time >= duration:
        if st.session_state.step < len(st.session_state.csv) - 1:
            st.session_state.step += 1
            st.session_state.step_start_time = time.time()
        else:
            st.session_state.playing = False

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
def apply_dgs_step(row):
    vs = st.session_state.valve_states
    vs.clear()

    # -------------------------------
    # CELL PRESSURE SELECTION
    # -------------------------------
    cell_p = csv_val(row, "TST_CellPresDemand")

    if cell_p > 0:
        if cell_p <= 10:
            vs["V-108"] = True          # low pressure
        elif cell_p <= 100:
            vs["V-107"] = True          # medium pressure
        else:
            vs["V-106"] = True          # high pressure

    cell_active = cell_p > 0

    # -------------------------------
    # INTERSPACE PRESSURE SELECTION
    # -------------------------------
    nde_p = csv_val(row, "TST_InterBPDemand_NDE")
    de_p  = csv_val(row, "TST_InterBPDemand_DE")

    inter_p = max(nde_p, de_p)

    if inter_p > 0:
        if inter_p <= 7:
            vs["V-111"] = True          # low pressure 0–7 bar
        elif inter_p <= 100:
            vs["V-110"] = True          # medium pressure 7–100 bar
        else:
            vs["V-109"] = True          # high pressure 100–450 bar

    nde = nde_p > 0
    de  = de_p > 0

    if nde:
        vs["V-112"] = True              # NDE interspace enable
    if de:
        vs["V-113"] = True              # DE interspace enable

    # -------------------------------
    # GAS INJECTION OVERRIDE
    # -------------------------------
    gas = csv_val(row, "TST_GasInjectionDemand") > 0

    if gas:
        # Gas injection valves
        vs["V-206"] = True
        vs["V-207"] = True

        # Feed interspaces back into pod
        vs["V-115"] = True
        vs["V-116"] = True

        nde = True
        de = True
    else:
        # Normal back-pressure mode
        if nde:
            vs["V-115"] = True
            vs["V-204"] = True

        if de:
            vs["V-116"] = True
            vs["V-208"] = True

    # -------------------------------
    # DGS POD VALVES
    # -------------------------------
    if cell_active:
        vs["cell"] = True
    if nde:
        vs["NDE in"] = True
    if de:
        vs["DE in"] = True

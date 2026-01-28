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
    st.session_state.pressure_state = {}

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
# APPLY STEP (FINAL LOGIC – VERIFIED)
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
    if v107: vs["V-107"] = True

    cell_active = v108 or v106 or v107

    # -------------------------------
    # INTERSPACE SOURCE
    # -------------------------------
    inter_source = (
        csv_val(row, "TST_InterBPDemand_NDE") > 0
        or csv_val(row, "TST_InterBPDemand_DE") > 0
    )

    if inter_source:
        vs["V-110"] = True
        vs["V-109"] = True

    # -------------------------------
    # INTERSPACE ENABLES
    # -------------------------------
    nde_enable = csv_val(row, "TST_InterBPDemand_NDE") > 0
    de_enable  = csv_val(row, "TST_InterBPDemand_DE") > 0

    if nde_enable: vs["V-112"] = True
    if de_enable:  vs["V-113"] = True

    nde_active = inter_source and nde_enable
    de_active  = inter_source and de_enable

    # -------------------------------
    # BACK PRESSURE – SUPPLY SIDE
    # -------------------------------
    if nde_active:
        vs["V-115"] = True
    if de_active:
        vs["V-116"] = True

    # -------------------------------
    # GAS INJECTION (THIS IS THE FIX)
    # -------------------------------
    gas_injection = csv_val(row, "TST_GasInjectionDemand") > 0

    if gas_injection:
        vs["V-206"] = True   # NDE return
        vs["V-207"] = True   # DE return

    if "V-115" in vs:
        vs["V-204"] = True   # NDE downstream

    if "V-116" in vs:
        vs["V-208"] = True   # DE downstream

    # -------------------------------
    # DGS VALVES
    # -------------------------------
    if cell_active:
        vs["cell"] = True
    if nde_active:
        vs["NDE in"] = True
    if de_active:
        vs["DE in"] = True

    st.session_state.pressure_state = {
        "cell": cell_active,
        "nde": nde_active,
        "de": de_active,
        "gas_injection": gas_injection,
    }

# =========================================================
# PIPE ACTIVE
# =========================================================
def pipe_active(pipe_idx, valves):
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
        active = pipe_active(i, valves)
        draw.line(
            [(p["x1"], p["y1"]), (p["x2"], p["y2"])],
            fill=(0, 255, 0) if active else (90, 90, 110),
            width=6 if active else 4,
        )

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

    csv_file = st.file_uploader("Upload Test CSV", type=["csv"])
    if csv_file and not st.session_state.csv_loaded:
        st.session_state.csv = pd.read_csv(csv_file, sep=";")
        st.session_state.step = 0
        st.session_state.csv_loaded = True
        st.success("CSV loaded")

    if st.session_state.csv is not None:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⏮ Previous Step"):
                st.session_state.step = max(0, st.session_state.step - 1)
                st.rerun()
        with col2:
            if st.button("⏭ Next Step"):
                st.session_state.step = min(
                    len(st.session_state.csv) - 1,
                    st.session_state.step + 1
                )
                st.rerun()

    st.markdown("---")
    st.subheader("Pressure State")
    for k, v in st.session_state.pressure_state.items():
        st.write(f"{k}: {'ON' if v else 'OFF'}")

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

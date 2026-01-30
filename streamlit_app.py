
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
if "panel" not in st.session_state:
    st.session_state.panel = "mixing"
if "csv" not in st.session_state:
    st.session_state.csv = None
if "step" not in st.session_state:
    st.session_state.step = 0
if "valve_states" not in st.session_state:
    st.session_state.valve_states = {}
if "calibration" not in st.session_state:
    st.session_state.calibration = False
if "indicators" not in st.session_state:
    st.session_state.indicators = {}
if "selected_indicator" not in st.session_state:
    st.session_state.selected_indicator = None

# =========================================================
# HELPERS
# =========================================================
def load_json(path):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}

def csv_val(row, key):
    if row is None or key not in row or pd.isna(row[key]):
        return 0.0
    return float(row[key])

# =========================================================
# BASIC PRESSURE LOGIC (STABLE)
# =========================================================
def apply_step(row):
    vs = st.session_state.valve_states
    vs.clear()

    cell_p = csv_val(row, "TST_CellPresDemand")
    nde_p  = csv_val(row, "TST_InterBPDemand_NDE")
    de_p   = csv_val(row, "TST_InterBPDemand_DE")

    # ---- Cell pressure ----
    if cell_p > 0:
        if cell_p <= 7:
            vs["V-108"] = True
        elif cell_p <= 100:
            vs["V-107"] = True
        else:
            vs["V-106"] = True
        vs["cell"] = True

    # ---- Interspace pressure ----
    inter_p = max(nde_p, de_p)
    if inter_p > 0:
        if inter_p <= 7:
            vs["V-111"] = True
        elif inter_p <= 100:
            vs["V-110"] = True
        else:
            vs["V-109"] = True

        vs["V-112"] = True
        vs["V-113"] = True

        if nde_p > 0:
            vs["NDE in"] = True
        if de_p > 0:
            vs["DE in"] = True

# =========================================================
# RENDER (VALVES + INDICATORS)
# =========================================================
def render(panel):
    cfg = PANELS[panel]
    img = Image.open(cfg["image"]).convert("RGBA")
    draw = ImageDraw.Draw(img)

    # ---- VALVES ----
    valves = load_json(cfg["valves"])
    for tag, v in valves.items():
        open_ = st.session_state.valve_states.get(tag, False)
        draw.ellipse(
            [v["x"] - 7, v["y"] - 7, v["x"] + 7, v["y"] + 7],
            fill=(0, 255, 0) if open_ else (255, 0, 0),
            outline="white",
        )
        draw.text((v["x"] + 10, v["y"] - 10), tag, fill="white")

    # ---- INDICATORS (FROM SESSION STATE) ----
    row = None
    if st.session_state.csv is not None:
        row = st.session_state.csv.iloc[st.session_state.step]

    for name, ind in st.session_state.indicators.items():
        value = csv_val(row, ind.get("source", ""))
        text = f"{value:.1f} {ind.get('unit','')}"

        x, y = ind["x"], ind["y"]
        pad = 4
        w = 8 * len(text)
        h = 16

        bg = (80, 80, 80) if (
            st.session_state.calibration
            and name == st.session_state.selected_indicator
        ) else (30, 30, 30)

        draw.rectangle(
            [x, y, x + w + pad * 2, y + h + pad * 2],
            fill=bg
        )
        draw.text((x + pad, y + pad), text, fill=(0, 255, 0))

    return img

# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.title("🏭 Rig Control")

    # Panel select
    new_panel = st.selectbox(
        "Panel",
        list(PANELS.keys()),
        format_func=lambda k: PANELS[k]["name"],
    )

    # Reload indicators when panel changes
    if new_panel != st.session_state.panel:
        st.session_state.panel = new_panel
        st.session_state.indicators = load_json(
            f"data/indicators_{new_panel}.json"
        )
        st.session_state.selected_indicator = None

    st.session_state.calibration = st.toggle("🎯 Indicator Calibration")

    uploaded = st.file_uploader("Upload CSV", type=["csv"])
    if uploaded is not None:
        st.session_state.csv = pd.read_csv(uploaded, sep=";")
        st.session_state.step = 0

    if st.session_state.csv is not None:
        if st.button("⏮ Previous Step"):
            st.session_state.step = max(0, st.session_state.step - 1)
            st.rerun()

        if st.button("⏭ Next Step"):
            st.session_state.step = min(
                len(st.session_state.csv) - 1,
                st.session_state.step + 1
            )
            st.rerun()

    # ---- INDICATOR CALIBRATION CONTROLS ----
    if st.session_state.calibration:
        st.markdown("---")
        st.subheader("🎯 Indicator Calibration")

        if st.session_state.indicators:
            st.session_state.selected_indicator = st.selectbox(
                "Select Indicator",
                list(st.session_state.indicators.keys())
            )

            ind = st.session_state.indicators[
                st.session_state.selected_indicator
            ]

            ind["x"] = st.number_input(
                "X", value=ind["x"], step=1
            )
            ind["y"] = st.number_input(
                "Y", value=ind["y"], step=1
            )

            st.success(
                "Indicator moved live — copy X/Y into JSON when done"
            )
        else:
            st.warning("No indicators JSON found for this panel")

# =========================================================
# MAIN
# =========================================================
if st.session_state.csv is not None:
    apply_step(st.session_state.csv.iloc[st.session_state.step])

st.title(PANELS[st.session_state.panel]["name"])
st.image(render(st.session_state.panel), use_container_width=True)

if st.session_state.csv is not None:
    st.markdown("### Step Status")
    st.write(
        f"Step {st.session_state.step + 1} / {len(st.session_state.csv)}"
    )
    st.write(st.session_state.csv.iloc[st.session_state.step])

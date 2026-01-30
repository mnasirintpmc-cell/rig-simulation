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
    "pressure_in": {
        "name": "Pressure Supply Panel",
        "valves": "data/valves_pressure_in.json",
        "image": "assets/p&id_pressure_in.png",
    },
    "dgs": {
        "name": "DGS Panel",
        "valves": "data/valves_dgs.json",
        "image": "assets/p&id_dgs.png",
    },
    "pressure_return": {
        "name": "Pressure Return Panel",
        "valves": "data/valves_pressure_return.json",
        "image": "assets/p&id_pressure_return.png",
    },
    "separation_seal": {
        "name": "Separation Seal Panel",
        "valves": "data/valves_separation_seal.json",
        "image": "assets/p&id_separation_seal.png",
    },
}

# =========================================================
# SESSION STATE
# =========================================================
if "panel" not in st.session_state:
    st.session_state.panel = "pressure_in"
if "csv" not in st.session_state:
    st.session_state.csv = None
if "step" not in st.session_state:
    st.session_state.step = 0
if "valve_states" not in st.session_state:
    st.session_state.valve_states = {}
if "calibration" not in st.session_state:
    st.session_state.calibration = False
if "cal_x" not in st.session_state:
    st.session_state.cal_x = 400
if "cal_y" not in st.session_state:
    st.session_state.cal_y = 300

# =========================================================
# HELPERS
# =========================================================
def load_json(path):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}

def csv_val(row, key):
    if row is None:
        return 0
    return float(row[key]) if key in row and pd.notna(row[key]) else 0

def draw_indicator(draw, x, y, text, highlight=False):
    pad = 4
    w = 8 * len(text)
    h = 16
    bg = (80, 80, 80) if highlight else (40, 40, 40)

    draw.rectangle(
        [x, y, x + w + pad * 2, y + h + pad * 2],
        fill=bg
    )
    draw.text((x + pad, y + pad), text, fill=(0, 255, 0))

# =========================================================
# RENDER
# =========================================================
def render(panel):
    cfg = PANELS[panel]
    img = Image.open(cfg["image"]).convert("RGBA")
    draw = ImageDraw.Draw(img)

    # ---- valves ----
    valves = load_json(cfg["valves"])
    for tag, v in valves.items():
        draw.ellipse(
            [v["x"] - 7, v["y"] - 7, v["x"] + 7, v["y"] + 7],
            fill=(255, 0, 0),
            outline="white",
        )
        draw.text((v["x"] + 10, v["y"] - 10), tag, fill="white")

    # ---- REAL INDICATORS (NORMAL MODE) ----
    if not st.session_state.calibration:
        ind_path = f"data/indicators_{panel}.json"
        indicators = load_json(ind_path)

        row = None
        if st.session_state.csv is not None:
            row = st.session_state.csv.iloc[st.session_state.step]

        for name, ind in indicators.items():
            value = csv_val(row, ind.get("source", ""))
            text = f"{value:.1f} {ind.get('unit', '')}"
            draw_indicator(draw, ind["x"], ind["y"], text)

    # ---- GENERIC CALIBRATION INDICATOR ----
    if st.session_state.calibration:
        draw_indicator(
            draw,
            st.session_state.cal_x,
            st.session_state.cal_y,
            "CAL 0.0",
            highlight=True
        )

    return img

# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.title("🏭 Rig Control")

    st.session_state.panel = st.selectbox(
        "Select Panel",
        list(PANELS.keys()),
        format_func=lambda k: PANELS[k]["name"]
    )

    st.session_state.calibration = st.toggle("🔧 Indicator Calibration Mode")

    uploaded = st.file_uploader("Upload Test CSV", type=["csv"])
    if uploaded:
        st.session_state.csv = pd.read_csv(uploaded, sep=";")
        st.session_state.step = 0

    if st.session_state.csv is not None:
        c1, c2 = st.columns(2)
        if c1.button("⏮ Previous Step"):
            st.session_state.step = max(0, st.session_state.step - 1)
        if c2.button("⏭ Next Step"):
            st.session_state.step = min(
                len(st.session_state.csv) - 1,
                st.session_state.step + 1
            )

    if st.session_state.calibration:
        st.markdown("---")
        st.subheader("🧪 Generic Indicator Position")
        st.session_state.cal_x = st.number_input("X", value=st.session_state.cal_x)
        st.session_state.cal_y = st.number_input("Y", value=st.session_state.cal_y)
        st.info("Copy X/Y into indicators_<panel>.json")

# =========================================================
# MAIN
# =========================================================
st.title(PANELS[st.session_state.panel]["name"])
st.image(render(st.session_state.panel), use_container_width=True)

if st.session_state.csv is not None:
    st.markdown("### ⏱ Step Status")
    st.write(f"Step {st.session_state.step + 1} / {len(st.session_state.csv)}")
    st.write(st.session_state.csv.iloc[st.session_state.step])

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
if "csv" not in st.session_state:
    st.session_state.csv = None
if "step" not in st.session_state:
    st.session_state.step = 0
if "panel" not in st.session_state:
    st.session_state.panel = "pressure_in"
if "valve_states" not in st.session_state:
    st.session_state.valve_states = {}
if "calibration" not in st.session_state:
    st.session_state.calibration = False
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

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def csv_val(row, key):
    if row is None:
        return 0.0
    return float(row[key]) if key in row and pd.notna(row[key]) else 0.0

def draw_indicator(draw, x, y, text, selected=False):
    pad = 4
    w = 8 * len(text)
    h = 16
    bg = (60, 60, 60) if not selected else (100, 100, 100)

    draw.rectangle(
        [x, y, x + w + pad * 2, y + h + pad * 2],
        fill=bg
    )
    draw.text(
        (x + pad, y + pad),
        text,
        fill=(0, 255, 0)
    )

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
        open_ = st.session_state.valve_states.get(tag, False)
        draw.ellipse(
            [v["x"] - 7, v["y"] - 7, v["x"] + 7, v["y"] + 7],
            fill=(0, 255, 0) if open_ else (255, 0, 0),
            outline="white",
        )
        draw.text((v["x"] + 10, v["y"] - 10), tag, fill="white")

    # ---- indicators (ALWAYS VISIBLE) ----
    ind_path = f"data/indicators_{panel}.json"
    indicators = load_json(ind_path)

    row = None
    if st.session_state.csv is not None:
        row = st.session_state.csv.iloc[st.session_state.step]

    for name, ind in indicators.items():
        value = csv_val(row, ind["source"])
        label = f"{value:.1f} {ind.get('unit','')}"
        draw_indicator(
            draw,
            ind["x"],
            ind["y"],
            label,
            selected=(name == st.session_state.selected_indicator)
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
        if c1.button("⏮ Previous"):
            st.session_state.step = max(0, st.session_state.step - 1)
        if c2.button("⏭ Next"):
            st.session_state.step = min(
                len(st.session_state.csv) - 1,
                st.session_state.step + 1
            )

# =========================================================
# CALIBRATION CONTROLS (SAFE TO DELETE LATER)
# =========================================================
if st.session_state.calibration:
    ind_path = f"data/indicators_{st.session_state.panel}.json"
    indicators = load_json(ind_path)

    st.sidebar.markdown("---")
    st.sidebar.subheader("🎯 Indicator Calibration")

    if indicators:
        sel = st.sidebar.selectbox(
            "Select Indicator",
            list(indicators.keys())
        )
        st.session_state.selected_indicator = sel
        ind = indicators[sel]

        x = st.sidebar.number_input("X", value=ind["x"], step=1)
        y = st.sidebar.number_input("Y", value=ind["y"], step=1)

        if st.sidebar.button("💾 Save Position"):
            indicators[sel]["x"] = int(x)
            indicators[sel]["y"] = int(y)
            save_json(ind_path, indicators)
            st.sidebar.success("Position saved")

    else:
        st.sidebar.info("No indicators JSON found")

# =========================================================
# MAIN
# =========================================================
st.title(PANELS[st.session_state.panel]["name"])
st.image(render(st.session_state.panel), use_container_width=True)

if st.session_state.csv is not None:
    st.markdown("### ⏱ Step Status")
    st.write(f"Step {st.session_state.step + 1} / {len(st.session_state.csv)}")
    st.write(st.session_state.csv.iloc[st.session_state.step])

import streamlit as st
import pandas as pd
import json
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
if "step" not in st.session_state:
    st.session_state.step = 0
if "panel" not in st.session_state:
    st.session_state.panel = "mixing"
if "valve_states" not in st.session_state:
    st.session_state.valve_states = {}
if "pressure" not in st.session_state:
    st.session_state.pressure = {
        "cell": False,
        "nde": False,
        "de": False,
        "nde_bias": False,
        "de_bias": False,
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
# APPLY STEP (REAL PHYSICS)
# =========================================================
def apply_step(row):
    vs = st.session_state.valve_states
    p = {"cell": False, "nde": False, "de": False, "nde_bias": False, "de_bias": False}

    vs.clear()

    # -------------------------------
    # PRESSURE SUPPLY (CELL)
    # -------------------------------
    if csv_val(row, "TST_CellPresDemand") > 0:
        vs["V-108"] = True   # shop air
        vs["V-107"] = True   # medium / high
        p["cell"] = True

    # -------------------------------
    # INTERSPACE SUPPLY
    # -------------------------------
    if csv_val(row, "TST_InterBPDemand_NDE") > 0:
        vs["V-110"] = True
        p["nde_bias"] = True

    if csv_val(row, "TST_InterBPDemand_DE") > 0:
        vs["V-109"] = True
        p["de_bias"] = True

    # -------------------------------
    # BACK PRESSURE ENABLE
    # -------------------------------
    if csv_val(row, "TST_InterPresDemand") > 0:
        vs["V-111"] = True

    # -------------------------------
    # DRY GAS SEAL DYNAMICS
    # -------------------------------
    if p["cell"]:
        p["nde"] = True
        p["de"] = True

    st.session_state.pressure = p

# =========================================================
# PIPE ACTIVE LOGIC (PRESSURE-BASED)
# =========================================================
def pipe_active(panel):
    p = st.session_state.pressure
    if panel in ["dgs", "return"]:
        return p["cell"]
    if panel == "supply":
        return p["cell"] or p["nde_bias"] or p["de_bias"]
    if panel == "mixing":
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

    # Pipes
    for p in pipes:
        draw.line(
            [(p["x1"], p["y1"]), (p["x2"], p["y2"])],
            fill=(0, 255, 0) if pipe_active(panel) else (90, 90, 110),
            width=6 if pipe_active(panel) else 4,
        )

    # Valves
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

    st.markdown("---")
    st.subheader("Pressure State")
    for k, v in st.session_state.pressure.items():
        st.write(f"{k}: {'✅' if v else '❌'}")

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

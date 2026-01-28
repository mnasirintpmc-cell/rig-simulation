import streamlit as st
import pandas as pd
import json
import os
from PIL import Image, ImageDraw

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(page_title="Rig Simulation", page_icon="🏭", layout="wide")

# =========================================================
# PANELS CONFIG
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
if "current_panel" not in st.session_state:
    st.session_state.current_panel = "mixing"

if "controllers" not in st.session_state:
    st.session_state.controllers = {}

if "test_pod" not in st.session_state:
    st.session_state.test_pod = {
        "gas_present": False,
        "pressurised": False,
        "seal_active": False,
    }

for panel in PANELS:
    if panel not in st.session_state.controllers:
        st.session_state.controllers[panel] = {
            "csv": None,
            "step": 0,
            "valve_states": {},
        }

# =========================================================
# HELPERS
# =========================================================
def load_json(path):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {} if "valves" in path else []

def load_csv(upload):
    return pd.read_csv(upload, sep=";")

def csv_value(row, col):
    return float(row[col]) if col in row.index else 0.0

# =========================================================
# CSV → VALVE LOGIC
# =========================================================
def apply_csv_to_valves(panel, valves, row, ctrl):
    for tag in valves:
        ctrl["valve_states"].setdefault(tag, False)

    if panel == "mixing":
        state = csv_value(row, "TST_GasInjectionDemand") > 0
        for tag in valves:
            ctrl["valve_states"][tag] = state

    elif panel == "supply":
        state = (
            csv_value(row, "TST_CellPresDemand") > 0
            or csv_value(row, "TST_InterPresDemand") > 0
        )
        for tag in valves:
            ctrl["valve_states"][tag] = state

    elif panel == "seal":
        state = csv_value(row, "TST_TestMode") > 0
        for tag in valves:
            ctrl["valve_states"][tag] = state

# =========================================================
# TEST POD STATE
# =========================================================
def update_test_pod():
    mixing = st.session_state.controllers["mixing"]
    supply = st.session_state.controllers["supply"]
    seal = st.session_state.controllers["seal"]

    st.session_state.test_pod["gas_present"] = any(mixing["valve_states"].values())
    st.session_state.test_pod["pressurised"] = any(supply["valve_states"].values())
    st.session_state.test_pod["seal_active"] = any(seal["valve_states"].values())

# =========================================================
# PIPE ACTIVE
# =========================================================
def pipe_active(panel, pipe_idx, valves):
    pipe_no = pipe_idx + 1

    for tag, data in valves.items():
        if st.session_state.controllers[panel]["valve_states"].get(tag, False):
            pipe_key = next((k for k in data if k.startswith("pipes")), None)
            if pipe_key and pipe_no in data[pipe_key]:
                if panel == "return":
                    return st.session_state.test_pod["pressurised"]
                return True
    return False

# =========================================================
# RENDER
# =========================================================
def render_panel(image_path, panel, valves, pipes):
    img = Image.open(image_path).convert("RGBA")
    draw = ImageDraw.Draw(img)

    for i, p in enumerate(pipes):
        active = pipe_active(panel, i, valves)
        draw.line(
            [(p["x1"], p["y1"]), (p["x2"], p["y2"])],
            fill=(0, 255, 0) if active else (80, 80, 100),
            width=6 if active else 4,
        )

    for tag, v in valves.items():
        open_ = st.session_state.controllers[panel]["valve_states"].get(tag, False)
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

    st.session_state.current_panel = st.selectbox(
        "Select Panel",
        list(PANELS.keys()),
        format_func=lambda k: PANELS[k]["name"],
    )

    ctrl = st.session_state.controllers[st.session_state.current_panel]

    csv_file = st.file_uploader(
        "Upload CSV",
        key=f"csv_{st.session_state.current_panel}",
        type=["csv"],
    )

    if csv_file:
        ctrl["csv"] = load_csv(csv_file)
        ctrl["step"] = 0
        st.success("CSV loaded")

    if st.button("⏭ Next Step"):
        if ctrl["csv"] is not None:
            ctrl["step"] += 1
            if ctrl["step"] >= len(ctrl["csv"]):
                ctrl["step"] = len(ctrl["csv"]) - 1
            st.rerun()

    st.markdown("---")
    st.subheader("TEST POD")
    for k, v in st.session_state.test_pod.items():
        st.write(f"{k}: {'✅' if v else '❌'}")

# =========================================================
# MAIN
# =========================================================
panel = st.session_state.current_panel
cfg = PANELS[panel]
ctrl = st.session_state.controllers[panel]

valves = load_json(cfg["valves"])
pipes = load_json(cfg["pipes"])

if ctrl["csv"] is not None:
    row = ctrl["csv"].iloc[ctrl["step"]]
    apply_csv_to_valves(panel, valves, row, ctrl)
    update_test_pod()

st.title(cfg["name"])
st.image(render_panel(cfg["image"], panel, valves, pipes), use_container_width=True)

if ctrl["csv"] is not None:
    st.markdown("### ⏱ Step Status")
    st.write(f"Row {ctrl['step'] + 1} / {len(ctrl['csv'])}")
    st.write(row)

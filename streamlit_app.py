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
        "name": "Gas Mixing",
        "valves": "data/valves_mixing.json",
        "pipes": "data/pipes_mixing.json",
        "image": "assets/p&id_mixing.png",
    },
    "supply": {
        "name": "Pressure Supply",
        "valves": "data/valves_pressure_in.json",
        "pipes": "data/pipes_pressure_in.json",
        "image": "assets/p&id_pressure_in.png",
    },
    "dgs": {
        "name": "DGS Pod",
        "valves": "data/valves_dgs.json",
        "pipes": "data/pipes_dgs.json",
        "image": "assets/p&id_dgs.png",
    },
    "return": {
        "name": "Pressure Return",
        "valves": "data/valves_pressure_return.json",
        "pipes": "data/pipes_pressure_return.json",
        "image": "assets/p&id_pressure_return.png",
    },
    "seal": {
        "name": "Separation Seal",
        "valves": "data/valves_separation_seal.json",
        "pipes": "data/pipes_separation_seal.json",
        "image": "assets/p&id_separation_seal.png",
    },
}

# =========================================================
# SESSION STATE
# =========================================================
for k, v in {
    "csv": None,
    "csv_id": None,
    "step": 0,
    "panel": "mixing",
    "valve_states": {},
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# =========================================================
# HELPERS
# =========================================================
def load_json(path):
    return json.load(open(path)) if os.path.exists(path) else {}

def csv_val(row, key):
    return float(row[key]) if key in row and pd.notna(row[key]) else 0.0

# =========================================================
# TEST TYPE DETECTION
# =========================================================
def detect_test_type(df):
    if "TST_SepSealControlTyp" in df.columns:
        return "SEAL"
    if "TST_CellPresDemand" in df.columns:
        return "DGS"
    return "UNKNOWN"

# =========================================================
# DGS LOGIC (UNCHANGED, VALIDATED)
# =========================================================
def apply_dgs(row):
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

    inter_src = (
        csv_val(row, "TST_InterBPDemand_NDE") > 0
        or csv_val(row, "TST_InterBPDemand_DE") > 0
    )
    if inter_src:
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
        nde = de = True
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
# SEPARATION SEAL LOGIC (NEW)
# =========================================================
def apply_seal(row):
    vs = st.session_state.valve_states
    vs.clear()

    mode = int(csv_val(row, "TST_SepSealControlTyp"))

    # Pressure source (shared)
    p = max(csv_val(row, "TST_SepSealPSet1"), csv_val(row, "TST_SepSealPSet2"))
    if p > 0:
        if p <= 10:
            vs["V-108"] = True
        elif p <= 100:
            vs["V-107"] = True
        else:
            vs["V-106"] = True

    # FLOW MODE
    if mode == 0:
        if csv_val(row, "TST_SepSealFlwSet1") > 0:
            vs["V-212"] = True
            vs["V-214"] = True
        if csv_val(row, "TST_SepSealFlwSet2") > 0:
            vs["V-213"] = True
            vs["V-215"] = True

    # PRESSURE MODE
    if mode == 1:
        if csv_val(row, "TST_SepSealPSet1") > 0:
            vs["V-212"] = True
            vs["V-214"] = True
        if csv_val(row, "TST_SepSealPSet2") > 0:
            vs["V-213"] = True
            vs["V-215"] = True

# =========================================================
# PIPE ACTIVE
# =========================================================
def pipe_active(idx, valves):
    pno = idx + 1
    for t, d in valves.items():
        if st.session_state.valve_states.get(t):
            for k in d:
                if k.startswith("pipes") and pno in d[k]:
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
        draw.line(
            [(p["x1"], p["y1"]), (p["x2"], p["y2"])],
            fill=(0,255,0) if pipe_active(i, valves) else (80,80,100),
            width=6 if pipe_active(i, valves) else 4
        )

    for t, v in valves.items():
        draw.ellipse(
            [v["x"]-7, v["y"]-7, v["x"]+7, v["y"]+7],
            fill=(0,255,0) if st.session_state.valve_states.get(t) else (255,0,0)
        )
        draw.text((v["x"]+10, v["y"]-10), t, fill="white")

    return img

# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.title("Rig Control")

    st.session_state.panel = st.selectbox(
        "Panel", list(PANELS), format_func=lambda k: PANELS[k]["name"]
    )

    up = st.file_uploader("Upload CSV", type="csv")
    if up:
        cid = (up.name, up.size)
        if cid != st.session_state.csv_id:
            st.session_state.csv = pd.read_csv(up, sep=";")
            st.session_state.csv_id = cid
            st.session_state.step = 0

    if st.session_state.csv is not None:
        c1, c2 = st.columns(2)
        if c1.button("◀ Previous"):
            st.session_state.step = max(0, st.session_state.step - 1)
            st.rerun()
        if c2.button("Next ▶"):
            st.session_state.step = min(
                len(st.session_state.csv)-1,
                st.session_state.step + 1
            )
            st.rerun()

# =========================================================
# MAIN
# =========================================================
if st.session_state.csv is not None:
    row = st.session_state.csv.iloc[st.session_state.step]
    ttype = detect_test_type(st.session_state.csv)

    if ttype == "DGS":
        apply_dgs(row)
    elif ttype == "SEAL":
        apply_seal(row)

st.title(PANELS[st.session_state.panel]["name"])
st.image(render(st.session_state.panel), use_container_width=True)

if st.session_state.csv is not None:
    st.markdown(f"**Step {st.session_state.step+1} / {len(st.session_state.csv)}**")

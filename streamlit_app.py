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
    "panel": "seal",
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

def detect_test_type(df):
    if "TST_SepSealControlTyp" in df.columns:
        return "SEAL"
    return "UNKNOWN"

# =========================================================
# SEPARATION SEAL LOGIC (WITH FLOW THRESHOLD)
# =========================================================
def apply_seal(row):
    vs = st.session_state.valve_states
    vs.clear()

    mode = int(csv_val(row, "TST_SepSealControlTyp"))

    # -------------------------------
    # PRESSURE SOURCE (shared)
    # -------------------------------
    p = max(csv_val(row, "TST_SepSealPSet1"), csv_val(row, "TST_SepSealPSet2"))
    if p > 0:
        if p <= 10:
            vs["V-108"] = True
        elif p <= 100:
            vs["V-107"] = True
        else:
            vs["V-106"] = True

    # -------------------------------
    # FLOW MODE
    # -------------------------------
    if mode == 0:
        f1 = csv_val(row, "TST_SepSealFlwSet1")
        f2 = csv_val(row, "TST_SepSealFlwSet2")

        if f1 > 0:
            vs["V-212"] = True
            vs["V-214"] = True
            if f1 > 500:
                vs["V-216"] = True   # NDE booster

        if f2 > 0:
            vs["V-213"] = True
            vs["V-215"] = True
            if f2 > 500:
                vs["V-217"] = True   # DE booster

    # -------------------------------
    # PRESSURE MODE
    # -------------------------------
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
        active = pipe_active(i, valves)
        draw.line(
            [(p["x1"], p["y1"]), (p["x2"], p["y2"])],
            fill=(0, 255, 0) if active else (90, 90, 110),
            width=6 if active else 4
        )

    for t, v in valves.items():
        open_ = st.session_state.valve_states.get(t)
        draw.ellipse(
            [v["x"] - 7, v["y"] - 7, v["x"] + 7, v["y"] + 7],
            fill=(0, 255, 0) if open_ else (255, 0, 0),
            outline="white"
        )
        draw.text((v["x"] + 10, v["y"] - 10), t, fill="white")

    return img

# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.title("Rig Control")

    st.session_state.panel = st.selectbox(
        "Panel", list(PANELS), format_func=lambda k: PANELS[k]["name"]
    )

    up = st.file_uploader("Upload Separation Seal CSV", type="csv")
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
                len(st.session_state.csv) - 1,
                st.session_state.step + 1
            )
            st.rerun()

# =========================================================
# MAIN
# =========================================================
if st.session_state.csv is not None:
    row = st.session_state.csv.iloc[st.session_state.step]
    apply_seal(row)

st.title(PANELS[st.session_state.panel]["name"])
st.image(render(st.session_state.panel), use_container_width=True)

# =========================================================
# STEP TABLE (NEW)
# =========================================================
if st.session_state.csv is not None:
    st.markdown("### 🧾 Test Steps (Current Highlighted)")
    df = st.session_state.csv.copy()
    df.insert(0, "STEP", range(1, len(df) + 1))

    st.dataframe(
        df,
        height=300,
        use_container_width=True
    )

    st.markdown(
        f"**▶ Current Step:** {st.session_state.step + 1} / {len(df)}"
    )

import streamlit as st
import pandas as pd
import json
import os
import time
from PIL import Image, ImageDraw

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="Rig Simulation Platform",
    page_icon="🏭",
    layout="wide"
)

# =========================================================
# SESSION STATE
# =========================================================
if "page" not in st.session_state:
    st.session_state.page = "home"

if "valve_states" not in st.session_state:
    st.session_state.valve_states = {}

if "csv" not in st.session_state:
    st.session_state.csv = None

if "step" not in st.session_state:
    st.session_state.step = 0

if "playing" not in st.session_state:
    st.session_state.playing = False

if "step_start_time" not in st.session_state:
    st.session_state.step_start_time = None

# =========================================================
# SYSTEM DEFINITIONS (SUPPLY SHOWN – OTHERS KEPT)
# =========================================================
SYSTEMS = {
    "supply": {
        "name": "⚡ Pressure Supply",
        "valves": "data/valves_pressure_in.json",
        "pipes": "data/pipes_pressure_in.json",
        "image": "assets/p&id_pressure_in.png",
    }
}

# =========================================================
# LOADERS
# =========================================================
def load_json(path):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {} if "valves" in path else []


def load_csv(upload):
    return pd.read_csv(upload, sep=";")


# =========================================================
# CSV → VALVE LOGIC (ALIGNED TO YOUR VALVES)
# =========================================================
def apply_csv_to_valves(valves, row):
    cell_pressure = float(row["TST_CellPresDemand"])
    inter_pressure = float(row["TST_InterPresDemand"])

    for tag in valves:
        # Cell pressure inlet
        if tag == "V-201":
            st.session_state.valve_states[tag] = cell_pressure > 0

        # Inter / supply manifold
        elif tag.startswith("V-10"):
            st.session_state.valve_states[tag] = inter_pressure > 0


# =========================================================
# STEP SEQUENCER
# =========================================================
def advance_step_if_needed():
    df = st.session_state.csv
    step = st.session_state.step
    duration = float(df.iloc[step]["TST_StepDuration"])
    now = time.time()

    if st.session_state.step_start_time is None:
        st.session_state.step_start_time = now
        return

    if now - st.session_state.step_start_time >= max(duration, 0.1):
        st.session_state.step += 1
        st.session_state.step_start_time = now

        if st.session_state.step >= len(df):
            st.session_state.step = len(df) - 1
            st.session_state.playing = False
            st.session_state.step_start_time = None


# =========================================================
# PIPE ACTIVE CHECK (FIXED FOR YOUR JSON)
# =========================================================
def pipe_active(pipe_idx, valves):
    pipe_no = pipe_idx + 1

    for tag, data in valves.items():
        if st.session_state.valve_states.get(tag, False):
            connected = data.get("pipes_pressure_in.json", [])
            if pipe_no in connected:
                return True
    return False


# =========================================================
# P&ID RENDER
# =========================================================
def render_pid(image_path, valves, pipes):
    if os.path.exists(image_path):
        img = Image.open(image_path).convert("RGBA")
    else:
        img = Image.new("RGBA", (900, 600), (40, 40, 60))

    draw = ImageDraw.Draw(img)

    # Pipes
    for i, pipe in enumerate(pipes):
        active = pipe_active(i, valves)
        color = (0, 255, 0) if active else (70, 70, 100)
        width = 6 if active else 4
        draw.line(
            [(pipe["x1"], pipe["y1"]), (pipe["x2"], pipe["y2"])],
            fill=color,
            width=width,
        )

    # Valves
    for tag, valve in valves.items():
        x, y = valve["x"], valve["y"]
        open_ = st.session_state.valve_states.get(tag, False)
        color = (0, 255, 0) if open_ else (255, 0, 0)
        draw.ellipse([x - 7, y - 7, x + 7, y + 7], fill=color, outline="white", width=2)
        draw.text((x + 10, y - 10), tag, fill="white")

    return img.convert("RGB")


# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.title("🏭 Rig Control")

    csv_file = st.file_uploader("Upload CSV", type=["csv"])
    if csv_file:
        st.session_state.csv = load_csv(csv_file)
        st.session_state.step = 0
        st.session_state.playing = False
        st.session_state.step_start_time = None
        st.success("CSV Loaded")

    if st.session_state.csv is not None:
        if st.button("▶ Play"):
            st.session_state.playing = True
            st.session_state.step_start_time = None

        if st.button("⏸ Pause"):
            st.session_state.playing = False


# =========================================================
# MAIN (SUPPLY SYSTEM)
# =========================================================
cfg = SYSTEMS["supply"]

valves = load_json(cfg["valves"])
pipes = load_json(cfg["pipes"])

for v in valves:
    st.session_state.valve_states.setdefault(v, False)

if st.session_state.csv is not None:
    row = st.session_state.csv.iloc[st.session_state.step]
    apply_csv_to_valves(valves, row)

    if st.session_state.playing:
        advance_step_if_needed()
        time.sleep(0.05)
        st.rerun()

# =========================================================
# STATUS
# =========================================================
st.markdown("## ⏱ Test Step Status")

total = len(st.session_state.csv)
current = st.session_state.step + 1
duration = float(row["TST_StepDuration"])
elapsed = (
    0 if st.session_state.step_start_time is None
    else time.time() - st.session_state.step_start_time
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Step", f"{current}/{total}")
c2.metric("Duration (s)", duration)
c3.metric("Elapsed (s)", f"{elapsed:.1f}")
c4.metric("State", "▶ PLAYING" if st.session_state.playing else "⏸ PAUSED")

# =========================================================
# P&ID VIEW
# =========================================================
st.title(cfg["name"])
img = render_pid(cfg["image"], valves, pipes)
st.image(img, use_container_width=True, caption="Green = Flow | Red = Closed Valve")

with st.expander("🔍 CSV Row"):
    st.write(row)

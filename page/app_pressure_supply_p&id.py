import streamlit as st
from PIL import Image, ImageDraw
import json
import math

st.set_page_config(layout="wide", page_title="Rig Simulation")

# ===================== CONFIG – CHANGE ONLY THESE 3 LINES PER P&ID =====================
SYSTEM_NAME = "Pressure Supply"                   
PID_FILE = "p&id_pressure_in.png"                   
VALVES_FILE = "valves_pressure_in.json"             
PIPES_FILE = "pipes_pressure_in.json"               
PRESSURE_SOURCES = [1, 3, 7]
# ===================== LOAD DATA =====================
def load_json(file):
    try:
        with open(file) as f:
            return json.load(f)
    except:
        st.error(f"Missing {file} — create it first!")
        return {} if "valves" in file else []

valves = load_json(VALVES_FILE)
pipes = load_json(PIPES_FILE)

# ===================== SESSION STATE (shared across all P&IDs) =====================
if "valve_states" not in st.session_state:
    st.session_state.valve_states = {tag: False for tag in valves}
if "selected_pipe" not in st.session_state:
    st.session_state.selected_pipe = None

# ===================== AUTOMATIC LEADER DETECTION (no hard-coding!) =====================
def find_leader_of_pipe(pipe_idx):
    pipe = pipes[pipe_idx]
    best_dist = float('inf')
    best_leader = None
    for tag, vdata in valves.items():
        if not st.session_state.valve_states.get(tag, False):
            continue
        dist = math.hypot(vdata["x"] - pipe["x1"], vdata["y"] - pipe["y1"])
        if dist < best_dist and dist <= 60:          # 60px tolerance
            best_dist = dist
            best_leader = pipe_idx
    return best_leader

def get_active_leaders():
    active = set()
    for i in range(len(pipes)):
        if find_leader_of_pipe(i) is not None:
            active.add(i)
    return active

# ===================== PRESSURE + FLOW LOGIC =====================
def get_pipe_status(idx):
    num = idx + 1
    active_leaders = get_active_leaders()

    # Has flow? (any open valve controls this pipe directly or via chain)
    has_flow = idx in active_leaders

    # Has pressure? (from source or upstream open path)
    has_pressure = num in PRESSURE_SOURCES
    if not has_pressure:
        for leader_idx in active_leaders:
            leader_num = leader_idx + 1
            if leader_num in PRESSURE_SOURCES:
                # Simple propagation: if upstream leader is active → pressure reaches here
                has_pressure = True
                break

    return has_flow, has_pressure

# ===================== RENDER =====================
def render():
    img = Image.open(PID_FILE).convert("RGBA")
    draw = ImageDraw.Draw(img)

    for i, pipe in enumerate(pipes):
        has_flow, has_pressure = get_pipe_status(i)
        if i == st.session_state.selected_pipe:
            color = (180, 0, 255)          # Purple = selected
        elif has_flow and has_pressure:
            color = (0, 255, 0)            # Green = flowing
        elif has_pressure:
            color = (100, 180, 255)        # Light blue = pressurized
        else:
            color = (60, 60, 100)          # Dark = empty

        w = 9 if i == st.session_state.selected_pipe else 6
        draw.line([(pipe["x1"], pipe["y1"]), (pipe["x2"], pipe["y2"])], fill=color, width=w)

        if i == st.session_state.selected_pipe:
            draw.ellipse([pipe["x1"]-7, pipe["y1"]-7, pipe["x1"]+7, pipe["y1"]+7], fill="red", outline="white", width=2)
            draw.ellipse([pipe["x2"]-7, pipe["y2"]-7, pipe["x2"]+7, pipe["y2"]+7], fill="red", outline="white", width=2)

    # Draw valves
    for tag, v in valves.items():
        color = (0, 255, 0) if st.session_state.valve_states.get(tag, False) else (255, 0, 0)
        draw.ellipse([v["x"]-12, v["y"]-12, v["x"]+12, v["y"]+12], fill=color, outline="white", width=3)
        draw.text((v["x"]+15, v["y"]-15), tag, fill="white", stroke_fill="black", stroke_width=2)

    return img.convert("RGB")

# ===================== UI =====================
st.title(f"Rig Simulation – {SYSTEM_NAME}")

with st.sidebar:
    st.header("Valve Controls")
    for tag in valves:
        state = st.session_state.valve_states.get(tag, False)
        label = f"{'OPEN' if state else 'CLOSED'} {tag}"
        if st.button(label, key=tag, use_container_width=True):
            st.session_state.valve_states[tag] = not state
            st.rerun()

    st.markdown("---")
    st.header("Pipe Selection")
    if st.button("Unselect Pipe", use_container_width=True):
        st.session_state.selected_pipe = None
        st.rerun()
    for i in range(len(pipes)):
        icon = "Selected" if i == st.session_state.selected_pipe else "Pipe"
        if st.button(f"{icon} {i+1}", key=f"p{i}", use_container_width=True):
            st.session_state.selected_pipe = i
            st.rerun()

col1, col2 = st.columns([3, 1])
with col1:
    st.image(render(), use_container_width=True,
             caption="Green = Flowing | Light Blue = Pressurized | Dark = Empty | Purple = Selected")

with col2:
    st.header("Live Status")
    flowing = sum(1 for i in range(len(pipes)) if get_pipe_status(i)[0])
    pressurized = sum(1 for i in range(len(pipes)) if get_pipe_status(i)[1])
    st.metric("Flowing Pipes", flowing)
    st.metric("Pressurized Pipes", pressurized)
    st.metric("Empty Pipes", len(pipes) - pressurized)

st.success(f"Universal simulator ready → Works with ANY valve tags & pipe layout!")
st.caption("Just change the 5 config lines at the top for each P&ID")

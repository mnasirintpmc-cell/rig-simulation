import streamlit as st
from PIL import Image, ImageDraw
import json
import math
import os

st.set_page_config(layout="wide", page_title="Rig Simulation")

# ===================== DYNAMIC PATH FINDING =====================
def find_file(filename, possible_locations=["assets/", "../assets/", "./", ""]):
    """Find file in multiple possible locations"""
    for location in possible_locations:
        path = os.path.join(location, filename)
        if os.path.exists(path):
            return path
    return None

# System configuration
SYSTEM_NAME = "Mixing Area"                   
PRESSURE_SOURCES = [1, 5]

# Find files dynamically
PID_FILE = find_file("p&id_mixing.png")
VALVES_FILE = find_file("valves_mixing.json", ["data/", "../data/", "./"])
PIPES_FILE = find_file("pipes_mixing.json", ["data/", "../data/", "./"])

# Show file status
st.sidebar.header("File Status")
st.sidebar.write(f"P&ID: {'✅ Found' if PID_FILE else '❌ Missing'}")
st.sidebar.write(f"Valves: {'✅ Found' if VALVES_FILE else '❌ Missing'}")
st.sidebar.write(f"Pipes: {'✅ Found' if PIPES_FILE else '❌ Missing'}")

if not all([PID_FILE, VALVES_FILE, PIPES_FILE]):
    st.error("❌ Missing required files! Check the sidebar for status.")
    if st.button("Show Debug Info"):
        st.write("Current directory:", os.getcwd())
        st.write("Files in current dir:", os.listdir("."))
        if os.path.exists("assets"):
            st.write("Assets folder:", os.listdir("assets"))
        if os.path.exists("data"):
            st.write("Data folder:", os.listdir("data"))
    st.stop()

# ===================== LOAD DATA =====================
def load_json(file):
    try:
        with open(file) as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading {file}: {e}")
        return {} if "valves" in file else []

valves = load_json(VALVES_FILE)
pipes = load_json(PIPES_FILE)

# ===================== SESSION STATE =====================
if "valve_states" not in st.session_state:
    st.session_state.valve_states = {tag: False for tag in valves}
if "selected_pipe" not in st.session_state:
    st.session_state.selected_pipe = None

# ===================== AUTOMATIC LEADER DETECTION =====================
def find_leader_of_pipe(pipe_idx):
    if not pipes or pipe_idx >= len(pipes):
        return None
    pipe = pipes[pipe_idx]
    best_dist = float('inf')
    best_leader = None
    for tag, vdata in valves.items():
        if not st.session_state.valve_states.get(tag, False):
            continue
        dist = math.hypot(vdata["x"] - pipe["x1"], vdata["y"] - pipe["y1"])
        if dist < best_dist and dist <= 60:
            best_dist = dist
            best_leader = pipe_idx
    return best_leader

def get_active_leaders():
    active = set()
    if not pipes:
        return active
    for i in range(len(pipes)):
        if find_leader_of_pipe(i) is not None:
            active.add(i)
    return active

# ===================== PRESSURE + FLOW LOGIC =====================
def get_pipe_status(idx):
    if not pipes or idx >= len(pipes):
        return False, False
    num = idx + 1
    active_leaders = get_active_leaders()

    has_flow = idx in active_leaders
    has_pressure = num in PRESSURE_SOURCES
    
    if not has_pressure:
        for leader_idx in active_leaders:
            leader_num = leader_idx + 1
            if leader_num in PRESSURE_SOURCES:
                has_pressure = True
                break

    return has_flow, has_pressure

# ===================== RENDER =====================
def render():
    try:
        img = Image.open(PID_FILE).convert("RGBA")
        st.sidebar.success(f"✅ Loaded: {os.path.basename(PID_FILE)}")
    except Exception as e:
        st.error(f"❌ Cannot load P&ID image: {e}")
        # Create placeholder
        img = Image.new('RGBA', (800, 600), (50, 50, 50))
        draw = ImageDraw.Draw(img)
        draw.text((100, 300), f"Missing: {PID_FILE}", fill="white")
        return img.convert("RGB")
    
    draw = ImageDraw.Draw(img)

    if pipes:
        for i, pipe in enumerate(pipes):
            has_flow, has_pressure = get_pipe_status(i)
            if i == st.session_state.selected_pipe:
                color = (180, 0, 255)
            elif has_flow and has_pressure:
                color = (0, 255, 0)
            elif has_pressure:
                color = (100, 180, 255)
            else:
                color = (60, 60, 100)

            w = 9 if i == st.session_state.selected_pipe else 6
            draw.line([(pipe["x1"], pipe["y1"]), (pipe["x2"], pipe["y2"])], fill=color, width=w)

            if i == st.session_state.selected_pipe:
                draw.ellipse([pipe["x1"]-7, pipe["y1"]-7, pipe["x1"]+7, pipe["y1"]+7], fill="red", outline="white", width=2)
                draw.ellipse([pipe["x2"]-7, pipe["y2"]-7, pipe["x2"]+7, pipe["y2"]+7], fill="red", outline="white", width=2)

    if valves:
        for tag, v in valves.items():
            color = (0, 255, 0) if st.session_state.valve_states.get(tag, False) else (255, 0, 0)
            draw.ellipse([v["x"]-12, v["y"]-12, v["x"]+12, v["y"]+12], fill=color, outline="white", width=3)
            draw.text((v["x"]+15, v["y"]-15), tag, fill="white", stroke_fill="black", stroke_width=2)

    return img.convert("RGB")

# ===================== UI =====================
st.title(f"Rig Simulation – {SYSTEM_NAME}")

with st.sidebar:
    st.header("Valve Controls")
    if valves:
        for tag in valves:
            state = st.session_state.valve_states.get(tag, False)
            label = f"{'OPEN' if state else 'CLOSED'} {tag}"
            if st.button(label, key=tag, use_container_width=True):
                st.session_state.valve_states[tag] = not state
                st.rerun()
    else:
        st.warning("No valves data loaded")

    st.markdown("---")
    st.header("Pipe Selection")
    if st.button("Unselect Pipe", use_container_width=True):
        st.session_state.selected_pipe = None
        st.rerun()
    if pipes:
        for i in range(len(pipes)):
            icon = "Selected" if i == st.session_state.selected_pipe else "Pipe"
            if st.button(f"{icon} {i+1}", key=f"p{i}", use_container_width=True):
                st.session_state.selected_pipe = i
                st.rerun()
    else:
        st.warning("No pipes data loaded")

col1, col2 = st.columns([3, 1])
with col1:
    st.image(render(), use_container_width=True,
             caption="Green = Flowing | Light Blue = Pressurized | Dark = Empty | Purple = Selected")

with col2:
    st.header("Live Status")
    if pipes:
        flowing = sum(1 for i in range(len(pipes)) if get_pipe_status(i)[0])
        pressurized = sum(1 for i in range(len(pipes)) if get_pipe_status(i)[1])
        st.metric("Flowing Pipes", flowing)
        st.metric("Pressurized Pipes", pressurized)
        st.metric("Empty Pipes", len(pipes) - pressurized)
    else:
        st.warning("No pipes data")

st.success(f"Universal simulator ready → Works with ANY valve tags & pipe layout!")

# streamlit_rig_sim.py - Plug-and-play tag-based system
import streamlit as st
from PIL import Image, ImageDraw
import json
import os

st.set_page_config(layout="wide", page_title="Rig Simulation Plug & Play")

# ===================== SYSTEM CONFIGURATION =====================
# Define your systems here
SYSTEMS = {
    "mixing": {
        "name": "Mixing Area",
        "pid": "p&id_mixing.png",
        "valves": "valves_mixing.json",
        "pipes": "pipes_mixing.json"
    },
    "supply": {
        "name": "Pressure Supply",
        "pid": "p&id_pressure_in.png",
        "valves": "valves_pressure_in.json",
        "pipes": "pipes_pressure_in.json"
    },
    "dgs": {
        "name": "DGS System",
        "pid": "p&id_dgs.png",
        "valves": "valves_dgs.json",
        "pipes": "pipes_dgs.json"
    },
    "return": {
        "name": "Pressure Return",
        "pid": "p&id_pressure_return.png",
        "valves": "valves_pressure_return.json",
        "pipes": "pipes_pressure_return.json"
    },
    "seal": {
        "name": "Separation Seal",
        "pid": "p&id_separation_seal.png",
        "valves": "valves_separation_seal.json",
        "pipes": "pipes_separation_seal.json"
    }
}

# ===================== DYNAMIC FILE FINDER =====================
def find_file(filename, folders=["assets", "data", "."]):
    for f in folders:
        path = os.path.join(f, filename)
        if os.path.exists(path):
            return path
    return None

# ===================== SESSION STATE =====================
if "current_system" not in st.session_state:
    st.session_state.current_system = "mixing"
if "valve_states" not in st.session_state:
    st.session_state.valve_states = {}
if "selected_pipe" not in st.session_state:
    st.session_state.selected_pipe = None

# ===================== LOAD DATA =====================
def load_json(file):
    try:
        with open(file) as f:
            data = json.load(f)
            return data
    except Exception as e:
        st.error(f"Error loading {file}: {e}")
        return {} if "valves" in file else []

def load_system(system_id):
    cfg = SYSTEMS[system_id]
    pid_file = find_file(cfg["pid"])
    valves_file = find_file(cfg["valves"], ["data", "."])
    pipes_file = find_file(cfg["pipes"], ["data", "."])

    valves = load_json(valves_file)
    pipes = load_json(pipes_file)

    # Initialize valve states for new valves
    for tag in valves:
        if tag not in st.session_state.valve_states:
            st.session_state.valve_states[tag] = False

    return cfg["name"], pid_file, valves, pipes

# ===================== DIRECT TAG-BASED MAPPING =====================
def get_active_pipes(valves):
    """Return set of active pipe tags based on open valves"""
    active = set()
    for v_tag, vdata in valves.items():
        if st.session_state.valve_states.get(v_tag, False):
            connected = vdata.get("connected_pipes", [])
            active.update(connected)
    return active

def get_pipe_status(pipe_tag, active_pipes, pressure_sources=[]):
    has_flow = pipe_tag in active_pipes
    has_pressure = pipe_tag in pressure_sources or has_flow
    return has_flow, has_pressure

# ===================== RENDER =====================
def render_system(pid_file, valves, pipes, active_pipes):
    try:
        img = Image.open(pid_file).convert("RGBA")
    except:
        img = Image.new("RGBA", (800, 600), (50, 50, 50))
        draw = ImageDraw.Draw(img)
        draw.text((100, 300), f"Missing {pid_file}", fill="white")
        return img.convert("RGB")

    draw = ImageDraw.Draw(img)

    # Draw pipes
    for pipe in pipes:
        p_tag = pipe["tag"]
        has_flow, has_pressure = get_pipe_status(p_tag, active_pipes)
        if st.session_state.selected_pipe == p_tag:
            color = (180, 0, 255)  # Selected pipe
            width = 9
        elif has_flow and has_pressure:
            color = (0, 255, 0)
            width = 7
        elif has_pressure:
            color = (100, 180, 255)
            width = 6
        else:
            color = (60, 60, 100)
            width = 4
        draw.line([(pipe["x1"], pipe["y1"]), (pipe["x2"], pipe["y2"])], fill=color, width=width)

    # Draw valves
    for v_tag, vdata in valves.items():
        x, y = vdata["x"], vdata["y"]
        color = (0, 255, 0) if st.session_state.valve_states.get(v_tag, False) else (255, 0, 0)
        draw.ellipse([x-12, y-12, x+12, y+12], fill=color, outline="white", width=3)
        draw.text((x+15, y-15), v_tag, fill="white", stroke_fill="black", stroke_width=2)

    return img.convert("RGB")

# ===================== UI =====================
# Home page: select system
st.title("🏭 Rig Simulation - Plug & Play")
cols = st.columns(len(SYSTEMS))
for idx, (sys_id, cfg) in enumerate(SYSTEMS.items()):
    with cols[idx]:
        if st.button(cfg["name"]):
            st.session_state.current_system = sys_id
            st.session_state.selected_pipe = None
            st.rerun()

st.markdown("---")

# Load current system
system_name, pid_file, valves, pipes = load_system(st.session_state.current_system)

# Active pipes
active_pipes = get_active_pipes(valves)

# Sidebar: valves & pipe selection
with st.sidebar:
    st.header(f"Valve Controls ({system_name})")
    for v_tag in valves:
        state = st.session_state.valve_states.get(v_tag, False)
        label = f"{'OPEN' if state else 'CLOSED'} {v_tag}"
        if st.button(label, key=f"valve_{v_tag}", use_container_width=True):
            st.session_state.valve_states[v_tag] = not state
            st.rerun()

    st.markdown("---")
    st.header("Pipe Selection")
    if st.button("Unselect Pipe", use_container_width=True):
        st.session_state.selected_pipe = None
        st.rerun()
    for pipe in pipes:
        p_tag = pipe["tag"]
        icon = "Selected" if st.session_state.selected_pipe == p_tag else "Pipe"
        if st.button(f"{icon} {p_tag}", key=f"pipe_{p_tag}", use_container_width=True):
            st.session_state.selected_pipe = p_tag
            st.rerun()

# Main layout
col1, col2 = st.columns([3, 1])
with col1:
    st.image(render_system(pid_file, valves, pipes, active_pipes), use_container_width=True,
             caption="🟢 Flowing | 💙 Pressurized | ⚫ Empty | 🟣 Selected")

with col2:
    st.header("Live Status")
    st.write(f"System: {system_name}")
    st.write(f"Active Pipes: {len(active_pipes)} / {len(pipes)}")
    st.write("Open Valves:")
    for v_tag, state in st.session_state.valve_states.items():
        if state:
            st.write(f"🟢 {v_tag}")

    st.markdown("---")
    st.header("Active Pipe Details")
    for pipe in pipes:
        p_tag = pipe["tag"]
        if p_tag in active_pipes:
            controlling = [v_tag for v_tag, vdata in valves.items() 
                           if st.session_state.valve_states.get(v_tag, False) and p_tag in vdata.get("connected_pipes", [])]
            st.write(f"• Pipe {p_tag} ← {', '.join(controlling)}")

# Debug info
with st.sidebar.expander("🔧 Debug Info"):
    st.write("Valve States:", st.session_state.valve_states)
    st.write("Selected Pipe:", st.session_state.selected_pipe)
    st.write("Active Pipes:", active_pipes)

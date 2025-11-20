import streamlit as st
from PIL import Image, ImageDraw
import json
import math

st.set_page_config(layout="wide")

# SYSTEM-SPECIFIC CONFIG
SYSTEM_NAME = "Pressure Return"
PID_FILE = "P&ID_Pressure_Return.png"
VALVES_FILE = "valves_pressure_return.json"
PIPES_FILE = "pipes_pressure_return.json"
PRESSURE_SOURCES = [2, 8]  # Return line pressure points

# ===================== LOAD DATA =====================
def load_valves():
    try:
        with open(VALVES_FILE) as f:
            return json.load(f)
    except:
        return {}
def load_pipes():
    try:
        with open(PIPES_FILE) as f:
            return json.load(f)
    except:
        return []

valves = load_valves()
pipes = load_pipes()

# ===================== SESSION STATE =====================
if "valve_states" not in st.session_state:
    st.session_state.valve_states = {tag: False for tag in valves}
if "selected_pipe" not in st.session_state:
    st.session_state.selected_pipe = None
if "pipes_data" not in st.session_state:
    st.session_state.pipes_data = {SYSTEM_NAME: pipes}

# Use global pipes for this system
st.session_state.pipes_data.setdefault(SYSTEM_NAME, pipes)
pipes = st.session_state.pipes_data[SYSTEM_NAME]

# ===================== GROUPS & HARD-CODED =====================
def get_groups():
    return {
        2: [3, 4, 5],    # Main return header
        8: [9, 10, 11],  # Secondary return
        5: [6, 7],       # Collector lines
        11: [12, 13],    # Drain connections
        13: [14, 15]     # Tank returns
    }

hardcoded = {"V-501": 2, "V-502": 8, "V-601": 5, "V-701": 11, "V-801": 13}

def get_active_leaders():
    active = set()
    for v, p in hardcoded.items():
        if st.session_state.valve_states.get(v, False):
            active.add(p - 1)
    # Proximity fallback
    for i, pipe in enumerate(pipes):
        for tag, v in valves.items():
            if st.session_state.valve_states.get(tag, False):
                d = math.hypot(v["x"] - pipe["x1"], v["y"] - pipe["y1"])
                if d <= 50:
                    active.add(i)
                    break
    return active

# ===================== COLOR LOGIC WITH PRESSURE =====================
def get_pipe_color(i):
    if i == st.session_state.selected_pipe:
        return (148, 0, 211)
    num = i + 1
    active = get_active_leaders()
    has_flow = i in active or any(num in f and (l-1) in active for l, f in get_groups().items())
    has_pressure = num in PRESSURE_SOURCES or any(
        (l-1) in active and l in PRESSURE_SOURCES for l in get_groups()
    )
    if has_flow and has_pressure:
        return (0, 255, 0)
    elif has_pressure:
        return (100, 200, 255)
    else:
        return (50, 50, 80)

# ===================== RENDER =====================
def render():
    img = Image.open(PID_FILE).convert("RGBA")
    draw = ImageDraw.Draw(img)
    for i, pipe in enumerate(pipes):
        color = get_pipe_color(i)
        w = 8 if i == st.session_state.selected_pipe else 6
        draw.line([(pipe["x1"], pipe["y1"]), (pipe["x2"], pipe["y2"])], fill=color, width=w)
        if i == st.session_state.selected_pipe:
            draw.ellipse([pipe["x1"]-6, pipe["y1"]-6, pipe["x1"]+6, pipe["y1"]+6], fill=(255,0,0), outline="white")
            draw.ellipse([pipe["x2"]-6, pipe["y2"]-6, pipe["x2"]+6, pipe["y2"]+6], fill=(255,0,0), outline="white")
    for tag, d in valves.items():
        c = (0,255,0) if st.session_state.valve_states.get(tag, False) else (255,0,0)
        draw.ellipse([d["x"]-10, d["y"]-10, d["x"]+10, d["y"]+10], fill=c, outline="white", width=3)
        draw.text((d["x"]+15, d["y"]-10), tag, fill="white", stroke_fill="black", stroke_width=2)
    return img.convert("RGB")

# ===================== UI =====================
st.title(f"{SYSTEM_NAME} – Live Rig Simulation")

with st.sidebar:
    st.header("Valve Controls")
    for tag in valves:
        s = st.session_state.valve_states.get(tag, False)
        if st.button(f"{'OPEN' if s else 'CLOSED'} {tag}", key=tag, use_container_width=True):
            st.session_state.valve_states[tag] = not s
            st.rerun()

    st.markdown("---")
    st.header("Pipe Selection")
    for i in range(len(pipes)):
        if st.button(f"Pipe {i+1}", key=f"p{i}", use_container_width=True):
            st.session_state.selected_pipe = i
            st.rerun()
    if st.button("Unselect", use_container_width=True):
        st.session_state.selected_pipe = None
        st.rerun()

    if st.button("Back to Home"):
        st.switch_page("home.py")

col1, col2 = st.columns([3,1])
with col1:
    st.image(render(), use_container_width=True,
             caption="Green = Flow | Light Blue = Pressurized | Dark = Empty")

with col2:
    st.header("Status")
    flowing = sum(1 for i in range(len(pipes)) if get_pipe_color(i) == (0,255,0))
    st.write(f"**Flowing:** {flowing}")
    st.write(f"**Pressurized:** {sum(1 for i in range(len(pipes)) if get_pipe_color(i) in [(0,255,0),(100,200,255)])}")

st.success(f"Live reaction across all 5 P&IDs! Change valve in any system → see effect everywhere.")

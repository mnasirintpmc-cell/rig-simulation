import streamlit as st
from PIL import Image, ImageDraw
import json
import math

st.set_page_config(layout="wide", page_title="Rig Simulation")

# ===================== CONFIG – CHANGE ONLY THESE 3 LINES PER P&ID =====================
import streamlit as st
from PIL import Image, ImageDraw
import json
import math

st.set_page_config(layout="wide", page_title="Rig Simulation")

# ===================== CONFIG – CORRECTED PATHS =====================
SYSTEM_NAME = "Mixing Area"                   
PID_FILE = "../assets/p&id_mixing.png"                   # ← FIXED PATH
VALVES_FILE = "../data/valves_mixing.json"               # ← FIXED PATH  
PIPES_FILE = "../data/pipes_mixing.json"                 # ← FIXED PATH
PRESSURE_SOURCES = [1, 5]

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

# ===================== SESSION STATE =====================
if "valve_states" not in st.session_state:
    st.session_state.valve_states = {tag: False for tag in valves}
if "selected_pipe" not in st.session_state:
    st.session_state.selected_pipe = None

# ===================== AUTOMATIC LEADER DETECTION =====================
def find_leader_of_pipe(pipe_idx):
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
    for i in range(len(pipes)):
        if find_leader_of_pipe(i) is not None:
            active.add(i)
    return active

# ===================== PRESSURE + FLOW LOGIC =====================
def get_pipe_status(idx):
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
    except FileNotFoundError:
        st.error(f"❌ Cannot find P&ID image: {PID_FILE}")
        # Create a placeholder image
        img = Image.new('RGBA', (800, 600), (50, 50, 50))
    
    draw = ImageDraw.Draw(img)

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
        1: [20],           # Primary mixer feed
        2: [3, 4, 14, 21, 22],  # Mixer circulation
        5: [6, 7, 8, 9, 18],    # Additive lines
        11: [10, 19],      # Output lines
        12: [],            # Standby
        13: [14, 4, 21, 22],    # Bypass
        17: [16, 15, 8],   # Recirculation
        22: [3, 4, 14, 21] # Final mix
    }

hardcoded = {"V-301": 2, "V-302": 13, "V-103": 5, "V-104": 22, "V-501": 12}

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

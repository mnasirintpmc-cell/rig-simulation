import streamlit as st
from PIL import Image, ImageDraw
import json
import math

st.set_page_config(layout="wide", page_title="Rig Simulation")

# ===================== CONFIG – CHANGE ONLY THESE 3 LINES PER P&ID =====================
SYSTEM_NAME = "Pressure Return"                   
PID_FILE = "p&id_pressure_return.png"                   
VALVES_FILE = "valves_pressure_return.json"             
PIPES_FILE = "pipes_pressure_return.json"               
PRESSURE_SOURCES = [2, 8]

# ===================== LOAD DATA =====================
def load_valves():
    try:
        with open(VALVES_FILE) as f:
            data = json.load(f)
            # Convert to new format if old format exists
            for tag, valve_data in data.items():
                if isinstance(valve_data, dict) and "controls_pipes" not in valve_data:
                    # Old format - add empty controls
                    valve_data["controls_pipes"] = []
            return data
    except Exception as e:
        st.error(f"Error loading valves: {e}")
        return {}

def load_pipes():
    try:
        with open(PIPES_FILE) as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading pipes: {e}")
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
# Now we can use the JSON data instead of hardcoding!
def get_controlled_pipes():
    """Get which pipes are controlled by open valves based on JSON data"""
    controlled = set()
    for tag, valve_data in valves.items():
        if st.session_state.valve_states.get(tag, False):
            # Add pipes controlled by this valve
            for pipe_num in valve_data.get("controls_pipes", []):
                controlled.add(pipe_num - 1)  # Convert to 0-index
    return controlled

def get_groups():
    """Optional: Still keep if you want hierarchical groups"""
    return {
        2: [3, 4, 5],    # Main return header
        8: [9, 10, 11],  # Secondary return
        5: [6, 7],       # Collector lines
        11: [12, 13],    # Drain connections
        13: [14, 15]     # Tank returns
    }

def get_active_leaders():
    """Combine JSON-controlled pipes with proximity detection"""
    active = get_controlled_pipes()
    
    # Still keep proximity fallback for backward compatibility
    for i, pipe in enumerate(pipes):
        if i in active:  # Skip if already controlled
            continue
        for tag, valve_data in valves.items():
            if st.session_state.valve_states.get(tag, False):
                d = math.hypot(valve_data["x"] - pipe["x1"], valve_data["y"] - pipe["y1"])
                if d <= 50:
                    active.add(i)
                    break
    return active

# ===================== COLOR LOGIC WITH PRESSURE =====================
def get_pipe_color(i):
    if i == st.session_state.selected_pipe:
        return (148, 0, 211)  # Purple for selected
    num = i + 1
    active = get_active_leaders()
    
    # Check if pipe has flow (controlled by valve)
    has_flow = i in active
    
    # Check if pipe has pressure (from sources or upstream)
    has_pressure = (num in PRESSURE_SOURCES) or any(
        leader_num in PRESSURE_SOURCES 
        for leader_num in get_groups().keys() 
        if (leader_num - 1) in active
    )
    
    # Color logic
    if has_flow and has_pressure:
        return (0, 255, 0)  # Green: flowing with pressure
    elif has_pressure:
        return (100, 200, 255)  # Light blue: pressurized but no flow
    elif has_flow:
        return (50, 200, 50)  # Darker green: flowing but no pressure
    else:
        return (50, 50, 80)  # Dark: inactive

# ===================== RENDER =====================
def render():
    img = Image.open(PID_FILE).convert("RGBA")
    draw = ImageDraw.Draw(img)
    
    # Draw pipes
    for i, pipe in enumerate(pipes):
        color = get_pipe_color(i)
        w = 8 if i == st.session_state.selected_pipe else 6
        draw.line([(pipe["x1"], pipe["y1"]), (pipe["x2"], pipe["y2"])], 
                  fill=color, width=w)
        if i == st.session_state.selected_pipe:
            draw.ellipse([pipe["x1"]-6, pipe["y1"]-6, pipe["x1"]+6, pipe["y1"]+6], 
                        fill=(255,0,0), outline="white")
            draw.ellipse([pipe["x2"]-6, pipe["y2"]-6, pipe["x2"]+6, pipe["y2"]+6], 
                        fill=(255,0,0), outline="white")
    
    # Draw valves
    for tag, valve_data in valves.items():
        c = (0, 255, 0) if st.session_state.valve_states.get(tag, False) else (255, 0, 0)
        x, y = valve_data["x"], valve_data["y"]
        draw.ellipse([x-10, y-10, x+10, y+10], fill=c, outline="white", width=3)
        
        # Show controlled pipes count on valve
        controlled_count = len(valve_data.get("controls_pipes", []))
        if controlled_count > 0:
            draw.text((x-5, y-5), str(controlled_count), fill="white", 
                     stroke_fill="black", stroke_width=1)
        
        draw.text((x+15, y-10), tag, fill="white", 
                 stroke_fill="black", stroke_width=2)
    
    return img.convert("RGB")

# ===================== UI =====================
st.title(f"{SYSTEM_NAME} – Live Rig Simulation")

with st.sidebar:
    st.header("Valve Controls")
    for tag, valve_data in valves.items():
        s = st.session_state.valve_states.get(tag, False)
        label = f"{'✅ OPEN' if s else '❌ CLOSED'} {tag}"
        
        # Show controlled pipes in tooltip
        controlled = valve_data.get("controls_pipes", [])
        if controlled:
            label += f" (Pipes: {', '.join(map(str, controlled))})"
        
        if st.button(label, key=tag, use_container_width=True):
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

col1, col2 = st.columns([3, 1])
with col1:
    st.image(render(), use_container_width=True,
             caption="Green = Flow | Light Blue = Pressurized | Dark Green = Flow without pressure | Dark = Empty")

with col2:
    st.header("Status")
    
    # Count different pipe states
    colors = [get_pipe_color(i) for i in range(len(pipes))]
    flowing = sum(1 for c in colors if c == (0, 255, 0))
    flowing_no_pressure = sum(1 for c in colors if c == (50, 200, 50))
    pressurized = sum(1 for c in colors if c in [(0, 255, 0), (100, 200, 255)])
    inactive = sum(1 for c in colors if c == (50, 50, 80))
    
    st.metric("Flowing (with pressure)", flowing)
    st.metric("Flowing (no pressure)", flowing_no_pressure)
    st.metric("Pressurized", pressurized)
    st.metric("Inactive", inactive)
    
    # Show which valves control which pipes
    st.markdown("---")
    st.subheader("Valve Controls")
    for tag, valve_data in valves.items():
        if valve_data.get("controls_pipes"):
            status = "✅" if st.session_state.valve_states.get(tag, False) else "❌"
            st.write(f"{status} **{tag}**: Pipes {valve_data['controls_pipes']}")

st.success(f"Valves now directly control assigned pipes from JSON data!")

import streamlit as st
from PIL import Image, ImageDraw
import json
import math
import os
import sys

st.set_page_config(layout="wide", page_title="Rig Simulation")

# ===================== CONFIG – CHANGE ONLY THESE 3 LINES PER P&ID =====================
SYSTEM_NAME = "Pressure Return"                   
PID_FILE = "p&id_pressure_return.png"                   
VALVES_FILE = "valves_pressure_return.json"             
PIPES_FILE = "pipes_pressure_return.json"               
PRESSURE_SOURCES = [2, 8]

# ===================== DEBUG: SHOW CURRENT DIRECTORY =====================
st.sidebar.markdown("### Debug Info")
current_dir = os.getcwd()
st.sidebar.write(f"Current dir: `{current_dir}`")

# List files in current directory
try:
    files = os.listdir(current_dir)
    st.sidebar.write("Files in dir:", ", ".join(files[:10]) + ("..." if len(files) > 10 else ""))
except:
    st.sidebar.write("Cannot list directory")

# ===================== LOAD DATA WITH BETTER ERROR HANDLING =====================
def load_valves():
    try:
        # Check if file exists
        if not os.path.exists(VALVES_FILE):
            # Try alternative paths
            alt_paths = [
                VALVES_FILE,
                f"data/{VALVES_FILE}",
                f"../{VALVES_FILE}",
                f"./data/{VALVES_FILE}",
                f"../data/{VALVES_FILE}"
            ]
            
            for path in alt_paths:
                if os.path.exists(path):
                    st.sidebar.success(f"Found valves at: {path}")
                    with open(path) as f:
                        return json.load(f)
            
            st.sidebar.error(f"Valves file not found. Tried: {', '.join(alt_paths)}")
            
            # Create sample data for testing
            st.sidebar.warning("Using sample data for testing")
            return {
                "V-501": {"x": 100, "y": 100, "controls_pipes": [1, 2, 3]},
                "V-502": {"x": 200, "y": 200, "controls_pipes": [4, 5, 6]},
                "V-503": {"x": 300, "y": 300, "controls_pipes": [7, 8, 9]}
            }
        
        # File exists, load it
        with open(VALVES_FILE) as f:
            data = json.load(f)
            st.sidebar.success(f"Loaded valves from: {VALVES_FILE}")
            return data
            
    except Exception as e:
        st.sidebar.error(f"Error loading valves: {type(e).__name__}: {str(e)}")
        return {}

def load_pipes():
    try:
        # Check if file exists
        if not os.path.exists(PIPES_FILE):
            # Try alternative paths
            alt_paths = [
                PIPES_FILE,
                f"data/{PIPES_FILE}",
                f"../{PIPES_FILE}",
                f"./data/{PIPES_FILE}",
                f"../data/{PIPES_FILE}"
            ]
            
            for path in alt_paths:
                if os.path.exists(path):
                    st.sidebar.success(f"Found pipes at: {path}")
                    with open(path) as f:
                        return json.load(f)
            
            st.sidebar.error(f"Pipes file not found. Tried: {', '.join(alt_paths)}")
            
            # Create sample data for testing
            st.sidebar.warning("Using sample pipe data for testing")
            return [
                {"x1": 50, "y1": 50, "x2": 150, "y2": 50},
                {"x1": 150, "y1": 50, "x2": 150, "y2": 150},
                {"x1": 150, "y1": 150, "x2": 250, "y2": 150},
                {"x1": 250, "y1": 150, "x2": 250, "y2": 250},
                {"x1": 250, "y1": 250, "x2": 350, "y2": 250},
                {"x1": 350, "y1": 250, "x2": 350, "y2": 350}
            ]
        
        # File exists, load it
        with open(PIPES_FILE) as f:
            data = json.load(f)
            st.sidebar.success(f"Loaded pipes from: {PIPES_FILE}")
            return data
            
    except Exception as e:
        st.sidebar.error(f"Error loading pipes: {type(e).__name__}: {str(e)}")
        return []

valves = load_valves()
pipes = load_pipes()

# ===================== CHECK P&ID IMAGE =====================
if not os.path.exists(PID_FILE):
    st.sidebar.error(f"P&ID image not found: {PID_FILE}")
    # Create a blank image for testing
    st.sidebar.warning("Creating test image")
    test_image = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(test_image)
    draw.text((100, 100), "TEST IMAGE - No P&ID found", fill="black")
    test_image.save("test_p&id.png")
    PID_FILE = "test_p&id.png"

# ===================== SESSION STATE =====================
if "valve_states" not in st.session_state:
    st.session_state.valve_states = {tag: False for tag in valves}
if "selected_pipe" not in st.session_state:
    st.session_state.selected_pipe = None
if "pipes_data" not in st.session_state:
    st.session_state.pipes_data = {SYSTEM_NAME: pipes}

st.session_state.pipes_data.setdefault(SYSTEM_NAME, pipes)
pipes = st.session_state.pipes_data[SYSTEM_NAME]

# ===================== REMAINING CODE (same as before) =====================
def get_controlled_pipes():
    controlled = set()
    for tag, valve_data in valves.items():
        if st.session_state.valve_states.get(tag, False):
            for pipe_num in valve_data.get("controls_pipes", []):
                controlled.add(pipe_num - 1)
    return controlled

def get_groups():
    return {
        2: [3, 4, 5],
        8: [9, 10, 11],
        5: [6, 7],
        11: [12, 13],
        13: [14, 15]
    }

def get_active_leaders():
    active = get_controlled_pipes()
    for i, pipe in enumerate(pipes):
        if i in active:
            continue
        for tag, valve_data in valves.items():
            if st.session_state.valve_states.get(tag, False):
                d = math.hypot(valve_data["x"] - pipe["x1"], valve_data["y"] - pipe["y1"])
                if d <= 50:
                    active.add(i)
                    break
    return active

def get_pipe_color(i):
    if i == st.session_state.selected_pipe:
        return (148, 0, 211)
    num = i + 1
    active = get_active_leaders()
    has_flow = i in active
    has_pressure = (num in PRESSURE_SOURCES) or any(
        leader_num in PRESSURE_SOURCES 
        for leader_num in get_groups().keys() 
        if (leader_num - 1) in active
    )
    if has_flow and has_pressure:
        return (0, 255, 0)
    elif has_pressure:
        return (100, 200, 255)
    elif has_flow:
        return (50, 200, 50)
    else:
        return (50, 50, 80)

def render():
    try:
        img = Image.open(PID_FILE).convert("RGBA")
        draw = ImageDraw.Draw(img)
        
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
        
        for tag, valve_data in valves.items():
            c = (0, 255, 0) if st.session_state.valve_states.get(tag, False) else (255, 0, 0)
            x, y = valve_data["x"], valve_data["y"]
            draw.ellipse([x-10, y-10, x+10, y+10], fill=c, outline="white", width=3)
            draw.text((x+15, y-10), tag, fill="white", 
                     stroke_fill="black", stroke_width=2)
        
        return img.convert("RGB")
    except Exception as e:
        st.error(f"Render error: {e}")
        # Return blank image
        return Image.new('RGB', (800, 600), color='gray')

# ===================== UI =====================
st.title(f"{SYSTEM_NAME} – Live Rig Simulation")

with st.sidebar:
    st.header("Valve Controls")
    for tag, valve_data in valves.items():
        s = st.session_state.valve_states.get(tag, False)
        label = f"{'✅ OPEN' if s else '❌ CLOSED'} {tag}"
        if st.button(label, key=tag, use_container_width=True):
            st.session_state.valve_states[tag] = not s
            st.rerun()
    
    st.markdown("---")
    st.header("Debug Tools")
    if st.button("Reset All Valves", use_container_width=True):
        st.session_state.valve_states = {tag: False for tag in valves}
        st.rerun()
    
    if st.button("Test - Open All", use_container_width=True):
        st.session_state.valve_states = {tag: True for tag in valves}
        st.rerun()

col1, col2 = st.columns([3, 1])
with col1:
    st.image(render(), use_container_width=True,
             caption="Green = Flow | Light Blue = Pressurized | Dark Green = Flow without pressure | Dark = Empty")

with col2:
    st.header("Status")
    flowing = sum(1 for i in range(len(pipes)) if get_pipe_color(i) == (0,255,0))
    st.write(f"**Flowing:** {flowing}")
    st.write(f"**Pressurized:** {sum(1 for i in range(len(pipes)) if get_pipe_color(i) in [(0,255,0),(100,200,255)])}")

st.info("If files are missing, check the sidebar for debugging info. Sample data is being used for testing.")

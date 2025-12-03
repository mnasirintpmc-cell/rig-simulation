import streamlit as st
from PIL import Image, ImageDraw
import json
import os

st.set_page_config(layout="wide", page_title="Rig Simulation")

# ===================== CONFIG =====================
SYSTEM_NAME = "Pressure Return"                   
PID_FILE = "assets/p&id_pressure_return.png"                    
VALVES_FILE = "data/valves_pressure_return.json"                
PIPES_FILE = "data/pipes_pressure_return.json"                  

# ===================== LOAD DATA =====================
def load_valves():
    try:
        with open(VALVES_FILE) as f:
            valves_data = json.load(f)
        st.sidebar.success(f"✅ Loaded {len(valves_data)} valves")
        return valves_data
    except Exception as e:
        st.sidebar.error(f"❌ Error loading valves: {e}")
        return {}

def load_pipes():
    try:
        with open(PIPES_FILE) as f:
            pipes_data = json.load(f)
        st.sidebar.success(f"✅ Loaded {len(pipes_data)} pipes")
        return pipes_data
    except Exception as e:
        st.sidebar.error(f"❌ Error loading pipes: {e}")
        return []

# Load data
valves = load_valves()
pipes = load_pipes()

# ===================== SIMPLE SESSION STATE =====================
if "valve_states" not in st.session_state:
    # Initialize all valves as closed
    st.session_state.valve_states = {tag: False for tag in valves}

if "selected_valve" not in st.session_state:
    st.session_state.selected_valve = None

# ===================== SIMPLE TOGGLE LOGIC =====================
def get_pipe_color(pipe_index, valves, valve_states):
    """
    Check if this pipe should be GREEN (active) because:
    1. A valve that controls this pipe is OPEN
    2. The pipe is in that valve's 'connected_pipes' list
    """
    # Check ALL valves to see if any open valve controls this pipe
    for valve_tag, valve_data in valves.items():
        if valve_states.get(valve_tag, False):  # Valve is OPEN
            # Check if this valve controls our pipe
            connected_pipes = valve_data.get("connected_pipes", [])
            # pipe_index is 0-based, connected_pipes might be 1-based or 0-based
            # Let's check both possibilities
            if (pipe_index in connected_pipes) or ((pipe_index + 1) in connected_pipes):
                return (0, 255, 0)  # GREEN - pipe is active!
    
    return (100, 100, 100)  # GRAY - pipe is inactive

# ===================== RENDER =====================
def render():
    # Load the P&ID image
    try:
        img = Image.open(PID_FILE).convert("RGBA")
    except:
        # Create a blank image if file not found
        img = Image.new('RGBA', (800, 600), (40, 40, 60))
        draw = ImageDraw.Draw(img)
        draw.text((50, 50), "P&ID Image Not Found", fill="white")
        return img.convert("RGB")
    
    draw = ImageDraw.Draw(img)
    
    # Draw pipes with color based on valve states
    for i, pipe in enumerate(pipes):
        color = get_pipe_color(i, valves, st.session_state.valve_states)
        # Make active pipes thicker
        width = 6 if color == (0, 255, 0) else 4
        draw.line([(pipe["x1"], pipe["y1"]), (pipe["x2"], pipe["y2"])], 
                  fill=color, width=width)
    
    # Draw valves
    for tag, valve_data in valves.items():
        is_open = st.session_state.valve_states.get(tag, False)
        x, y = valve_data["x"], valve_data["y"]
        
        # Valve color: green=open, red=closed
        valve_color = (0, 255, 0) if is_open else (255, 0, 0)
        
        # Draw valve
        draw.ellipse([x-8, y-8, x+8, y+8], 
                    fill=valve_color, outline="white", width=2)
        
        # Show how many pipes this valve controls
        connected_count = len(valve_data.get("connected_pipes", []))
        if connected_count > 0:
            # Small number inside valve
            draw.text((x-4, y-6), str(connected_count), 
                     fill="white", stroke_fill="black", stroke_width=1)
        
        # Valve label
        draw.text((x+10, y-10), tag, 
                 fill="white", stroke_fill="black", stroke_width=1)
    
    return img.convert("RGB")

# ===================== UI =====================
st.title(f"🔧 {SYSTEM_NAME} System")

with st.sidebar:
    st.header("🎛️ Valve Controls")
    st.write("Click to toggle valves. Open valves will turn their connected pipes GREEN.")
    
    # Create a button for each valve
    for tag, valve_data in valves.items():
        is_open = st.session_state.valve_states.get(tag, False)
        
        # Show which pipes this valve controls
        connected_pipes = valve_data.get("connected_pipes", [])
        pipe_info = ""
        if connected_pipes:
            pipe_info = f" → Pipes: {connected_pipes}"
        
        button_text = f"{'🟢 OPEN' if is_open else '🔴 CLOSED'} {tag}{pipe_info}"
        
        if st.button(button_text, key=tag, use_container_width=True):
            # Toggle the valve state
            st.session_state.valve_states[tag] = not is_open
            st.rerun()
    
    # Stats
    st.markdown("---")
    st.header("📊 Stats")
    open_valves = sum(1 for state in st.session_state.valve_states.values() if state)
    active_pipes = sum(1 for i in range(len(pipes)) 
                       if get_pipe_color(i, valves, st.session_state.valve_states) == (0, 255, 0))
    
    st.metric("Open Valves", open_valves)
    st.metric("Active Pipes", active_pipes)
    st.metric("Total Pipes", len(pipes))
    
    # Reset button
    if st.button("🔄 Close All Valves", use_container_width=True):
        for tag in valves:
            st.session_state.valve_states[tag] = False
        st.rerun()
    
    # Test button
    if st.button("🧪 Open All Valves", use_container_width=True):
        for tag in valves:
            st.session_state.valve_states[tag] = True
        st.rerun()

# Main display
col1, col2 = st.columns([3, 1])

with col1:
    st.image(render(), use_container_width=True,
             caption="🟢 Green pipes = Connected to OPEN valve | 🔴 Red valve = CLOSED | 🟢 Green valve = OPEN")

with col2:
    st.header("🎯 How It Works")
    st.write("1. **Valves control pipes** based on JSON data")
    st.write("2. **Open a valve** → its connected pipes turn GREEN")
    st.write("3. **Close a valve** → its pipes turn GRAY")
    st.write("4. **Multiple valves** can control the same pipe")
    
    st.markdown("---")
    st.header("🔗 Valve Connections")
    
    for tag, valve_data in valves.items():
        is_open = st.session_state.valve_states.get(tag, False)
        connected_pipes = valve_data.get("connected_pipes", [])
        
        status = "🟢" if is_open else "🔴"
        st.write(f"{status} **{tag}** → Pipes: {connected_pipes}")
        
        # Show which pipes are currently active from this valve
        if is_open and connected_pipes:
            active_count = 0
            for pipe_num in connected_pipes:
                # Check if this pipe would be green
                pipe_idx = pipe_num if isinstance(pipe_num, int) else pipe_num - 1
                if 0 <= pipe_idx < len(pipes):
                    active_count += 1
            if active_count > 0:
                st.write(f"  → Activating {active_count} pipes")

# Debug info in expander
with st.expander("🔍 Debug Info"):
    st.write("**Valves Data:**")
    st.json(valves)
    st.write("**Pipes Data (first 5):**")
    st.json(pipes[:5] if pipes else [])
    st.write("**Current Valve States:**")
    st.json(st.session_state.valve_states)

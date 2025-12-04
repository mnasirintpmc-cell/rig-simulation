
# streamlit_app.py - DIRECT VALVE-TO-PIPE MAPPING
import streamlit as st
from PIL import Image, ImageDraw
import json
import os

st.set_page_config(
    page_title="Rig Simulation",
    page_icon="🏭",
    layout="wide"
)

# Initialize session state
if 'current_system' not in st.session_state:
    st.session_state.current_system = "home"
if 'valve_states' not in st.session_state:
    st.session_state.valve_states = {}
if 'active_pipes' not in st.session_state:
    st.session_state.active_pipes = {}

# System files mapping
SYSTEM_FILES = {
    "mixing": {
        "name": "Mixing System",
        "valves": "data/valves_mixing.json",
        "pipes": "data/pipes_mixing.json",
        "image": "assets/p&id_mixing.png"
    },
    "supply": {
        "name": "Pressure Supply", 
        "valves": "data/valves_pressure_in.json",
        "pipes": "data/pipes_pressure_in.json",
        "image": "assets/p&id_pressure_in.png"
    },
    "dgs": {
        "name": "DGS System",
        "valves": "data/valves_dgs.json",
        "pipes": "data/pipes_dgs.json", 
        "image": "assets/p&id_dgs.png"
    },
    "return": {
        "name": "Pressure Return",
        "valves": "data/valves_pressure_return.json",
        "pipes": "data/pipes_pressure_return.json",
        "image": "assets/p&id_pressure_return.png"
    },
    "seal": {
        "name": "Separation Seal",
        "valves": "data/valves_separation_seal.json",
        "pipes": "data/pipes_separation_seal.json",
        "image": "assets/p&id_separation_seal.png"
    }
}

# ==================== LOAD DATA ====================
def load_data(system):
    """Load valves and pipes for a system"""
    config = SYSTEM_FILES[system]
    
    # Load valves
    valves = {}
    if os.path.exists(config["valves"]):
        with open(config["valves"], 'r') as f:
            valves = json.load(f)
            # DEBUG: Show what's loaded
            st.sidebar.write(f"🔧 Loaded {len(valves)} valves")
            for v, data in list(valves.items())[:3]:  # Show first 3
                st.sidebar.write(f"  {v}: {data.get('connected_pipes', 'NO CONNECTIONS')}")
    else:
        st.error(f"Missing valves file: {config['valves']}")
    
    # Load pipes
    pipes = []
    if os.path.exists(config["pipes"]):
        with open(config["pipes"], 'r') as f:
            pipes = json.load(f)
            st.sidebar.write(f"📏 Loaded {len(pipes)} pipes")
    else:
        st.error(f"Missing pipes file: {config['pipes']}")
    
    return valves, pipes, config["image"]

# ==================== DIRECT MAPPING LOGIC ====================
def get_pipe_status(pipe_index, valves, valve_states):
    """
    DIRECT MAPPING: Check ALL valves to see if ANY open valve controls this pipe
    """
    pipe_display_num = pipe_index + 1  # For display (1-based)
    
    for valve_tag, valve_data in valves.items():
        if valve_states.get(valve_tag, False):  # Valve is OPEN
            # Get connected pipes from valve JSON
            connected_pipes = valve_data.get("connected_pipes", [])
            
            # DEBUG: Show what we're checking
            if pipe_index == 0:  # Just for first pipe
                st.sidebar.write(f"Checking {valve_tag}: connected to {connected_pipes}")
            
            # Check if this valve controls our pipe
            # Handle both 0-based and 1-based indexing
            if pipe_display_num in connected_pipes:
                return "active"  # This valve controls the pipe!
            elif pipe_index in connected_pipes:
                return "active"  # This valve controls the pipe (0-based)
    
    return "inactive"

# ==================== SIMPLE RENDER ====================
def render_system(valves, pipes, image_path, system_name):
    """Render with DIRECT valve-to-pipe mapping"""
    # Load image
    try:
        img = Image.open(image_path).convert("RGBA")
    except:
        img = Image.new('RGBA', (800, 600), (50, 50, 70))
    
    draw = ImageDraw.Draw(img)
    
    # Draw all pipes first
    for i, pipe in enumerate(pipes):
        status = get_pipe_status(i, valves, st.session_state.valve_states)
        
        if status == "active":
            color = (0, 255, 0)  # GREEN - controlled by open valve
            width = 8
        else:
            color = (100, 100, 100)  # GRAY - inactive
            width = 4
        
        draw.line([(pipe["x1"], pipe["y1"]), (pipe["x2"], pipe["y2"])], 
                 fill=color, width=width)
        
        # Label pipe number
        mid_x = (pipe["x1"] + pipe["x2"]) // 2
        mid_y = (pipe["y1"] + pipe["y2"]) // 2
        draw.text((mid_x, mid_y), str(i+1), fill="white")
    
    # Draw valves on top
    for valve_tag, valve_data in valves.items():
        x, y = valve_data["x"], valve_data["y"]
        is_open = st.session_state.valve_states.get(valve_tag, False)
        
        # Valve color
        valve_color = (0, 255, 0) if is_open else (255, 0, 0)  # Green if open, red if closed
        
        # Draw valve
        draw.ellipse([x-12, y-12, x+12, y+12], 
                    fill=valve_color, outline="white", width=3)
        
        # Show connected pipe count
        connected = valve_data.get("connected_pipes", [])
        if connected:
            draw.text((x-6, y-8), str(len(connected)), 
                     fill="white", stroke_fill="black")
        
        # Valve label
        draw.text((x+15, y-12), valve_tag, 
                 fill="white", stroke_fill="black")
    
    return img.convert("RGB")

# ==================== HOME PAGE ====================
if st.session_state.current_system == "home":
    st.title("🏭 Rig Simulation - Direct Valve Control")
    st.markdown("### Click a system to toggle valves and see EXACT pipe connections")
    
    # Navigation buttons
    cols = st.columns(5)
    systems = [
        ("mixing", "🔧", "Mixing"),
        ("supply", "⚡", "Supply"),
        ("dgs", "🎮", "DGS"),
        ("return", "🔄", "Return"),
        ("seal", "🔒", "Seal")
    ]
    
    for idx, (sys_id, icon, name) in enumerate(systems):
        with cols[idx]:
            if st.button(f"{icon}\n**{name}**", use_container_width=True):
                st.session_state.current_system = sys_id
                st.rerun()
    
    st.markdown("---")
    st.info("**How it works:** Each valve JSON has a 'connected_pipes' list. When you open a valve, ONLY those specific pipes turn GREEN.")

# ==================== SYSTEM PAGE ====================
else:
    system = st.session_state.current_system
    config = SYSTEM_FILES[system]
    
    # Load data
    valves, pipes, image_path = load_data(system)
    
    # Initialize valve states
    for tag in valves:
        if tag not in st.session_state.valve_states:
            st.session_state.valve_states[tag] = False
    
    # Header
    st.title(f"{config['name']}")
    
    if st.button("← Back to Home"):
        st.session_state.current_system = "home"
        st.rerun()
    
    st.markdown("---")
    
    # Two column layout
    col_viz, col_controls = st.columns([3, 1])
    
    with col_controls:
        st.header("🎛️ Valve Controls")
        
        # Show valve connection info
        for tag, valve_data in valves.items():
            is_open = st.session_state.valve_states.get(tag, False)
            connected_pipes = valve_data.get("connected_pipes", [])
            
            # Button with clear status
            if is_open:
                btn_text = f"🟢 OPEN: {tag}"
                btn_color = "green"
            else:
                btn_text = f"🔴 CLOSED: {tag}"
                btn_color = "red"
            
            # Create columns for button and info
            col_btn, col_info = st.columns([2, 1])
            
            with col_btn:
                if st.button(btn_text, key=f"btn_{tag}", use_container_width=True):
                    # TOGGLE the valve
                    st.session_state.valve_states[tag] = not is_open
                    st.rerun()
            
            with col_info:
                if connected_pipes:
                    st.write(f"→ {len(connected_pipes)} pipes")
        
        st.markdown("---")
        st.header("📊 Live Status")
        
        # Calculate active pipes
        active_count = 0
        for i in range(len(pipes)):
            if get_pipe_status(i, valves, st.session_state.valve_states) == "active":
                active_count += 1
        
        open_valves = sum(1 for v in st.session_state.valve_states.values() if v)
        
        st.metric("Active Pipes", active_count)
        st.metric("Open Valves", f"{open_valves}/{len(valves)}")
        
        # Control buttons
        st.markdown("---")
        st.header("⚙️ Quick Actions")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Open ALL", use_container_width=True):
                for tag in valves:
                    st.session_state.valve_states[tag] = True
                st.rerun()
        
        with col2:
            if st.button("Close ALL", use_container_width=True):
                for tag in valves:
                    st.session_state.valve_states[tag] = False
                st.rerun()
        
        # Show connection details
        st.markdown("---")
        st.header("🔗 Connections")
        
        for tag, valve_data in valves.items():
            is_open = st.session_state.valve_states.get(tag, False)
            connected = valve_data.get("connected_pipes", [])
            
            if connected:
                status = "🟢" if is_open else "🔴"
                st.write(f"{status} **{tag}** → Pipes: {connected}")
    
    with col_viz:
        # Render and display
        if os.path.exists(image_path):
            img = render_system(valves, pipes, image_path, system)
            st.image(img, use_container_width=True, 
                    caption="🟢 GREEN pipes = Controlled by OPEN valves | 🔴 RED valve = CLOSED | 🟢 GREEN valve = OPEN")
        else:
            st.error(f"Image not found: {image_path}")
            # Show JSON data for debugging
            with st.expander("🔍 Debug: Show loaded data"):
                st.write("**Valves (first 3):**")
                for tag, data in list(valves.items())[:3]:
                    st.json({tag: data})
                
                st.write("**Pipes (first 3):**")
                st.json(pipes[:3] if pipes else [])
        
        # Active pipes list
        st.markdown("---")
        st.subheader("✅ Active Pipes (Green)")
        
        active_list = []
        for i in range(len(pipes)):
            if get_pipe_status(i, valves, st.session_state.valve_states) == "active":
                # Find which valves control this pipe
                controlling_valves = []
                for tag, valve_data in valves.items():
                    if st.session_state.valve_states.get(tag, False):
                        connected = valve_data.get("connected_pipes", [])
                        if (i+1) in connected or i in connected:
                            controlling_valves.append(tag)
                
                if controlling_valves:
                    active_list.append(f"**Pipe {i+1}** ← {', '.join(controlling_valves)}")
        
        if active_list:
            for item in active_list:
                st.write(f"• {item}")
        else:
            st.write("No active pipes. Open valves to activate their connected pipes.")

# ==================== DEBUG INFO ====================
with st.sidebar:
    st.title("🔧 Debug Panel")
    
    if st.session_state.current_system != "home":
        st.write(f"**System:** {st.session_state.current_system}")
        
        # Show current valve states
        st.write("**Valve States:**")
        for tag, state in list(st.session_state.valve_states.items())[:10]:
            st.write(f"{'🟢' if state else '🔴'} {tag}: {'OPEN' if state else 'CLOSED'}")
        
        # Check JSON structure
        st.write("**JSON Field Check:**")
        if valves:
            sample_valve = list(valves.keys())[0]
            sample_data = valves[sample_valve]
            if "connected_pipes" in sample_data:
                st.success(f"✓ 'connected_pipes' field found in {sample_valve}")
                st.write(f"Sample: {sample_valve} → {sample_data['connected_pipes']}")
            else:
                st.error(f"✗ 'connected_pipes' field NOT found in {sample_valve}")
                st.write("Available fields:", list(sample_data.keys()))
        
        # Test mapping
        if st.button("Test Pipe 1 Mapping"):
            if pipes:
                status = get_pipe_status(0, valves, st.session_state.valve_states)
                st.write(f"Pipe 1 status: {status}")
                
                # Show which valves control it
                controlling = []
                for tag, valve_data in valves.items():
                    connected = valve_data.get("connected_pipes", [])
                    if 1 in connected or 0 in connected:
                        controlling.append(f"{tag} (connected to: {connected})")
                
                if controlling:
                    st.write("Controlled by:", controlling)
                else:
                    st.write("Not controlled by any valve")

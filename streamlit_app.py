# streamlit_app.py - EXACT VISUALS, WORKING PIPE TOGGLE
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
    st.session_state.active_pipes = set()

# System files
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
    config = SYSTEM_FILES[system]
    
    valves = {}
    if os.path.exists(config["valves"]):
        with open(config["valves"], 'r') as f:
            valves = json.load(f)
    
    pipes = []
    if os.path.exists(config["pipes"]):
        with open(config["pipes"], 'r') as f:
            pipes = json.load(f)
    
    return valves, pipes, config["image"]

# ==================== SIMPLE PIPE TOGGLE LOGIC ====================
def toggle_valve(system, valve_tag):
    """Toggle a valve and update connected pipes"""
    # Get current state
    current_state = st.session_state.valve_states.get(valve_tag, False)
    # Toggle it
    st.session_state.valve_states[valve_tag] = not current_state
    
    # Load valves to get connected pipes
    valves, pipes, _ = load_data(system)
    valve_data = valves.get(valve_tag, {})
    connected_pipes = valve_data.get("connected_pipes", [])
    
    # Show in sidebar what we're doing
    st.sidebar.write(f"🚨 **DEBUG:** Toggling {valve_tag}")
    st.sidebar.write(f"Connected pipes in JSON: {connected_pipes}")
    
    # Convert to 0-based indices
    pipe_indices = []
    for pipe_num in connected_pipes:
        if isinstance(pipe_num, int):
            pipe_idx = pipe_num - 1  # Convert 1-based to 0-based
            if 0 <= pipe_idx < len(pipes):
                pipe_indices.append(pipe_idx)
    
    st.sidebar.write(f"Pipe indices (0-based): {pipe_indices}")
    
    # Update active pipes
    active_pipes = set(st.session_state.active_pipes)
    
    if not current_state:  # Valve was closed, now opening
        for idx in pipe_indices:
            active_pipes.add(idx)
        st.sidebar.write(f"✅ Added pipes: {pipe_indices}")
    else:  # Valve was open, now closing
        # Check if other valves also control these pipes
        for idx in pipe_indices:
            # Check all other valves
            other_valve_controls = False
            for other_tag, other_data in valves.items():
                if other_tag == valve_tag:
                    continue
                if st.session_state.valve_states.get(other_tag, False):
                    other_connected = other_data.get("connected_pipes", [])
                    if (idx + 1) in other_connected:
                        other_valve_controls = True
                        break
            
            if not other_valve_controls:
                active_pipes.discard(idx)
                st.sidebar.write(f"✅ Removed pipe: {idx}")
            else:
                st.sidebar.write(f"⚠️ Pipe {idx} kept active (other valve controls it)")
    
    st.session_state.active_pipes = active_pipes
    st.sidebar.write(f"Total active pipes: {len(active_pipes)}")

# ==================== RENDER - EXACTLY YOUR VISUALS ====================
def render_system(valves, pipes, image_path, system):
    """Render with YOUR EXACT valve sizes and visuals"""
    try:
        img = Image.open(image_path).convert("RGBA")
    except:
        img = Image.new('RGBA', (800, 600), (40, 40, 60))
    
    draw = ImageDraw.Draw(img)
    
    # Draw pipes
    for i, pipe in enumerate(pipes):
        if i in st.session_state.active_pipes:
            color = (0, 255, 0)  # GREEN
            width = 6
        else:
            color = (50, 50, 80)  # YOUR DARK BLUE
            width = 4
        
        # Draw pipe line
        draw.line([(pipe["x1"], pipe["y1"]), (pipe["x2"], pipe["y2"])], 
                 fill=color, width=width)
        
        # Draw pipe endpoints if selected
        if i in st.session_state.active_pipes:
            # Show pipe number at midpoint
            mid_x = (pipe["x1"] + pipe["x2"]) // 2
            mid_y = (pipe["y1"] + pipe["y2"]) // 2
            draw.text((mid_x, mid_y), str(i+1), fill="white")
    
    # Draw valves - YOUR EXACT SIZE AND STYLE
    for tag, valve_data in valves.items():
        is_open = st.session_state.valve_states.get(tag, False)
        
        # YOUR EXACT VALVE COLORS
        c = (0, 255, 0) if is_open else (255, 0, 0)  # Green if open, Red if closed
        
        # YOUR EXACT VALVE SIZE: ellipse [x-10, y-10, x+10, y+10]
        x, y = valve_data["x"], valve_data["y"]
        draw.ellipse([x-10, y-10, x+10, y+10], 
                    fill=c, outline="white", width=3)  # YOUR EXACT STYLE
        
        # YOUR EXACT TEXT: (x+15, y-10) with stroke_width=2
        draw.text((x+15, y-10), tag, 
                 fill="white", stroke_fill="black", stroke_width=2)
    
    return img.convert("RGB")

# ==================== HOME PAGE ====================
if st.session_state.current_system == "home":
    st.title("🏭 Rig Simulation")
    
    # Navigation
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
                st.session_state.active_pipes = set()  # Reset for new system
                st.rerun()

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
    
    # Layout
    col1, col2 = st.columns([3, 1])
    
    with col2:
        st.header("Valve Controls")
        
        # Show all valves
        for tag in valves:
            s = st.session_state.valve_states.get(tag, False)
            
            # Show which pipes this valve controls
            valve_data = valves.get(tag, {})
            connected = valve_data.get("connected_pipes", [])
            pipe_info = f" → Pipes: {connected}" if connected else ""
            
            # Button with YOUR exact text format
            button_text = f"{'OPEN' if s else 'CLOSED'} {tag}{pipe_info}"
            
            if st.button(button_text, key=tag, use_container_width=True):
                # Use the toggle function
                toggle_valve(system, tag)
                st.rerun()
        
        st.markdown("---")
        st.header("Pipe Selection")
        
        # Pipe buttons
        for i in range(len(pipes)):
            pipe_num = i + 1
            if st.button(f"Pipe {pipe_num}", key=f"p{i}", use_container_width=True):
                # Just for selection, not toggling
                st.sidebar.write(f"Selected Pipe {pipe_num} (index {i})")
        
        if st.button("Unselect", use_container_width=True):
            pass
        
        if st.button("Back to Home"):
            st.session_state.current_system = "home"
            st.rerun()
    
    with col1:
        # Render image
        if os.path.exists(image_path):
            img = render_system(valves, pipes, image_path, system)
            st.image(img, use_container_width=True,
                    caption="Green = Flow | Dark = Empty")
        else:
            st.error(f"Image not found: {image_path}")
            
            # Show debug info
            with st.expander("Debug Info"):
                st.write("**Valves:**")
                st.json(valves)
                
                st.write("**Pipes (first 5):**")
                st.json(pipes[:5] if pipes else [])
        
        # Status
        st.header("Status")
        flowing = len(st.session_state.active_pipes)
        st.write(f"**Flowing Pipes:** {flowing}")
        
        # Show which pipes are active
        if st.session_state.active_pipes:
            active_list = sorted([p+1 for p in st.session_state.active_pipes])
            st.write(f"**Active Pipes:** {active_list}")
        
        # Show valve connections
        st.markdown("---")
        st.subheader("Valve Connections")
        for tag, valve_data in valves.items():
            connected = valve_data.get("connected_pipes", [])
            if connected:
                state = "OPEN" if st.session_state.valve_states.get(tag, False) else "CLOSED"
                st.write(f"**{tag}** ({state}): Pipes {connected}")

# ==================== DEBUG SIDEBAR ====================
with st.sidebar:
    st.title("🔧 Debug Panel")
    
    if st.session_state.current_system != "home":
        st.write(f"**System:** {system}")
        st.write(f"**Active Pipes (0-based):** {sorted(st.session_state.active_pipes)}")
        st.write(f"**Active Pipes (1-based):** {sorted([p+1 for p in st.session_state.active_pipes])}")
        
        # Check one valve's connections
        if valves:
            sample_valve = list(valves.keys())[0]
            sample_data = valves[sample_valve]
            connected = sample_data.get("connected_pipes", [])
            
            st.write(f"**{sample_valve} connections:**")
            st.write(f"JSON says: {connected}")
            
            # Show what that means
            if connected:
                st.write("Means these pipes (1-based):")
                for pipe_num in connected:
                    if isinstance(pipe_num, int):
                        pipe_idx = pipe_num - 1
                        if 0 <= pipe_idx < len(pipes):
                            st.write(f"  {pipe_num} → pipes[{pipe_idx}]")
                        else:
                            st.write(f"  {pipe_num} → ERROR: Out of range!")
        
        # Test button
        if st.button("Test Pipe 1 Mapping"):
            if valves and pipes:
                # Find which valves control pipe 1
                controlling_valves = []
                for tag, valve_data in valves.items():
                    connected = valve_data.get("connected_pipes", [])
                    if 1 in connected:
                        controlling_valves.append(tag)
                
                if controlling_valves:
                    st.success(f"Pipe 1 is controlled by: {controlling_valves}")
                else:
                    st.error("Pipe 1 is not controlled by any valve!")

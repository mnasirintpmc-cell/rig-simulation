# streamlit_app.py - YOUR VALVE SIZE WITH DEBUG TOOL
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
if 'show_debug' not in st.session_state:
    st.session_state.show_debug = True  # Start with debug visible
if 'selected_valve_for_pipes' not in st.session_state:
    st.session_state.selected_valve_for_pipes = None
if 'pipes_to_add' not in st.session_state:
    st.session_state.pipes_to_add = []

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
    
    # Load pipes
    pipes = []
    if os.path.exists(config["pipes"]):
        with open(config["pipes"], 'r') as f:
            pipes = json.load(f)
    
    return valves, pipes, config["image"]

def save_valves(system, valves):
    """Save valves back to file"""
    config = SYSTEM_FILES[system]
    with open(config["valves"], 'w') as f:
        json.dump(valves, f, indent=2)

# ==================== PIPE STATUS LOGIC ====================
def get_pipe_status(pipe_index, valves, valve_states):
    """Check if pipe is controlled by any open valve"""
    pipe_num = pipe_index + 1  # Convert to 1-based
    
    for valve_tag, valve_data in valves.items():
        if valve_states.get(valve_tag, False):  # Valve is OPEN
            connected_pipes = valve_data.get("connected_pipes", [])
            if pipe_num in connected_pipes:
                return "active"
    
    return "inactive"

# ==================== RENDER - YOUR EXACT VALVE SIZE ====================
def render_system(valves, pipes, image_path):
    """Render with YOUR EXACT valve size and visuals"""
    try:
        img = Image.open(image_path).convert("RGBA")
    except:
        img = Image.new('RGBA', (800, 600), (50, 50, 70))
    
    draw = ImageDraw.Draw(img)
    
    # Draw pipes
    for i, pipe in enumerate(pipes):
        status = get_pipe_status(i, valves, st.session_state.valve_states)
        
        if status == "active":
            color = (0, 255, 0)  # GREEN
            width = 6
        else:
            color = (50, 50, 80)  # YOUR DARK BLUE
            width = 4
        
        draw.line([(pipe["x1"], pipe["y1"]), (pipe["x2"], pipe["y2"])], 
                 fill=color, width=width)
    
    # Draw valves - YOUR EXACT SIZE: [x-10, y-10, x+10, y+10]
    for valve_tag, valve_data in valves.items():
        is_open = st.session_state.valve_states.get(valve_tag, False)
        x, y = valve_data["x"], valve_data["y"]
        
        # YOUR EXACT COLORS
        c = (0, 255, 0) if is_open else (255, 0, 0)
        
        # YOUR EXACT VALVE SIZE
        draw.ellipse([x-10, y-10, x+10, y+10], 
                    fill=c, outline="white", width=3)
        
        # YOUR EXACT TEXT POSITION
        draw.text((x+15, y-10), valve_tag, 
                 fill="white", stroke_fill="black", stroke_width=2)
    
    return img.convert("RGB")

# ==================== HOME PAGE ====================
if st.session_state.current_system == "home":
    st.title("🏭 Rig Simulation")
    
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
        st.header("Valve Controls")
        
        # Valve buttons - YOUR EXACT FORMAT
        for tag in valves:
            s = st.session_state.valve_states.get(tag, False)
            
            # Get connected pipes for display
            valve_data = valves.get(tag, {})
            connected = valve_data.get("connected_pipes", [])
            pipe_info = f" → Pipes: {connected}" if connected else ""
            
            # YOUR EXACT BUTTON TEXT
            button_text = f"{'OPEN' if s else 'CLOSED'} {tag}{pipe_info}"
            
            if st.button(button_text, key=tag, use_container_width=True):
                st.session_state.valve_states[tag] = not s
                st.rerun()
        
        st.markdown("---")
        st.header("Pipe Selection")
        
        for i in range(len(pipes)):
            if st.button(f"Pipe {i+1}", key=f"p{i}", use_container_width=True):
                # Store selected pipe for debug tool
                if i+1 not in st.session_state.pipes_to_add:
                    st.session_state.pipes_to_add.append(i+1)
                st.rerun()
        
        if st.button("Unselect", use_container_width=True):
            st.session_state.selected_valve_for_pipes = None
            st.session_state.pipes_to_add = []
            st.rerun()
        
        if st.button("Back to Home"):
            st.session_state.current_system = "home"
            st.rerun()
    
    with col_viz:
        # Render and display
        if os.path.exists(image_path):
            img = render_system(valves, pipes, image_path)
            st.image(img, use_container_width=True,
                    caption="Green = Flow | Dark = Empty")
        else:
            st.error(f"Image not found: {image_path}")
        
        # Status display
        st.header("Status")
        flowing = sum(1 for i in range(len(pipes)) 
                     if get_pipe_status(i, valves, st.session_state.valve_states) == "active")
        st.write(f"**Flowing:** {flowing}")

# ==================== DEBUG TOOL (Collapsible) ====================
with st.sidebar:
    st.title("🔧 Pipe Connection Tool")
    
    # Toggle debug visibility
    if st.button("🔧 Show/Hide Connection Tool"):
        st.session_state.show_debug = not st.session_state.show_debug
        st.rerun()
    
    if st.session_state.show_debug and st.session_state.current_system != "home":
        st.warning("🛠️ **DEBUG MODE ACTIVE**")
        
        # Show current system info
        st.write(f"**System:** {system}")
        st.write(f"**Total Pipes:** {len(pipes)}")
        st.write(f"**Total Valves:** {len(valves)}")
        
        # Step 1: Select a valve to configure
        st.subheader("1. Select Valve")
        valve_options = list(valves.keys())
        if valve_options:
            selected_valve = st.selectbox(
                "Choose valve to configure:",
                valve_options,
                key="valve_selector"
            )
            
            # Show current connections for this valve
            valve_data = valves.get(selected_valve, {})
            current_pipes = valve_data.get("connected_pipes", [])
            st.write(f"**Current connections:** {current_pipes}")
            
            # Step 2: Select pipes to connect
            st.subheader("2. Select Pipes")
            st.write("Click pipe buttons in main panel to select them")
            
            if st.session_state.pipes_to_add:
                st.write(f"**Selected pipes:** {st.session_state.pipes_to_add}")
                
                # Step 3: Update connections
                st.subheader("3. Update Connections")
                
                col_add, col_replace = st.columns(2)
                
                with col_add:
                    if st.button("➕ Add These Pipes", use_container_width=True):
                        # Add pipes to valve
                        if "connected_pipes" not in valve_data:
                            valve_data["connected_pipes"] = []
                        
                        for pipe_num in st.session_state.pipes_to_add:
                            if pipe_num not in valve_data["connected_pipes"]:
                                valve_data["connected_pipes"].append(pipe_num)
                        
                        valves[selected_valve] = valve_data
                        save_valves(system, valves)
                        st.success(f"Added pipes {st.session_state.pipes_to_add} to {selected_valve}")
                        st.session_state.pipes_to_add = []
                        st.rerun()
                
                with col_replace:
                    if st.button("🔄 Replace All Pipes", use_container_width=True):
                        # Replace all pipes
                        valve_data["connected_pipes"] = st.session_state.pipes_to_add.copy()
                        valves[selected_valve] = valve_data
                        save_valves(system, valves)
                        st.success(f"Set {selected_valve} to control pipes {st.session_state.pipes_to_add}")
                        st.session_state.pipes_to_add = []
                        st.rerun()
                
                if st.button("🗑️ Clear Selection", use_container_width=True):
                    st.session_state.pipes_to_add = []
                    st.rerun()
            
            # Step 4: Clear connections
            st.subheader("4. Clear Connections")
            if current_pipes:
                if st.button("❌ Remove ALL connections", use_container_width=True):
                    valve_data["connected_pipes"] = []
                    valves[selected_valve] = valve_data
                    save_valves(system, valves)
                    st.success(f"Cleared all pipes from {selected_valve}")
                    st.rerun()
            
            # Show all valve connections
            st.subheader("📋 All Valve Connections")
            for tag, data in valves.items():
                connected = data.get("connected_pipes", [])
                if connected:
                    st.write(f"**{tag}**: {connected}")
                else:
                    st.write(f"**{tag}**: ❌ No pipes connected")
        
        # Quick test
        st.subheader("🧪 Quick Test")
        if st.button("Test Pipe 1 Connection"):
            if pipes:
                # Find which valves control pipe 1
                controlling = []
                for tag, data in valves.items():
                    connected = data.get("connected_pipes", [])
                    if 1 in connected:
                        controlling.append(tag)
                
                if controlling:
                    st.success(f"✅ Pipe 1 is controlled by: {controlling}")
                else:
                    st.error("❌ Pipe 1 is not controlled by any valve!")
                    st.info("Use the tool above to connect pipes to valves")
        
        # Quick actions
        st.subheader("⚡ Quick Actions")
        if st.button("Connect First Valve to First 3 Pipes"):
            if valves:
                first_valve = list(valves.keys())[0]
                valves[first_valve]["connected_pipes"] = [1, 2, 3]
                save_valves(system, valves)
                st.success(f"Connected {first_valve} to pipes 1, 2, 3")
                st.rerun()

# ==================== HIDDEN WHEN NOT IN USE ====================
# This footer only shows when debug is hidden
if not st.session_state.show_debug:
    st.sidebar.info("🔧 Connection tool is hidden. Click 'Show/Hide Connection Tool' to configure valve-pipe connections.")

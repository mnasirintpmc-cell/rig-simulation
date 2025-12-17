# streamlit_app.py - CALIBRATION MODE FOR PIPE-VALVE CONNECTIONS
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
if 'calibration_mode' not in st.session_state:
    st.session_state.calibration_mode = False
if 'selected_valve' not in st.session_state:
    st.session_state.selected_valve = None
if 'selected_pipes' not in st.session_state:
    st.session_state.selected_pipes = set()

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
    else:
        st.error(f"Missing valves file: {config['valves']}")
    
    # Load pipes
    pipes = []
    if os.path.exists(config["pipes"]):
        with open(config["pipes"], 'r') as f:
            pipes = json.load(f)
    else:
        st.error(f"Missing pipes file: {config['pipes']}")
    
    return valves, pipes, config["image"]

def save_valves(system, valves):
    """Save valves back to file"""
    config = SYSTEM_FILES[system]
    with open(config["valves"], 'w') as f:
        json.dump(valves, f, indent=2)
    st.success(f"✅ Saved valve connections to {config['valves']}")

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

# ==================== RENDER ====================
def render_system(valves, pipes, image_path):
    """Render system with valve and pipe states"""
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
            color = (50, 50, 80)  # DARK BLUE
            width = 4
        
        draw.line([(pipe["x1"], pipe["y1"]), (pipe["x2"], pipe["y2"])], 
                 fill=color, width=width)
        
        # Show pipe number if in calibration mode
        if st.session_state.calibration_mode:
            mid_x = (pipe["x1"] + pipe["x2"]) // 2
            mid_y = (pipe["y1"] + pipe["y2"]) // 2
            pipe_num = i + 1
            draw.text((mid_x-5, mid_y-5), str(pipe_num), 
                     fill="white", stroke_fill="black")
    
    # Draw valves
    for valve_tag, valve_data in valves.items():
        x, y = valve_data["x"], valve_data["y"]
        is_open = st.session_state.valve_states.get(valve_tag, False)
        
        # Valve color
        if valve_tag == st.session_state.selected_valve:
            color = (180, 0, 255)  # PURPLE for selected valve in calibration
        else:
            color = (0, 255, 0) if is_open else (255, 0, 0)
        
        # Draw valve - YOUR EXACT SIZE
        draw.ellipse([x-10, y-10, x+10, y+10], 
                    fill=color, outline="white", width=3)
        
        # Valve label
        draw.text((x+15, y-10), valve_tag, 
                 fill="white", stroke_fill="black", stroke_width=2)
    
    return img.convert("RGB")

# ==================== HOME PAGE ====================
if st.session_state.current_system == "home":
    st.title("🏭 Rig Simulation with Calibration Mode")
    
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
    st.info("**Toggle Calibration Mode** to connect pipes to valves. **Normal Mode** to simulate flow.")

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
    
    # Header with calibration toggle
    col_title, col_calib = st.columns([3, 1])
    with col_title:
        st.title(f"{config['name']}")
    with col_calib:
        if st.button("🔧 Calibration Mode" if not st.session_state.calibration_mode else "🏁 Normal Mode",
                    use_container_width=True):
            st.session_state.calibration_mode = not st.session_state.calibration_mode
            st.session_state.selected_valve = None
            st.session_state.selected_pipes = set()
            st.rerun()
    
    if st.button("← Back to Home"):
        st.session_state.current_system = "home"
        st.rerun()
    
    st.markdown("---")
    
    # Main layout
    col_viz, col_controls = st.columns([3, 1])
    
    with col_controls:
        if st.session_state.calibration_mode:
            st.header("🎯 CALIBRATION MODE")
            st.warning("Select a valve, then select pipes it should control")
            
            # Valve selection for calibration
            st.subheader("1. Select Valve")
            valve_list = list(valves.keys())
            selected_valve = st.selectbox("Choose valve:", valve_list, 
                                         index=valve_list.index(st.session_state.selected_valve) 
                                         if st.session_state.selected_valve in valve_list else 0)
            
            if st.button("🎯 Select This Valve", use_container_width=True):
                st.session_state.selected_valve = selected_valve
                # Load current connections
                current_valve = valves.get(selected_valve, {})
                current_pipes = current_valve.get("connected_pipes", [])
                st.session_state.selected_pipes = set(current_pipes)
                st.rerun()
            
            if st.session_state.selected_valve:
                st.success(f"**Selected:** {st.session_state.selected_valve}")
                
                # Show current connections
                current_valve = valves.get(st.session_state.selected_valve, {})
                current_pipes = current_valve.get("connected_pipes", [])
                st.write(f"**Currently controls:** {current_pipes}")
                
                # Pipe selection
                st.subheader("2. Select Pipes")
                st.write(f"Total pipes in system: {len(pipes)}")
                
                # Select all/none buttons
                col_all, col_none = st.columns(2)
                with col_all:
                    if st.button("✅ Select All", use_container_width=True):
                        st.session_state.selected_pipes = set(range(1, len(pipes) + 1))
                        st.rerun()
                with col_none:
                    if st.button("❌ Clear All", use_container_width=True):
                        st.session_state.selected_pipes = set()
                        st.rerun()
                
                # Pipe grid - ALL YOUR PIPES
                st.subheader("📋 Pipe Selection")
                st.write("Click pipe numbers to select/deselect:")
                
                # Show pipes in a grid
                cols_per_row = 6
                for row_start in range(0, len(pipes), cols_per_row):
                    cols = st.columns(cols_per_row)
                    for col_idx in range(cols_per_row):
                        pipe_num = row_start + col_idx + 1
                        if pipe_num <= len(pipes):
                            with cols[col_idx]:
                                is_selected = pipe_num in st.session_state.selected_pipes
                                btn_text = f"✅{pipe_num}" if is_selected else f"⬜{pipe_num}"
                                if st.button(btn_text, key=f"pipe_{pipe_num}", 
                                           use_container_width=True):
                                    if is_selected:
                                        st.session_state.selected_pipes.remove(pipe_num)
                                    else:
                                        st.session_state.selected_pipes.add(pipe_num)
                                    st.rerun()
                
                # Show selected count
                st.write(f"**Selected:** {len(st.session_state.selected_pipes)} pipes")
                if st.session_state.selected_pipes:
                    st.write(f"Pipes: {sorted(st.session_state.selected_pipes)}")
                
                # Save button
                st.subheader("3. Save Connections")
                if st.button("💾 Save to Valve JSON", use_container_width=True, type="primary"):
                    if st.session_state.selected_valve:
                        # Update valve data
                        valves[st.session_state.selected_valve]["connected_pipes"] = sorted(st.session_state.selected_pipes)
                        save_valves(system, valves)
                        st.rerun()
                
                # Reset button
                if st.button("🔄 Deselect Valve", use_container_width=True):
                    st.session_state.selected_valve = None
                    st.session_state.selected_pipes = set()
                    st.rerun()
            
            # Show all valve connections
            st.markdown("---")
            st.subheader("📊 All Valve Connections")
            for tag, data in valves.items():
                connected = data.get("connected_pipes", [])
                if connected:
                    st.write(f"**{tag}:** {connected}")
                else:
                    st.write(f"**{tag}:** ❌ No connections")
        
        else:
            # NORMAL MODE - Valve controls
            st.header("🎛️ Valve Controls")
            
            for tag in valves:
                s = st.session_state.valve_states.get(tag, False)
                
                # Get connected pipes for display
                valve_data = valves.get(tag, {})
                connected = valve_data.get("connected_pipes", [])
                pipe_info = f" → Pipes: {connected}" if connected else ""
                
                button_text = f"{'OPEN' if s else 'CLOSED'} {tag}{pipe_info}"
                
                if st.button(button_text, key=tag, use_container_width=True):
                    st.session_state.valve_states[tag] = not s
                    st.rerun()
            
            st.markdown("---")
            st.header("Pipe Selection")
            
            for i in range(len(pipes)):
                if st.button(f"Pipe {i+1}", key=f"p{i}", use_container_width=True):
                    # Just show info about this pipe
                    controlling_valves = []
                    for tag, data in valves.items():
                        connected = data.get("connected_pipes", [])
                        if (i+1) in connected:
                            controlling_valves.append(tag)
                    
                    if controlling_valves:
                        st.sidebar.info(f"Pipe {i+1} controlled by: {controlling_valves}")
                    else:
                        st.sidebar.warning(f"Pipe {i+1} not controlled by any valve")
            
            if st.button("Unselect", use_container_width=True):
                st.session_state.selected_valve = None
                st.rerun()
            
            if st.button("Back to Home"):
                st.session_state.current_system = "home"
                st.rerun()
            
            # Stats
            st.markdown("---")
            st.header("📊 Status")
            
            active_count = 0
            for i in range(len(pipes)):
                if get_pipe_status(i, valves, st.session_state.valve_states) == "active":
                    active_count += 1
            
            open_valves = sum(1 for v in st.session_state.valve_states.values() if v)
            
            st.metric("Active Pipes", active_count)
            st.metric("Open Valves", f"{open_valves}/{len(valves)}")
            st.metric("Total Pipes", len(pipes))
    
    with col_viz:
        # Render and display
        if os.path.exists(image_path):
            img = render_system(valves, pipes, image_path)
            caption = "🔧 CALIBRATION MODE - Purple valve = selected for configuration" if st.session_state.calibration_mode else "Green = Flow | Dark = Empty"
            st.image(img, use_container_width=True, caption=caption)
        else:
            st.error(f"Image not found: {image_path}")
            
            # Show pipe data
            with st.expander("📋 Show All Pipes"):
                st.write(f"**Total Pipes:** {len(pipes)}")
                for i, pipe in enumerate(pipes):
                    st.write(f"**Pipe {i+1}:** Start({pipe['x1']},{pipe['y1']}) → End({pipe['x2']},{pipe['y2']})")
        
        # Active pipes info
        if not st.session_state.calibration_mode:
            st.markdown("---")
            st.subheader("✅ Active Pipes")
            
            active_pipes = []
            for i in range(len(pipes)):
                if get_pipe_status(i, valves, st.session_state.valve_states) == "active":
                    active_pipes.append(i+1)
            
            if active_pipes:
                st.write(f"**Pipes with flow:** {active_pipes}")
            else:
                st.write("No active pipes. Open valves to activate flow.")

# ==================== CALIBRATION GUIDE ====================
with st.sidebar:
    st.title("📖 Calibration Guide")
    
    if st.session_state.current_system != "home":
        if st.session_state.calibration_mode:
            st.success("**CALIBRATION MODE ACTIVE**")
            st.write("1. **Select a valve** from dropdown")
            st.write("2. **Click pipe numbers** to select/deselect")
            st.write("3. **Click 'Save to Valve JSON'**")
            st.write("4. **Switch to Normal Mode** to test")
            st.write("5. **Open valves** to see connected pipes turn GREEN")
            
            # Quick load for mixing system (your 22 pipes)
            if system == "mixing" and len(pipes) == 22:
                st.markdown("---")
                st.subheader("⚡ Quick Setup for Mixing")
                
                if st.button("Load All 22 Pipes as Options"):
                    st.info("Pipes 1-22 are now available for selection")
                    # Just show info
                    st.write("Available pipes: 1 through 22")
        
        else:
            st.info("**NORMAL MODE**")
            st.write("• **Click valves** to open/close them")
            st.write("• **Connected pipes** will turn GREEN")
            st.write("• **Enable Calibration Mode** to change connections")
        
        # Debug info
        st.markdown("---")
        st.subheader("🔍 System Info")
        st.write(f"**System:** {system}")
        st.write(f"**Valves:** {len(valves)}")
        st.write(f"**Pipes:** {len(pipes)}")
        
        # Check valve connections
        st.subheader("🔗 Connection Check")
        valves_without_connections = []
        for tag, data in valves.items():
            connected = data.get("connected_pipes", [])
            if not connected:
                valves_without_connections.append(tag)
        
        if valves_without_connections:
            st.error(f"❌ Valves without connections: {valves_without_connections}")
            st.info("Use Calibration Mode to add pipe connections")
        else:
            st.success("✅ All valves have connections!")

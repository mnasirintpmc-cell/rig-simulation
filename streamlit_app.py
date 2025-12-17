# streamlit_app.py - TAG-BASED PIPE-VALVE MAPPING
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
if 'pipe_states' not in st.session_state:
    st.session_state.pipe_states = {}

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

# ==================== LOAD AND TAG DATA ====================
def load_and_tag_data(system):
    """
    Load valves and pipes, then create pipe tags if they don't exist.
    Returns: valves, tagged_pipes, image_path
    """
    config = SYSTEM_FILES[system]
    
    # Load valves
    valves = {}
    if os.path.exists(config["valves"]):
        with open(config["valves"], 'r') as f:
            valves = json.load(f)
    else:
        st.error(f"Missing: {config['valves']}")
        return {}, [], ""
    
    # Load pipes and add tags
    pipes = []
    if os.path.exists(config["pipes"]):
        with open(config["pipes"], 'r') as f:
            pipes_data = json.load(f)
            
            # Check if pipes already have tags
            if pipes_data and isinstance(pipes_data, list):
                if len(pipes_data) > 0 and "tag" in pipes_data[0]:
                    # Pipes already have tags
                    pipes = pipes_data
                else:
                    # Add tags to pipes (P-1, P-2, etc.)
                    pipes = []
                    for i, pipe_data in enumerate(pipes_data):
                        tagged_pipe = pipe_data.copy()
                        tagged_pipe["tag"] = f"P-{i+1}"  # Add tag
                        pipes.append(tagged_pipe)
    else:
        st.error(f"Missing: {config['pipes']}")
        return {}, [], ""
    
    return valves, pipes, config["image"]

# ==================== DIRECT TOGGLE LOGIC ====================
def toggle_valve_and_pipes(valve_tag, valves, current_state):
    """
    When a valve is toggled:
    1. Flip the valve state
    2. Toggle ALL pipes in its connected_pipes list
    3. Return updated pipe states
    """
    # Get the valve data
    valve_data = valves.get(valve_tag, {})
    connected_pipes_refs = valve_data.get("connected_pipes", [])
    
    # The new valve state (opposite of current)
    new_valve_state = not current_state
    
    # Get all pipe tags from our tagged pipes
    pipe_tags = [pipe["tag"] for pipe in st.session_state.get('pipes_data', [])]
    
    # Debug: Show what we're working with
    st.sidebar.write(f"🚨 DEBUG: Valve {valve_tag}")
    st.sidebar.write(f"Connected refs: {connected_pipes_refs}")
    st.sidebar.write(f"Available pipe tags: {pipe_tags}")
    
    # Update pipe states based on valve
    pipe_states = st.session_state.pipe_states.copy()
    
    for pipe_ref in connected_pipes_refs:
        # Convert pipe_ref to pipe_tag
        pipe_tag = None
        
        # Try different ways pipe_ref might be stored
        if isinstance(pipe_ref, str) and pipe_ref.startswith("P-"):
            # Already a pipe tag like "P-1"
            pipe_tag = pipe_ref
        elif isinstance(pipe_ref, int):
            # Number reference (1-based or 0-based)
            # Try 1-based first (P-1, P-2, etc.)
            if 1 <= pipe_ref <= len(pipe_tags):
                pipe_tag = pipe_tags[pipe_ref - 1]
            # Try 0-based
            elif 0 <= pipe_ref < len(pipe_tags):
                pipe_tag = pipe_tags[pipe_ref]
        
        if pipe_tag:
            if new_valve_state:  # Valve opening
                pipe_states[pipe_tag] = True  # Turn pipe ON
                st.sidebar.write(f"  → Turning ON {pipe_tag}")
            else:  # Valve closing
                # Check if other valves also control this pipe
                other_valves_controlling = False
                for other_valve, other_data in valves.items():
                    if other_valve == valve_tag:
                        continue  # Skip current valve
                    if st.session_state.valve_states.get(other_valve, False):
                        other_refs = other_data.get("connected_pipes", [])
                        if pipe_ref in other_refs:
                            other_valves_controlling = True
                            break
                
                if not other_valves_controlling:
                    pipe_states[pipe_tag] = False  # Turn pipe OFF
                    st.sidebar.write(f"  → Turning OFF {pipe_tag}")
                else:
                    st.sidebar.write(f"  → Keeping {pipe_tag} ON (other valve controls it)")
    
    return new_valve_state, pipe_states

# ==================== SIMPLE RENDER ====================
def render_system(valves, pipes, image_path):
    """Render with current valve and pipe states"""
    # Load image
    try:
        img = Image.open(image_path).convert("RGBA")
    except:
        img = Image.new('RGBA', (800, 600), (50, 50, 70))
        draw = ImageDraw.Draw(img)
        draw.text((100, 100), "P&ID Image", fill="white")
        return img.convert("RGB")
    
    draw = ImageDraw.Draw(img)
    
    # Store pipes in session state for reference
    st.session_state.pipes_data = pipes
    
    # Draw all pipes with their states
    for pipe in pipes:
        pipe_tag = pipe.get("tag", "Unknown")
        is_active = st.session_state.pipe_states.get(pipe_tag, False)
        
        if is_active:
            color = (0, 255, 0)  # GREEN - active
            width = 8
        else:
            color = (100, 100, 100)  # GRAY - inactive
            width = 4
        
        draw.line([(pipe["x1"], pipe["y1"]), (pipe["x2"], pipe["y2"])], 
                 fill=color, width=width)
        
        # Show pipe tag/number
        mid_x = (pipe["x1"] + pipe["x2"]) // 2
        mid_y = (pipe["y1"] + pipe["y2"]) // 2
        draw.text((mid_x, mid_y), pipe_tag, fill="white")
    
    # Draw valves on top
    for valve_tag, valve_data in valves.items():
        x, y = valve_data["x"], valve_data["y"]
        is_open = st.session_state.valve_states.get(valve_tag, False)
        
        # Valve color
        valve_color = (0, 255, 0) if is_open else (255, 0, 0)
        
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
    st.title("🏭 Rig Simulation - Tag-Based System")
    st.markdown("### Each pipe now has a tag (P-1, P-2, etc.) for valve mapping")
    
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
                # Reset pipe states for new system
                st.session_state.pipe_states = {}
                st.rerun()
    
    st.markdown("---")
    st.info("**NEW:** Pipes are now tagged. Valves reference these tags in their 'connected_pipes' field.")

# ==================== SYSTEM PAGE ====================
else:
    system = st.session_state.current_system
    config = SYSTEM_FILES[system]
    
    # Load and tag data
    valves, pipes, image_path = load_and_tag_data(system)
    
    # Initialize valve and pipe states
    for tag in valves:
        if tag not in st.session_state.valve_states:
            st.session_state.valve_states[tag] = False
    
    # Initialize pipe states if not done
    for pipe in pipes:
        pipe_tag = pipe.get("tag")
        if pipe_tag and pipe_tag not in st.session_state.pipe_states:
            st.session_state.pipe_states[pipe_tag] = False
    
    # Header
    st.title(f"{config['name']}")
    
    if st.button("← Back to Home"):
        st.session_state.current_system = "home"
        st.rerun()
    
    st.markdown("---")
    
    # Main layout
    col_viz, col_controls = st.columns([3, 1])
    
    with col_controls:
        st.header("🎛️ Valve Controls")
        st.markdown("Click to toggle valve and its connected pipes")
        
        # Valve buttons with DIRECT toggling
        for valve_tag, valve_data in valves.items():
            current_state = st.session_state.valve_states.get(valve_tag, False)
            connected_refs = valve_data.get("connected_pipes", [])
            
            # Show button with current state
            if current_state:
                btn_text = f"🟢 **{valve_tag}** - OPEN"
                btn_help = f"Controls: {connected_refs}"
            else:
                btn_text = f"🔴 **{valve_tag}** - CLOSED"
                btn_help = f"Controls: {connected_refs}"
            
            if st.button(btn_text, 
                        key=f"valve_{valve_tag}",
                        help=btn_help,
                        use_container_width=True):
                # Direct toggle logic
                new_state, new_pipe_states = toggle_valve_and_pipes(
                    valve_tag, valves, current_state
                )
                
                # Update states
                st.session_state.valve_states[valve_tag] = new_state
                st.session_state.pipe_states.update(new_pipe_states)
                st.rerun()
            
            # Show what pipes this valve controls
            if connected_refs:
                # Convert refs to readable format
                readable_refs = []
                for ref in connected_refs:
                    if isinstance(ref, int):
                        readable_refs.append(f"P-{ref}")
                    else:
                        readable_refs.append(str(ref))
                st.caption(f"Controls: {', '.join(readable_refs)}")
        
        st.markdown("---")
        st.header("📊 Status")
        
        # Counts
        open_valves = sum(1 for v in st.session_state.valve_states.values() if v)
        active_pipes = sum(1 for v in st.session_state.pipe_states.values() if v)
        
        st.metric("Open Valves", f"{open_valves}/{len(valves)}")
        st.metric("Active Pipes", f"{active_pipes}/{len(pipes)}")
        
        # Quick controls
        st.markdown("---")
        st.header("⚙️ Quick Actions")
        
        if st.button("🟢 Open ALL Valves", use_container_width=True):
            for valve_tag in valves:
                st.session_state.valve_states[valve_tag] = True
                # Also activate all connected pipes
                valve_data = valves[valve_tag]
                connected_refs = valve_data.get("connected_pipes", [])
                for ref in connected_refs:
                    if isinstance(ref, int) and 1 <= ref <= len(pipes):
                        st.session_state.pipe_states[f"P-{ref}"] = True
            st.rerun()
        
        if st.button("🔴 Close ALL Valves", use_container_width=True):
            for valve_tag in valves:
                st.session_state.valve_states[valve_tag] = False
            # Reset all pipe states
            for pipe in pipes:
                pipe_tag = pipe.get("tag")
                if pipe_tag:
                    st.session_state.pipe_states[pipe_tag] = False
            st.rerun()
        
        # Show pipe states
        st.markdown("---")
        st.header("🔗 Pipe States")
        
        for pipe in pipes[:10]:  # Show first 10
            pipe_tag = pipe.get("tag", "Unknown")
            is_active = st.session_state.pipe_states.get(pipe_tag, False)
            status = "🟢 ON" if is_active else "⚫ OFF"
            st.write(f"{status} **{pipe_tag}**")
    
    with col_viz:
        # Render and display
        if os.path.exists(image_path):
            img = render_system(valves, pipes, image_path)
            st.image(img, use_container_width=True, 
                    caption=f"{config['name']} - Green pipes = ON | Gray pipes = OFF")
        else:
            st.error(f"Image not found: {image_path}")
        
        # Connection table
        st.markdown("---")
        st.subheader("🔗 Valve-to-Pipe Connections")
        
        connection_table = []
        for valve_tag, valve_data in valves.items():
            connected_refs = valve_data.get("connected_pipes", [])
            valve_state = st.session_state.valve_states.get(valve_tag, False)
            
            # Convert refs to pipe tags
            pipe_tags = []
            for ref in connected_refs:
                if isinstance(ref, int):
                    pipe_tags.append(f"P-{ref}")
                else:
                    pipe_tags.append(str(ref))
            
            if pipe_tags:
                status = "🟢 OPEN" if valve_state else "🔴 CLOSED"
                connection_table.append({
                    "Valve": valve_tag,
                    "Status": status,
                    "Controls": ", ".join(pipe_tags)
                })
        
        # Display as table
        for conn in connection_table:
            cols = st.columns([1, 1, 2])
            cols[0].write(f"**{conn['Valve']}**")
            cols[1].write(conn['Status'])
            cols[2].write(conn['Controls'])

# ==================== DEBUG SIDEBAR ====================
with st.sidebar:
    st.title("🔧 Debug Info")
    
    if st.session_state.current_system != "home":
        st.write(f"**Current System:** {system}")
        
        # Show sample data
        if valves:
            st.write("**Sample Valve Data:**")
            sample_valve = list(valves.keys())[0]
            st.json({sample_valve: valves[sample_valve]})
        
        if pipes:
            st.write("**Sample Pipe Data:**")
            st.json(pipes[0] if len(pipes) > 0 else {})
            
            # Show all pipe tags
            pipe_tags = [p.get("tag", "No tag") for p in pipes]
            st.write(f"**Pipe Tags:** {pipe_tags[:10]}{'...' if len(pipe_tags) > 10 else ''}")
        
        # Show current states
        st.write("**Current States:**")
        st.write(f"Valves: {sum(st.session_state.valve_states.values())} open")
        st.write(f"Pipes: {sum(st.session_state.pipe_states.values())} active")
        
        # Test button
        if st.button("Test Mapping", key="test_map"):
            if valves and pipes:
                sample_valve = list(valves.keys())[0]
                valve_data = valves[sample_valve]
                connected = valve_data.get("connected_pipes", [])
                st.write(f"**{sample_valve}** connects to: {connected}")
                
                # Show what those correspond to
                pipe_tags = [p.get("tag") for p in pipes]
                st.write(f"Available pipe tags: {pipe_tags}")
                
                # Try to map
                for ref in connected:
                    if isinstance(ref, int):
                        if 1 <= ref <= len(pipe_tags):
                            st.write(f"  {ref} → {pipe_tags[ref-1]}")
                        else:
                            st.write(f"  {ref} → OUT OF RANGE")

# ==================== FOOTER ====================
st.markdown("---")
st.caption("🏭 Tag-Based Rig Simulation | Valves control specific tagged pipes")

# streamlit_app.py - INDEX-BASED PIPE-VALVE MAPPING
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
        st.error(f"Missing: {config['valves']}")
    
    # Load pipes
    pipes = []
    if os.path.exists(config["pipes"]):
        with open(config["pipes"], 'r') as f:
            pipes = json.load(f)
    else:
        st.error(f"Missing: {config['pipes']}")
    
    return valves, pipes, config["image"]

# ==================== INDEX-BASED MAPPING ====================
def update_pipe_states():
    """
    Update which pipes are active based on valve states.
    Pipe references in valve JSON are 1-BASED indices.
    Example: "connected_pipes": [1, 16] means pipes[0] and pipes[15]
    """
    if st.session_state.current_system == "home":
        return set()
    
    valves, pipes, _ = load_data(st.session_state.current_system)
    active_pipes = set()
    
    for valve_tag, valve_data in valves.items():
        if st.session_state.valve_states.get(valve_tag, False):  # Valve is OPEN
            connected_pipes = valve_data.get("connected_pipes", [])
            
            # Convert 1-based indices to 0-based indices
            for pipe_ref in connected_pipes:
                if isinstance(pipe_ref, int):
                    # Pipe ref is 1-based: 1 = pipes[0], 2 = pipes[1], etc.
                    pipe_idx = pipe_ref - 1
                    if 0 <= pipe_idx < len(pipes):
                        active_pipes.add(pipe_idx)
    
    return active_pipes

# ==================== RENDER - ORIGINAL VISUALS ====================
def render_system(valves, pipes, image_path):
    """Render with ORIGINAL valve sizes and visuals"""
    # Load image
    try:
        img = Image.open(image_path).convert("RGBA")
    except:
        img = Image.new('RGBA', (800, 600), (40, 40, 60))
    
    draw = ImageDraw.Draw(img)
    
    # Update active pipes
    active_pipes = update_pipe_states()
    
    # Draw pipes
    for i, pipe in enumerate(pipes):
        if i in active_pipes:
            color = (0, 255, 0)  # GREEN - active
            width = 6
        else:
            color = (100, 100, 100)  # GRAY - inactive
            width = 4
        
        draw.line([(pipe["x1"], pipe["y1"]), (pipe["x2"], pipe["y2"])], 
                 fill=color, width=width)
    
    # Draw valves - ORIGINAL SIZE AND STYLE
    for valve_tag, valve_data in valves.items():
        x, y = valve_data["x"], valve_data["y"]
        is_open = st.session_state.valve_states.get(valve_tag, False)
        
        # Valve color
        valve_color = (0, 255, 0) if is_open else (255, 0, 0)
        
        # ORIGINAL VALVE SIZE (from your working code)
        draw.ellipse([x-10, y-10, x+10, y+10],  # ← YOUR ORIGINAL SIZE
                    fill=valve_color, outline="white", width=3)
        
        # Valve label - ORIGINAL STYLE
        draw.text((x+15, y-10), valve_tag, 
                 fill="white", stroke_fill="black", stroke_width=2)
    
    return img.convert("RGB")

# ==================== HOME PAGE ====================
if st.session_state.current_system == "home":
    st.title("🏭 Rig Simulation - Index-Based Mapping")
    st.markdown("### Valves control pipes by index position in the pipes array")
    
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
    st.info("**Mapping Logic:** Valve JSON 'connected_pipes': [1, 16] → pipes[0] and pipes[15]")

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
                btn_text = f"🟢 {tag} - OPEN"
            else:
                btn_text = f"🔴 {tag} - CLOSED"
            
            if st.button(btn_text, key=f"btn_{tag}", use_container_width=True):
                # Toggle the valve
                st.session_state.valve_states[tag] = not is_open
                st.rerun()
            
            # Show which pipes this valve controls (as indices)
            if connected_pipes:
                # Convert to display format: show as 1-based
                display_pipes = [str(p) for p in connected_pipes]
                st.caption(f"Controls pipes: {', '.join(display_pipes)}")
        
        st.markdown("---")
        st.header("📊 Status")
        
        # Update and get active pipes
        active_pipes = update_pipe_states()
        open_valves = sum(1 for v in st.session_state.valve_states.values() if v)
        
        st.metric("Active Pipes", len(active_pipes))
        st.metric("Open Valves", f"{open_valves}/{len(valves)}")
        st.metric("Total Pipes", len(pipes))
        
        # Control buttons
        st.markdown("---")
        st.header("⚙️ Controls")
        
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
        
        # Show active pipes
        st.markdown("---")
        st.header("🔗 Active Pipes")
        
        if active_pipes:
            # Convert 0-based to 1-based for display
            active_display = [str(p+1) for p in sorted(active_pipes)]
            st.write(f"Pipes: {', '.join(active_display)}")
        else:
            st.write("No active pipes")
    
    with col_viz:
        # Render and display
        if os.path.exists(image_path):
            img = render_system(valves, pipes, image_path)
            st.image(img, use_container_width=True, 
                    caption="🟢 Green pipes = Controlled by open valves")
        else:
            st.error(f"Image not found: {image_path}")
        
        # Connection table
        st.markdown("---")
        st.subheader("🔗 Valve-Pipe Connections")
        
        # Show mapping table
        connection_data = []
        for valve_tag, valve_data in valves.items():
            connected = valve_data.get("connected_pipes", [])
            if connected:
                valve_state = st.session_state.valve_states.get(valve_tag, False)
                
                # Which of these pipes are currently active?
                active_from_this = []
                for pipe_ref in connected:
                    pipe_idx = pipe_ref - 1  # Convert to 0-based
                    if pipe_idx in active_pipes:
                        active_from_this.append(str(pipe_ref))
                
                connection_data.append({
                    "Valve": valve_tag,
                    "Status": "🟢 OPEN" if valve_state else "🔴 CLOSED",
                    "Controls": f"Pipes {connected}",
                    "Active": f"{len(active_from_this)}/{len(connected)}"
                })
        
        # Display as table
        for conn in connection_data:
            cols = st.columns([1, 1, 2, 1])
            cols[0].write(f"**{conn['Valve']}**")
            cols[1].write(conn['Status'])
            cols[2].write(conn['Controls'])
            cols[3].write(conn['Active'])

# ==================== DEBUG SIDEBAR ====================
with st.sidebar:
    st.title("🔧 Debug Info")
    
    if st.session_state.current_system != "home":
        # Show mapping explanation
        st.write("**Mapping Logic:**")
        st.write("valves.json → 'connected_pipes': [1, 16]")
        st.write("means: pipes[0] and pipes[15]")
        
        # Show sample data
        if valves:
            st.write("**Sample Valve Data:**")
            sample_valve = list(valves.keys())[0]
            sample_data = valves[sample_valve]
            st.json({sample_valve: sample_data})
            
            # Show what pipes it references
            connected = sample_data.get("connected_pipes", [])
            if connected:
                st.write(f"**{sample_valve}** references pipes:")
                for ref in connected:
                    pipe_idx = ref - 1
                    if 0 <= pipe_idx < len(pipes):
                        st.write(f"  {ref} → pipes[{pipe_idx}]")
                    else:
                        st.write(f"  {ref} → OUT OF RANGE (max: {len(pipes)})")
        
        # Show current states
        st.write("**Current States:**")
        active_pipes = update_pipe_states()
        st.write(f"Active pipes (0-based): {sorted(active_pipes)}")
        st.write(f"Active pipes (1-based): {[p+1 for p in sorted(active_pipes)]}")

# ==================== FOOTER ====================
st.markdown("---")
st.caption("🏭 Index-Based Rig Simulation | Valve 'connected_pipes' uses 1-based pipe indices")

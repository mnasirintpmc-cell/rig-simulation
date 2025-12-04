import streamlit as st
from PIL import Image, ImageDraw
import json, os

def run(valve_states):
    # ===================== FILE PATHS =====================
    PID_FILE = os.path.join("assets", "p&id_mixing.png")
    PIPES_FILE = os.path.join("data", "pipes_mixing.json")
    VALVES_FILE = os.path.join("data", "valves_mixing.json")

    # Load JSON
    with open(PIPES_FILE) as f:
        pipes_raw = json.load(f)
    with open(VALVES_FILE) as f:
        valves_raw = json.load(f)

    # Pipes with tags
    pipes = []
    for idx, pipe in enumerate(pipes_raw):
        pipe["tag"] = f"P{idx+1}"
        pipes.append(pipe)

    # Map valves to pipe tags
    valves = {}
    for v_tag, vdata in valves_raw.items():
        connected_tags = []
        for key, indices in vdata.items():
            if key.endswith(".json") and isinstance(indices, list):
                for i in indices:
                    if isinstance(i,int) and 1 <= i <= len(pipes):
                        connected_tags.append(pipes[i-1]["tag"])
        valves[v_tag] = {
            "x": vdata.get("x",0),
            "y": vdata.get("y",0),
            "connected_pipes": connected_tags
        }

    # Determine active pipes based on open valves
    active_pipes = set()
    for v_tag, p_list in valves.items():
        if valve_states.get(v_tag, False):
            active_pipes.update(p_list["connected_pipes"] if isinstance(p_list, dict) else [])

    # Render P&ID
    try:
        img = Image.open(PID_FILE).convert("RGBA")
    except:
        img = Image.new("RGBA", (1200,600),(50,50,50))
        draw = ImageDraw.Draw(img)
        draw.text((100,300), f"Missing {PID_FILE}", fill="white")

    draw = ImageDraw.Draw(img)

    # Draw pipes
    for pipe in pipes:
        color = (0,255,0) if pipe["tag"] in active_pipes else (60,60,100)
        width = 7 if pipe["tag"] in active_pipes else 4
        draw.line([(pipe["x1"],pipe["y1"]),(pipe["x2"],pipe["y2"])], fill=color, width=width)

    # Draw valves
    for v_tag, vdata in valves.items():
        x, y = vdata["x"], vdata["y"]
        color = (0,255,0) if valve_states.get(v_tag, False) else (255,0,0)
        draw.ellipse([x-12,y-12,x+12,y+12], fill=color, outline="white", width=3)
        draw.text((x+15,y-15), v_tag, fill="white", stroke_fill="black", stroke_width=2)

    # Resize image to fit screen height (approx 80% of viewport)
    max_height = 700  # adjust this as needed
    w, h = img.size
    ratio = max_height / h
    new_w, new_h = int(w * ratio), int(h * ratio)
    img_resized = img.resize((new_w, new_h))

    st.image(img_resized, use_column_width=True, caption="Valve status on P&ID")

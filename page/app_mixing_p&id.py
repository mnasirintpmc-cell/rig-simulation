import streamlit as st
from PIL import Image, ImageDraw
import json, os


def run(valve_states):

    PID = "assets/p&id_mixing.png"
    PIPES = "data/pipes_mixing.json"
    VALVES = "data/valves_mixing.json"

    # ---- Load JSON ----
    pipes = json.load(open(PIPES))
    valves_raw = json.load(open(VALVES))

    # Tag pipes (P1, P2, ...)
    for i, p in enumerate(pipes):
        p["tag"] = f"P{i+1}"

    # Build valve structure
    valves = {}
    for v_tag, vdata in valves_raw.items():
        connected = []
        for key, lst in vdata.items():
            if isinstance(lst, list):
                for idx in lst:
                    if isinstance(idx, int) and 1 <= idx <= len(pipes):
                        connected.append(pipes[idx - 1]["tag"])

        valves[v_tag] = {
            "x": vdata["x"],
            "y": vdata["y"],
            "pipes": connected
        }

    # Determine active pipes
    active = set()
    for v_tag, vdata in valves.items():
        if valve_states.get(v_tag, False):
            active.update(vdata["pipes"])

    # Load P&ID
    try:
        img = Image.open(PID).convert("RGBA")
    except:
        img = Image.new("RGBA", (1400, 800), (40,40,40))
        d = ImageDraw.Draw(img)
        d.text((20,20), "Missing P&ID Image", fill="white")

    draw = ImageDraw.Draw(img)

    # Draw Pipes
    for p in pipes:
        color = (0,255,0) if p["tag"] in active else (80,80,120)
        width = 7 if p["tag"] in active else 4
        draw.line([(p["x1"], p["y1"]), (p["x2"], p["y2"])], fill=color, width=width)

    # Draw Valves
    for tag, v in valves.items():
        color = (0,255,0) if valve_states.get(tag, False) else (255,0,0)
        x, y = v["x"], v["y"]
        draw.ellipse([x-12, y-12, x+12, y+12], fill=color, outline="white", width=3)
        draw.text((x+18, y-10), tag, fill="white")

    # FIX IMAGE HEIGHT SO NO SCROLL
    max_h = 650
    w, h = img.size
    ratio = max_h / h
    img = img.resize((int(w * ratio), int(h * ratio)))

    st.image(img, use_column_width=False)

mport os
return None
idx = max(0, min(self.index - 1, len(self.df) - 1))
return self.df.iloc[idx].to_dict()




# ---------- Rendering helpers ----------


def render_system_image(pid_image_path, pipes, valves, valve_states, selected_pipe=None, caption_text=None):
try:
img = Image.open(pid_image_path).convert("RGBA")
except Exception:
img = Image.new("RGBA", (1000, 700), (40, 40, 40))
draw = ImageDraw.Draw(img)


# draw pipes
for i, pipe in enumerate(pipes):
x1, y1, x2, y2 = pipe["x1"], pipe["y1"], pipe["x2"], pipe["y2"]
status = get_pipe_status(i, pipes, valves, valve_states)
if i == selected_pipe:
color = (180, 0, 255)
w = 9
elif status[0] and status[1]:
color = (0, 255, 0)
w = 8
elif status[1]:
color = (100, 180, 255)
w = 6
else:
color = (60, 60, 100)
w = 4
draw.line([(x1, y1), (x2, y2)], fill=color, width=w)
midx = (x1 + x2) // 2
midy = (y1 + y2) // 2
draw.text((midx, midy), str(i + 1), fill="white")


# draw valves
for tag, v in valves.items():
x, y = v.get("x", 0), v.get("y", 0)
is_open = valve_states.get(tag, False)
color = (0, 255, 0) if is_open else (255, 0, 0)
r = 8
draw.ellipse([x - r, y - r, x + r, y + r], fill=color, outline="white")
draw.text((x + 12, y - 10), tag, fill="white")


return img.convert("RGB")




# ---------- Logic: pipe status from valve->pipe mapping ----------


def get_pipe_status(pipe_index, pipes, valves, valve_states):
"""Return (has_flow, has_pressure) for pipe_index.
Logic: any open valve that lists this pipe (either 1-based or 0-based) activates flow.
Pressure propagates from pressure source pipes listed inside a system config in page files.
"""
has_flow = False
# check valve lists
for tag, v in valves.items():
if not valve_states.get(tag, False):
continue
# valves can have keys like 'pipes_mixing.json' or 'connected_pipes'
for k, val in v.items():
if isinstance(val, list):
if (pipe_index + 1) in val or pipe_index in val:
has_flow = True
break
if has_flow:
break


# Pressure determination is left to the page config; default to False
has_pressure = False
return has_flow, has_pressure

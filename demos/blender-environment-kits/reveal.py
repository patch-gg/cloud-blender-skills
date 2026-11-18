"""Presentation: a sweep that grows the scatter across the terrain, left to right in the shot. A Geometry
Nodes modifier, first on Terrain, writes two point attributes that scatter.py takes as --mask (its density
factor): `reveal` (0 ahead of a moving front, 1 behind it) and `reveal_rock` (reveal x ENV_Slope, so rocks
favour steep ground). The front is driven by the Scene Time node: no keyframes, any frame renders alone.
It leaves the scene after the sweep, so scatter.py's numbers count the whole forest.
Run in the session before scatter.py:
    cloud.py run reveal.py -- --frames 20 92 --x -330 330 --width 70 --axis 1 0   (axis: sweep direction in XY)
"""
import argparse
import json
import sys

import bpy

ap = argparse.ArgumentParser()
ap.add_argument("--target", default="Terrain")
ap.add_argument("--frames", type=float, nargs=2, default=(20, 92))
ap.add_argument("--x", type=float, nargs=2, default=(-330, 330))
ap.add_argument("--width", type=float, default=70)
ap.add_argument("--axis", type=float, nargs=2, default=(1.0, 0.0))
a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])

ng = bpy.data.node_groups.get("DEMO_Reveal") or bpy.data.node_groups.new("DEMO_Reveal", "GeometryNodeTree")
ng.nodes.clear()
ng.interface.clear()
ng.is_modifier = True
ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
N, L = ng.nodes.new, ng.links.new
gi, go = N("NodeGroupInput"), N("NodeGroupOutput")

t = N("GeometryNodeInputSceneTime")
front = N("ShaderNodeMapRange")  # frame -> front x, eased
front.interpolation_type = "SMOOTHSTEP"
L(t.outputs["Frame"], front.inputs["Value"])
front.inputs["From Min"].default_value, front.inputs["From Max"].default_value = a.frames
front.inputs["To Min"].default_value, front.inputs["To Max"].default_value = a.x

pos = N("ShaderNodeVectorMath")  # distance along the sweep axis
pos.operation = "DOT_PRODUCT"
L(N("GeometryNodeInputPosition").outputs[0], pos.inputs[0])
pos.inputs[1].default_value = (a.axis[0], a.axis[1], 0.0)
lo = N("ShaderNodeMath")
lo.operation = "SUBTRACT"
L(front.outputs[0], lo.inputs[0])
lo.inputs[1].default_value = a.width / 2
hi = N("ShaderNodeMath")
hi.operation = "ADD"
L(front.outputs[0], hi.inputs[0])
hi.inputs[1].default_value = a.width / 2
rev = N("ShaderNodeMapRange")  # x < front - w/2 -> 1, x > front + w/2 -> 0
rev.interpolation_type = "SMOOTHSTEP"
L(pos.outputs["Value"], rev.inputs["Value"])
L(lo.outputs[0], rev.inputs["From Min"])
L(hi.outputs[0], rev.inputs["From Max"])
rev.inputs["To Min"].default_value, rev.inputs["To Max"].default_value = 1.0, 0.0

slope = N("GeometryNodeInputNamedAttribute")
slope.data_type = "FLOAT"
slope.inputs["Name"].default_value = "ENV_Slope"
rock = N("ShaderNodeMath")
rock.operation = "MULTIPLY"
L(rev.outputs[0], rock.inputs[0])
L(slope.outputs["Attribute"], rock.inputs[1])

geo = gi.outputs[0]
for name, src in (("reveal", rev.outputs[0]), ("reveal_rock", rock.outputs[0])):
    st = N("GeometryNodeStoreNamedAttribute")
    st.data_type, st.domain = "FLOAT", "POINT"
    st.inputs["Name"].default_value = name
    L(geo, st.inputs["Geometry"])
    L(src, st.inputs["Value"])
    geo = st.outputs["Geometry"]
L(geo, go.inputs[0])

ob = bpy.data.objects[a.target]
md = ob.modifiers.get("DEMO_Reveal") or ob.modifiers.new("DEMO_Reveal", "NODES")
md.node_group = ng
if ob.modifiers[0] != md:  # first, so every scatter layer reads it (5.2 has no ObjectModifiers.move)
    with bpy.context.temp_override(object=ob, active_object=ob):
        bpy.ops.object.modifier_move_to_index(modifier=md.name, index=0)
bpy.context.scene.frame_set(int(a.frames[1]) + 1)
print("@@JSON@@" + json.dumps({"ok": True, "modifier": md.name, "frames": a.frames, "x": a.x,
                               "width": a.width, "axis": a.axis, "stack": [m.name for m in ob.modifiers]}))

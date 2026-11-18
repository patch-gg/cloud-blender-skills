"""Finish the vest: Corrective Smooth after its Armature (the rigging skill's fix for collapsing: a 30-degree twist
pinched two creases into its front), bound in the rest pose; then its material, quilted nylon (horizontal
baffles from a band texture on the vest's rest coordinates, so the quilting rides along when it deforms), with a
reveal for the clip: above the `Reveal` height (0-1 up the vest) it is cut away, and a thin band just below the
cut is pink (#F53CD1) and glows: the edge being made.
Run in the session (rig in its rest pose): cloud.py run vest_finish.py -- --object Vest [--color 0.82 0.8 0.76]
"""
import json
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ob = bpy.data.objects[argv[argv.index("--object") + 1] if "--object" in argv else "Vest"]
col = [float(x) for x in argv[argv.index("--color") + 1:argv.index("--color") + 4]] if "--color" in argv \
    else [0.82, 0.8, 0.76]
PINK = (0.913, 0.045, 0.638, 1.0)

cs = ob.modifiers.new("CorrectiveSmooth", "CORRECTIVE_SMOOTH")   # last in the stack: after the Armature
cs.rest_source = "BIND"
with bpy.context.temp_override(object=ob, active_object=ob):
    bpy.ops.object.correctivesmooth_bind(modifier=cs.name)

m = bpy.data.materials.new("M_Vest")
nt = m.node_tree
bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
bsdf.inputs["Base Color"].default_value = (*col, 1.0)
bsdf.inputs["Roughness"].default_value = 0.42
bsdf.inputs["Sheen Weight"].default_value = 0.35
bsdf.inputs["Emission Color"].default_value = PINK
L = nt.links.new
tc = nt.nodes.new("ShaderNodeTexCoord")
sep = nt.nodes.new("ShaderNodeSeparateXYZ")
L(tc.outputs["Generated"], sep.inputs["Vector"])
# quilting: soft bands along the vest's height, as bump
wave = nt.nodes.new("ShaderNodeTexWave")
wave.wave_type, wave.bands_direction = "BANDS", "Z"
wave.inputs["Scale"].default_value = 2.6
wave.inputs["Distortion"].default_value = 0.0
L(tc.outputs["Generated"], wave.inputs["Vector"])
ramp = nt.nodes.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].position, ramp.color_ramp.elements[1].position = 0.0, 0.35
L(wave.outputs["Fac"], ramp.inputs["Fac"])
bump = nt.nodes.new("ShaderNodeBump")
bump.inputs["Strength"].default_value = 0.55
bump.inputs["Distance"].default_value = 0.01
L(ramp.outputs["Color"], bump.inputs["Height"])
L(bump.outputs["Normal"], bsdf.inputs["Normal"])
# reveal: z (0-1 up the vest, rest pose) below Reveal is cloth, a 3% band under the cut is pink
rev = nt.nodes.new("ShaderNodeValue")
rev.name = rev.label = "Reveal"
rev.outputs[0].default_value = 1.2
lt = nt.nodes.new("ShaderNodeMath")
lt.operation = "LESS_THAN"
L(sep.outputs["Z"], lt.inputs[0])
L(rev.outputs[0], lt.inputs[1])
L(lt.outputs[0], bsdf.inputs["Alpha"])
lo = nt.nodes.new("ShaderNodeMath")
lo.operation = "SUBTRACT"
L(rev.outputs[0], lo.inputs[0])
lo.inputs[1].default_value = 0.03
gt = nt.nodes.new("ShaderNodeMath")
gt.operation = "GREATER_THAN"
L(sep.outputs["Z"], gt.inputs[0])
L(lo.outputs[0], gt.inputs[1])
band = nt.nodes.new("ShaderNodeMath")
band.operation = "MULTIPLY"
L(gt.outputs[0], band.inputs[0])
L(lt.outputs[0], band.inputs[1])
glow = nt.nodes.new("ShaderNodeMath")
glow.operation = "MULTIPLY"
glow.inputs[1].default_value = 4.0
L(band.outputs[0], glow.inputs[0])
L(glow.outputs[0], bsdf.inputs["Emission Strength"])
tint = nt.nodes.new("ShaderNodeMix")                      # the band is pink cloth too, not just a glow
tint.data_type = "RGBA"
L(band.outputs[0], tint.inputs["Factor"])
tint.inputs["A"].default_value = (*col, 1.0)
tint.inputs["B"].default_value = PINK
L(tint.outputs["Result"], bsdf.inputs["Base Color"])
ob.data.materials.clear()
ob.data.materials.append(m)
print("@@JSON@@" + json.dumps({"ok": True, "object": ob.name, "material": m.name, "color": col,
                               "modifiers": [md.type for md in ob.modifiers]}))

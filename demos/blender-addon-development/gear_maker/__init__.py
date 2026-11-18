"""Gear Maker - an extension built from blender-addon-development's template (4.2+ extension format)."""
import bpy

from . import operators, ui

classes = (
    operators.GEARMAKER_PG_settings,
    operators.GEARMAKER_OT_add_gear,
    ui.GEARMAKER_PT_main,
    ui.GEARMAKER_AP_preferences,
)


def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.Scene.gear_maker = bpy.props.PointerProperty(type=operators.GEARMAKER_PG_settings)
    bpy.types.VIEW3D_MT_mesh_add.append(ui.menu_func)


def unregister():
    bpy.types.VIEW3D_MT_mesh_add.remove(ui.menu_func)
    del bpy.types.Scene.gear_maker
    for c in reversed(classes):
        bpy.utils.unregister_class(c)

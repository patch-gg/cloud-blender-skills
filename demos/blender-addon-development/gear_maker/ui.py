import bpy


class GEARMAKER_PT_main(bpy.types.Panel):
    bl_label = "Gear Maker"
    bl_idname = "GEARMAKER_PT_main"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Gear Maker"  # sidebar (N) tab

    def draw(self, context):
        s = context.scene.gear_maker
        col = self.layout.column(align=True)
        col.use_property_split = True
        for p in ("teeth", "module", "width", "bore", "spokes", "metal"):
            col.prop(s, p)
        self.layout.operator("gear_maker.add_gear", icon="SETTINGS")


class GEARMAKER_AP_preferences(bpy.types.AddonPreferences):
    bl_idname = __package__  # extensions: package name, never a hard-coded string

    bevel: bpy.props.BoolProperty(name="Bevel new gears", default=True)

    def draw(self, context):
        self.layout.prop(self, "bevel")


def menu_func(self, context):
    self.layout.operator("gear_maker.add_gear", icon="SETTINGS")

bl_info = {
    "name": "Reloader",
    "author": "Rob Stenson",
    "version": (0, 1),
    "blender": (3, 0, 0),
    #"location": "Text Editor > Dev Tab > Icon Viewer",
    "location": "View3D > Toolshelf",
    "description": "Reloading external scripts automatically",
    "warning": "",
    "wiki_url": "",
    "category": "Reloader",
}

import bpy, time

from bpy_extras.io_utils import ImportHelper
from pathlib import Path
from os.path import relpath
from runpy import run_path


class ReloaderPropertiesGroup(bpy.types.PropertyGroup):
    script_path: bpy.props.StringProperty(name="Path", default="")
    script_watch: bpy.props.BoolProperty(name="Watch", default=True)
    script_watch_interval: bpy.props.FloatProperty(name="Interval", default=0.25)
    reload_count: bpy.props.IntProperty(name="Reload Count", default=0)


def run_script(context):
    rl = context.scene.reloader
    rl.reload_count += 1
    print("RUN SCRIPT", rl.script_path)
    path = Path(rl.script_path)
    res = run_path(path, init_globals=dict(BLENDER_RELOADER=True, BLENDER_RELOADER_COUNT=rl.reload_count))
    print("> ran external <")


class ReloaderPanel(bpy.types.Panel):
    bl_label = "Reloader"
    bl_idname = "RELOADER_PT_MAINPANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Reloader"
    
    #bl_space_type = "TEXT_EDITOR"
    #bl_region_type = "UI"
    #bl_category = "Dev"
    
    @classmethod
    def poll(cls, context):
        return True
    
    def draw(self, context):
        layout = self.layout
        rl = context.scene.reloader
        
        if rl.script_path:
            blend_path = Path(bpy.data.filepath).absolute()
            rlpath = Path(rl.script_path).absolute()
            rel = Path(relpath(rlpath, blend_path)).parent
            
            #try:
            row = layout.row()
            row.label(text=f"{rel}")
            row.label(text=f"{rlpath.name}")
            
            layout.row().prop(rl, "script_watch", text="Reload on Save")
            layout.row().prop(rl, "script_watch_interval")
            
            #layout.row().prop(rl, "script_last_mod")
        
            layout.row().operator("wm.reloader_run_script", text="Run Script")
            layout.row().operator("wm.reloader_choose_script", text="Change Script")
        
        else:
            layout.row().operator("wm.reloader_choose_script", text="Choose Script")
        
        layout.row().operator("wm.reloader_reload_addons", text="Reload all Addons")


class WM_OT_ReloaderChooseScript(bpy.types.Operator, ImportHelper):
    bl_idname = "wm.reloader_choose_script"
    bl_label = "Choose script file"
    
    filter_glob: bpy.props.StringProperty(
        default='*.py;',
        options={'HIDDEN'}
    )
    
    some_boolean: bpy.props.BoolProperty(
        name='Do a thing',
        description='Do a thing with the file you\'ve selected',
        default=True,
    )

    def execute(self, context):
        path = Path(self.filepath)
        
        context.scene.reloader.script_path = str(path)
        context.scene.reloader.reload_count = 0

        #bpy.ops.wm.reloader_watch_script()
        
        return {'FINISHED'}


class WM_OT_ReloaderRunScript(bpy.types.Operator):
    bl_idname = "wm.reloader_run_script"
    bl_label = "Run script"

    def execute(self, context):
        run_script(context)
        return {'FINISHED'}


class WM_OT_ReloaderReloadAddons(bpy.types.Operator):
    bl_idname = "wm.reloader_reload_addons"
    bl_label = "Reload Addons"

    def execute(self, context):
        print("HERE!")
        bpy.ops.script.reload()
        return {'FINISHED'}


class WT_OT_ReloaderWatchScript(bpy.types.Operator):
    bl_idname = "wm.reloader_watch_script"
    bl_label = "Watch script"
    
    _timer = None
    _last_updated = 0
    
    def modal(self, context, event):
        if event.type == 'TIMER':
            rl = context.scene.reloader
            ctx = context.copy()
            
            path = rl.script_path
            if path:
                path = Path(path)
                mod = path.stat().st_mtime
                #print(rl.script_last_mod, mod, time.time())
                #if rl.script_last_mod
                if mod > self._last_updated:
                    print("CHANGED!", mod, self._last_updated)
                    self._last_updated = time.time()
                    #context.view_layer.update()
                    run_script(context)
    
        return {'PASS_THROUGH'}
    
    def execute(self, context):
        rl = context.scene.reloader
        wm = context.window_manager
        
        self._timer = wm.event_timer_add(
            rl.script_watch_interval, window=context.window)
        
        wm.modal_handler_add(self)

        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
        print('timer removed')


classes = [
    WM_OT_ReloaderReloadAddons,
    WM_OT_ReloaderChooseScript,
    WM_OT_ReloaderRunScript,
    WT_OT_ReloaderWatchScript,
    ReloaderPanel,
    ReloaderPropertiesGroup,
]

addon_keymaps = []

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.reloader = bpy.props.PointerProperty(type=ReloaderPropertiesGroup, name="Reloader", description="Reloader properties")

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon

    if kc:
        addon_keymaps.append([
            km:=kc.keymaps.new(name='3D View Generic', space_type='VIEW_3D'),
            km.keymap_items.new(WM_OT_ReloaderReloadAddons.bl_idname, type='T', value='PRESS', shift=True)
        ])

    print("--RELOADER--")
    #bpy.ops.wm.reloader_watch_script()


def unregister():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    
    addon_keymaps.clear()

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
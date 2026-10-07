"""Run in Blender's Text Editor, then use the 3D View sidebar > KAJU Elevator."""
import bpy

LEVELS = [
    ('about', '01 / About me'), ('skills', '02 / Skills'),
    ('projects', '03 / Projects'), ('experience', '04 / Experience & education'),
]


def show_level(scene, level_id):
    for item, _ in LEVELS:
        col = bpy.data.collections.get('Elevator / Dialog / ' + item)
        if col:
            col.hide_render = item != level_id
            col.hide_viewport = item != level_id
        landing = bpy.data.collections.get('Elevator / Destination / ' + item)
        if landing:
            landing.hide_render = item != level_id
            landing.hide_viewport = item != level_id
    scene['selected_level'] = level_id or ''
    if level_id:
        scene.camera = bpy.data.objects.get('Elevator / Dialog review camera')
    display = bpy.data.objects.get('Elevator / Current floor display')
    if display and display.type == 'FONT':
        display.data.body = next((f'{i+1:02}' for i, (key, _) in enumerate(LEVELS) if key == level_id), '--')
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()


class KAZE_OT_preview_level(bpy.types.Operator):
    bl_idname = 'kaze.preview_level'
    bl_label = 'Preview level dialog'
    level_id: bpy.props.StringProperty()

    def execute(self, context):
        show_level(context.scene, self.level_id)
        if bpy.data.objects.get('Elevator / Full journey camera'):
            start_departure(context)
        return {'FINISHED'}


class KAZE_OT_close_dialog(bpy.types.Operator):
    bl_idname = 'kaze.close_dialog'
    bl_label = 'Close dialog'

    def execute(self, context):
        show_level(context.scene, None)
        return {'FINISHED'}


class KAZE_OT_pick_levels(bpy.types.Operator):
    bl_idname = 'kaze.pick_levels'
    bl_label = 'Enable viewport button clicks'
    _timer = None
    _last = None

    def execute(self, context):
        if context.scene.get('floor_picking_enabled'):
            return {'CANCELLED'}
        context.scene['floor_picking_enabled'] = True
        self._timer = context.window_manager.event_timer_add(.2, window=context.window)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if not context.scene.get('floor_picking_enabled') or event.type == 'ESC':
            context.scene['floor_picking_enabled'] = False
            context.window_manager.event_timer_remove(self._timer)
            return {'CANCELLED'}
        if event.type == 'TIMER':
            obj = context.view_layer.objects.active
            if obj and obj != self._last:
                self._last = obj
                level_id = obj.get('level_id')
                if level_id:
                    show_level(context.scene, level_id)
                    if bpy.data.objects.get('Elevator / Full journey camera'):
                        start_departure(context)
                elif obj.get('interaction') == 'close-level-dialog':
                    show_level(context.scene, None)
        return {'PASS_THROUGH'}


def start_departure(context):
    scene = context.scene
    scene.camera = bpy.data.objects['Elevator / Full journey camera']
    scene.frame_set(181)
    scene.frame_start = 181
    scene.frame_end = 510
    for area in context.screen.areas if context.screen else []:
        if area.type == 'VIEW_3D':
            area.spaces.active.region_3d.view_perspective = 'CAMERA'
    if context.screen and not context.screen.is_animation_playing:
        bpy.ops.screen.animation_play()


class KAZE_OT_journey(bpy.types.Operator):
    bl_idname = 'kaze.journey'
    bl_label = 'Replay elevator journey'
    mode: bpy.props.StringProperty(default='entry')

    def execute(self, context):
        scene = context.scene
        scene.camera = bpy.data.objects['Elevator / Full journey camera']
        if self.mode == 'entry':
            show_level(scene, None)
            scene.frame_start = 1
            scene.frame_end = 180
            scene.frame_set(1)
        else:
            show_level(scene, scene.get('selected_level') or 'about')
            start_departure(context)
            return {'FINISHED'}
        for area in context.screen.areas if context.screen else []:
            if area.type == 'VIEW_3D':
                area.spaces.active.region_3d.view_perspective = 'CAMERA'
        if context.screen and not context.screen.is_animation_playing:
            bpy.ops.screen.animation_play()
        return {'FINISHED'}


class KAZE_OT_stop_picking(bpy.types.Operator):
    bl_idname = 'kaze.stop_picking'
    bl_label = 'Disable viewport button clicks'

    def execute(self, context):
        context.scene['floor_picking_enabled'] = False
        return {'FINISHED'}


class KAZE_PT_elevator(bpy.types.Panel):
    bl_label = 'KAJU / Elevator levels'
    bl_idname = 'KAZE_PT_elevator'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'KAJU Elevator'

    def draw(self, context):
        self.layout.label(text='Four destinations / doors already open')
        if bpy.data.objects.get('Elevator / Full journey camera'):
            self.layout.operator('kaze.journey', text='Replay entry / stop at selection').mode = 'entry'
            self.layout.operator('kaze.journey', text='Replay selected departure').mode = 'exit'
        for key, label in reversed(LEVELS):
            op = self.layout.operator('kaze.preview_level', text=label, depress=context.scene.get('selected_level') == key)
            op.level_id = key
        self.layout.operator('kaze.close_dialog')
        self.layout.separator()
        self.layout.operator('kaze.stop_picking' if context.scene.get('floor_picking_enabled') else 'kaze.pick_levels')
        self.layout.label(text='Click a floor mesh in Object Mode.')
        self.layout.label(text='Press Esc to stop floor picking.')


CLASSES = [KAZE_OT_preview_level, KAZE_OT_close_dialog, KAZE_OT_pick_levels, KAZE_OT_stop_picking, KAZE_OT_journey, KAZE_PT_elevator]
for cls in CLASSES:
    previous = getattr(bpy.types, cls.__name__, None)
    if previous:
        bpy.utils.unregister_class(previous)
    bpy.utils.register_class(cls)


def kaze_stop_at_journey_end(scene, depsgraph=None):
    if (scene.camera and scene.camera.name == 'Elevator / Full journey camera'
            and scene.frame_current >= scene.frame_end
            and bpy.context.screen and bpy.context.screen.is_animation_playing):
        bpy.ops.screen.animation_cancel(restore_frame=False)


for handler in list(bpy.app.handlers.frame_change_post):
    if handler.__name__ == 'kaze_stop_at_journey_end':
        bpy.app.handlers.frame_change_post.remove(handler)
bpy.app.handlers.frame_change_post.append(kaze_stop_at_journey_end)

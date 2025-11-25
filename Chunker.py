bl_info = {
    "name": "Chunker",
    "author": "JoshMakesStuff (optimized + non-cutting)",
    "version": (1, 4, 0),
    "blender": (4, 0, 0),
    "location": "View3D > UI > Chunker",
    "description": "Split a mesh into xy grid chunks using Boolean or fast non-cutting method",
    "category": "Mesh",
}

# I CANNOT BELIEVE THIS DIDNT EXIST BEFORE LOL
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
# WHAT'RE YOU LOOKIN AT??? GO AWAY STINKY!
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
# OK FINE YOU CAN STAY BUT JUST DON'T TOUCH ANYTHING
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.
#.

import bpy
from mathutils import Vector

class ChunkerOperator(bpy.types.Operator):
    """Split object into chunks (optimized, optional non-cutting)"""
    bl_idname = "mesh.chunker"
    bl_label = "Chunk Object"
    bl_options = {'REGISTER', 'UNDO'}

    # --- Operator properties ---
    x_count: bpy.props.IntProperty(name="X Count", default=1, min=1)
    y_count: bpy.props.IntProperty(name="Y Count", default=1, min=1)
    debug: bpy.props.BoolProperty(name="Debug", default=True, description="Print detailed chunk info")
    use_cutting: bpy.props.BoolProperty(name="Use Cutting", default=True, description="If disabled, just select vertices in the chunk instead of cutting")

    @classmethod
    def poll(cls, context):
        # Only allow this operator if an active mesh object is selected in Object mode
        return (context.active_object
                and context.active_object.type == 'MESH'
                and context.mode == 'OBJECT')

    def execute(self, context):
        obj = context.active_object
        mesh = obj.data
        matrix = obj.matrix_world

        # --- Fast bounding box calculation ---
        bbox_world = [matrix @ Vector(c) for c in obj.bound_box]
        xs = [v.x for v in bbox_world]
        ys = [v.y for v in bbox_world]
        zs = [v.z for v in bbox_world]

        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        min_z, max_z = min(zs), max(zs)

        size_x = max_x - min_x
        size_y = max_y - min_y
        size_z = max_z - min_z

        # Bail out if object has zero or negative dimensions
        if size_x <= 0 or size_y <= 0:
            self.report({'ERROR'}, "Invalid bounding box")
            return {'CANCELLED'}

        # --- Calculate step sizes for each chunk ---
        x_step = size_x / self.x_count
        y_step = size_y / self.y_count
        height = size_z + 0.1  # Slightly extend in Z to avoid clipping
        z_center = min_z + size_z * 0.5

        # Debug info in console
        if self.debug:
            print(f"[CHUNKER] Object: {obj.name}, Grid: {self.x_count}x{self.y_count}")
            print(f"[CHUNKER] Size: ({size_x:.2f}, {size_y:.2f}, {size_z:.2f})")
            print(f"[CHUNKER] Mode: {'Cutting' if self.use_cutting else 'Non-Cutting'}")

        # --- Create or get a dedicated collection for chunks ---
        col_name = f"{obj.name}_Chunks"
        chunks_col = bpy.data.collections.get(col_name)
        if not chunks_col:
            chunks_col = bpy.data.collections.new(col_name)
            context.scene.collection.children.link(chunks_col)

        # --- Optional cutter object for Boolean mode ---
        if self.use_cutting:
            bpy.ops.mesh.primitive_cube_add(size=2, location=(0,0,0))
            cutter = context.active_object
            cutter.name = f"{obj.name}_Cutter"
            cutter.display_type = 'WIRE'
            # Move cutter to chunks collection
            for c in cutter.users_collection:
                c.objects.unlink(cutter)
            chunks_col.objects.link(cutter)

        view_layer = context.view_layer

        # Store current selection and active object so we can restore later
        prev_active = view_layer.objects.active
        prev_selected = list(context.selected_objects)

        chunks_created = 0
        half_x_step = x_step * 0.5
        half_y_step = y_step * 0.5
        half_height = height * 0.5

        # --- Main loop to create chunks ---
        for ix in range(self.x_count):
            cx = min_x + x_step * ix + half_x_step
            for iy in range(self.y_count):
                cy = min_y + y_step * iy + half_y_step

                min_cx = cx - half_x_step
                max_cx = cx + half_x_step
                min_cy = cy - half_y_step
                max_cy = cy + half_y_step

                if self.use_cutting:
                    # --- Cutting mode: Boolean intersection ---
                    cutter.location = (cx, cy, z_center)
                    cutter.scale = (half_x_step, half_y_step, half_height)

                    new_mesh = mesh.copy()
                    chunk_name = f"{obj.name}_Chunk_{ix}_{iy}"
                    chunk_obj = bpy.data.objects.new(chunk_name, new_mesh)
                    chunks_col.objects.link(chunk_obj)
                    chunk_obj.matrix_world = matrix.copy()

                    mod = chunk_obj.modifiers.new(name="ChunkerBool", type='BOOLEAN')
                    mod.operation = 'INTERSECT'
                    mod.object = cutter
                    mod.solver = 'EXACT'
                    bpy.context.view_layer.objects.active = chunk_obj
                    bpy.ops.object.modifier_apply(modifier=mod.name)
                    chunks_created += 1

                else:
                    # --- Non-cutting mode: create chunk by selecting vertices ---
                    verts = []
                    faces = []
                    vert_map = {}

                    for vidx, v in enumerate(mesh.vertices):
                        co_world = matrix @ v.co
                        if min_cx <= co_world.x <= max_cx and min_cy <= co_world.y <= max_cy:
                            vert_map[vidx] = len(verts)
                            verts.append(co_world)

                    for f in mesh.polygons:
                        face_indices = [vert_map[i] for i in f.vertices if i in vert_map]
                        if len(face_indices) == len(f.vertices):
                            faces.append(face_indices)

                    chunk_mesh = bpy.data.meshes.new(f"{obj.name}_Chunk_{ix}_{iy}")
                    chunk_mesh.from_pydata(verts, [], faces)
                    chunk_mesh.update()
                    chunk_obj = bpy.data.objects.new(f"{obj.name}_Chunk_{ix}_{iy}", chunk_mesh)
                    chunks_col.objects.link(chunk_obj)
                    chunks_created += 1

                    if self.debug:
                        print(f"[CHUNKER] Chunk ({ix},{iy}) -> Vertices: {len(verts)}, Faces: {len(faces)}")

        # --- Restore previous selection and hide original ---
        bpy.ops.object.select_all(action='DESELECT')
        for obj_sel in prev_selected:
            if obj_sel and obj_sel.name in bpy.data.objects:
                obj_sel.select_set(True)
        view_layer.objects.active = prev_active

        obj.hide_set(True)  # Hide original mesh

        # Remove cutter if used
        if self.use_cutting:
            bpy.data.objects.remove(cutter, do_unlink=True)

        self.report({'INFO'}, f"Created {chunks_created} chunks")
        if self.debug:
            print(f"[CHUNKER] Completed: {chunks_created} chunks created")

        return {'FINISHED'}


class ChunkerPanel(bpy.types.Panel):
    bl_label = "Chunker"
    bl_idname = "OBJECT_PT_chunker"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Chunker"

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.label(text="Chunk Grid:")
        row = col.row(align=True)
        row.prop(context.scene, "chunker_x")
        row.prop(context.scene, "chunker_y")
        col.separator()
        col.prop(context.scene, "chunker_debug", text="Debug Output")
        col.prop(context.scene, "chunker_cutting", text="Use Cutting")
        col.separator()
        op = col.operator("mesh.chunker", text="Chunk Object", icon='MOD_ARRAY')
        op.x_count = context.scene.chunker_x
        op.y_count = context.scene.chunker_y
        op.debug = context.scene.chunker_debug
        op.use_cutting = context.scene.chunker_cutting


def register():
    bpy.utils.register_class(ChunkerOperator)
    bpy.utils.register_class(ChunkerPanel)
    # --- Scene properties for UI ---
    bpy.types.Scene.chunker_x = bpy.props.IntProperty(
        name="X", default=1, min=1, max=100,
        description="Number of chunks along X axis"
    )
    bpy.types.Scene.chunker_y = bpy.props.IntProperty(
        name="Y", default=1, min=1, max=100,
        description="Number of chunks along Y axis"
    )
    bpy.types.Scene.chunker_debug = bpy.props.BoolProperty(
        name="Debug", default=False,
        description="Print debug information to console"
    )
    bpy.types.Scene.chunker_cutting = bpy.props.BoolProperty(
        name="Use Cutting", default=True,
        description="Toggle between Boolean cutting or fast non-cutting chunking"
    )


def unregister():
    try:
        del bpy.types.Scene.chunker_debug
        del bpy.types.Scene.chunker_y
        del bpy.types.Scene.chunker_x
        del bpy.types.Scene.chunker_cutting
    except AttributeError:
        pass
    bpy.utils.unregister_class(ChunkerPanel)
    bpy.utils.unregister_class(ChunkerOperator)


if __name__ == "__main__":
    register()

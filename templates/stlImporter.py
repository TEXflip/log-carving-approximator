import bpy
import sys

argv = sys.argv
argv = argv[argv.index("--") + 1:]

if bpy.context.mode != 'OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=True)
bpy.ops.import_mesh.stl(filepath=argv[0])
bpy.ops.import_mesh.stl(filepath=argv[1])
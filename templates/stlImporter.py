import bpy
import sys
from mathutils import Quaternion, Vector

def vecRotation(v2):
    # v1.normalize()
    v1 = Vector((0,0,1))
    v2.normalize()
    if v1 == -v2:
        v1.orthogonal().normalize()
        return Quaternion((0, v1[0], v1[1], v1[2])).to_euler()
    half = (v1+v2).normalized()
    cross = v1.cross(half)
    return Quaternion((v1.dot(half), cross[0], cross[1], cross[2])).to_euler()

argv = sys.argv
argv = argv[argv.index("--") + 1:]

if bpy.context.mode != 'OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=True)
bpy.ops.import_mesh.stl(filepath=argv[0])
bpy.ops.import_mesh.stl(filepath=argv[1])

cuts = []
for c in argv[2].split(';'):
    cuts.append([float(n) for n in c.split(',')])

for c in cuts:
    bpy.ops.mesh.primitive_plane_add(size=3, location=Vector(c[:3]), rotation=vecRotation(Vector(c[3:])))

for o in bpy.data.objects:
    if "Plane" in o.name:
        o.display_type = "WIRE"
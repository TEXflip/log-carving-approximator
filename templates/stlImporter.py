import bpy
import sys
from mathutils import Quaternion, Vector
import math

def vecRotation(v1, v2):
    v1 = Vector(v1)
    v2.normalize()
    if v1 == -v2:
        v1 = Vector((0,v1[2],-v1[1]))
        return Quaternion((0, v1[0], v1[1], v1[2])).to_euler()
    half = (v1+v2).normalized()
    cross = v1.cross(half)
    return Quaternion((v1.dot(half), cross[0], cross[1], cross[2])).to_euler()

def generateWedge(origin, rotation, angle):
    scale = 15
    angleRad = angle * (math.pi/180) * 0.5
    vx = math.sin(angleRad)
    vy = math.cos(angleRad)
    v3y = 1 if angle > 90 else vy
    
    vertices = [(0,0,-1), (vx,vy,-1), (0,v3y,-1), (-vx,vy,-1),  # lower face vertices
                (0,0,1), (vx,vy,1), (0,v3y,1), (-vx,vy,1)]     # upper face vertices
    edges = [(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),(0,4),(1,5),(2,6),(3,7)]
    faces = [(3,2,1,0), (7,4,5,6), (3,0,4,7), (2,3,7,6), (1,2,6,5), (0,1,5,4)]
    
    new_mesh = bpy.data.meshes.new('wedge')
    new_mesh.from_pydata(vertices, edges, faces)
    new_mesh.update()
    
    wedge = bpy.data.objects.new('wedge', new_mesh)
    bpy.data.collections["Collection"].objects.link(wedge)
    
    wedge.scale = (scale, scale*5, scale)
    wedge.rotation_euler = vecRotation((0,-1,0),Vector(rotation))
    wedge.location = origin

    return wedge

argv = sys.argv
argv = argv[argv.index("--") + 1:]

if bpy.context.mode != 'OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=True)
bpy.ops.import_mesh.stl(filepath=argv[0])
bpy.ops.import_mesh.stl(filepath=argv[1])

if argv[2] == "plane":
    cuts = []
    for c in argv[3].split(';'):
        cuts.append([float(n) for n in c.split(',')])

    for c in cuts:
        bpy.ops.mesh.primitive_plane_add(size=3, location=Vector(c[:3]), rotation=vecRotation((0,0,1),Vector(c[3:])))

    for o in bpy.data.objects:
        if "Plane" in o.name:
            o.display_type = "WIRE"
else:
    cuts = []
    for c in argv[3].split(';'):
        cuts.append([float(n) for n in c.split(',')])

    for c in cuts:
        generateWedge(c[0:3], c[3:6], c[6])

    for o in bpy.data.objects:
        if "wedge" in o.name:
            o.display_type = "WIRE"
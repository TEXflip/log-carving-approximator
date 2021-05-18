import random
import bpy
import bmesh
import trimesh
import numpy as np
from mathutils import Vector, Quaternion
from math import radians

objects = bpy.data.objects
context = bpy.context

def vecRotation(v1, v2):
    # v1.normalize()
    v2.normalize()
    if v1 == -v2:
        v1.orthogonal().normalize()
        return Quaternion((0, v1[0], v1[1], v1[2])).to_euler()
    half = (v1+v2).normalized()
    cross = v1.cross(half)
    return Quaternion((v1.dot(half), cross[0], cross[1], cross[2])).to_euler()

def slice(mesh, origin, normal):
    newcube = cube.copy()
    empty = bpy.data.objects.new("empty", None)
    bpy.data.collections["Collection"].objects.link(empty)
    newcube.parent = empty
    empty.location = origin
    empty.rotation_euler = vecRotation(Vector((0,0,1)), Vector(normal))
    bool = mesh.modifiers.new(type="BOOLEAN", name="bool")
    bool.double_threshold = 0.000025
    bool.object = newcube
    bool.operation = 'INTERSECT'
    return bool
    # remesh = mesh.modifiers.new(type='REMESH', name='remesh')
    # remesh.mode = 'SHARP'
    # remesh.octree_depth = 5 # default is 4, higher finer details
    # triangulate = mesh.modifiers.new(type='TRIANGULATE', name='triangulate')
    # bpy.ops.object.mode_set(mode = 'OBJECT')
    # mesh.select_set(True)
    # bpy.ops.object.convert()
    # bpy.ops.object.select_all(action='DESELECT')
    # mesh.select_set(True)

def computeVolume(mesh):
    bm = bmesh.new()
    bm.from_mesh(mesh)
    volume = bm.calc_volume()
    return volume * (context.scene.unit_settings.scale_length ** 3.0) * 1e6

if __name__ == "__main__":
    # reset the workspace
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=True)

    # create base cube for the boolean operation
    bpy.ops.mesh.primitive_cube_add(location=(0, 0, 250), size=500, rotation=(0.0, 0.0, 0.0), enter_editmode=False)
    cube = objects['Cube']

    # import cylinder
    bpy.ops.import_mesh.stl(filepath='3D models/cylinder.stl')
    cylinder = objects['Cylinder']

    # compute sphere volume
    bpy.ops.import_mesh.stl(filepath='3D models/sphere.stl')
    sphere = objects['Sphere']
    sphereVolume = computeVolume(sphere.data)
    bpy.ops.object.select_all(action='DESELECT')
    sphere.select_set(True)
    bpy.ops.object.delete()

    # compute planes (origin & normal) for the cuts
    sphere_trimesh = trimesh.load('3D models/sphere.stl', force='mesh') # only in lecture to read the vertexes
    oldOrig = {}
    cuts = []

    for i, normal in enumerate(sphere_trimesh.face_normals):
        face = sphere_trimesh.faces[i]
        origin = sphere_trimesh.vertices[face[0]]

        intOrig = (origin*1000).astype(np.int32)
        origin = origin.tolist()
        hashValue = hash(intOrig)
        if not (hashValue in oldOrig):
            oldOrig[hashValue] = 0
            normal = (np.array(normal) * -1).tolist()
            cuts.append([i, origin, normal])

    random.shuffle(cuts)
    print('total cuts: ', len(cuts))

    # do the cuts
    for i, cut in enumerate(cuts):
        bool = slice(cylinder, cut[1], cut[2])
        bpy.context.view_layer.objects.active = cylinder
        bpy.ops.object.modifier_apply(modifier=bool.name)
        currVol = computeVolume(cylinder.data)
        print("cut n. {0} \t diff. volume: {1:.0f}       ".format(i+1,currVol-sphereVolume), end='\r')
    print()

    # export the model
    bpy.ops.object.select_all(action='DESELECT')
    cylinder.select_set(True)
    bpy.ops.export_mesh.stl(filepath='cylinderCut.stl', use_selection=True)
import numpy as np
import trimesh
import json

sphere = trimesh.load('3D models/sphere.stl', force='mesh')
cylinder = trimesh.load('3D models/cylinder.stl', force='mesh')

sphereVolume = sphere.volume
oldOrig = {}
planes = []

for i, normal in enumerate(sphere.face_normals):
    face = sphere.faces[i]
    origin = sphere.vertices[face[0]]

    intOrig = (origin*1000).astype(np.int32)
    origin = origin.tolist()
    hashValue = hash(intOrig)

    if not (hashValue in oldOrig):
        oldOrig[hashValue] = 0
        normal = (np.array(normal) * -1).tolist()
        cylinder = cylinder.slice_plane(plane_origin=origin, plane_normal=normal, cap=True, cached_dots=None)
        planes.append({"orig":origin, "norm":normal})
        cylinder.merge_vertices()
        print("i: {2}\t Volume diff.: {0} \t vertices: {1}".format(cylinder.volume - sphereVolume, len(cylinder.vertices),i))

    if i > 11: # il 12 taglio non e' watertight
        break

file_out = open('blender sessions/planes.json', "w")
json.dump(planes, file_out, indent=2)

# print(cylinder.is_watertight)
# cylinder.export('cylinderCut.stl')
cylinder.show()
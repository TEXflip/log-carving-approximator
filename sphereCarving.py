import numpy as np
import trimesh
import json
from customBlenderScripts import customSliceMesh

sphere = trimesh.load('3D models/sphere.stl', force='mesh')
cylinder = trimesh.load('3D models/cylinder.stl', force='mesh')

sphereVolume = sphere.volume
oldOrig = {}
planes = []
print(len(sphere.face_normals))
for i, normal in enumerate(sphere.face_normals):
    face = sphere.faces[i]
    origin = sphere.vertices[face[0]]

    intOrig = (origin*1000).astype(np.int32)
    origin = origin.tolist()
    hashValue = hash(intOrig)

    if not (hashValue in oldOrig):
        oldOrig[hashValue] = 0
        normal = (np.array(normal) * -1).tolist()
        # cylinder = cylinder.slice_plane(plane_origin=origin, plane_normal=normal, cap=True, cached_dots=None)
        cylinder = customSliceMesh(cylinder, origin, normal)
        planes.append({"orig":origin, "norm":normal})
        cylinder.merge_vertices()
        print("i: {2}\t Volume diff.: {0} \t vertices: {1}".format(cylinder.volume - sphereVolume, len(cylinder.vertices),i))

        # if not cylinder.is_watertight:
        #     cylinder.show()
        #     cylinder.export('cylinderCut.stl')

    if i > 20: # il 12 taglio non e' watertight
        break

file_out = open('blender sessions/planes.json', "w")
json.dump(planes, file_out, indent=2)
cylinder.export('cylinderCut.stl')
# print(cylinder.is_watertight)
cylinder.show()
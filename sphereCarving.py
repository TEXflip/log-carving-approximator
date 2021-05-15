import numpy as np
import trimesh
import json
from customBlenderScripts import customSliceMesh
import random

sphere = trimesh.load('3D models/sphere.stl', force='mesh')
cylinder = trimesh.load('3D models/cylinder.stl', force='mesh')

sphereVolume = sphere.volume
oldOrig = {}
planes = []

cuts = []
for i, normal in enumerate(sphere.face_normals):
    face = sphere.faces[i]
    origin = sphere.vertices[face[0]]

    intOrig = (origin*1000).astype(np.int32)
    origin = origin.tolist()
    hashValue = hash(intOrig)
    if not (hashValue in oldOrig):
        oldOrig[hashValue] = 0
        normal = (np.array(normal) * -1).tolist()
        cuts.append([i, origin, normal])

random.shuffle(cuts)
print('total cuts: ', len(cuts))

for i, cut in enumerate(cuts):
    # cylinder = cylinder.slice_plane(plane_origin=origin, plane_normal=normal, cap=True, cached_dots=None)
    out = customSliceMesh(cylinder, cut[1], cut[2])
    planes.append({"orig":cut[1], "norm":cut[2]})

    try:
        out.volume
    except:
        print("i: ",i,"\t slice error: cut rejected")
        continue
    else:
        cylinder = out

    # cylinder.merge_vertices()
    print("i: {2}\t Volume diff.: {0} \t vertices: {1}".format(cylinder.volume - sphereVolume, len(cylinder.vertices),i))

    if cylinder.volume - sphereVolume < 0.1:
        break

file_out = open('blender sessions/planes.json', "w")
json.dump(planes, file_out, indent=2)
cylinder.export('cylinderCut.stl')
# print(cylinder.is_watertight)
cylinder.show()
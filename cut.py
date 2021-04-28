import showObj
from pywavefront import Wavefront

obj = Wavefront('3D models/cubeWithNormal.obj',collect_faces=True)

# il formato dipende dai dati presenti (Normals, UV, colors)
# con solo i vertici: [v0.x, v0.y, v0.z, v1.x, v1.y, ...] per ogni triangolo
# print(obj.materials['default0'].vertices)
print(obj.mesh_list[0].faces)
print(obj.vertices[0])

# obj.materials['default0'].vertices = obj.materials['default0'].vertices[9*6:]

showObj.show(obj, False)
import numpy as np
import trimesh

mesh = trimesh.load('3D models/bulbasaur.STL', force='mesh')

mesh.invert() # inverte le normali

print(mesh.volume)

# taglio con piano orizzontale
slice1 = trimesh.intersections.slice_mesh_plane(mesh, plane_normal=[0,0,1], plane_origin=[10,0,10], cap=True, cached_dots=None)

# taglio con piano verticale
slice2 = trimesh.intersections.slice_mesh_plane(mesh, plane_normal=[1,0, 0], plane_origin=[5,0,10], cap=True, cached_dots=None)

# unione dei due pezzi
union = trimesh.boolean.union([slice1, slice2],'scad')

union.show()


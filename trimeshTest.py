import numpy as np
import trimesh

mesh = trimesh.load('3D models/bulbasaur.STL', force='mesh')

mesh.invert()
slice= trimesh.intersections.slice_mesh_plane(mesh, plane_normal=[1,0,0], plane_origin=mesh.centroid, cap=True, cached_dots=None)

slice.show()
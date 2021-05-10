import numpy as np
import trimesh

# mesh = trimesh.load('3D models/test_cube_website2.STL', force='mesh')
mesh = trimesh.load('3D models/bulbasaur.STL', force='mesh')

mesh.invert() # inverte le normali

print('Difference volume: ' + str(mesh.volume))

# --------- generazione taglio con 2 piani ------------
# taglio con piano orizzontale
slice1 = trimesh.intersections.slice_mesh_plane(mesh, plane_normal=[0,0,1], plane_origin=[10,0,10], cap=True, cached_dots=None)

# taglio con piano verticale
slice2 = trimesh.intersections.slice_mesh_plane(mesh, plane_normal=[1,0, 0], plane_origin=[5,0,10], cap=True, cached_dots=None)

# unione dei due pezzi
union = trimesh.boolean.union([slice1, slice2], 'scad')

union.show()

#---------- controllo intersezione con un piano -----------

# intersection = trimesh.intersections.mesh_plane(mesh, plane_normal=[0,0,1], plane_origin=[10,0,10], return_faces=False, cached_dots=None)
intersection = slice = mesh.section(plane_normal=[0,0,1], plane_origin=[10,0,30])

# l'oggetto == NoneType se non trova un'intersezione
intersection.show()

# ----------- controllo intersezione di due piani con la mesh --------

# taglio con piano orizzontale
slice1 = trimesh.intersections.slice_mesh_plane(mesh, plane_normal=[0,0,-1], plane_origin=[10,0,10], cap=True, cached_dots=None)

# taglio con piano verticale
slice2 = trimesh.intersections.slice_mesh_plane(mesh, plane_normal=[-1,0, 0], plane_origin=[5,0,10], cap=True, cached_dots=None)

# intersezione dei due pezzi
difference = trimesh.boolean.intersection([slice2, slice1], 'scad')

# l'oggetto == NoneType se non trova un'intersezione (idem per slice1 e slice2)
difference.show()



# print('Intersection volume: ' + str(intersection.volume))
# print('Difference volume: ' + str(difference.volume))
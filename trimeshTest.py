import numpy as np
import trimesh

mesh = trimesh.load('3D models/cube.obj', force='mesh')

slice = mesh.section(plane_origin=mesh.centroid, 
                     plane_normal=[0,0,1])

slice.show()
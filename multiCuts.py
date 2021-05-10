import math
import numpy as np
import trimesh
import random
from trimesh import collision
import showObj


def triRandomVector():
    a = random.uniform(-1, 1)
    b = random.uniform(-1, 1)
    c = random.uniform(-1, 1)
    s = abs(a) + abs(b) + abs(c)
    d = [a/s, b/s, c/s]
    return d


def triRandomOrigin(mesh):
    a = random.uniform(mesh.bounds[0][0], mesh.bounds[1][0])
    b = random.uniform(mesh.bounds[0][1], mesh.bounds[1][1])
    c = random.uniform(mesh.bounds[0][2], mesh.bounds[1][2])
    d = [a, b, c]
    return d

def scaleMesh(scaleFactor, meshToScale):
    Matrix = np.eye(4)
    Matrix[:2, :2] /= scaleFactor[:2]
    meshToScale.apply_transform(matrix)
    return meshToScale

def pushFromCentroid(mesh):
    centroid = mesh.centroid
    vector = triRandomOrigin(mesh)
    diff = centroid - vector
    toReturn = vector + diff*0.3
    return toReturn





mesh = trimesh.load('3D models/bulbasaur.STL', force='mesh')
cubo = trimesh.load('3D models/test_cube_website.stl', force='mesh')


def testMultipleCuts():
    # tagli con piani verticali
    slicev1 = trimesh.intersections.slice_mesh_plane(cubo, plane_normal=[1,0, 0], plane_origin=[2,0,0], cap=True, cached_dots=None)
    slicev2 = trimesh.intersections.slice_mesh_plane(cubo, plane_normal=[-1,0, 0], plane_origin=[10,0,0], cap=True, cached_dots=None)

    # piano orizzontale
    sliceo = trimesh.intersections.slice_mesh_plane(cubo, plane_normal=[0 ,0, 1], plane_origin=[10,0,10], cap=True, cached_dots=None)

    # taglio 1
    union1 = trimesh.boolean.union([sliceo, slicev1], 'scad')

    # taglio 2
    union2 = trimesh.boolean.union([sliceo, slicev2], 'scad')

    differenza2= cubo.difference(union2, 'scad')
    differenza1= cubo.difference(union1, 'scad')

    unioneTagli = differenza1.union(differenza2, engine='scad', debug=True)
    unioneTagli.show()

    collisionChecker = collision.CollisionManager()
    
    collisionChecker.add_object('shapes', unioneTagli, transform=None)

    print('Collisione fra i due volumi tagliati è: ' + str(collisionChecker.in_collision_internal()))
    



# if(cubo.is_watertight == True):
#     print('Cubo is watertight')
# else:
#     print('Cubo is not watertight')
#     trimesh.repair.fill_holes(cubo)


cuboTagliato = cubo

for i in range(30):

    # genero 2 fette, ognuna caratterizzata da un punto random nella bounding box della mesh e da un versore random
    slice1 = trimesh.intersections.slice_mesh_plane(cubo, plane_normal=triRandomVector(), plane_origin=triRandomOrigin(cubo), cap=True, cached_dots=None)
    slice2 = trimesh.intersections.slice_mesh_plane(cubo, plane_normal=triRandomVector(), plane_origin=triRandomOrigin(cubo), cap=True, cached_dots=None)

    # unisco le fette formando un unico taglio
    union = trimesh.boolean.union([slice1, slice2], 'scad')

    # tolgo il taglio dal volume da scolpire
    cuboTagliato = cubo.difference(union, 'scad')

    # aggiorno il volume da scolpire e la mesh totale del volume tolto
    # se unioneTagli non è già presente, la inizializzo (casomai potrei inizializzarla solo al primo ciclo for)
    cubo = cuboTagliato
    if 'unioneTagli' not in globals():
        unioneTagli = union
    else:
        unioneTagli = unioneTagli.union(union, engine='scad', debug=True)
    print('Ciclo numero ' + str(i) + ' eseguito con successo')


    # controllare che il volume da scolpire sia watertight; se non lo è, aggiustarlo
    
    if(cubo.is_watertight == True):
        print('Cubo is watertight')
    else:
        print('Cubo is not watertight')
        trimesh.repair.fill_holes(cubo)







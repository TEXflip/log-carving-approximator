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


# La seguente funzione è una dimostrazione di come vorrei che funzionasse il programma.
# Purtroppo, quando applico le stesse operazioni più volte, ricevo degli errori

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

    differenza2 = cubo.difference(union2, 'scad')
    differenza1 = cubo.difference(union1, 'scad')

    unioneTagli = differenza1.union(differenza2, engine='scad', debug=True)
    unioneTagli.show()

    collisionChecker = collision.CollisionManager()
    
    collisionChecker.add_object('shapes', unioneTagli, transform=None)

    print('Collisione fra i due volumi tagliati è: ' + str(collisionChecker.in_collision_internal()))
    
    

# Questi sono gli errori dello script: i primi 2 sono i più comuni, l'ultimo ormai non viene mai

    # --- ValueError: Input mesh must be watertight to cap slice
    # --- subprocess.CalledProcessError: Command '['/usr/bin/openscad', '/tmp/tmptj9id9ht', '-o', '/tmp/tmpdpsj2m3h.off']' returned non-zero exit status 1.
    # --- AttributeError: 'NoneType' object has no attribute 'to_planar' 





def cutObject():

    

    if not ('cuboTagliato' in globals()):
        global cuboTagliato
        cuboTagliato = [cubo]
        print('cuboTagliato initialized')
        print('Volume of cuboTagliato is: ' + str(cuboTagliato[0].volume))


    # tagli con piani randomici
    slice1 = trimesh.intersections.slice_mesh_plane(cuboTagliato[-1], plane_normal=triRandomVector(), plane_origin=cuboTagliato[-1].centroid, cap=True, cached_dots=None)
    slice2 = trimesh.intersections.slice_mesh_plane(cuboTagliato[-1], plane_normal=triRandomVector(), plane_origin=cuboTagliato[-1].centroid, cap=True, cached_dots=None)



    # taglio 1 = volume tolto
    unione = trimesh.boolean.union([slice2, slice1], engine='scad')
    # unione.show()

    # aggiorno volume rimasto
    # in questo punto viene generata la nuova mesh non watertight

    cuboTagliato.append(trimesh.boolean.difference([cuboTagliato[-1], unione], engine='scad'))
        


    # teoricamente, i metodi di repair dovrebbero rendere una mesh watertight. Però non funzionano in questo caso
    j = 1
    if not cuboTagliato[-1].is_watertight:
        # while not cuboTagliato[-1].is_watertight:
        trimesh.repair.fill_holes(cuboTagliato[-1])
        trimesh.repair.fix_inversion(cuboTagliato[-1])
        trimesh.repair.fix_normals(cuboTagliato[-1])
        trimesh.repair.fix_winding(cuboTagliato[-1])
        cuboTagliato[-1].show()




    # inizializzo o aggiorno l'insieme dei tagli
    if not ('unioneTagli' in globals()):
        global unioneTagli
        unioneTagli = unione
    else:
        unioneTagli = unioneTagli.union(unione, engine = 'scad', debug = True)
    




# è solamente una run del programma

for i in range(30):
    cutObject()








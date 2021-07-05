from inspyred.benchmarks import ec
import bpy
import bmesh
import numpy as np
import random
import math
import mathutils
from mathutils.bvhtree import BVHTree


# script created by modifying "problem.py" with the text from "cut.py"

scaleFactor = 10
penaltyFactor = 10 # pensalty should depend on volume ratio between targetMesh and carvingMesh



class taglio:
    def __init__(self, _distanceFromOrigin, _desiredAngle, _rotY, _rotZ, _rotEmptyX, _rotEmptyZ):
        self.distanceFromOrigin = -abs(_distanceFromOrigin) # this way, it mantains the point towards the origin
        self.desiredAngle = _desiredAngle
        self.rotZ = _rotZ
        self.rotY = _rotY
        self.rotEmptyZ = _rotEmptyZ
        self.rotEmptyX = _rotEmptyX
    
    def setValues(self, _distanceFromOrigin, _desiredAngle, _rotY, _rotZ, _rotEmptyX, _rotEmptyZ):
        self.distanceFromOrigin = -abs(_distanceFromOrigin) # this way, it mantains the point towards the origin
        self.desiredAngle = _desiredAngle
        self.rotZ = _rotZ
        self.rotY = _rotY
        self.rotEmptyZ = _rotEmptyZ
        self.rotEmptyX = _rotEmptyX
    
    def stampa(self):
        print('Stampa del taglio:')
        print('distanceFromOrigin: ', self.distanceFromOrigin)
        print('rotY: ', self.rotY)
        print('rotZ: ', self.rotZ)
        print('rotEmptyX: ', self.rotEmptyX)
        print('rotEmptyZ: ', self.rotEmptyZ)
    
    def compute(self, _cylinder, _empty):
        # desiredAngle = ampiezza desiderata per la fetta, deve essere fra 0 e 180 gradi
        angle = 180 - self.desiredAngle
        radians = angle * math.pi / 180

        # use this cube to make the cylinder into a wedge
        bpy.ops.mesh.primitive_cube_add(location = (1, 0,0))
        baseCube = bpy.context.active_object
        
        bpy.context.view_layer.objects.active = _cylinder

        # cut the cylinder in half like a cheese slice
        bpy.ops.object.modifier_add(type='BOOLEAN')
        bpy.context.object.modifiers["Boolean"].object = baseCube
        bpy.ops.object.modifier_apply(modifier="Boolean")

        # assign the parenting
        bpy.ops.object.empty_add(location = (0,0,0))
        cubeEmpty = bpy.context.active_object
        baseCube.parent = cubeEmpty
        
        # rotate the empty (and the cube too)
        cubeEmpty.rotation_euler = (0,0,radians)

        # apply the modifier and create the wedge
        bpy.context.view_layer.objects.active = _cylinder
        bpy.ops.object.modifier_add(type='BOOLEAN')
        bpy.context.object.modifiers["Boolean"].object = baseCube
        bpy.ops.object.modifier_apply(modifier="Boolean")

        # rotate the wedge of half its angle to point it to the origin
        halfAngle = (180 - angle) / 2
        radians = halfAngle * math.pi / 180
        _cylinder.rotation_euler = (0,0,radians)
        
        # remove the cube and its empty
        bpy.data.objects.remove(cubeEmpty, do_unlink=True)
        bpy.data.objects.remove(baseCube, do_unlink=True)
        
        """
        #limitazioni per fare in modo che sia sempre la punta del cuneo ad incidere il materiale
        angleLimit = 60
        if self.rotZ > angleLimit:
            self.rotZ = angleLimit
        elif self.rotZ < -angleLimit:
            self.rotZ = -angleLimit
        """
        
        # rotate the wedge
        bpy.context.view_layer.objects.active = _cylinder
        bpy.context.active_object.rotation_euler[1] = math.radians(self.rotY)        
        bpy.context.active_object.rotation_euler[2] = math.radians(self.rotZ)
        
        # translate the wedge
        shift = [0, self.distanceFromOrigin, 0]
        _cylinder.location += mathutils.Vector(shift)
        
        # check and adjust parenting
        if _cylinder.parent != _empty:
            _cylinder.parent = _empty
        
        # rotate the empty, which is the wedge parent
        bpy.context.view_layer.objects.active = _empty
        
        bpy.context.active_object.rotation_euler[0] = math.radians(self.rotEmptyX)
        bpy.context.active_object.rotation_euler[2] = math.radians(self.rotEmptyZ)


    # returns the volume of meshToCarve after the intersection with the cylinder
    def computeVolume(self, meshToCarve, _cylinder, _empty):

        taglioTemp = taglio(self.distanceFromOrigin, self.desiredAngle, self.rotY, self.rotZ, 
                self.rotEmptyX, self.rotEmptyZ)

        taglioTemp.compute(_cylinder, _empty)
        taglioTemp.scale(_cylinder, scaleFactor)
        taglioTemp.applyTransform(_cylinder, _empty)

        # create copy of meshToCarve to apply the boolean modifiers
        meshToCarveTemp = meshToCarve.copy()
        bpy.context.view_layer.objects.active = meshToCarveTemp

        # apply the modifiers
        bpy.ops.object.modifier_add(type='BOOLEAN')
        bpy.context.object.modifiers["Boolean"].object = _cylinder
        bpy.ops.object.modifier_apply(modifier="Boolean")

        bpy.context.view_layer.objects.active = meshToCarve
        me = bpy.context.object.data

        # Get a BMesh representation
        bm = bmesh.new()   # create an empty BMesh
        bm.from_mesh(me)   # fill it in from a Mesh

        volume = bm.calc_volume()

        # Finish up, write the bmesh back to the mesh
        bm.to_mesh(me)
        bm.free()

        bpy.data.objects.remove(meshToCarveTemp, do_unlink=True)

        return volume

        
    # scale the wedge
    def scale(self, _cylinder, scaleFactor):
        bpy.context.view_layer.objects.active = _cylinder
        bpy.context.object.scale[0] = scaleFactor
        bpy.context.object.scale[1] = scaleFactor
        bpy.context.object.scale[2] = scaleFactor
    

    # verifies if obj1 intersects obj2
    # obj1 e obj2 must be of object type (in Blender of course)
    def verifyIntersect(self, obj1, obj2):
        return verifyIntersect(obj1, obj2)
        
        
    def applyTransform(self, _cylinder, _empty):
        bpy.context.view_layer.objects.active = _empty
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    
        bpy.context.view_layer.objects.active = _cylinder
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)


# verifies if obj1 intersects obj2
# obj1 e obj2 must be of object type (in Blender of course)
def verifyIntersect(obj1, obj2):
    # create bmesh objects
    bm1 = bmesh.new()
    bm2 = bmesh.new()

    # fill bmesh data from objects
    bpy.context.view_layer.objects.active = obj1
    me = bpy.context.object.data
    bm1.from_mesh(me)
    
    bpy.context.view_layer.objects.active = obj2
    me = bpy.context.object.data
    bm2.from_mesh(me)            
    
    bm1.transform(obj1.matrix_world)
    bm2.transform(obj2.matrix_world) 

    # make BVH tree from BMesh of objects
    obj1_BVHtree = BVHTree.FromBMesh(bm1)
    obj2_BVHtree = BVHTree.FromBMesh(bm2)           

    # get intersecting pairs
    inter = obj1_BVHtree.overlap(obj2_BVHtree)

    # if list is empty, no objects are touching
    if inter != []:
        # print(str(obj1.name) + " and " + str(obj2.name) + " are touching!")
        return True
    else:
        return False


def is_inside(p, obj):    
    result, point, normal, face = obj.closest_point_on_mesh(p)    
    p2 = point-p    
    v = p2.dot(normal)    
    return not(v < 0.0)


class BlenderWedgeProblem:
    def __init__(self, targetMeshPath, carvingMeshPath, random):
        
        # reset the workspace
        objects = bpy.data.objects
        self.context = bpy.context
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=True)
        
        # import cylinder
        bpy.ops.import_mesh.stl(filepath=carvingMeshPath) # '3D models/cylinder.stl'
        self.carvingMesh = objects['Cylinder']
        
        # import sphere
        bpy.ops.import_mesh.stl(filepath=targetMeshPath) # '3D models/sphere.stl'
        self.targetMesh = objects['Sphere']
        
        self.random = random
        self.targetVolume = self.computeVolume(self.targetMesh.data)
        self.initialVolume = self.computeVolume(self.carvingMesh.data)
        self.maximize = True
        self.terminator = ec.terminators.generation_termination
        self.replacer = ec.replacers.generational_replacement    
        self.variator = [ec.variators.uniform_crossover,ec.variators.gaussian_mutation]
        self.selector = ec.selectors.tournament_selection


    # generates and array of elements of type "taglio"
    def generator(self, args):
        
        arrayDiTagli = []

        for i in range(args["pop_size"]):
            # add empty, cylinder, calculate randomly the parameters and create a "taglio"
            distanceFromOrigin = random.uniform(0 , 2)
            desiredAngle = random.uniform(0 , 180)
            rotY = random.uniform( 0 , 360 )
            rotZ = random.uniform( 0 , 360 )
            rotEmptyX = random.uniform( 0 , 360 )
            rotEmptyZ = random.uniform( 0 , 360 )
            taglioToAppend = taglio(distanceFromOrigin, desiredAngle, rotY,rotZ, rotEmptyX,rotEmptyZ)
            arrayDiTagli.append(taglioToAppend)

        return arrayDiTagli
    
    # for every candidate, check the fitness
    # the fitness is the quantity of removed volume
    def evaluator(self, candidates, args):
        
        volumeTargetMesh = self.computeVolume(self.targetMesh)
        volumeCarvingMesh = self.computeVolume(self.carvingMesh)

        fitness = []
        for c in candidates:
            bpy.ops.object.empty_add()
            _empty = bpy.context.active_object
            bpy.ops.mesh.primitive_cylinder_add()
            _cylinder = bpy.context.active_object

            c.compute(_cylinder, _empty)
            c.scale(_cylinder, scaleFactor)
            c.applyTransform(_cylinder, _empty)

            carvingMeshTemp = self.carvingMesh.copy()
            targetMeshTemp = self.targetMesh.copy()

            volume = 0

            if verifyIntersect(targetMeshTemp, _cylinder, self.targetMesh) == True:
                volume -= penaltyFactor * abs(volumeTargetMesh - c.computeVolume(targetMeshTemp, _cylinder, _empty))

            volume += abs (volumeCarvingMesh - c.computeVolume(carvingMeshTemp, _cylinder, _empty))

            fitness.append(volume)

        bpy.data.objects.remove(_cylinder, do_unlink=True)
        bpy.data.objects.remove(_empty, do_unlink=True)

        return fitness


    def computeVolume(self, mesh):
        # Get a BMesh representation
        bm = bmesh.new()   # create an empty BMesh
        bm.from_mesh(mesh)   # fill it in from a Mesh

        volume = bm.calc_volume()

        bm.free()
        return volume # * 1000


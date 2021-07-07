import bpy
import bmesh
import numpy as np
import random
import math
from mathutils import Quaternion, Vector
from mathutils.bvhtree import BVHTree
import trimesh


# script created by modifying "problem.py" with the text from "cut.py"

fastModifierThreshold = 2e-05

class taglio:
    def __init__(self, origin, rotation, angle):
        self.origin = origin
        self.rotation = rotation
        self.angle = angle
        self.toRad = math.pi/180
        self.scale = 10

    def compute(self):
        angleRad = self.angle * self.toRad * 0.5
        vx = math.sin(angleRad)
        vy = math.cos(angleRad)
        v3y = 1 if self.angle > 90 else vy
        
        vertices = [(0,0,-1), (vx,vy,-1), (0,v3y,-1), (-vx,vy,-1),  # lower face vertices
                    (0,0,1), (vx,vy,1), (0,v3y,1), (-vx,vy,1)]     # upper face vertices
        edges = [(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),(0,4),(1,5),(2,6),(3,7)]
        faces = [(3,2,1,0), (7,4,5,6), (3,0,4,7), (2,3,7,6), (1,2,6,5), (0,1,5,4)]
        
        new_mesh = bpy.data.meshes.new('wedge')
        new_mesh.from_pydata(vertices, edges, faces)
        new_mesh.update()
        
        wedge = bpy.data.objects.new('wedge', new_mesh)
        bpy.data.collections["Collection"].objects.link(wedge)
        
        wedge.scale = (self.scale, self.scale, self.scale)
        wedge.rotation_euler = self.rotation
        wedge.location = self.origin

        return wedge

    # returns the volume of meshToCarve after the intersection with the wedge
    def cutAndVolume(self, meshToCarve, wedge):
        # apply the modifiers
        bool = meshToCarve.modifiers.new(type="BOOLEAN", name="bool")
        # bool.double_threshold = 0.000025
        bool.object = wedge
        bool.operation = 'DIFFERENCE'
        
        # Get a BMesh representation
        bm = bmesh.new()   # create an empty BMesh
        bm.from_object(meshToCarve, bpy.context.evaluated_depsgraph_get())

        volume = bm.calc_volume()
        
        bm.free()
        
        meshToCarve.modifiers.remove(bool)
        
        return volume

def is_inside(ray_origin, obj):
    ray_destination = Vector((1e10,0,0))
    mat = obj.matrix_local.inverted()
    result, loc, normal, face_idx = obj.ray_cast(mat @ ray_origin, mat @ ray_destination)

    if face_idx == -1:
        return False
    
    max_expected_intersections = 1000
    fudge_distance = 0.0001
    direction = (ray_destination - loc)
    dir_len = direction.length
    amount = fudge_distance / dir_len
    
    i = 1
    while (face_idx != -1):
        
        loc = loc.lerp(direction, amount)    
        result, loc, normal, face_idx = obj.ray_cast(mat @ ray_origin, mat @ ray_destination)

        if face_idx == -1:
            break
        i += 1
        if i > max_expected_intersections:
            break

    return not ((i % 2) == 0)

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
        return is_inside(obj1.location, obj2)


class BlenderWedgeProblem2:
    def __init__(self, targetMeshPath, carvingMeshPath, random):
        
        self.targetMeshPath = targetMeshPath
        self.carvingMeshPath = carvingMeshPath

        # reset the workspace
        objects = bpy.data.objects
        self.context = bpy.context
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=True)
        
        # import cylinder
        self.carvingMesh = self.importStl(carvingMeshPath)
        
        # import sphere
        self.targetMesh = self.importStl(targetMeshPath)
        
        self.random = random
        self.targetVolume = self.computeVolume(self.targetMesh)
        self.initialVolume = self.computeVolume(self.carvingMesh)
        self.maximize = True

        self.bestCuts = np.empty((0,7), np.float32)

        target_trimesh = trimesh.load(targetMeshPath, force='mesh') # readonly the vertexes
        oldOrig = {}
        self.cuts = []

        for i, normal in enumerate(target_trimesh.face_normals):
            face = target_trimesh.faces[i]
            origin = target_trimesh.vertices[face[0]] * 1.1

            intOrig = (origin*1000).astype(np.int32)
            # origin = origin
            hashValue = hash(intOrig)
            if not (hashValue in oldOrig):
                oldOrig[hashValue] = 0
                normal = (np.array(normal) * -1)
                rotation = self.vecRotation(Vector(normal))
                angle = random.uniform(0, 180)
                candidate = np.concatenate((origin, rotation, [angle]), axis=0)
                # candidate = origin.tolist() + normal.tolist()
                self.cuts.append(candidate)

        self.random.shuffle(self.cuts)

    # custom importing function correctly return the imported object
    def importStl(self, filepath):
        old_objs = set(bpy.data.objects)
        bpy.ops.import_mesh.stl(filepath=filepath)
        imported_objs = set(bpy.data.objects) - old_objs
        return imported_objs.pop()

    # generates and array of elements of type "taglio"
    def generator(self, random, args):
        rndint = random.randint(0, len(self.cuts))
        return self.cuts[rndint]
    
    # for every candidate, check the fitness
    # the fitness is the quantity of removed volume
    def evaluator(self, candidates, args):

        fitness = []
        for i,c in enumerate(candidates):
            t = taglio(c[0:3], c[3:6], c[6])
            wedge = t.compute()

            volume = t.cutAndVolume(self.carvingMesh, wedge)

            candidateFitness = self.initialVolume - volume
            candidateFitness -= self.initialVolume if volume <= 0 else 0

            if verifyIntersect(self.targetMesh, wedge):
                # candidateFitness -= penaltyFactor * abs(volumeTargetMesh - t.computeVolume(self.targetMesh, _cylinder, _empty))
                candidateFitness -= self.initialVolume

            fitness.append(candidateFitness)

            bpy.data.objects.remove(wedge, do_unlink=True)

        return fitness

    def computeVolume(self, obj):
        # Get a BMesh representation
        bm = bmesh.new()   # create an empty BMesh
        bm.from_object(obj, bpy.context.evaluated_depsgraph_get())

        volume = bm.calc_volume()

        bm.free()
        return volume # * 1000

    # save the resulting model
    def SaveCarvingMesh(self, filepath):
        bpy.ops.object.select_all(action='DESELECT')
        self.carvingMesh.select_set(True)
        bpy.ops.export_mesh.stl(filepath=filepath, use_selection=True)

    
    def sliceAndApply(self, c):
        t = taglio(c[0:3], c[3:6], c[6])
        wedge = t.compute()

        bpy.context.view_layer.objects.active = self.carvingMesh
        bool = self.carvingMesh.modifiers.new(type="BOOLEAN", name="bool")
        bool.object = wedge
        bool.operation = 'DIFFERENCE'
        bpy.ops.object.modifier_apply(modifier=bool.name)

    # apply the cut after "slice_application_evaluations" evaluations
    def custom_observer(self, population, num_generations, num_evaluations, args):
        if num_generations > 0 and num_generations % args["slice_application_generation"] == 0:
            final_pop_fitnesses = np.asarray([guy.fitness for guy in population])
            final_pop_candidates = np.asarray([guy.candidate for guy in population])
            
            sort_indexes = sorted(range(len(final_pop_fitnesses)), key=final_pop_fitnesses.__getitem__)
            final_pop_fitnesses = final_pop_fitnesses[sort_indexes]
            final_pop_candidates = final_pop_candidates[sort_indexes]
            self.sliceAndApply(final_pop_candidates[-1])

            self.bestCuts = np.append(self.bestCuts, np.array([final_pop_candidates[-1]]), axis=0)

    def SaveCarvingMesh(self, filepath, mesh):
        bpy.ops.object.select_all(action='DESELECT')
        self.carvingMesh.select_set(True)
        bpy.ops.export_mesh.stl(filepath=filepath, use_selection=True)

    # from normal to euler rotation coordinates
    def vecRotation(self, v2):
        # v1.normalize()
        v1 = Vector((0,-1,0))
        v2.normalize()
        if v1 == -v2:
            v1.orthogonal().normalize()
            return Quaternion((0, v1[0], v1[1], v1[2])).to_euler()
        half = (v1+v2).normalized()
        cross = v1.cross(half)
        return Quaternion((v1.dot(half), cross[0], cross[1], cross[2])).to_euler()
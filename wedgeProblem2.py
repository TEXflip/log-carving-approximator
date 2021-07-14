import bpy
import bmesh
from mathutils import Quaternion, Vector
from mathutils.bvhtree import BVHTree
import numpy as np
import math
from inspyred.ec import Bounder 
import copy
import time


# script created by modifying "problem.py" with the text from "cut.py"

fastModifierThreshold = 1e-10

class taglio:
    def __init__(self, origin, rotation, angle, fastBoolean = True):
        self.origin = origin
        self.rotation = rotation
        self.angle = angle
        self.toRad = math.pi/180
        self.scale = 30
        self.fastBoolean = fastBoolean
        self.mesh = None
        self.wedge = None

    def compute(self):
        angleRad = self.angle * 0.5
        vx = math.sin(angleRad)
        vy = math.cos(angleRad)
        v3y = 1 if self.angle > (math.pi/2) else vy
        
        vertices = [(0,0,-0.5), (vx,vy,-0.5), (0,v3y,-0.5), (-vx,vy,-0.5),  # lower face vertices
                    (0,0,0.5), (vx,vy,0.5), (0,v3y,0.5), (-vx,vy,0.5)]     # upper face vertices
        edges = [(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),(0,4),(1,5),(2,6),(3,7)]
        faces = [(3,2,1,0), (7,4,5,6), (3,0,4,7), (2,3,7,6), (1,2,6,5), (0,1,5,4)]

        self.mesh = bpy.data.meshes.new('wedge')


        self.mesh.from_pydata(vertices, edges, faces)
        
        self.wedge = bpy.data.objects.new('wedge', self.mesh)

        self.wedge.scale = (self.scale, self.scale, self.scale)
        self.wedge.rotation_euler = self.vecRotation(Vector(self.rotation))
        self.wedge.location = self.origin

        return self.wedge

    # returns the volume of meshToCarve after the intersection with the wedge
    def cutAndVolume(self, meshToCarve, wedge):
        # apply the modifiers
        bool = meshToCarve.modifiers.new(type="BOOLEAN", name="bool")
        if self.fastBoolean:
            bool.solver = 'FAST'
            bool.double_threshold = fastModifierThreshold
        bool.object = wedge
        bool.operation = 'DIFFERENCE'
        
        # Get a BMesh representation
        bm = bmesh.new()   # create an empty BMesh
        bm.from_object(meshToCarve, bpy.context.evaluated_depsgraph_get())

        volume = bm.calc_volume()

        bm.free()
        meshToCarve.modifiers.remove(bool)
        
        return volume

    # from normal to euler rotation coordinates
    def vecRotation(self, v2):
        # v1.normalize()
        v1 = Vector((0,-1,0))
        v2.normalize()
        if v1 == -v2:
            v1 = Vector((0,0,1))
            return Quaternion((0, v1[0], v1[1], v1[2])).to_euler()
        half = (v1+v2).normalized()
        cross = v1.cross(half)
        return Quaternion((v1.dot(half), cross[0], cross[1], cross[2])).to_euler()

def is_inside(ray_origin, obj2_BVHtree):
    ray_destination = Vector((1e10,0,0))
    loc, normal, face_idx, dist = obj2_BVHtree.ray_cast(ray_origin, ray_destination)

    if face_idx == None:
        return False
    
    max_expected_intersections = 1000
    fudge_distance = 0.0001
    direction = (ray_destination - loc)
    dir_len = direction.length
    amount = fudge_distance / dir_len
    
    i = 1
    while (face_idx != None):
        
        loc = loc.lerp(direction, amount)    
        loc, normal, face_idx, dist = obj2_BVHtree.ray_cast(ray_origin, ray_destination)

        if face_idx == None:
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
    bm1.from_mesh(obj1.data)
    bm2.from_mesh(obj2.data)            
    
    bm1.transform(obj1.matrix_world)
    bm2.transform(obj2.matrix_world) 

    # make BVH tree from BMesh of objects
    obj1_BVHtree = BVHTree.FromBMesh(bm1)
    obj2_BVHtree = BVHTree.FromBMesh(bm2)           

    # get intersecting pairs
    inter = obj1_BVHtree.overlap(obj2_BVHtree)
    bm1.free()
    bm2.free()

    # if list is empty, no objects are touching
    if inter != []:
        # print(str(obj1.name) + " and " + str(obj2.name) + " are touching!")
        return True
    else:
        return is_inside(obj1.location, obj2_BVHtree)


class BlenderWedgeProblem2:
    def __init__(self, targetMeshPath, carvingMeshPath, random, fastBoolean = True):
        
        self.targetMeshPath = targetMeshPath
        self.carvingMeshPath = carvingMeshPath
        self.fastBoolean = fastBoolean
        self.bounder = Bounder([-2,-2,-2,-90,-90,-90, 0.0872665], [2,2,2,90,90,90, math.pi])

        # reset the workspace
        objects = bpy.data.objects
        self.context = bpy.context
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=True)
        bpy.ops.outliner.orphans_purge()
        
        # import cylinder
        self.carvingMesh = self.importStl(carvingMeshPath)
        
        # import sphere
        self.targetMesh = self.importStl(targetMeshPath)
        
        self.random = random
        self.targetVolume = self.computeVolume(self.targetMesh)
        self.initialVolume = self.computeVolume(self.carvingMesh)
        self.maximize = True
        self.num_vars = 7

        self.bestCuts = np.empty((0,7), np.float32)
        self.bestFit = []

        # prepare a list of initial cuts for the generator
        self.cuts = []
        for v in self.targetMesh.data.vertices:
            origin = (self.targetMesh.matrix_world @ v.co) * 1.05
            normal = -origin/np.linalg.norm(origin)
            # rotation = self.vecRotation(normal)
            candidate = np.concatenate((origin, normal, [math.pi]), axis=0)
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
        rndint = random.randint(0, len(self.cuts)-1)
        return self.cuts[rndint]

    # for every candidate, check the fitness
    # the fitness is the quantity of removed volume
    def evaluator(self, candidates, args):
        times = []
        
        fitness = []
        for i,c in enumerate(candidates):
            t = taglio(c[0:3], c[3:6], c[6], self.fastBoolean)

            wedge = t.compute()

            volume = t.cutAndVolume(self.carvingMesh, wedge)

            candidateFitness = self.initialVolume - volume
            if self.fastBoolean:
                candidateFitness -= self.initialVolume if volume <= 0 else 0

            if verifyIntersect(self.targetMesh, wedge):
                # candidateFitness -= penaltyFactor * abs(volumeTargetMesh - t.computeVolume(self.targetMesh, _cylinder, _empty))
                candidateFitness -= self.initialVolume
            fitness.append(candidateFitness)

            bpy.data.meshes.remove(t.mesh)
        
        return fitness

    def computeVolume(self, obj):
        # Get a BMesh representation
        bm = bmesh.new()   # create an empty BMesh
        bm.from_object(obj, bpy.context.evaluated_depsgraph_get())

        volume = bm.calc_volume()

        bm.free()
        return volume

    def is_feasible(self, fitness):
        return fitness > 0 and fitness < self.initialVolume

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
        # if self.fastBoolean:
        #     bool.solver = 'FAST'
        #     bool.double_threshold = fastModifierThreshold
        bool.object = wedge
        bool.operation = 'DIFFERENCE'
        bpy.ops.object.modifier_apply(modifier=bool.name)

    def custom_gaussian_mutation(self, random, candidates, args):
        def mutate(random, candidate, args):
            mut_rate = args.setdefault('custom_mutation_rate', [0.8,0.8,0.8,0.5,0.5,0.5, 0.1])
            mean = args.setdefault('gaussian_mean', 0.0)
            stdev = args.setdefault('custom_gaussian_stdev', [0.25,0.25,0.25,10,10,10,10])
            mutant = copy.copy(candidate)
            for i, m in enumerate(mutant):
                if random.random() < mut_rate[i]:
                    mutant[i] += random.gauss(mean, stdev[i])
            mutant = self.bounder(mutant, args)
            return mutant
        mutants = []
        for i, cs in enumerate(candidates):
            mutants.append(mutate(random, cs, args))
        return mutants

    # apply the cut after "slice_application_evaluations" evaluations
    def custom_observer(self, population, num_generations, num_evaluations, args):
        if num_generations > 0 and num_generations % args["slice_application_generation"] == 0:
            final_pop_fitnesses = np.asarray([guy.fitness for guy in population])
            final_pop_candidates = np.asarray([guy.candidate for guy in population])
            
            sort_indexes = sorted(range(len(final_pop_fitnesses)), key=final_pop_fitnesses.__getitem__)
            final_pop_fitnesses = final_pop_fitnesses[sort_indexes]
            final_pop_candidates = final_pop_candidates[sort_indexes]

            bestCand = final_pop_candidates[-1]
            bestFit = final_pop_fitnesses[-1]

            if self.is_feasible(bestFit):
                self.sliceAndApply(bestCand)
                self.bestCuts = np.append(self.bestCuts, np.array([bestCand]), axis=0)
                self.bestFit.append(bestFit)

    def SaveCarvingMesh(self, filepath, mesh):
        bpy.ops.object.select_all(action='DESELECT')
        self.carvingMesh.select_set(True)
        bpy.ops.export_mesh.stl(filepath=filepath, use_selection=True)
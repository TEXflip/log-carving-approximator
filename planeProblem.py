import bpy
import bmesh
from mathutils import Vector, Quaternion
import numpy as np
from inspyred.ec import Bounder

class BlenderPlaneProblem:
    def __init__(self, targetMeshPath, carvingMeshPath, fastMode = True):
        # reset the workspace
        self.targetMeshPath = targetMeshPath
        self.carvingMeshPath = carvingMeshPath
        self.fastBooleanTH = 1e-10
        self.fastBoolean = fastMode
        self.scale = 20

        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=True)
        bpy.ops.outliner.orphans_purge()

        # import cylinder
        self.carvingMesh = self.importStl(carvingMeshPath)

        # import sphere
        self.targetMesh = self.importStl(targetMeshPath)
        
    # custom importing function correctly return the imported object
    def importStl(self, filepath):
        old_objs = set(bpy.data.objects)
        bpy.ops.import_mesh.stl(filepath=filepath)
        imported_objs = set(bpy.data.objects) - old_objs
        return imported_objs.pop()

    def computeVolume(self, obj):
        # Get a BMesh representation
        bm = bmesh.new()   # create an empty BMesh
        bm.from_object(obj, bpy.context.evaluated_depsgraph_get())

        volume = bm.calc_volume()

        bm.free()
        return volume # * 1000

    # from normal to euler rotation coordinates
    def vecRotation(self, v2):
        # v1.normalize()
        v1 = Vector((0,0,-1))
        v2.normalize()
        if v1 == -v2:
            v1 = Vector((0,1,0))
            return Quaternion((0, v1[0], v1[1], v1[2])).to_euler()
        half = (v1+v2).normalized()
        cross = v1.cross(half)
        return Quaternion((v1.dot(half), cross[0], cross[1], cross[2])).to_euler()

    # generate the boolean modifier that slices the model 
    # according to an orgin and a normal
    def slice(self, mesh, origin, normal):
        vertices = [(-1,-1,0), (1,-1,0), (1,1,0), (-1,1,0),  # lower face vertices
                    (-1,-1,1), (1,-1,1), (1,1,1), (-1,1,1)]     # upper face vertices
        edges = [(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),(0,4),(1,5),(2,6),(3,7)]
        faces = [(3,2,1,0), (7,4,5,6), (3,0,4,7), (2,3,7,6), (1,2,6,5), (0,1,5,4)]
        
        new_mesh = bpy.data.meshes.new('cube')
        new_mesh.from_pydata(vertices, edges, faces)
        new_mesh.update()
        
        cube = bpy.data.objects.new('cube', new_mesh)
        bpy.data.collections["Collection"].objects.link(cube)
        
        cube.scale = (self.scale, self.scale, self.scale)
        cube.rotation_euler = self.vecRotation(Vector(normal))
        cube.location = origin

        # create boolean modifier on the carving mesh and apply cube boolean intersection
        bool = mesh.modifiers.new(type="BOOLEAN", name="bool")
        if self.fastBoolean:
            bool.solver = 'FAST'
            bool.double_threshold = self.fastBooleanTH
        bool.object = cube
        bool.operation = 'DIFFERENCE'

        return bool
    
    # compute the minimum relative distance respect to the normal of the plane
    # and all the points of the mesh
    def intersect(self, obj, origin, normal):
        vxs = obj.data.vertices
        min = float('inf')
        for v in vxs:
            p1 = origin - obj.matrix_world @ v.co
            d = -p1.dot(normal)
            if min > d:
                min = d
        return min

    # Make a slice and compute the volume
    def sliceAndVolume(self, slice):
        # apply slice
        bool = self.slice(self.carvingMesh, slice[:3], slice[3:])

        #compute volume
        volume = self.computeVolume(self.carvingMesh)

        # remove the copies
        self.carvingMesh.modifiers.remove(bool)
        bpy.data.objects.remove(bpy.data.objects["cube"], do_unlink=True)

        return volume

    def sliceAndApply(self, slice):
        # apply slice
        bool = self.slice(self.carvingMesh, slice[:3], slice[3:])

        # apply boolean modifier
        bpy.context.view_layer.objects.active = self.carvingMesh
        bpy.ops.object.modifier_apply(modifier=bool.name)

        #compute volume
        volume = self.computeVolume(self.carvingMesh)

        # remove the empty
        bpy.data.objects.remove(bpy.data.objects["cube"], do_unlink=True)

        return volume
    
    # save the resulting model
    def SaveCarvingMesh(self, filepath):
        bpy.ops.object.select_all(action='DESELECT')
        self.carvingMesh.select_set(True)
        bpy.ops.export_mesh.stl(filepath=filepath, use_selection=True)

class PlaneCutProblem(BlenderPlaneProblem):
    def __init__(self, targetMeshPath, carvingMeshPath, random, fastMode = True):
        super(PlaneCutProblem, self).__init__(targetMeshPath, carvingMeshPath, fastMode=fastMode)
        self.random = random
        self.targetVolume = self.computeVolume(self.targetMesh)
        self.initialVolume = self.computeVolume(self.carvingMesh)
        print("carving Mesh initial Volume: ", self.initialVolume)
        self.maximize = True
        self.bounder = Bounder([-2,-2,-2,-1,-1,-1], [2,2,2,1,1,1])
        self.bestCuts = np.empty((0,6), np.float32)
        self.bestFit = []

        # prepare a list of initial cuts for the generator
        self.cuts = []
        for v in self.targetMesh.data.vertices:
            origin = self.targetMesh.matrix_world @ v.co
            normal = -origin/np.linalg.norm(origin)
            candidate = np.concatenate((origin, normal), axis=0)
            self.cuts.append(candidate)

        self.random.shuffle(self.cuts)
    
    def generator(self, random, args):
        # piani di taglio
        rndint = random.randint(0, len(self.cuts))
        return self.cuts[rndint]
        
    def evaluator(self, candidates, args):
        fitness = []
        for c in candidates:
            volume = self.sliceAndVolume(c)
            candidateFitness = (self.initialVolume - volume) - self.penalty(c)
            if self.fastBoolean: # way to prevent vanishing boolean application
                candidateFitness -= self.initialVolume if volume == 0 else 0
            fitness.append(candidateFitness)
        # print(fitness)

        return fitness

    def penalty(self, c):
        relDist = self.intersect(self.targetMesh, Vector(c[:3]), Vector(c[3:]))
        if relDist > 0:
            return 0
        else:
            return self.initialVolume

    def is_feasible(self, fitness):
        return fitness > 0 and fitness < self.initialVolume

    # apply the cut after "slice_application_evaluations" evaluations (witout regeneration only)
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
                print("\r --- Cut n. " + "{:.0}".format(num_generations / args["slice_application_generation"]), end='')

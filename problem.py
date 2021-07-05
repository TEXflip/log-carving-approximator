import bpy
import bmesh
from mathutils import Vector, Quaternion
import trimesh
import numpy as np

class BlenderProblem:
    def __init__(self, targetMeshPath, carvingMeshPath):
        # reset the workspace
        objects = bpy.data.objects
        self.context = bpy.context
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=True)

        # create base cube for the boolean operation
        bpy.ops.mesh.primitive_cube_add(location=(0, 0, 250), size=500, rotation=(0.0, 0.0, 0.0), enter_editmode=False)
        self.cube = objects["Cube"]

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

    def updateCarvingMesh(self, carvingMeshPath):
        bpy.ops.object.select_all(action='DESELECT')
        self.carvingMesh.select_set(True)
        bpy.ops.object.delete()
        # import new carvingMesh
        self.carvingMesh = self.importStl(carvingMeshPath)

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
        v1 = Vector((0,0,1))
        v2.normalize()
        if v1 == -v2:
            v1.orthogonal().normalize()
            return Quaternion((0, v1[0], v1[1], v1[2])).to_euler()
        half = (v1+v2).normalized()
        cross = v1.cross(half)
        return Quaternion((v1.dot(half), cross[0], cross[1], cross[2])).to_euler()

    # generate the boolean modifier that slices the model 
    # according to an orgin and a normal
    def slice(self, mesh, origin, normal):

        # copy the cube
        newcube = self.cube.copy()
        empty = bpy.data.objects.new("empty", None)

        # create empty to rotate the cube
        bpy.data.collections["Collection"].objects.link(empty)
        bpy.data.collections["Collection"].objects.link(newcube)
        newcube.parent = empty
        empty.location = origin
        empty.rotation_euler = self.vecRotation(Vector(normal))

        # create boolean modifier on the carving mesh and apply cube boolean intersection
        bool = mesh.modifiers.new(type="BOOLEAN", name="bool")
        bool.double_threshold = 0.000025
        bool.object = newcube
        bool.operation = 'INTERSECT'

        return bool, newcube
    
    # compute the minimum relative distance respect to the normal of the plane
    # and all the points of the mesh
    def minDistFromPlane(self, obj, origin, normal):
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
        bool, newcube = self.slice(self.carvingMesh, slice[:3], slice[3:])

        #compute volume
        volume = self.computeVolume(self.carvingMesh)

        # remove the copies
        self.carvingMesh.modifiers.remove(bool)
        bpy.ops.object.select_all(action='DESELECT')
        newcube.select_set(True)
        bpy.data.objects["empty"].select_set(True)
        bpy.ops.object.delete()

        return volume

    def sliceAndApply(self, slice):
        # apply slice
        bool, newcube = self.slice(self.carvingMesh, slice[:3], slice[3:])

        # apply boolean modifier
        bpy.context.view_layer.objects.active = self.carvingMesh
        bpy.ops.object.modifier_apply(modifier=bool.name)

        #compute volume
        volume = self.computeVolume(self.carvingMesh)

        # remove the empty
        bpy.ops.object.select_all(action='DESELECT')
        newcube.select_set(True)
        bpy.data.objects["empty"].select_set(True)
        bpy.ops.object.delete()

        return volume
    
    # save the resulting model
    def SaveCarvingMesh(self, filepath):
        bpy.ops.object.select_all(action='DESELECT')
        self.carvingMesh.select_set(True)
        bpy.ops.export_mesh.stl(filepath=filepath, use_selection=True)

class PlaneCut(BlenderProblem):
    def __init__(self, targetMeshPath, carvingMeshPath, random):
        super(PlaneCut, self).__init__(targetMeshPath, carvingMeshPath)
        self.random = random
        self.targetVolume = self.computeVolume(self.targetMesh)
        self.initialVolume = self.computeVolume(self.carvingMesh)
        print("carving Mesh initial Volume: ",self.initialVolume)
        self.maximize = True
        self.bestCusts = []


        sphere_trimesh = trimesh.load(targetMeshPath, force='mesh') # only in lecture to read the vertexes
        oldOrig = {}
        self.cuts = []

        for i, normal in enumerate(sphere_trimesh.face_normals):
            face = sphere_trimesh.faces[i]
            origin = sphere_trimesh.vertices[face[0]]

            intOrig = (origin*1000).astype(np.int32)
            # origin = origin
            hashValue = hash(intOrig)
            if not (hashValue in oldOrig):
                oldOrig[hashValue] = 0
                normal = (np.array(normal) * -1)
                candidate = np.concatenate((origin, normal), axis=0)
                self.cuts.append(candidate)

        self.random.shuffle(self.cuts)
    
    def generator(self, random, args):
        # piani di taglio
        rndint = self.random.randint(0, len(self.cuts))
        return self.cuts[rndint]
        
    def evaluator(self, candidates, args):

        fitness = []
        for c in candidates:
            volume = self.sliceAndVolume(c)
            candidateFitness = (self.initialVolume - volume) - self.constraint(c)
            fitness.append(candidateFitness)

        return fitness

    def constraint(self, c):
        relDist = self.minDistFromPlane(self.targetMesh, c[:3], c[3:])
        if relDist > 0:
            return 0
        else:
            # return -relDist * 100 + 10
            return self.initialVolume

    # apply the cut after "slice_application_evaluations" evaluations
    def customObserver(self, population, num_generations, num_evaluations, args):
        if num_evaluations % args["slice_application_evaluations"] == 0:
            final_pop_fitnesses = np.asarray([guy.fitness for guy in population])
            final_pop_candidates = np.asarray([guy.candidate for guy in population])
            
            sort_indexes = sorted(range(len(final_pop_fitnesses)), key=final_pop_fitnesses.__getitem__)
            final_pop_fitnesses = final_pop_fitnesses[sort_indexes]
            final_pop_candidates = final_pop_candidates[sort_indexes]
            self.sliceAndApply(final_pop_candidates[-1])

            print("\ngeneration: ", num_generations)
            print("cut applyed: ", final_pop_candidates[-1],"\n")
            self.bestCusts.append(final_pop_candidates[-1])

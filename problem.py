from inspyred.benchmarks import ec
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
        self.cube = objects['Cube']

        # import cylinder
        bpy.ops.import_mesh.stl(filepath=carvingMeshPath) # '3D models/cylinder.stl'
        self.carvingMesh = objects['Cylinder']

        # import sphere
        bpy.ops.import_mesh.stl(filepath=targetMeshPath) # '3D models/sphere.stl'
        self.targetMesh = objects['Sphere']


    def computeVolume(self, mesh):
        me = bpy.context.object.data

        # Get a BMesh representation
        bm = bmesh.new()   # create an empty BMesh
        bm.from_mesh(me)   # fill it in from a Mesh

        volume = bm.calc_volume()

        # Finish up, write the bmesh back to the mesh
        bm.to_mesh(me)
        bm.free()
        return volume

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
        newcube.parent = empty
        empty.location = origin
        empty.rotation_euler = self.vecRotation(Vector(normal))

        # create boolean modifier on the carving mesh and apply cube boolean intersection
        bool = mesh.modifiers.new(type="BOOLEAN", name="bool")
        bool.double_threshold = 0.000025
        bool.object = newcube
        bool.operation = 'INTERSECT'

        return bool
    
    # Make a slice and comupte the volume
    def sliceAndVolume(self, slice):

        # copy the carving mesh
        tempMesh = self.carvingMesh.copy()
        tempMesh.data = self.carvingMesh.data.copy()
        bpy.data.collections["Collection"].objects.link(tempMesh)

        # apply slice
        bool = self.slice(tempMesh, slice[:3], slice[3:])

        # apply boolean modifier
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode = 'OBJECT')
        bpy.context.view_layer.objects.active = tempMesh
        bpy.ops.object.modifier_apply(modifier=bool.name)

        #compute volume
        volume = self.computeVolume(self.carvingMesh.data)

        # remove the copy
        bpy.ops.object.select_all(action='DESELECT')
        tempMesh.select_set(True)
        bpy.ops.object.delete()

        return volume
    
    # make a slice and save the resulting model
    def sliceAndSave(self, slice, filepath):
        tempMesh = self.carvingMesh.copy()
        tempMesh.data = self.carvingMesh.data.copy()
        bpy.data.collections["Collection"].objects.link(tempMesh)
        bool = self.slice(tempMesh, slice[:3], slice[3:])
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode = 'OBJECT')
        bpy.context.view_layer.objects.active = tempMesh
        bpy.ops.object.modifier_apply(modifier=bool.name)
        bpy.ops.object.select_all(action='DESELECT')
        tempMesh.select_set(True)
        bpy.ops.export_mesh.stl(filepath=filepath, use_selection=True)
        bpy.ops.object.delete()

class PlaneCut(BlenderProblem):
    def __init__(self, targetMeshPath, carvingMeshPath, random):
        super(PlaneCut, self).__init__(targetMeshPath, carvingMeshPath)
        self.random = random
        self.targetVolume = self.computeVolume(self.targetMesh.data)
        self.initialVolume = self.computeVolume(self.carvingMesh.data)
        self.maximize = True
        self.terminator = ec.terminators.generation_termination
        self.replacer = ec.replacers.generational_replacement    
        self.variator = [ec.variators.uniform_crossover,ec.variators.gaussian_mutation]
        self.selector = ec.selectors.tournament_selection

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
            fitness.append(self.initialVolume - volume)

        return fitness
from inspyred.benchmarks import Benchmark
import bpy
import bmesh
from mathutils import Vector, Quaternion

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
        bm = bmesh.new()
        bm.from_mesh(mesh)
        volume = bm.calc_volume()
        return volume * (self.context.scene.unit_settings.scale_length ** 3.0) * 1e6

    def vecRotation(v1, v2):
        # v1.normalize()
        v2.normalize()
        if v1 == -v2:
            v1.orthogonal().normalize()
            return Quaternion((0, v1[0], v1[1], v1[2])).to_euler()
        half = (v1+v2).normalized()
        cross = v1.cross(half)
        return Quaternion((v1.dot(half), cross[0], cross[1], cross[2])).to_euler()

    def slice(self, mesh, origin, normal):
        newcube = self.cube.copy()
        empty = bpy.data.objects.new("empty", None)
        bpy.data.collections["Collection"].objects.link(empty)
        newcube.parent = empty
        empty.location = origin
        empty.rotation_euler = self.vecRotation(Vector((0,0,1)), Vector(normal))
        bool = mesh.modifiers.new(type="BOOLEAN", name="bool")
        bool.double_threshold = 0.000025
        bool.object = newcube
        bool.operation = 'INTERSECT'
        return bool

class PlaneCut(BlenderProblem):
    def __init__(self, targetMeshPath, carvingMeshPath):
        super(targetMeshPath, carvingMeshPath)
        self.targetVolume = self.computeVolume(self.targetMesh.data)
        self.maximize = False
    
    def generator(self, random, args):
        # piani di taglio 
        return {'origin': [0,0,0], 'normal': [0,0,1]}
        
    def evaluator(self, candidates, args):
        fitness = []
        for c in candidates:
            self.slice(self.carvingMesh, c.origin, c.normal) # gestire molteplici tagli contemporaneamente
            bpy.context.view_layer.objects.active = self.carvingMesh
            bpy.ops.object.modifier_apply(modifier=bool.name)
            currVol = self.computeVolume(self.carvingMesh.data)

        return 0 # volume
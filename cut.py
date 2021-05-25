import bpy
import random
import mathutils
import bmesh
import math


def generateCut(listaDiCilindri, desiredAngle):
    # desiredAngle = ampiezza desiderata per la fetta, deve essere fra 0 e 180 gradi
    angle = 180 - desiredAngle
    radians = angle * math.pi / 180

    bpy.ops.mesh.primitive_cube_add(location = (1, 0,0))
    baseCube = bpy.context.active_object

    bpy.ops.mesh.primitive_cylinder_add()
    baseCylinder = bpy.context.active_object

    # taglio il cilindro a metà, come se fosse una forma di formaggio molto alta
    bpy.ops.object.modifier_add(type='BOOLEAN')
    bpy.context.object.modifiers["Boolean"].object = baseCube
    bpy.ops.object.modifier_apply(modifier="Boolean")

    # in base all'angolo, scelgo la dimensione della "fetta di formaggio" finale
    # ma prima assegno il parenting con l'empty
    bpy.ops.object.empty_add(location = (0,0,0))
    cubeEmpty = bpy.context.active_object
    baseCube.parent = cubeEmpty

    #ruoto l'empty, e quindi anche il cubo
    cubeEmpty.rotation_euler = (0,0,radians)

    # applico il modificatore
    bpy.context.view_layer.objects.active = baseCylinder
    bpy.ops.object.modifier_add(type='BOOLEAN')
    bpy.context.object.modifiers["Boolean"].object = baseCube
    bpy.ops.object.modifier_apply(modifier="Boolean")

    # ruotare la fetta di metà il suo angolo (esempio se è ampia 60, ruotarla di 30 attorno all'origine
    halfAngle = (180 - angle) / 2
    radians = halfAngle * math.pi / 180
    baseCylinder.rotation_euler = (0,0,radians)
    
    # aggiungo alla lista il taglio
    listaDiCilindri.append(baseCylinder)
    
    # rimuovo il cubo e il suo empty
    bpy.data.objects.remove(cubeEmpty, do_unlink=True)
    bpy.data.objects.remove(baseCube, do_unlink=True)


    
cutsList = [] # contiene gli oggetti che saranno usati per le intersezioni
emptyList = [] # contiene gli empties (che fanno da parent alle fette)

for i in range(100):
    generateCut(cutsList, random.uniform(0, 180))


for each in cutsList:    
    bpy.ops.object.empty_add(location = (0,0,0))
    _empty = bpy.context.active_object
    each.parent = _empty
    emptyList.append(_empty)
    


class taglio:
    def __init__(self, _distanceFromOrigin, _rotY, _rotZ, _rotEmptyX, _rotEmptyZ, _emptyParent, _cutSon):
        self.distanceFromOrigin = -abs(_distanceFromOrigin) # così mantiene la punta verso l'origine
        self.rotZ = _rotZ
        self.rotY = _rotY
        self.rotEmptyZ = _rotEmptyZ
        self.rotEmptyX = _rotEmptyX
        self.emptyParent = _emptyParent
        self.cutSon = _cutSon
    
    def stampa(self):
        print('Stampa del taglio:')
        print('distanceFromOrigin: ', self.distanceFromOrigin)
        print('rotY: ', self.rotY)
        print('rotZ: ', self.rotZ)
        print('rotEmptyX: ', self.rotEmptyX)
        print('rotEmptyZ: ', self.rotEmptyZ)
        print('emptyParent: ', self.emptyParent)
        print('cutSon: ', self.cutSon)
    
    def compute(self):        
        #limitazioni per fare in modo che sia sempre la punta del cuneo ad incidere il materiale
        angleLimit = 60
        if self.rotZ > angleLimit:
            self.rotZ = angleLimit
        elif self.rotZ < -angleLimit:
            self.rotZ = -angleLimit
          
        # ruotare il cuneo
        bpy.context.view_layer.objects.active = self.cutSon
        print('Active object is: ', bpy.context.view_layer.objects.active)
        bpy.context.active_object.rotation_euler[1] = math.radians(self.rotY)        
        bpy.context.active_object.rotation_euler[2] = math.radians(self.rotZ)
        # PS sarebbe bello, appena creato il cuneo, riuscire ad applicare la sua prima rotazione

        # traslare il cuneo
        shift = [0, self.distanceFromOrigin, 0]
        self.cutSon.location += mathutils.Vector(shift)
        
        #check and adjust parenting
        if self.cutSon.parent != self.emptyParent:
            self.cutSon.parent = self.emptyParent
        
        # ruotare l'empty che fa da parent al cuneo
        bpy.context.view_layer.objects.active = self.emptyParent
        print('Active object is: ', bpy.context.view_layer.objects.active)
        bpy.context.active_object.rotation_euler[0] = math.radians(self.rotEmptyX)
        bpy.context.active_object.rotation_euler[2] = math.radians(self.rotEmptyZ)
        
    # scala il cuneo/fetta
    def scale(self, scaleFactor):
        bpy.context.view_layer.objects.active = self.cutSon
        bpy.context.object.scale[0] = scaleFactor
        bpy.context.object.scale[1] = scaleFactor
        bpy.context.object.scale[2] = scaleFactor



listaClassiTaglio = []

for _empty, _cut in zip(emptyList, cutsList):
        distanceFromOrigin = random.uniform(0 , 2)
        rotY = random.uniform( 0 , 90 )
        rotZ = random.uniform( 0 , 90 )
        rotEmptyX = random.uniform( 0 , 360 )
        rotEmptyZ = random.uniform( 0 , 360 )
        taglioToAppend = taglio(distanceFromOrigin, rotY,rotZ,rotEmptyX,rotEmptyZ, _empty, _cut)
        taglioToAppend.compute()
        listaClassiTaglio.append(taglioToAppend)
        
for each in listaClassiTaglio:
    each.stampa()
    each.scale(1)



bpy.ops.mesh.primitive_cube_add(location=(0,0,0), scale = (1, 1, 1))
cuboDaTagliare = bpy.context.active_object

# per ogni oggetto nella lista, applico il modificatore di differenza booleana 
# fra quell'oggetto e il volume da scolpire
for obj in cutsList:
    bpy.ops.object.modifier_add(type='BOOLEAN')
    bpy.context.object.modifiers["Boolean"].object = obj
    bpy.ops.object.modifier_apply(modifier="Boolean")



# Calcolo del volume

me = bpy.context.object.data


# Get a BMesh representation
bm = bmesh.new()   # create an empty BMesh
bm.from_mesh(me)   # fill it in from a Mesh

volume = bm.calc_volume()
print('volume è ', volume)


# Finish up, write the bmesh back to the mesh
bm.to_mesh(me)
bm.free()  



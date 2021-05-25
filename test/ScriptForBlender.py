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

for i in range(60):
    generateCut(cutsList, random.uniform(0, 180))


for each in cutsList:    
    bpy.ops.object.empty_add(location = (0,0,0))
    _empty = bpy.context.active_object
    each.parent = _empty
    emptyList.append(_empty)
    
    
# allontano o avvicino al centro il cuneo
for each in cutsList:
        # ora modifico la posizione della fetta (non dell'empty) allontanandola dall'origine facendola muovere lungo l'asse Y; così resta puntata verso l'origine
    shift = [0, random.uniform(-0.5,-1), 0]
    each.location += mathutils.Vector(shift)
    
    
    
# ruoto e traslo l'empty che fa da parent
for each in emptyList:     
    radians = random.randint(0,360) * math.pi / 180
    each.rotation_euler = (radians,0,radians)



bpy.ops.mesh.primitive_cube_add(location=(0,0,0.5), scale = (1, 1, 1))
cuboDaTagliare = bpy.context.active_object



# per ogni oggetto nella lista, applico il modificatore di differenza booleana 
# fra quell'oggetto e il volume da scolpire

for obj in cutsList:
    bpy.ops.object.modifier_add(type='BOOLEAN')
    bpy.context.object.modifiers["Boolean"].object = obj
    bpy.ops.object.modifier_apply(modifier="Boolean")






# per calcolare le intersezioni fra il cubo e la collection di fette, posso posizionarle tutte all'esterno del cubo, con la punta rivolta verso l'origine
# creo un empty che posiziono nell'origine, e lo rendo il parent di tutte le fette

# ogni fetta sarà caratterizzata da :
#    un'angolo (che ne determina l'ampiezza) -> dalla funzione
#    la scala (che determina quanto volume interseca) -> modificare la scala della fetta
#    la rotazione attorno al cubo -> modificare rotazione dell'empty



# ______________________________________________________

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



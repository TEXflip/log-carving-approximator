import bpy
import random
import mathutils
import bmesh
import math
from mathutils.bvhtree import BVHTree

scaleFactor = 10

class taglio:
    def __init__(self, _distanceFromOrigin, _desiredAngle, _rotY, _rotZ, _rotEmptyX, _rotEmptyZ,
     _emptyParent, _cutSon):
        self.distanceFromOrigin = -abs(_distanceFromOrigin) # così mantiene la punta verso l'origine
        self.desiredAngle = _desiredAngle
        self.rotZ = _rotZ
        self.rotY = _rotY
        self.rotEmptyZ = _rotEmptyZ
        self.rotEmptyX = _rotEmptyX
        self.emptyParent = _emptyParent
        self.cutSon = _cutSon
    
    def setValues(self, _distanceFromOrigin, _desiredAngle, _rotY, _rotZ,
            _rotEmptyX, _rotEmptyZ, _emptyParent, _cutSon):
        self.distanceFromOrigin = -abs(_distanceFromOrigin) # così mantiene la punta verso l'origine
        self.desiredAngle = _desiredAngle
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
        # desiredAngle = ampiezza desiderata per la fetta, deve essere fra 0 e 180 gradi
        angle = 180 - desiredAngle
        # print('Angle: ', angle, '\nself.desiredAngle: ', self.desiredAngle, '\desiredAngle: ', desiredAngle)
        radians = angle * math.pi / 180

        bpy.ops.mesh.primitive_cube_add(location = (1, 0,0), scale=(1, 1, 1))
        baseCube = bpy.context.active_object
        
        bpy.context.view_layer.objects.active = self.cutSon

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
        bpy.context.view_layer.objects.active = self.cutSon
        bpy.ops.object.modifier_add(type='BOOLEAN')
        bpy.context.object.modifiers["Boolean"].object = baseCube
        bpy.ops.object.modifier_apply(modifier="Boolean")

        # ruotare la fetta di metà il suo angolo (esempio se è ampia 60, ruotarla di 30 attorno all'origine
        halfAngle = (180 - angle) / 2
        radians = halfAngle * math.pi / 180
        self.cutSon.rotation_euler = (0,0,radians)
        
        
        # rimuovo il cubo e il suo empty
        bpy.data.objects.remove(cubeEmpty, do_unlink=True)
        bpy.data.objects.remove(baseCube, do_unlink=True)
        
        #limitazioni per fare in modo che sia sempre la punta del cuneo ad incidere il materiale
        angleLimit = 60
        if self.rotZ > angleLimit:
            self.rotZ = angleLimit
        elif self.rotZ < -angleLimit:
            self.rotZ = -angleLimit
        
        # ruotare il cuneo
        bpy.context.view_layer.objects.active = self.cutSon
        bpy.context.active_object.rotation_euler[1] = math.radians(self.rotY)        
        bpy.context.active_object.rotation_euler[2] = math.radians(self.rotZ)
        
        # traslare il cuneo
        shift = [0, self.distanceFromOrigin, 0]
        self.cutSon.location += mathutils.Vector(shift)
        
        #check and adjust parenting
        if self.cutSon.parent != self.emptyParent:
            self.cutSon.parent = self.emptyParent
        
        # ruotare l'empty che fa da parent al cuneo
        bpy.context.view_layer.objects.active = self.emptyParent
        
        bpy.context.active_object.rotation_euler[0] = math.radians(self.rotEmptyX)
        bpy.context.active_object.rotation_euler[2] = math.radians(self.rotEmptyZ)
        
    # scala il cuneo/fetta
    def scale(self, scaleFactor):
        bpy.context.view_layer.objects.active = self.cutSon
        bpy.context.object.scale[0] = scaleFactor
        bpy.context.object.scale[1] = scaleFactor
        bpy.context.object.scale[2] = scaleFactor
    
    def delete(self):
        bpy.data.objects.remove(self.cutSon, do_unlink=True) # prima versione
        bpy.data.objects.remove(self.emptyParent, do_unlink=True) # prima versione



    # verifica se il taglio interseca la mesh obiettivo
    # target e cutToCheck devono essere degli objects
    # crea un "taglio" temporaneo a cui applicare le trasformate (loc, rot, trasl) e poi
    #       controlla l'intersezione su quello. In questo modo, possiamo semplicemente cambiare
    #       i valori di rotazioni e traslazioni sul "taglio originale" senza applicarli
    # però l'empty e il cuneo sono nuovi e diversi dagli altri
    def verifyIntersect(self, obj2):
        return verifyIntersect(self.cutSon, obj2)
        
    def applyTransform(self):
        bpy.context.view_layer.objects.active = self.emptyParent
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    
        bpy.context.view_layer.objects.active = self.cutSon
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

def is_inside(p, obj):    
    result, point, normal, face = obj.closest_point_on_mesh(p)    
    p2 = point-p    
    v = p2.dot(normal)    
    return not(v < 0.0)

# verifica se il taglio interseca la mesh obiettivo
# obj1 e obj2 devono essere degli objects
def verifyIntersect(obj1, obj2):
    #create bmesh objects
    bm1 = bmesh.new()
    bm2 = bmesh.new()

    #fill bmesh data from objects
    bpy.context.view_layer.objects.active = obj1
    me = bpy.context.object.data
    bm1.from_mesh(me)
    
    bpy.context.view_layer.objects.active = obj2
    me = bpy.context.object.data
    bm2.from_mesh(me)            
    
    bm1.transform(obj1.matrix_world)
    bm2.transform(obj2.matrix_world) 

    #make BVH tree from BMesh of objects
    obj1_BVHtree = BVHTree.FromBMesh(bm1)
    obj2_BVHtree = BVHTree.FromBMesh(bm2)           

    #get intersecting pairs
    inter = obj1_BVHtree.overlap(obj2_BVHtree)

    #if list is empty, no objects are touching
    if inter != []:
        # print(str(obj1.name) + " and " + str(obj2.name) + " are touching!")
        return True
    
    # return is_inside(obj2.location, obj1)
    elif is_inside(obj2.location, obj1) == True:
        print('eccolo')
        return True
    else:
        return False



bpy.ops.mesh.primitive_cube_add(location = (0, 0, 0), scale=(0.6, 0.6, 0.6))
targetObject = bpy.context.active_object

listaClassiTaglio = []

# aggiungo l'oggetto da intagliare
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0), scale = (1, 1, 1))
cuboDaTagliare = bpy.context.active_object



# inizializzo i tagli con valori dati in input
for i in range(30):
    bpy.ops.object.empty_add()
    _empty = bpy.context.active_object
    bpy.ops.mesh.primitive_cylinder_add()
    _cut = bpy.context.active_object

    
    distanceFromOrigin = random.uniform(0 , 2)
    desiredAngle = random.uniform(0 , 180)
    rotY = random.uniform( 0 , 90 )
    rotZ = random.uniform( 0 , 90 )
    rotEmptyX = random.uniform( 0 , 360 )
    rotEmptyZ = random.uniform( 0 , 360 )
    
    # inizializzo il taglio
    taglioTemp = taglio(distanceFromOrigin, desiredAngle, rotY,rotZ,
                            rotEmptyX,rotEmptyZ, _empty, _cut)
    
    
    taglioTemp.compute()
    
    taglioTemp.scale(scaleFactor)

    taglioTemp.applyTransform()
    
    # continuo a creare nuovi tagli finchè si intersecano con il mio oggetto target
    if taglioTemp.verifyIntersect(targetObject) == True:
        print('An intersection between ', taglioTemp.cutSon.name, ' and ',
        targetObject.name, ' occured - recalculating the cut')
        
        j = 1
        # ripeto quello fatto prima dell' "if" e rifaccio il check delle intersezioni
        while taglioTemp.verifyIntersect(targetObject) == True:
            # print('iterazione ', j, ' del ciclo while')
            j += 1
            taglioTemp.delete()
            bpy.ops.object.empty_add()
            _empty = bpy.context.active_object
            bpy.ops.mesh.primitive_cylinder_add()
            _cut = bpy.context.active_object
            distanceFromOrigin = random.uniform(0 , 2)
            desiredAngle = random.uniform(0 , 180)
            rotY = random.uniform( 0 , 90 )
            rotZ = random.uniform( 0 , 90 )
            rotEmptyX = random.uniform( 0 , 360 )
            rotEmptyZ = random.uniform( 0 , 360 )
            # taglioTemp = taglio(distanceFromOrigin, desiredAngle, rotY,rotZ,rotEmptyX,rotEmptyZ, _empty, _cut)
            taglioTemp.setValues(distanceFromOrigin, desiredAngle, rotY,rotZ,rotEmptyX,rotEmptyZ, _empty, _cut)
            taglioTemp.compute()
            taglioTemp.scale(scaleFactor)
            taglioTemp.applyTransform()
            if taglioTemp.verifyIntersect(targetObject) == False:
                print('Intersezione risolta dopo ', j, ' ricalcoli')
    
    # aggiungo cilindro e empty
    bpy.ops.object.empty_add()
    _newEmpty = bpy.context.active_object
    bpy.ops.mesh.primitive_cylinder_add()
    _newCut = bpy.context.active_object
    
    #creo il taglio definitivo, a cui assegno i parametri di quello temporaneo che, in caso di 
    # intersezione, dovrebbero essere stati corretti nel ciclo while
    # dopodichè, cancello il taglio temporaneo
    taglioToAppend = taglio(distanceFromOrigin, desiredAngle, rotY,rotZ,
                        rotEmptyX,rotEmptyZ, _newEmpty, _newCut)
    
    taglioToAppend.setValues(taglioTemp.distanceFromOrigin, taglioTemp.desiredAngle, taglioTemp.rotY, 
    taglioTemp.rotZ, taglioTemp.rotEmptyX, taglioTemp.rotEmptyZ, _newEmpty, _newCut)
    
    taglioTemp.delete()
    
    taglioToAppend.compute()
    taglioToAppend.scale(scaleFactor)
    taglioToAppend.applyTransform()

    listaClassiTaglio.append(taglioToAppend)


# rendo cuboDaTagliare l'active object (prima lo era targetObject)
bpy.context.view_layer.objects.active = cuboDaTagliare

# per ogni oggetto nella lista, applico il modificatore di differenza booleana 
# fra quell'oggetto e il volume da scolpire
for obj in listaClassiTaglio:
    print('Angle: ', obj.desiredAngle)
    bpy.ops.object.modifier_add(type='BOOLEAN')
    bpy.context.object.modifiers["Boolean"].object = obj.cutSon
    bpy.ops.object.modifier_apply(modifier="Boolean")

"""
for obj in listaClassiTaglio:
    # rimuovo l'oggetto
    bpy.data.objects.remove(obj.cutSon, do_unlink=True) # prima versione
    bpy.data.objects.remove(obj.emptyParent, do_unlink=True) # prima versione
"""
# -------   Calcolo del volume

me = bpy.context.object.data

# rimuovo l'oggetto finale scolpito
# bpy.data.objects.remove(cuboDaTagliare, do_unlink=True)

# Get a BMesh representation
bm = bmesh.new()   # create an empty BMesh
bm.from_mesh(me)   # fill it in from a Mesh

volume = bm.calc_volume()
print('Il volume è ', volume)

# Finish up, write the bmesh back to the mesh
bm.to_mesh(me)
bm.free()
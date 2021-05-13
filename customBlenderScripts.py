from trimesh.interfaces.generic import MeshScript
from distutils.spawn import find_executable
import trimesh
import numpy as np
import os

_search_path = os.environ['PATH']
_blender_executable = find_executable('blender', path=_search_path)
template = open('templates/blender_bool.py.template').read()

def customSliceMesh(mesh, origin, normal):
    # exists = _blender_executable is not None

    origin = '({0},{1},{2})'.format(origin[0],origin[1],origin[2])
    normal = '({0},{1},{2})'.format(normal[0],normal[1],normal[2])
    script = template.replace('$ORIGIN', origin).replace('$NORMAL', normal)

    with MeshScript(meshes=np.array([mesh]), script=script, debug=False) as blend:
        try:
            result = blend.run(_blender_executable + ' --background --python $SCRIPT')
        except:
            print("Error during custom slice")
            result = None

    return result
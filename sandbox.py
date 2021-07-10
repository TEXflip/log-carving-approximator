from inspyred import ec, swarm
from planeProblem import PlaneCutProblem
from wedgeProblem import BlenderWedgeProblem, taglio
from wedgeProblem2 import BlenderWedgeProblem2
import matplotlib.pylab as plt
import numpy as np
import os
import sys
import plot_utils
from inspyred_utils import NumpyRandomWrapper
import time
### Choose the algorithm between EC and PSO
algorithms_list = {"ec" : 0, "pso" : 1, "es" : 2}
ALGORITHM = algorithms_list["ec"]
REGENERATION = False

args = {}

# --- Global Params

args["initial_pop_storage"] = {}
args["max_generations"] = 10
args["slice_application_generation"] = 10 # number of generations before appling the best slice, only if REGENERATION = False
args["pop_size"] = args["num_selected"] = 10 # population size
args["num_offspring"] = 10
args["num_evolutions"] = 5 # only if REGENERATION = True
args["fig_title"] = 'Model Sculpting Approximation'

# --- Evolutionary Computation params ---

args["num_elites"] = 1
args["gaussian_stdev"] = 0.25
args["crossover_rate"] = 0.2
args["mutation_rate"] = 0.8
args["tournament_size"] = 3

# --- Particle Swarm Optimization params ---

args["inertia"] = 1
args["cognitive_rate"] = 1.8
args["social_rate"] = 2.

# --- Evolutionary Strategies params ---

args["tau"] = None
args["tau_prime"] = None
args["epsilon"] = 0.00001

if __name__ == "__main__":
    rng = NumpyRandomWrapper(42) # in sostanza, è una sorta di random.seed()
    # problem = PlaneCutProblem('3D models/bulbasaur.stl', '3D models/cylinder.stl', rng)
    # problem = BlenderWedgeProblem('3D models/diamond.stl', '3D models/cylinder.stl', rng)
    problem = BlenderWedgeProblem2('3D models/diamond.stl', '3D models/cylinder.stl', rng)

    pop = []
    for i in range(10):
        pop.append(problem.generator(rng, args))

    fit = problem.evaluator(pop, args)
    print(fit)

    cuts_string = '"' + ';'.join(','.join('%0.7f' %x for x in y) for y in pop) + '"'
    if isinstance(problem, PlaneCutProblem):
        problem.SaveCarvingMesh("finalModel.stl")
        command = 'blender -P templates/stlImporter.py -- "finalModel.stl" "' + problem.targetMeshPath + '" plane ' + cuts_string
        # print(command)
        os.system(command)
    else:
        problem.SaveCarvingMesh("finalModel3.stl", problem.carvingMesh)
        command = 'blender -P templates/stlImporter.py -- "finalModel3.stl" "' + problem.targetMeshPath + '" wedge ' + cuts_string
        # print(command)
        os.system(command)
from inspyred import ec, swarm
from planeProblem import PlaneCutProblem
from wedgeProblem import BlenderWedgeProblem, taglio
import matplotlib.pylab as plt
import numpy as np
import os
import sys
import plot_utils
from inspyred_utils import NumpyRandomWrapper
import time

def supressLog():
    # redirect log output to a file
    logfile = 'blender_evolution.log'
    open(logfile, 'w').close()
    old = os.dup(1)
    sys.stdout.flush()
    os.close(1)
    os.open(logfile, os.O_WRONLY)
    return old

def reactivateLog(old):
    os.close(1)
    os.dup(old)
    os.close(old)

def getBestAndWorst(pop):
    final_pop_fitnesses = np.asarray([guy.fitness for guy in pop])
    final_pop_candidates = np.asarray([guy.candidate for guy in pop])
    
    sort_indexes = sorted(range(len(final_pop_fitnesses)), key=final_pop_fitnesses.__getitem__)
    final_pop_fitnesses = final_pop_fitnesses[sort_indexes]
    final_pop_candidates = final_pop_candidates[sort_indexes]
    
    return final_pop_candidates[-1], final_pop_candidates[0]

### Choose the algorithm between EC and PSO
algorithms_list = {"ec" : 0, "pso" : 1, "es" : 2}
ALGORITHM = algorithms_list["ec"]
REGENERATION = False

args = {}

# --- Global Params

args["initial_pop_storage"] = {}
args["max_generations"] = 20
args["slice_application_generation"] = 20 # number of generations before appling the best slice, only if REGENERATION = False
args["pop_size"] = args["num_selected"] = 10 # population size
args["num_offspring"] = 10
args["num_evolutions"] = 20 # only if REGENERATION = True
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
    # problem = PlaneCutProblem('3D models/diamond.stl', '3D models/cylinder.stl', rng)
    problem = BlenderWedgeProblem('3D models/diamond.stl', '3D models/cylinder.stl', rng)

    initial_pop_storage = {}
    
    if ALGORITHM == algorithms_list["ec"]:
        algorithm = ec.EvolutionaryComputation(rng)
        algorithm.replacer = ec.replacers.generational_replacement
        algorithm.variator = [ec.variators.uniform_crossover, ec.variators.gaussian_mutation] # no need to do custom mutator or crossover
        algorithm.selector = ec.selectors.tournament_selection

    elif ALGORITHM == algorithms_list["pso"]:
        algorithm = swarm.PSO(rng)

    # elif ALGORITHM == algorithms_list["es"]:
    #     algorithm = ec.ES(rng)

    algorithm.terminator = ec.terminators.generation_termination
    algorithm.observer = [plot_utils.plot_observer, plot_utils.initial_pop_observer]
    
    if not REGENERATION:
        algorithm.observer += [problem.custom_observer]
    # algorithm.bounder = ec.Bounder([-2,-2,-2,-2,-2,-2], [2,2,2,2,2,2])

    # Generates a random plane
    generator = problem.generator
    evaluator = problem.evaluator

    oldStdOut = supressLog()

    if not REGENERATION:
        final_pop = algorithm.evolve(generator, evaluator, maximize=problem.maximize, **args)
    else:
        args["num_evolution"] = 0
        for i in range(args["num_evolutions"]):
            args["fig_title"] = "Evolution n. " + str(args["num_evolution"])
            final_pop = algorithm.evolve(generator, evaluator, maximize=problem.maximize, **args)
            b, w = getBestAndWorst(final_pop)
            problem.sliceAndApply(b)
            problem.bestCuts = np.append(problem.bestCuts, np.array([b]), axis=0)
            args["num_evolution"] += 1
            plt.close()

    reactivateLog(oldStdOut)

    # for i, c in enumerate(final_pop):
    #     print(str(i)+') ', c)
    print("selected cuts: ", problem.bestCuts)


    plt.ioff()
    
    plt.show()


    if isinstance(problem, PlaneCutProblem):
        cuts_string = '"' + ';'.join(','.join('%0.7f' %x for x in y) for y in problem.bestCuts) + '"'
        problem.SaveCarvingMesh("finalModel.stl")
        command = 'blender -P templates/stlImporter.py -- "finalModel.stl" "' + problem.targetMeshPath + '" ' + cuts_string
        print(command)
        os.system(command)
    else:
        # c = problem.bestCuts
        # mesh = taglio(c[0], c[1], c[2], c[3], c[4], c[5])
        # t = taglio(c[0][0], c[0][1], c[0][2], c[0][3], c[0][4], c[0][5])
        problem.SaveCarvingMesh("finalModel3.stl", problem.carvingMesh)
        command = 'blender -P templates/stlImporter.py -- "finalModel.stl" "' + problem.targetMeshPath + '" '
        print(command)
        os.system(command)
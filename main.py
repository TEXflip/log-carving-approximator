from inspyred import ec, swarm
from planeProblem import PlaneCutProblem
from wedgeProblem import BlenderWedgeProblem, taglio
from wedgeProblem2 import BlenderWedgeProblem2
import matplotlib.pylab as plt
import numpy as np
import os
import plot_utils
from inspyred_utils import NumpyRandomWrapper

def getBest(pop):
    final_pop_fitnesses = np.asarray([guy.fitness for guy in pop])
    final_pop_candidates = np.asarray([guy.candidate for guy in pop])
    
    sort_indexes = sorted(range(len(final_pop_fitnesses)), key=final_pop_fitnesses.__getitem__)
    final_pop_fitnesses = final_pop_fitnesses[sort_indexes]
    final_pop_candidates = final_pop_candidates[sort_indexes]
    
    return final_pop_candidates[-1], final_pop_fitnesses[-1]

### Choose the algorithm between EC and PSO
algorithms_list = {"ec" : 0, "pso" : 1, "es" : 2}
ALGORITHM = algorithms_list["ec"]
REGENERATION = True

args = {}

# --- Global Params

args["initial_pop_storage"] = {}
args["max_generations"] = 20
args["slice_application_generation"] = 20 # number of generations before appling the best slice, only if REGENERATION = False
args["pop_size"] = args["num_selected"] = 100 # population size
args["num_offspring"] = 100
args["num_evolutions"] = 10 # only if REGENERATION = True
args["fig_title"] = 'Model Sculpting Approximation'

# --- Evolutionary Computation params ---

args["num_elites"] = 1
args["gaussian_stdev"] = 0.1
args["custom_gaussian_stdev"] = [0.1,0.1,0.1,0.1,0.1,0.1,5]
args["crossover_rate"] = 0.5
args["mutation_rate"] = 1
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
    rng = NumpyRandomWrapper(0)
    # problem = PlaneCutProblem('3D models/bulbasaur.stl', '3D models/cylinder.stl', rng)
    # problem = BlenderWedgeProblem('3D models/bulbasaur.stl', '3D models/cylinder.stl', rng)
    problem = BlenderWedgeProblem2('3D models/bulbasaur.stl', '3D models/cylinder.stl', rng, fastBoolean=True)

    if ALGORITHM == algorithms_list["ec"]:
        algorithm = ec.EvolutionaryComputation(rng)
        algorithm.replacer = ec.replacers.generational_replacement
        if isinstance(problem, BlenderWedgeProblem2):
            algorithm.variator = [ec.variators.uniform_crossover, problem.custom_gaussian_mutation]
        else:
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

    # Generates a random plane
    generator = problem.generator
    evaluator = problem.evaluator

    if not REGENERATION:
        final_pop = algorithm.evolve(generator, evaluator, maximize=problem.maximize, bounder=problem.bounder, **args)
    else:
        args["num_evolution"] = 0
        for i in range(args["num_evolutions"]):
            args["fig_title"] = "Evolution n. " + str(args["num_evolution"])
            final_pop = algorithm.evolve(generator, evaluator, maximize=problem.maximize, **args)

            b, f = getBest(final_pop)
            if problem.is_feasible(f):
                problem.sliceAndApply(b)
                problem.bestCuts = np.append(problem.bestCuts, np.array([b]), axis=0)
            args["num_evolution"] += 1
            plt.close()

    for i, c in enumerate(final_pop):
        print(str(i)+') ', c)
    print("selected cuts: ", problem.bestCuts)


    plt.ioff()
    plt.show()

    cuts_string = '"' + ';'.join(','.join('%0.7f' %x for x in y) for y in problem.bestCuts) + '"'
    if isinstance(problem, PlaneCutProblem):
        problem.SaveCarvingMesh("finalModel.stl")
        command = 'blender -P templates/stlImporter.py -- "finalModel.stl" "' + problem.targetMeshPath + '" plane ' + cuts_string
        os.system(command)
    else:
        problem.SaveCarvingMesh("finalModel3.stl", problem.carvingMesh)
        command = 'blender -P templates/stlImporter.py -- "finalModel3.stl" "' + problem.targetMeshPath + '" wedge ' + cuts_string
        os.system(command)
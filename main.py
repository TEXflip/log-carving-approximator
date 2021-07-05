from inspyred import ec
from problem import PlaneCut
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

def getBestWrost(pop):
    final_pop_fitnesses = np.asarray([guy.fitness for guy in pop])
    final_pop_candidates = np.asarray([guy.candidate for guy in pop])
    
    sort_indexes = sorted(range(len(final_pop_fitnesses)), key=final_pop_fitnesses.__getitem__)
    final_pop_fitnesses = final_pop_fitnesses[sort_indexes]
    final_pop_candidates = final_pop_candidates[sort_indexes]
    
    return final_pop_candidates[0], final_pop_candidates[-1]

args = {}
args["initial_pop_storage"] = {}
args["max_generations"] = 100
args["num_elites"] = 1
args["gaussian_stdev"] = 0.25
args["crossover_rate"] = 0.2
args["mutation_rate"] = 0.8
args["slice_application_generation"] = 20 # number of generations before appling the best slice

args["pop_size"] = args["num_selected"] = 10 # population size
args["num_offspring"] = 10 #lambda
args["tournament_size"] = 3

args["fig_title"] = 'ES'

if __name__ == "__main__":
    rng = NumpyRandomWrapper(42) # in sostanza, è una sorta di random.seed()
    problem = PlaneCut('3D models/sphere.stl', '3D models/cylinder.stl', rng)

    initial_pop_storage = {}
    
    algorithm = ec.EvolutionaryComputation(rng)
    algorithm.terminator = ec.terminators.generation_termination
    algorithm.replacer = ec.replacers.generational_replacement
    algorithm.variator = [ec.variators.uniform_crossover, ec.variators.gaussian_mutation] # no need to do custom mutator or crossover
    algorithm.selector = ec.selectors.tournament_selection
    algorithm.observer = [plot_utils.plot_observer, plot_utils.initial_pop_observer, problem.custom_observer]
    # algorithm.bounder = ec.Bounder([-1,-1,-1,-1,-1,-1], [1,1,1,1,1,1])

    # Generates a random plane
    generator = problem.generator
    evaluator = problem.evaluator

    oldStdOut = supressLog()

    final_pop = algorithm.evolve(generator, evaluator, maximize=problem.maximize, **args)

    reactivateLog(oldStdOut)

    # for i, c in enumerate(final_pop):
    #     print(str(i)+') ', c)
    print("selected cuts: ", problem.bestCuts)


    plt.ioff()
    plt.show()

    cuts_string = '"' + ';'.join(','.join('%0.5f' %x for x in y) for y in problem.bestCuts) + '"'
    problem.SaveCarvingMesh("finalModel.stl")
    command = 'blender -P templates/stlImporter.py -- "finalModel.stl" "3D models/sphere.stl" ' + cuts_string
    print(command)
    os.system(command)
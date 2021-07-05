from inspyred import ec
from problem import PlaneCut
import matplotlib.pylab as plt
import numpy as np
import os
import sys
import plot_utils
from inspyred_utils import NumpyRandomWrapper
import random
import time

def supressLog():
    # redirect log output to a file
    logfile = 'blender_evolution.log'
    open(logfile, 'a').close()
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
args["sigma"] = 10.0
args["crossover_rate"] = 0.
args["slice_application_evaluations"] = 200 # number of evaluations before apply the best slice

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
    algorithm.observer = [plot_utils.plot_observer, plot_utils.initial_pop_observer, problem.customObserver]

    # Generates a random plane
    generator = problem.generator
    evaluator = problem.evaluator

    oldStdOut = supressLog()

    final_pop = algorithm.evolve(generator, evaluator, maximize=problem.maximize, **args)

    reactivateLog(oldStdOut)

    # for i, c in enumerate(final_pop):
    #     print(str(i)+') ', c)
    print("selected cuts: ", problem.bestCusts)

    
    plt.ioff()
    plt.show()

    problem.SaveCarvingMesh("finalModel.stl")
    os.system('blender -P templates/stlImporter.py -- "finalModel.stl" "3D models/sphere.stl"')
from inspyred import ec
from problem import PlaneCut
import matplotlib.pylab as plt
import os
import sys
import plot_utils
from inspyred_utils import NumpyRandomWrapper
import random
import time

def supressLog():
    # redirect log output to a file
    logfile = 'blender_render.log'
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

args = {}
args["max_generations"] = 20
args["sigma"] = 5.0

"""
args["pop_size"] = args["num_selected"] = 10 # population size
args["num_offspring"] = 50 #lambda
#args["tournament_size"] = 2
"""

args["pop_size"] = args["num_selected"] = 10 # population size
args["num_offspring"] = 10 #lambda
#args["tournament_size"] = 2

args["fig_title"] = 'ES'

if __name__ == "__main__":
    rng = NumpyRandomWrapper(0) # in sostanza, è una sorta di random.seed()
    problem = PlaneCut('3D models/sphere.stl', '3D models/cylinder.stl', rng)

    initial_pop_storage = {}
    
    algorithm = ec.EvolutionaryComputation(rng)
    algorithm.terminator = ec.terminators.generation_termination
    algorithm.replacer = ec.replacers.generational_replacement
    algorithm.variator = [ec.variators.uniform_crossover, ec.variators.gaussian_mutation]
    algorithm.selector = ec.selectors.tournament_selection
    algorithm.observer = [plot_utils.plot_observer, plot_utils.initial_pop_observer]

    # Generates a random plane
    generator = problem.generator
    evaluator = problem.evaluator
    # algorithm.observer = [plot_utils.plot_observer,plot_utils.initial_pop_observer]
    algorithm.maximize = problem.maximize

    oldStdOut = supressLog()

    final_pop = algorithm.evolve(generator, evaluator, initial_pop_storage={}, **args)
    plt.show()

    reactivateLog(oldStdOut)

    for i, c in enumerate(final_pop):
        print(str(i)+') ', c)
    
    plt.ioff()
    plt.show()
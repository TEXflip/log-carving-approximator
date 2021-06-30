from inspyred import ec
from problem import PlaneCut
import plot_utils
from inspyred_utils import NumpyRandomWrapper
import random
import time

args = {}
args["max_generations"] = 2
args["sigma"] = 5.0

"""
args["pop_size"] = args["num_selected"] = 10 # population size
args["num_offspring"] = 50 #lambda
#args["tournament_size"] = 2
"""

args["pop_size"] = args["num_selected"] = 100 # population size
args["num_offspring"] = 500 #lambda
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

    # Generates a random plane
    generator = problem.generator
    evaluator = problem.evaluator
    # algorithm.observer = [plot_utils.plot_observer,plot_utils.initial_pop_observer]
    algorithm.maximize = problem.maximize

    final_pop = algorithm.evolve(generator, evaluator, **args)

    i = 1
    for c in final_pop:
        print(i, ') ', c)
        i += 1
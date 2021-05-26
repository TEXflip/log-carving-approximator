from inspyred import ec
from problem import PlaneCut
import plot_utils
from inspyred_utils import NumpyRandomWrapper

args = {}
args["max_generations"] = 1
args["sigma"] = 1.0

args["num_selected"] = 5 # population size
args["num_offspring"] = 50 #lambda

args["fig_title"] = 'ES'

if __name__ == "__main__":
    rng = NumpyRandomWrapper(0)
    problem = PlaneCut('3D models/sphere.stl', '3D models/cylinder.stl', rng)

    initial_pop_storage = {}
    
    algorithm = ec.EvolutionaryComputation(rng)
    algorithm.terminator = ec.terminators.generation_termination
    algorithm.replacer = ec.replacers.generational_replacement    
    algorithm.variator = [ec.variators.uniform_crossover,ec.variators.gaussian_mutation]
    algorithm.selector = ec.selectors.tournament_selection
    generator = problem.generator
    evaluator = problem.evaluator
    # algorithm.observer = [plot_utils.plot_observer,plot_utils.initial_pop_observer]
    algorithm.maximize = problem.maximize

    final_pop = algorithm.evolve(generator, evaluator, pop_size=args["num_selected"], **args)

    for c in final_pop:
        print(c)
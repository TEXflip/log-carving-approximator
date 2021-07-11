from inspyred import ec, swarm
import numpy as np
import json
from inspyred_utils import NumpyRandomWrapper
from es import ES, GLOBAL, INDIVIDUAL
import sys

def getBest(pop):
    final_pop_fitnesses = np.asarray([guy.fitness for guy in pop])
    final_pop_candidates = np.asarray([guy.candidate for guy in pop])
    
    sort_indexes = sorted(range(len(final_pop_fitnesses)), key=final_pop_fitnesses.__getitem__)
    final_pop_fitnesses = final_pop_fitnesses[sort_indexes]
    final_pop_candidates = final_pop_candidates[sort_indexes]
    
    return final_pop_candidates[-1], final_pop_fitnesses[-1]

def runExperiment(problemType, target, carving, algorithm, regeneration, seed, **args):
    from planeProblem import PlaneCutProblem
    from wedgeProblem2 import BlenderWedgeProblem2
    rng = NumpyRandomWrapper(seed)

    if problemType == "plane":
        problem = PlaneCutProblem(target, carving, rng)
    else:
        problem = BlenderWedgeProblem2(target, carving, rng, fastBoolean=False)
    # problem = BlenderWedgeProblem('3D models/diamond.stl', '3D models/cylinder.stl', rng)

    if algorithm == "ec":
        algorithm = ec.EvolutionaryComputation(rng)
        algorithm.replacer = ec.replacers.generational_replacement
        if isinstance(problem, BlenderWedgeProblem2):
            algorithm.variator = [ec.variators.uniform_crossover, problem.custom_gaussian_mutation]
        else:
            algorithm.variator = [ec.variators.uniform_crossover, ec.variators.gaussian_mutation] # no need to do custom mutator or crossover
        algorithm.selector = ec.selectors.tournament_selection

    elif algorithm == "pso":
        algorithm = swarm.PSO(rng)

    elif algorithm == "es":
        algorithm = ES(rng)

    algorithm.terminator = ec.terminators.generation_termination
    
    if not regeneration:
        algorithm.observer = [problem.custom_observer]

    # Generates a random plane
    generator = problem.generator
    evaluator = problem.evaluator

    if not regeneration:
        final_pop = algorithm.evolve(generator, evaluator, maximize=problem.maximize, bounder=problem.bounder, **args)
    else:
        args["num_evolution"] = 0
        for i in range(args["num_evolutions"]):
            args["fig_title"] = "Evolution n. " + str(args["num_evolution"]+1)
            print("\r --- Evolution n. " + str(args["num_evolution"]), end='')
            final_pop = algorithm.evolve(generator, evaluator, maximize=problem.maximize, **args)
            b, f = getBest(final_pop)
            if problem.is_feasible(f):
                problem.sliceAndApply(b[:problem.num_vars])
                problem.bestCuts = np.append(problem.bestCuts, np.array([b[:problem.num_vars]]), axis=0)
                problem.bestFit.append(f)
            args["num_evolution"] += 1
    print()
    return problem.bestFit

def runMultiExperiments(file_params):
    in_f = open(file_params)
    p = json.load(in_f)
    in_f.close()

    experiments = []
    for i in range(p["runs"]):
        print("\n --- Experiment ", i+1, " --- \n")
        fits = runExperiment(p["problemType"], p["targetMeshFilepath"], p["carvingMeshFilepath"],
                        p["algorithm"], p["regeneration"], p["seeds"][i], **p["args"])
        experiments.append(fits)
    
    out = json.dumps(experiments, indent=4)
    f = open(file_params[:-5]+"_results.json", mode='w')
    f.write(out)
    f.close()

runMultiExperiments(sys.argv[1])

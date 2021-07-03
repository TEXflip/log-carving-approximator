from pylab import *
import sys
import numpy as np

def plot_1D(axis, problem, x_limits) :
    dx = (x_limits[1] - x_limits[0])/200.0
    x = np.arange(x_limits[0], x_limits[1]+dx, dx)
    x = x.reshape(len(x),1)
    y = problem.evaluator(x, None)
    axis.plot(x,y,'-b')

def plot_2D(axis, problem, x_limits) :
    dx = (x_limits[1] - x_limits[0])/50.0
    x = np.arange(x_limits[0], x_limits[1]+dx, dx)
    z = np.asarray( [problem.evaluator([[i,j] for i in x], None) for j in x])
    return axis.contourf(x, x, z, 64, cmap=cm.hot_r)
    
def plot_results_1D(problem, individuals_1, fitnesses_1, 
                    individuals_2, fitnesses_2, title_1, title_2, args) :
    fig = figure(args["fig_title"] + ' (initial and final population)')
    ax1 = fig.add_subplot(2,1,1)
    ax1.plot(individuals_1, fitnesses_1, '.b', markersize=7)
    lim = max(np.array(list(map(abs,ax1.get_xlim()))))
    
    ax2 = fig.add_subplot(2,1,2)
    ax2.plot(individuals_2, fitnesses_2, '.b', markersize=7)
    lim = max([lim] + np.array(list(map(abs, ax2.get_xlim()))))

    ax1.set_xlim(-lim, lim)
    ax2.set_xlim(-lim, lim)

    plot_1D(ax1, problem, [-lim, lim])
    plot_1D(ax2, problem, [-lim, lim])
    
    ax1.set_ylabel('Fitness')
    ax2.set_ylabel('Fitness')
    ax1.set_title(title_1)
    ax2.set_title(title_2)

def plot_results_2D(problem, individuals_1, individuals_2, 
                    title_1, title_2, args) :
    fig = figure(args["fig_title"] + ' (initial and final population)')
    ax1 = fig.add_subplot(2,1,1, aspect='equal')
    ax1.plot(individuals_1[:,0], individuals_1[:,1], '.b', markersize=7)
    lim = max(np.array(list(map(abs,ax1.get_xlim()))) + np.array(list(map(abs,ax1.get_ylim()))))

    ax2 = fig.add_subplot(2,1,2, aspect='equal')
    ax2.plot(individuals_2[:,0], individuals_2[:,1], '.b', markersize=7)
    lim = max([lim] + 
              np.array(list(map(abs,ax2.get_xlim()))) +
              np.array(list(map(abs,ax2.get_ylim()))))

    ax1.set_xlim(-lim, lim)
    ax1.set_ylim(-lim, lim)
    ax1.set_title(title_1) 
    ax1.locator_params(nbins=5)
    
    ax2.set_xlim(-lim, lim)
    ax2.set_ylim(-lim, lim)
    ax2.set_title(title_2)    
    ax2.set_xlabel('x0')
    ax2.set_ylabel('x1')
    ax2.locator_params(nbins=5)
    
    plot_2D(ax1, problem, [-lim, lim])
    c = plot_2D(ax2, problem, [-lim, lim])
    fig.subplots_adjust(right=0.8)
    cax = fig.add_axes([0.85, 0.15, 0.05, 0.7])
    colorbar_ = colorbar(c, cax=cax)
    colorbar_.ax.set_ylabel('Fitness')

"""
    the original plot_observer
"""

import inspyred.ec.analysis

def plot_observer(population, num_generations, num_evaluations, args):
    """Plot the output of the evolutionary computation as a graph.
        
        This function plots the performance of the EC as a line graph
        using matplotlib and numpy. The graph consists of a blue line
        representing the best fitness, a green line representing the
        average fitness, and a red line representing the median fitness.
        It modifies the keyword arguments variable 'args' by including an
        entry called 'plot_data'.
        
        If this observer is used, the calling script should also import
        the matplotlib library and should end the script with::
        
        matplotlib.pyplot.show()
        
        Otherwise, the program may generate a runtime error.
        
        .. note::
        
        This function makes use of the matplotlib and numpy libraries.
        
        .. Arguments:
        population -- the population of Individuals
        num_generations -- the number of elapsed generations
        num_evaluations -- the number of candidate solution evaluations
        args -- a dictionary of keyword arguments
        
        """
    import matplotlib.pyplot as plt
    import numpy
    
    stats = inspyred.ec.analysis.fitness_statistics(population)
    best_fitness = stats['best']
    worst_fitness = stats['worst']
    median_fitness = stats['median']
    average_fitness = stats['mean']
    colors = ['black', 'blue', 'green', 'red']
    labels = ['average', 'median', 'best', 'worst']
    data = []
    if num_generations == 0:
        figure(args["fig_title"] + ' (fitness trend)')
        plt.ion()
        data = [[num_evaluations], [average_fitness], [median_fitness], [best_fitness], [worst_fitness]]
        lines = []
        for i in range(4):
            line, = plt.plot(data[0], data[i+1], color=colors[i], label=labels[i])
            lines.append(line)
        args['plot_data'] = data
        args['plot_lines'] = lines
        plt.xlabel('Evaluations')
        plt.ylabel('Fitness')
    else:
        data = args['plot_data']
        data[0].append(num_evaluations)
        data[1].append(average_fitness)
        data[2].append(median_fitness)
        data[3].append(best_fitness)
        data[4].append(worst_fitness)
        lines = args['plot_lines']
        for i, line in enumerate(lines):
            line.set_xdata(numpy.array(data[0]))
            line.set_ydata(numpy.array(data[i+1]))
        args['plot_data'] = data
        args['plot_lines'] = lines
    ymin = min([min(d) for d in data[1:]])
    ymax = max([max(d) for d in data[1:]])
    yrange = ymax - ymin
    plt.xlim((0, num_evaluations))
    plt.ylim((ymin - 0.1*yrange, ymax + 0.1*yrange))
    plt.draw()
    plt.pause(0.001)
    plt.legend()
    plt.show()

def initial_pop_observer(population, num_generations, num_evaluations, args):
    if num_generations == 0:
        args["initial_pop_storage"]["individuals"] = np.asarray([guy.candidate for guy in population]) 
        args["initial_pop_storage"]["fitnesses"] = np.asarray([guy.fitness for guy in population]) 
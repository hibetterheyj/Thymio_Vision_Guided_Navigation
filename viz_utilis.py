import matplotlib.pyplot as plt
import numpy
import time
import math
from matplotlib import colors

def coordinate_alignment(x_pos_est, y_pos_est, orient):
    if orient == 0:
        return x_pos_est, y_pos_est
    elif orient == math.pi/2:
        return y_pos_est, x_pos_est
    elif orient == pi:
        return [-est for est in x_pos_est], [-est for est in y_pos_est]
    elif orient == 3*pi/2 or orient == -pi/2:
        return y_pos_est, [-est for est in x_pos_est]

def orient_marker(orient):
    if orient == 0:
        return ">"
    elif orient == math.pi/2:
        return "^"
    elif orient == pi:
        return "<"
    elif orient == 3*pi/2 or orient == -pi/2:
        return "v"

def plot_est_result_xy(x_pos_est, y_pos_est, start, goal, orient, unit_dis=8):
    observed_len = len(x_pos_est)
    x_pos_est_plot = [x_pos_est[i][0] for i in range(observed_len)]
    y_pos_est_plot = [y_pos_est[i][0] for i in range(observed_len)]
    fig, ax = plt.subplots(figsize=(5,3),dpi=150)
    x_plot, y_plot = coordinate_alignment(x_pos_est_plot, y_pos_est_plot, orient)
    x_plot = [ele+start[0]*unit_dis for ele in x_plot]
    y_plot = [ele+start[1]*unit_dis for ele in y_plot]
    ax.plot(x_plot,y_plot,"g",linewidth=3,marker=orient_marker(orient),markersize=5, label="Estimated trajectory")
    ax.plot(start[0]*unit_dis,start[1]*unit_dis,"b",marker="o",markersize=5, label="Starting point")
    ax.plot(goal[0]*unit_dis,goal[1]*unit_dis,"y",marker="o",markersize=5, label="Ending point")
    ax.set_xlabel("Horizonal Estimated Position")
    ax.set_ylabel("Vertical Estimated Position")
    x_ticks = numpy.arange(start[0]-1, goal[0]+2) * unit_dis
    ax.set_xticks(x_ticks)
    y_ticks = numpy.arange(start[1]-1, goal[1]+2) * unit_dis
    ax.set_yticks(y_ticks)
    ax.set_yticklabels(y_ticks)
    ax.grid(True)
    ax.legend(loc='best')

"""
===========================================
====== For implementation without video ======
# show grid
#Plotting the grid
w, h = 10, 6
start = (2,0) # indicate by blue
goal = (4,3) # indicate by yellow
plot_curr_map(w, h, start, goal)

# show path
Example:
path = [(1, 0), (2, 0), (3, 0), (4, 0), (5, 0), (5, 1), (6, 1), (6, 2), (7, 2), (7, 3), (8, 3), (8, 4), (9, 4)]
#Creating the grid
w = 10
h = 6

# Basic
plotPathSW(path, w, h)

# Set experiment name and not save
experi_name="test"
plotPathSW(path, w, h, experi_name)

# Set experiment name and save with dpi=300
experi_name="test"
plotPathSW(path, w, h, experi_name, True)
"""

def create_empty(w,h):
    
    fig, ax = plt.subplots(figsize=(w,h))
    major_ticks = numpy.arange(0, w, 1)
    minor_ticks = numpy.arange(0, h, 1)
    ax.set_xticks(major_ticks)
    ax.set_yticks(minor_ticks)
    ax.grid(which='minor', alpha=0.5)
    ax.grid(which='major', alpha=0.5)
    ax.set_ylim([-0.5,h-0.5])
    ax.set_xlim([-0.5,w-0.5])
    ax.grid(True)
    
    return fig, ax

def plot_curr_map(w, h, start=None, goal=None):
    
    fig, ax = create_empty(w, h)
    data = numpy.ones((w, h))
    # Select the colors with which to display obstacles and free cells
    cmap = colors.ListedColormap(['white', "blue", "yellow", 'black'])  #
    for ii in range(w):
        if ii & 1 == 0: # row index is even
            for jj in range(h):
                data[ii][jj] = jj & 1
        elif ii & 1 == 1: # row index is odd
            for jj in range(h):
                data[ii][jj] = (jj-1) & 1
    if start != None:
        data[start[0]][start[1]] = 1/3
    if goal != None:  
        data[goal[0]][goal[1]] = 2/3

    # Converting the random values into occupied and free cells
    occupancy_grid = data.copy()

    # Displaying the map
    ax.imshow(occupancy_grid.transpose(), cmap=cmap)
    ax.set_title("Grid map")

def create_empty_plot_rect_normal(w, h, unit_dis=8):
    """
    Helper function to create a figure of the desired dimensions & grid
    
    :param max_val: dimension of the map along the x and y dimensions
    :return: the fig and ax objects.
    """
    fig, ax = plt.subplots(figsize=(8,8))
    x_ticks = numpy.arange(0, w+1)
    major_ticks = numpy.arange(0, w+1) * unit_dis
    ax.set_xticks(x_ticks)
    ax.set_xticklabels(major_ticks)
    y_ticks = numpy.arange(0, h+1)
    minor_ticks = numpy.arange(0, h+1) * unit_dis
    ax.set_yticks(y_ticks)
    ax.set_yticklabels(minor_ticks)
    ax.grid(which='minor', alpha=0.7)
    ax.grid(which='major', alpha=0.7)
    ax.set_xlim([-0.5,w+0.5])
    ax.set_ylim([-0.5,h+0.5])
    ax.set_xlabel("x (cm)")
    ax.set_ylabel("y (cm)")
    ax.grid(True)
    
    return fig, ax

def plotPathSW(path, w, h, experi_name=None, save_flag=False, unit_dis=8):
    fig, ax = create_empty_plot_rect_normal(w, h, unit_dis)
    # Creating the occupancy grid
    cmap = "gray_r"
    data = numpy.zeros((w, h)) # Create a grid of w x h random values

    path_grid = data.copy()
    step_num = len(path)
    level_num = step_num - 1
    start = 0.2
    end = 0.8
    for i in range(step_num):
        p = path[i]
        path_grid[p[0], p[1]] = start + i * (end-start)/level_num

    # Displaying the map
    ax.imshow(path_grid.transpose(), cmap=cmap)
    if save_flag:
        now = time.strftime("_%H_%M_%S")
        fig.savefig(experi_name+now+".png",dpi=300)

"""
===========================================
====== For implementation with video ======
Example:
path = [(9,2), (9,3), (9,4), (9,5), (9,6), (9,7), (9,8), (8,8), (8,9)]
#Creating the grid
w = 20
h = 12

# Basic
plotPath(path, w, h)

# Set experiment name and not save
experi_name="test"
plotPath(path, w, h, experi_name)

# Set experiment name and save with dpi=300
experi_name="test"
plotPath(path, w, h, experi_name, True)
"""

def create_empty_plot_rect(w, h):
    """
    Helper function to create a figure of the desired dimensions & grid
    
    :param max_val: dimension of the map along the x and y dimensions
    :return: the fig and ax objects.
    """
    fig, ax = plt.subplots(figsize=(8,8))
    y_ticks = numpy.arange(0, w+1)
    major_ticks = numpy.arange(w, -1, -1)
    ax.set_xticks(y_ticks)
    ax.set_xticklabels(major_ticks)
    x_ticks = numpy.arange(0, h+1)
    ax.set_yticks(x_ticks)
    ax.grid(which='minor', alpha=0.7)
    ax.grid(which='major', alpha=0.7)
    ax.set_ylim([-0.5,h+0.5])
    ax.set_xlim([-0.5,w+0.5])
    ax.set_xlabel("<- y")
    ax.set_ylabel("x")
    ax.grid(True)
    
    return fig, ax

def plotPath(path, w, h, experi_name=None, save_flag=False):
    fig, ax = create_empty_plot_rect(w, h)
    # Creating the occupancy grid
    cmap = "gray_r"
    data = numpy.zeros((w, h)) # Create a grid of w x h random values

    path_grid = data.copy()
    step_num = len(path)
    level_num = step_num - 1
    start = 0.2
    end = 0.8
    for i in range(step_num):
        p = path[i]
        path_grid[w-p[1], p[0]] = start + i * (end-start)/level_num

    # Displaying the map
    ax.imshow(path_grid.transpose(), cmap=cmap)
    if save_flag:
        now = time.strftime("_%H_%M_%S")
        fig.savefig(experi_name+now+".png",dpi=300)


"""
=======================================
====== plotPathOld is deprecated ======
# Basic
plotPathOld(path, w, h)

## for more cmap, please refer to https://matplotlib.org/tutorials/colors/colormaps.html
# plot with gray_r colormap
cmap_name = 'gray_r'
plotPathOld(path, w, h, True, cmap=plt.get_cmap(cmap_name))

# plot with Reds colormap
cmap_name = 'Reds'
plotPathOld(path, w, h, True, cmap=plt.get_cmap(cmap_name))
====== plotPathOld is deprecated ======
=======================================
"""
def plotPathOld(path, w, h, cmap_flag=False, cmap=None):
    fig, ax = create_empty_plot_rect(w, h)
    # Creating the occupancy grid
    if not(cmap_flag):
        cmap = colors.ListedColormap(['white', '#FFCCCC', 'pink', '#FF9999', '#FF6666','red']) # Select the colors with which to display obstacles and free cells
    else:
        cmap = cmap
    data = numpy.zeros((w, h)) # Create a grid of w x h random values

    path_grid = data.copy()
    step_num = len(path)
    level_num = step_num - 1
    start = 0.2
    end = 0.8
    for i in range(step_num):
        p = path[i]
        path_grid[w-p[1], p[0]] = start + i * (end-start)/level_num

    # Displaying the map
    ax.imshow(path_grid.transpose(), cmap=cmap)
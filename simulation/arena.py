from simulation.firefighter import Firefighter
from simulation.drone import Drone
from simulation.firetruck import FireTruck
from simulation.geometry import Rectangle, Point
from simulation.cell import *
import math
import random
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import enum
import itertools


class Arena():
    # init_fire is an array of 2-tuples specifying the initial cells which are
    # on fire: [(x1,y1), (x2,y2)].
    def __init__(self, init_fire_cells, num_agents=5,
                 network=None, show_plot=False, wind=(0, 0)):
        self.__width = 100  # m (1 km)
        self.__height = 100  # m (1 km) - each pixel is 1 m2
        self.__rectangle = Rectangle(0, 0, self.__width, self.__height)
        # Keeps track of the cells on fire, so that it doesn't have to check all of the cells in the grid on every iteration.
        # List of cell coordinates.
        self.__on_fire = []
        self.__wind = wind

        self.__agent_list = []
        self.__show_plot = show_plot

        if self.__show_plot:
            self.__fig = plt.figure()
            self.__ax = self.__fig.add_subplot(111, aspect='equal')
            self.__ax.set_autoscale_on(False)
            self.__ax.axis([0, self.__width, 0, self.__height])
        # The evolved network
        self.__net = network

        # Create grid - 2D array of Cell objects.
        # Coordinate system aligns with axes - bottom left is (0,0).
        self.__fire_grid = [[Cell((j, i)) for i in range(
            self.__width)] for j in range(self.__height)]

        # 'Start' fire at given coordinates
        self.initialise_fire(init_fire_cells)
        self.initialise_agents(num_agents)
        # For stochasticity
        random.seed()

        # Calculate effect of wind on spread of fire.
        # Populates dictionary 'self.__wind_spread_modifiers_by_offset', used
        # in Cell.update(...)
        self.calculate_wind_spread_prob_modifiers()

    def initialise_fire(self, init_fire_cells):
        for x, y in init_fire_cells:
            self.__fire_grid[x][y].set_state(CellState.ON_FIRE)
            self.__on_fire.append((x, y))

    def initialise_agents(self, num_agents: int, seed=42):
        random.seed(seed)
        for i in range(num_agents):
            position = self.__rectangle.random_point_int(seed)
            self.__agent_list.append(
                Firefighter(
                    self.__rectangle,
                    theta=random.uniform(
                        0,
                        2 * math.pi),
                    pos=position,
                    encoding=0))
            self.__fire_grid[position.x()][position.y()].add_one_agent()

    def add_trench(self, trench_coords):
        for x, y in trench_coords:
            self.__fire_grid[x][y].set_state(CellState.TRENCH)

    def extinguish(self, extinguish_coords):
        for x, y in extinguish_coords:
            if self.__fire_grid[x][y].get_state() == CellState.ON_FIRE:
                self.__fire_grid[x][y].set_state(CellState.BURNABLE)

    # For calculating the effect of wind on the spread of the fire.
    def calculate_wind_spread_prob_modifiers(self):
        # Normalise wind and convert to numpy vector (array).
        # TODO Temp - coordinates are backwards in current coordinate system -
        # have to swap elements.
        wind_np = np.array([self.__wind[1], self.__wind[0]])
        # Normalise
        wind_norm = np.linalg.norm(wind_np)
        if not wind_norm == 0:
            wind_np = wind_np / wind_norm

        # Initialise dictionary
        self.__wind_spread_modifiers_by_offset = {}

        # Calculate probability modifiers for each offset (e.g. N, E, S, W) depending on wind direction.
        # List 'neighbourhood' defined in simulation.cell.
        for offset in neighbourhood:
            # Alter transmission probability depending on direction of wind.
            offset_np = np.array(offset)
            # > 0 ==> wind in same direction; < 0 ==> wind in opposite direction.
            wind_modifier = np.dot(offset_np, wind_np)
            # Hyperbolic tangent has a range of -1 to 1.
            self.__wind_spread_modifiers_by_offset[offset] = math.tanh(
                wind_modifier)

    def image_from_pattern(self):
        coloured_pattern = np.ones(
            (self.__width, self.__height, 4), dtype=np.uint8) * 255

        for x, y in itertools.product(
                range(self.__width), range(self.__height)):
            fire_cell = self.__fire_grid[x][y]
            # Flipping to match coordinate axes in output image
            # TODO I don't fully understand the image coordinate system (doesn't seem
            # to match up with normal x and y) - should this be self.__width or
            # self.__height?
            x = (self.__width - 1) - x
            if fire_cell.get_state() == CellState.ON_FIRE:
                # yellow
                coloured_pattern[x, y, 2] = 0
            elif fire_cell.get_state() == CellState.BURNT_OUT:
                # black
                coloured_pattern[x, y, 0] = 50
                coloured_pattern[x, y, 1] = 50
                coloured_pattern[x, y, 2] = 50
            elif fire_cell.get_state() == CellState.BURNABLE:
                # colour green proportional to amount of fuel remaining
                coloured_pattern[x, y, 0] = 0
                coloured_pattern[x, y, 1] = 255 * \
                    fire_cell.get_remaining_fuel() / 100
                coloured_pattern[x, y, 2] = 0
            elif fire_cell.get_state() == CellState.TRENCH:
                # lilac
                coloured_pattern[x, y, 1] = 0

        img = Image.fromarray(coloured_pattern, mode="RGBA")
        return img

    def update(self):

        # Update agents
        # Gets populated during the iteration
        for agent in self.__agent_list:
            agent.update(self.__fire_grid, self.__net)

        # Update fire
        on_fire_next_itr = []
        for x, y in self.__on_fire:
            self.__fire_grid[x][y].update(
                self.__on_fire,
                on_fire_next_itr,
                self.__fire_grid,
                (self.__width,
                 self.__height),
                self.__wind_spread_modifiers_by_offset)
        self.__on_fire = on_fire_next_itr

    def get_fitness_function(self):
        num_fighters_alive = 0
        squares_on_fire = 0
        burnt_squares = 0
        untouched_squares = 0
        for agent in self.__agent_list:
            if agent.alive:
                num_fighters_alive = num_fighters_alive + 1

        for row in self.__fire_grid:
            for c in row:
                if c.get_state() == CellState.BURNT_OUT:
                    burnt_squares = burnt_squares + 1
                elif c.get_state() == CellState.ON_FIRE:
                    squares_on_fire = squares_on_fire + 1
                elif c.get_state() == CellState.BURNABLE:
                    untouched_squares = untouched_squares + 1

        return num_fighters_alive * 5 + untouched_squares - squares_on_fire - burnt_squares

    def plot(self):
        if self.__show_plot:
            self.__ax.cla()
            # flip x and y so that they are consistent with the representation
            y = [a.position().y() for a in self.__agent_list]
            x = [a.position().x() for a in self.__agent_list]
            colors = [a.color() for a in self.__agent_list]
            self.__ax.scatter(y, x, c=colors)
            self.__ax.axis([0, self.__width, 0, self.__height])
            self.__ax.imshow(
                self.image_from_pattern(), extent=(
                    self.__ax.axis()))
            plt.pause(0.03)


# Testing
if __name__ == "__main__":
    a = Arena()

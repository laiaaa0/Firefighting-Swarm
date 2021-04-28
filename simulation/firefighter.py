from simulation import agent
from simulation.geometry import Point, Rectangle
from simulation.cell import Cell, CellState
import enum 
import numpy as np

class Action(enum.Enum):
    EXTINGUISH=1
    TRENCH=2
    BURN=3
    MOVE=4
    NONE=5

class Direction(enum.Enum):
    NORTH = 1
    SOUTH = 2
    EAST = 3
    WEST = 4
    NONE = 5
    
    def __new__(cls, value):
        member = object.__new__(cls)
        member._value_ = value
        return member

    def __int__(self):
        return self.value

direction_list = np.array([[0,1],[0,-1],[1,0],[-1,0],[0,0]])
class Firefighter(agent.Agent):
    def __init__(
            self,
            arena: Rectangle,
            theta: float,
            pos: Point,
            encoding: int):
        speed = 5  # km/h
        speed = speed * 3600 / 1000  # m/s
        super().__init__(arena, speed, theta, pos, False, 0, encoding)
        self.direction = Direction.NONE
        self.alive = True

    def color(self):
        return [1, 0, 0]

    def agent_type(self):
        return agent.Type.FIGHTER


    def move(self,new_pos, pattern):
        #pattern[self._current_position.x(),self._current_position.y()][1] = pattern[self._current_position.x(),self._current_position.y()][1] -1
        self._current_position= new_pos
        #pattern[self._current_position.x(),self._current_position.y()][1] =  pattern[self._current_position.x(),self._current_position.y()][1] +1
    
    def do_action(self, dir:Direction, action, pattern):
        direction_value = direction_list[int(dir)-1]
        new_pos = self._current_position+Point(direction_value[0],direction_value[1])
        if self._arena_rect.contains(new_pos):
            if action == Action.EXTINGUISH:
                pattern[new_pos.x(),new_pos.y()] = 0
            elif action == Action.MOVE:
                self.move(new_pos,pattern)
            elif action == Action.TRENCH:
                pattern[new_pos.x(),new_pos.y()] = 2
            elif action == Action.BURN:
                pattern[new_pos.x(),new_pos.y()] = 1
            else:
                pass

    def get_network_input(self, pattern):
        directions = np.array([[-1,1],[0,1],[1,1],[-1,0],[0,0],[1,0],[-1,-1],[0,-1],[1,-1]], dtype=np.int8)
        positions = [int(self._current_position.x()), int(self._current_position.y())]+directions
        inputs = []
        for [posx,posy] in positions:
            if self._arena_rect.contains(Point(posx,posy)):
                inputs.append(pattern[posx][posy])
            else:
                inputs.append(0)

        return inputs

    def update(self, fire_grid):
        if self.alive:
            # select action and direction from network
            pass
            #self.do_action(Direction.NORTH, Action.MOVE, pattern)
        if fire_grid[self._current_position.x()][self._current_position.y()].get_state() == CellState.ON_FIRE:
            self.alive=False



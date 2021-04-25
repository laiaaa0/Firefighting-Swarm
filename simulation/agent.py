from simulation.geometry import Point, Rectangle
import math
import copy
import enum


class State(enum.Enum):
    GOING_TO_REFILL = 1
    GOING_TO_FIRE = 2
    ON_FIRE = 3

class Agent():
    def __init__(
            self,
            arena: Rectangle,
            speed: float,
            theta: float,
            pos: Point,
            can_be_on_fire: bool,
            max_capacity : int,
            encoding: str):
        self._base_speed = speed
        self._current_speed = speed
        self.__current_position = pos
        self._direction_theta = theta
        self.__arena_rect = arena
        self.__can_be_on_fire = can_be_on_fire
        self.__encoding = encoding
        self._max_capacity = max_capacity
        self.__water_tank_location = Point(400, 400)
        self._drop_rate = 17# Liters/m^2 (https://bedtimemath.org/fun-math-firefighting/)
        


    def position(self):
        return self.__current_position

    def rebound(self):
        self._direction_theta = self.__arena_rect.rebound(
            self.__current_position, self._direction_theta)

    def color(self):
        return [0, 0, 0]

    def index_in_grid(self, pos: Point):
        # position range from -width/2 to +width/2, -height/2 to +height/2
        # numpy range from 0 to width and from 0 to height
        width = self.__arena_rect.width()
        height = self.__arena_rect.height()
        transformed_position = pos + \
            Point(width / 2, height / 2)
        x = max(0, min(int(transformed_position.x()),
                       width - 1))
        y = max(0, min(int(transformed_position.y()),
                       height - 1))
        return (x, y)

    def go_to_refill(self):
        direction = self.__water_tank_location - self.position()
        if direction.norm() < 5:  # refill
            self._current_liters = self._max_capacity
        else:
            self._direction_theta = math.atan2(
                direction.y(), direction.x())
            self._current_speed = min(self._base_speed, direction.norm())


    def is_position_on_fire(self, pattern, pos):
        (index_x, index_y) = self.index_in_grid(pos)
        return pattern[index_x, index_y]

    def update(self, fire_pattern):
        new_pos = copy.copy(self.__current_position)
        new_pos.update(
            self._current_speed, self._direction_theta)

        if self.__can_be_on_fire or not self.is_position_on_fire(
                fire_pattern, new_pos):
            self.__current_position = new_pos

        else:
            if self._current_speed > 10:
                self._current_speed = self._current_speed / 2
            else:
                self._current_speed = 0  # stop at the fire boundary

        if not self.__arena_rect.contains(self.__current_position):
            self.rebound()

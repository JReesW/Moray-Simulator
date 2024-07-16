"""
Some handy maths functions
"""

import math


point = tuple[float, float]


def between(a: float, b: float, distance: float) -> float:
    """
    Return the number between number a and number b, at a given proportional distance.
    Distance closer to 0 is closer to a, distance closer to 1 is closer to b, distance 0.5 is exactly halfway
    """
    # TODO: don't use min(), it should always go from a to b instead of from the smaller one to the larger one
    _min = min(a, b)
    diff = abs(a - b)

    return _min + diff * distance


def between_points(a: point, b: point, distance: float) -> point:
    """
    Return the point between point a and point b, at a given proportional distance.
    Distance closer to 0 is closer to a, distance closer to 1 is closer to b, distance 0.5 is exactly halfway
    """
    ax, ay = a
    bx, by = b

    distance = math.dist(a, b) * distance
    angle = math.atan2(ay - by, ax - bx)
    return ax - (math.cos(angle) * distance), ay - (math.sin(angle) * distance)

"""
Some handy maths functions
"""

import math


point = tuple[float, float]
triangle = tuple[point, point, point]


def _x(p: point) -> float:
    """
    Return the X-component of a point
    """
    return p[0]


def _y(p: point) -> float:
    """
    Return the Y-component of a point
    """
    return p[1]


def sign(n: float) -> float:
    """
    Return the sign of a number. Returns 0 for 0
    """
    return 1 if n > 0 else -1 if n < 0 else 0


def clamp(n: float, _min: float, _max: float) -> float:
    """
    Clamp a given value between a given minimum and a given maximum
    """
    return max(min(n, _max), _min)


def between(a: float, b: float, distance: float) -> float:
    """
    Return the number between number a and number b, at a given proportional distance.
    Distance closer to 0 is closer to a, distance closer to 1 is closer to b, distance 0.5 is exactly halfway
    """
    diff = b - a
    return a + diff * distance


def between_points(a: point, b: point, distance: float) -> point:
    """
    Return the point between point a and point b, at a given proportional distance.
    Distance closer to 0 is closer to a, distance closer to 1 is closer to b, distance 0.5 is exactly halfway.
    """
    ax, ay = a
    bx, by = b

    distance = math.dist(a, b) * distance
    angle = math.atan2(ay - by, ax - bx)
    return ax - (math.cos(angle) * distance), ay - (math.sin(angle) * distance)


def is_numeric(s: str) -> bool:
    """
    Return whether the string is a valid float or not.
    Differs from str.isnumeric() by allowing a negative sign and decimal separator.
    """
    try:
        _ = float(s)
        return True
    except ValueError:
        return False


def point_in_triangle(p: point, t: triangle) -> bool:
    """
    Check whether a given point lies inside a given triangle

    https://stackoverflow.com/a/2049593
    """
    def _sign(p1: point, p2: point, p3: point):
        return (_x(p1) - _x(p3)) * (_y(p2) - _y(p3)) - (_x(p2) - _x(p3)) * (_y(p1) - _y(p3))

    v1, v2, v3 = t
    d1 = _sign(p, v1, v2)
    d2 = _sign(p, v2, v3)
    d3 = _sign(p, v3, v1)

    has_neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
    has_pos = (d1 > 0) or (d2 > 0) or (d3 > 0)

    return not (has_neg and has_pos)


def triangle_centroid(t: triangle) -> point:
    """
    Return the centroid of a given triangle
    """
    a, b, c = t
    return (_x(a) + _x(b) + _x(c)) / 3, (_y(a) + _y(b) + _y(c)) / 3

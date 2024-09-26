from simulator import Connection, Inspectable
from simulator.component import Component


class Pump(Component, Inspectable):
    def __init__(self, pos: (int, int) = (0, 0)):
        Component.__init__(self, (3, 3), [
            Connection("E", 1),
            Connection("W", 1)
        ], pos=pos)
        Inspectable.__init__(self, "Pump", "Voltage", "V", (300, 90))
        self.load_image("images/pump.png")

        self.direction = "E"
        self.opposite_direction = "W"

        self.circuit_pump = None

    def rotate(self, clockwise=True):
        Component.rotate(self, clockwise)

        cw = 1 if clockwise else -1
        self.direction = "NESW"[("NESW".index(self.direction) + cw) % 4]
        self.opposite_direction = "NESW"[("NESW".index(self.opposite_direction) + cw) % 4]

    def get_from_to(self):
        _from = next(c for c in self.connections if c.direction == self.opposite_direction)
        _to = next(c for c in self.connections if c.direction == self.direction)
        return _from, _to

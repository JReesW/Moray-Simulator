from simulator import Connection
from simulator.component import Component


class Pump(Component):
    def __init__(self, pos: (int, int) = (0, 0)):
        Component.__init__(self, (3, 3), [
            Connection("E", 1),
            Connection("W", 1)
        ], pos=pos)
        self.load_image("images/pump.png")

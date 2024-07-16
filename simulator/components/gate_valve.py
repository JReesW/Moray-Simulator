import simulator
from simulator import Connection
from simulator.component import Component


class GateValve(Component):
    def __init__(self, pos: (int, int) = (0, 0)):
        Component.__init__(self, (3, 3), [
            Connection("N", 1),
            Connection("S", 1)
        ], pos=pos)
        self.load_image("images/gatevalve.png")

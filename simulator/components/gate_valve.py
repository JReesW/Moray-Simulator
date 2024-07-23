from simulator import Connection, Inspectable
from simulator.component import Component


class GateValve(Component, Inspectable):
    def __init__(self, pos: (int, int) = (0, 0)):
        Component.__init__(self, (3, 3), [
            Connection("N", 1),
            Connection("S", 1)
        ], pos=pos)
        Inspectable.__init__(self, "Gate Valve", "Resistance", "Ω", (300, 90))
        self.load_image("images/gatevalve.png")

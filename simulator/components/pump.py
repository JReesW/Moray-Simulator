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

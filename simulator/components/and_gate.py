import simulator
from simulator import Connection
from simulator.component import Component


class AndGate(Component):
    def __init__(self, scene: "simulator.SimulationScene", tile_size: int, pos: (int, int) = (0, 0)):
        Component.__init__(self, scene, (3, 3), tile_size, [
            Connection("W", 0),
            Connection("W", 2),
            Connection("E", 1)
        ], pos=pos)
        self.load_image("images/andvalve.png")

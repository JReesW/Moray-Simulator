import pygame.image
from pygame import Surface, Rect
from pygame.sprite import Sprite

from engine.things import Draggable
from engine.grid import Grid


def components_list():
    return {
        "Gate Valve": GateValve,
        "Globe Valve": GlobeValve,
        "Ball Valve": BallValve,
        "Diaphragm": Diaphragm,
        "Three-Way Valve": ThreeWayValve,
        "Pump": Pump
    }


class Component(Draggable):
    def __init__(self,
                 dimensions: (int, int),
                 tile_size: int,
                 image: Surface = None,
                 rect: Rect = None,
                 pos: (int, int) = (0, 0)
                 ):
        Draggable.__init__(self, image, rect, pos)

        self.dim = dimensions
        self.w, self.h = tile_size * self.dim[0], tile_size * self.dim[1]
        self.tile_size = tile_size
        self.rect = Rect(*pos, self.w, self.h)

        # self.connections = []

    def load_image(self, path: str):
        """
        Load the component's image from its given path
        """
        self.image = pygame.transform.smoothscale(pygame.image.load(path), (self.w, self.h))

    def snap_to_grid(self, grid: Grid):
        """
        Snap this component to a snapping point on the grid
        """
        self.pos = grid.snap(self.pos, self.dim)

    def rotate(self, clockwise=True):
        """
        Rotate the component by a 90-degree rotation
        """
        self.image = pygame.transform.rotate(self.image, -90 if clockwise else 90)
        self.shadow.image = pygame.transform.rotate(self.shadow.image, -90 if clockwise else 90)

    def handle_events(self, events, **kwargs):
        super().handle_events(events, **kwargs)

        for event in events:
            if event.type == pygame.KEYDOWN:
                if self.held and event.key == pygame.K_r:
                    if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                        self.rotate(False)
                    else:
                        self.rotate()

    def update(self, camera, *args, **kwargs):
        Draggable.update(self, camera, *args, **kwargs)

        if "grid" in kwargs:
            self.snap_to_grid(kwargs["grid"])

    def kill(self):
        """
        Kill the component and its shadow
        """
        Sprite.kill(self)
        Sprite.kill(self.shadow)


class GateValve(Component):
    def __init__(self, tile_size: int, pos: (int, int) = (0, 0)):
        Component.__init__(self, (3, 3), tile_size, pos=pos)
        self.load_image("images/gatevalve.png")


class GlobeValve(Component):
    def __init__(self, tile_size: int, pos: (int, int) = (0, 0)):
        Component.__init__(self, (3, 3), tile_size, pos=pos)
        self.load_image("images/globevalve.png")


class BallValve(Component):
    def __init__(self, tile_size: int, pos: (int, int) = (0, 0)):
        Component.__init__(self, (3, 3), tile_size, pos=pos)
        self.load_image("images/ballvalve.png")


class Diaphragm(Component):
    def __init__(self, tile_size: int, pos: (int, int) = (0, 0)):
        Component.__init__(self, (3, 3), tile_size, pos=pos)
        self.load_image("images/diaphragm.png")


class ThreeWayValve(Component):
    def __init__(self, tile_size: int, pos: (int, int) = (0, 0)):
        Component.__init__(self, (3, 3), tile_size, pos=pos)
        self.load_image("images/threewayvalve.png")


class Pump(Component):
    def __init__(self, tile_size: int, pos: (int, int) = (0, 0)):
        Component.__init__(self, (3, 3), tile_size, pos=pos)
        self.load_image("images/pump.png")

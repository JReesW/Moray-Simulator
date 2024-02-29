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

        # self.shadow = None

        # self.connections = []
        # self.rotated = False

    def load_image(self, path: str):
        self.image = pygame.transform.smoothscale(pygame.image.load(path), (self.w, self.h))

    def snap_to_grid(self, grid: Grid):
        self.pos = grid.snap(self.pos, self.dim)

    def update(self, camera, *args, **kwargs):
        Draggable.update(self, camera, *args, **kwargs)

        if "grid" in kwargs:
            self.snap_to_grid(kwargs["grid"])

    def kill(self):
        Sprite.kill(self)
        Sprite.kill(self.shadow)


class GateValve(Component):
    def __init__(self, tile_size: int, pos: (int, int) = (0, 0)):
        Component.__init__(self, (3, 3), tile_size, pos=pos)
        self.load_image("images/gatevalve.png")
        self.rect = pygame.Rect(*pos, self.w, self.h)

        self.tile_size = tile_size


class GlobeValve(Component):
    def __init__(self, tile_size: int, pos: (int, int) = (0, 0)):
        Component.__init__(self, (3, 3), tile_size, pos=pos)
        self.load_image("images/globevalve.png")
        self.rect = pygame.Rect(*pos, self.w, self.h)

        self.tile_size = tile_size


class BallValve(Component):
    def __init__(self, tile_size: int, pos: (int, int) = (0, 0)):
        Component.__init__(self, (3, 3), tile_size, pos=pos)
        self.load_image("images/ballvalve.png")
        self.rect = pygame.Rect(*pos, self.w, self.h)

        self.tile_size = tile_size


class Diaphragm(Component):
    def __init__(self, tile_size: int, pos: (int, int) = (0, 0)):
        Component.__init__(self, (3, 3), tile_size, pos=pos)
        self.load_image("images/diaphragm.png")
        self.rect = pygame.Rect(*pos, self.w, self.h)

        self.tile_size = tile_size


class ThreeWayValve(Component):
    def __init__(self, tile_size: int, pos: (int, int) = (0, 0)):
        Component.__init__(self, (3, 3), tile_size, pos=pos)
        self.load_image("images/threewayvalve.png")
        self.rect = pygame.Rect(*pos, self.w, self.h)

        self.tile_size = tile_size


class Pump(Component):
    def __init__(self, tile_size: int, pos: (int, int) = (0, 0)):
        Component.__init__(self, (3, 3), tile_size, pos=pos)
        self.load_image("images/pump.png")
        self.rect = pygame.Rect(*pos, self.w, self.h)

        self.tile_size = tile_size

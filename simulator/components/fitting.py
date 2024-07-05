import pygame

import simulator
from simulator import Connection, Pipe
from simulator.component import Component

from engine.things import Draggable
from engine import colors


class Fitting(Component):
    def __init__(self, scene: "simulator.SimulationScene", pos: (int, int) = (0, 0)):
        Component.__init__(self, scene, (1, 1), [
            Connection("N", 0),
            Connection("E", 0),
            Connection("S", 0),
            Connection("W", 0)
        ], pos=pos)
        self.bg_image = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        pygame.draw.circle(self.bg_image, colors.black, (self.w / 2, self.h / 2), 2)
        self.image = self.bg_image.copy()

    def update(self, camera, *args, **kwargs):
        Draggable.update(self, camera, *args, **kwargs)

        self.image = self.bg_image.copy()

        if self.scene.components.has(self):
            if any([self.grid_overlap(comp) for comp in self.scene.floating_components if not isinstance(comp, Pipe)]):
                red = pygame.Surface(self.rect.size, pygame.SRCALPHA)
                red.fill((*colors.red, 75))
                self.image.blit(red, (0, 0))

        half_t = self.grid.tile_size // 2
        for connection in self.connections:
            if connection.connection is not None:
                if connection.direction == "N":
                    pygame.draw.line(self.image, colors.black, (half_t, 0), (half_t, half_t), 5)
                elif connection.direction == "E":
                    pygame.draw.line(self.image, colors.black, (self.w, half_t), (half_t, half_t), 5)
                elif connection.direction == "S":
                    pygame.draw.line(self.image, colors.black, (half_t, self.h), (half_t, half_t), 5)
                elif connection.direction == "W":
                    pygame.draw.line(self.image, colors.black, (0, half_t), (half_t, half_t), 5)
        self.shadow.reload()

        if "show_connectors" in kwargs and kwargs["show_connectors"]:
            conn_image = pygame.Surface(self.rect.size, pygame.SRCALPHA)
            for k, (coord, connected) in self.connector_coords().items():
                if connected and all([not isinstance(k.connection.connectable, t) for t in [Fitting, Pipe]]):
                    coord = coord[0] - self.snapped_rect.left, coord[1] - self.snapped_rect.top
                    pygame.draw.circle(conn_image, colors.lime, coord, 7, 3)
            self.image.blit(conn_image, (0, 0))

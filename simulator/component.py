import pygame.image
from pygame import Surface, Rect

from simulator import Connection, Connectable
from engine.things import Draggable
from engine import colors, director


class Component(Connectable):
    def __init__(self,
                 dimensions: (int, int),
                 connections: [Connection],
                 image: Surface = None,
                 rect: Rect = None,
                 pos: (int, int) = (0, 0)
                 ):
        Connectable.__init__(self, dimensions, image, rect, pos, connections)

        self.bg_image = None

        self.dim = dimensions
        t = director.scene.grid.tile_size
        self.w, self.h = t * self.dim[0], t * self.dim[1]
        self.rect = Rect(*pos, self.w, self.h)

    def load_image(self, path: str):
        """
        Load the component's image from its given path
        """
        self.bg_image = pygame.transform.smoothscale(pygame.image.load(path).convert_alpha(), (self.w, self.h))
        self.image = self.bg_image.copy()

    def rotate(self, clockwise=True):
        """
        Rotate the component by a 90-degree rotation
        """
        self.bg_image = pygame.transform.rotate(self.bg_image, -90 if clockwise else 90)
        self.shadow.image = pygame.transform.rotate(self.shadow.image, -90 if clockwise else 90)
        self.rotate_connections(clockwise)

    def handle_events(self, events, **kwargs):
        Draggable.handle_events(self, events, **kwargs)

        for event in events:
            if event.type == pygame.KEYDOWN:
                if self.held and event.key == pygame.K_r:
                    if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                        self.rotate(False)
                    else:
                        self.rotate()

    def update(self, camera, *args, **kwargs):
        Draggable.update(self, camera, *args, **kwargs)

        self.image = self.bg_image.copy()

        if director.scene.components.has(self):
            # Draw red if a dragging component is overlapping this component
            # TODO: maybe add back  if not isinstance(comp, Pipe)  at end of comprehension
            if any([self.grid_overlap(comp) for comp in director.scene.floating_components]):
                red = Surface(self.rect.size, pygame.SRCALPHA)
                red.fill((*colors.red, 75))
                self.image.blit(red, (0, 0))

        # Draw connectors
        if "show_connectors" in kwargs and kwargs["show_connectors"]:
            conn_image = Surface(self.rect.size, pygame.SRCALPHA)
            for k, (coord, connected) in self.connector_coords().items():
                color = colors.lime if connected or k in self.possible_connections else colors.dark_orange
                coord = coord[0] - self.snapped_rect.left, coord[1] - self.snapped_rect.top
                pygame.draw.circle(conn_image, color, coord, 7, 3)
            self.image.blit(conn_image, (0, 0))

        self.possible_connections = []

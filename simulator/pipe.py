import pygame

from engine import colors, debug
from engine.scene import Camera
from engine.things import Draggable, Shadow
from engine.maths import between

import simulator
from simulator.connectable import Connectable, Connection

import math


class PipeLayer:
    """
    Manages the placement of pipes
    """

    def __init__(self, scene: "simulator.SimulationScene"):
        self.scene = scene
        self.held = None

        self.count = 0

    def handle_events(self, events, camera: Camera):
        # Will only get called if the panel's mode is "pipe"

        mouse = pygame.mouse.get_pos()

        for event in events:
            if self.held is None and event.type == pygame.MOUSEBUTTONDOWN:
                gx, gy = self.scene.grid.tile_coord(camera.untranslate(mouse))
                self.held = Pipe(self, (gx, gy), (gx, gy))
                self.count += 1
                self.held.name = f"Pipe {self.count}"
                self.held.held = False
                pygame.sprite.Sprite.add(self.held, self.scene.pipes)
                pygame.sprite.Sprite.add(Shadow(self.held), self.scene.shadows)
                self.held.update_pipelaying()
            elif self.held is not None and event.type == pygame.MOUSEBUTTONUP:
                self.held.init_connections()
                self.held.on_drop()
                self.held = None

        if self.held is not None:
            gx, gy = self.scene.grid.tile_coord(camera.untranslate(mouse))

            # Pipes can only be 1 wide
            if abs(gx - self.held.begin[0]) > abs(gy - self.held.begin[1]):
                nx, ny = gx, self.held.begin[1]
            else:
                nx, ny = self.held.begin[0], gy

            if self.held.end != (nx, ny):
                self.held.end = (nx, ny)
                self.held.update_pipelaying()


class Pipe(Connectable):
    def __init__(self, pipelayer, begin, end):
        Connectable.__init__(
            self,
            (0, 0)
        )

        self.scene = pipelayer.scene
        self.pipelayer = pipelayer
        self.grid = self.scene.grid

        self.begin = begin
        self.end = end
        self.horizontal = False

        self.bg_image = None
        self.image = pygame.Surface((0, 0))
        self.rect = pygame.Rect(0, 0, 0, 0)

        self.node = None
        self.current = None

    def init_connections(self):
        """
        Create and set the pipe's connections once the pipelayer has finished creating this pipe
        """
        self.dimensions = self.dim
        if self.horizontal:
            self.connections = [Connection("W", 0), Connection("E", 0)]
        else:
            self.connections = [Connection("N", 0), Connection("S", 0)]

        for connection in self.connections:
            connection.connectable = self

    @property
    def dim(self):
        return abs(self.begin[0] - self.end[0]) + 1, abs(self.begin[1] - self.end[1]) + 1

    def calc_rect(self):
        t = self.grid.tile_size

        bx, by = self.grid.world_coord(self.begin)
        ex, ey = self.grid.world_coord(self.end)

        left, top = min(bx, ex), min(by, ey)
        right, bottom = max(bx, ex), max(by, ey)
        right, bottom = t + right, t + bottom
        w, h = abs(left - right), abs(top - bottom)

        return pygame.Rect(left, top, w, h)

    def handle_events(self, events, **kwargs):
        Draggable.handle_events(self, events, **kwargs)

        mouse = pygame.mouse.get_pos()
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_b:
                    if self.rect.collidepoint(*mouse):
                        print(self.dimensions)

    def update(self, camera, *args, **kwargs):
        if self.pipelayer.held is not self:
            Draggable.update(self, camera, *args, **kwargs)

        self.image = pygame.Surface(self.rect.size, pygame.SRCALPHA)

        if abs(self.begin[1] - self.end[1]) + 1 > 1:
            self.horizontal = False
        elif abs(self.begin[0] - self.end[0]) + 1 > 1:
            self.horizontal = True

        t = self.grid.tile_size
        mod1 = t // 2 if self.connections and self.connections[0].connection is None else 0
        mod2 = t // 2 if self.connections and self.connections[1].connection is None else 0
        if not self.horizontal:
            start_pos = (t // 2, mod1)
            end_pos = (t // 2, self.rect.height - mod2)
        else:
            start_pos = (mod1, t // 2)
            end_pos = (self.rect.width - mod2, t // 2)

        pygame.draw.line(self.image, colors.black, start_pos, end_pos, 3)

        self.shadow.reload(image=self.image)

        if "show_connectors" in kwargs and kwargs["show_connectors"]:
            conn_image = pygame.Surface(self.rect.size, pygame.SRCALPHA)
            for k, (coord, connected) in self.connector_coords().items():
                if connected and k.connection.connectable.__class__.__name__ not in ["Fitting", "Pipe"]:
                    coord = coord[0] - self.snapped_rect.left, coord[1] - self.snapped_rect.top
                    pygame.draw.circle(conn_image, colors.lime, coord, 7, 3)
            self.image.blit(conn_image, (0, 0))

        if "simulating" in kwargs and kwargs["simulating"]:
            if self.current is not None:
                speed_factor = max(5 - math.ceil((self.current.current / self.current.max_current) * 4), 1)
                frame_mod = 15 * 2 ** (speed_factor - 1)

                h = 0 if self.horizontal else 1
                length = abs(self.end[h] - self.begin[h]) + 1

                frame = kwargs["frame"] % frame_mod
                offsets = [t * (frame / frame_mod) + t * i for i in range(-1, length + 1)]

                ball = pygame.Surface((t // 2, t // 2), pygame.SRCALPHA)
                color = colors.alter(colors.dodger_blue, (self.current.current / self.current.max_current) / 2 + 0.5)
                pygame.draw.circle(ball, color, ball.get_rect().center, t // 4)
                pygame.draw.circle(ball, colors.black, ball.get_rect().center, t // 4, 1)

                for offset in offsets:
                    rect = ball.get_rect()
                    if self.horizontal:
                        if self.current.direction == "E":
                            rect.center = (offset, self.rect.height // 2)
                        else:
                            rect.center = (self.rect.width - offset, self.rect.height // 2)
                    else:
                        if self.current.direction == "S":
                            rect.center = (self.rect.width // 2, offset)
                        else:
                            rect.center = (self.rect.width // 2, self.rect.height - offset)
                    self.image.blit(ball, rect)

    def update_pipelaying(self):
        if self.begin[0] < self.end[0] or self.begin[1] < self.end[1]:
            begin = self.grid.world_coord(self.begin)
            end = self.grid.world_coord(self.end, corner="bottomright")
        else:
            begin = self.grid.world_coord(self.end)
            end = self.grid.world_coord(self.begin, corner="bottomright")

        w, h = abs(begin[0] - end[0]), abs(begin[1] - end[1])
        self.rect = pygame.Rect(*self.scene.camera.translate(begin), w, h)
        self.pos = self.scene.camera.untranslate(self.rect.center)

    def on_drop(self):
        Connectable.on_drop(self)

        w, h = abs(self.begin[0] - self.end[0]) + 1, abs(self.begin[1] - self.end[1]) + 1
        self.pos = self.grid.snap(self.pos, (w, h))

        d = self.grid.tile_size // 2

        left, top = self.scene.camera.untranslate(self.rect.topleft)
        right, bottom = self.scene.camera.untranslate(self.rect.bottomright)
        self.begin = self.grid.tile_coord((left + d, top + d))
        self.end = self.grid.tile_coord((right - d, bottom - d))

        self.shadow.reload(rect=self.rect)

    def __repr__(self):
        return f"Pipe {id(self)}"

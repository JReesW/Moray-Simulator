import pygame
# from pygame.sprite import Sprite

from engine import colors
from engine.scene import Camera
from engine.things import Draggable, Shadow

import simulator
from simulator.connectable import Connectable


class PipeLayer:
    """
    Manages the placement of pipes
    """

    def __init__(self, scene: "simulator.SimulationScene"):
        self.scene = scene
        self.held = None

    def handle_events(self, events, camera: Camera):
        # Will only get called if the panel's mode is "pipe"

        mouse = pygame.mouse.get_pos()

        for event in events:
            if self.held is None and event.type == pygame.MOUSEBUTTONDOWN:
                gx, gy = self.scene.grid.tile_coord(camera.untranslate(mouse))
                self.held = Pipe(self, (gx, gy), (gx, gy))
                self.held.held = False
                pygame.sprite.Sprite.add(self.held, self.scene.pipes)
                pygame.sprite.Sprite.add(Shadow(self.held), self.scene.shadows)
                self.held.update_image(camera)
            elif self.held is not None and event.type == pygame.MOUSEBUTTONUP:
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
                self.held.update_image(camera)


class Pipe(Draggable, Connectable):
    def __init__(self, pipelayer, begin, end):
        Draggable.__init__(
            self,
            pipelayer.scene,
            group=pipelayer.scene.pipes,
            float_group=pipelayer.scene.floating_components
        )
        Connectable.__init__(self, "")

        self.scene = pipelayer.scene
        self.pipelayer = pipelayer
        self.grid = self.scene.grid

        self.begin = begin
        self.end = end
        self.horizontal = False

        self.image = pygame.Surface((0, 0))
        self.rect = pygame.Rect(0, 0, 0, 0)

    def calc_rect(self):
        t = self.grid.tile_size

        bx, by = self.grid.world_coord(self.begin)
        ex, ey = self.grid.world_coord(self.end)

        left, top = min(bx, ex), min(by, ey)
        right, bottom = max(bx, ex), max(by, ey)
        right, bottom = t + right, t + bottom
        w, h = abs(left - right), abs(top - bottom)

        return pygame.Rect(left, top, w, h)

    def update(self, camera, *args, **kwargs):
        if self.pipelayer.held is not self:
            Draggable.update(self, camera, *args, **kwargs)

    def update_image(self, camera):
        if self.begin[0] < self.end[0] or self.begin[1] < self.end[1]:
            begin = self.grid.world_coord(self.begin)
            end = self.grid.world_coord(self.end, corner="bottomright")
        else:
            begin = self.grid.world_coord(self.end)
            end = self.grid.world_coord(self.begin, corner="bottomright")

        t = self.grid.tile_size
        w, h = abs(begin[0] - end[0]), abs(begin[1] - end[1])
        self.rect = pygame.Rect(*begin, w, h)
        self.pos = camera.translate(self.rect.center)

        self.image = pygame.Surface((w, h), pygame.SRCALPHA)

        # Draw a vertical line if the width is 1
        if abs(self.begin[0] - self.end[0]) + 1 == 1:
            self.horizontal = False
            pygame.draw.line(self.image, colors.black, (t // 2, t // 2), (t // 2, h - t // 2), 3)
        else:  # Otherwise a horizontal line
            self.horizontal = True
            pygame.draw.line(self.image, colors.black, (t // 2, t // 2), (w - t // 2, t // 2), 3)

        self.shadow.reload(rect=self.rect)

    def on_drop(self):
        if self.scene.panel.rect.collidepoint(*self.pos):
            self.kill()
            self.scene.audio.play_sound("delete")
        else:
            w, h = abs(self.begin[0] - self.end[0]) + 1, abs(self.begin[1] - self.end[1]) + 1
            self.pos = self.grid.snap(self.pos, (w, h))

            d = self.grid.tile_size // 2
            self.begin = self.grid.tile_coord((self.rect.left + d, self.rect.top + d))
            self.end = self.grid.tile_coord((self.rect.right - d, self.rect.bottom - d))

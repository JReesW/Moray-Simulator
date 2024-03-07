import pygame
# from pygame.sprite import Sprite

from engine import colors
from engine.scene import Camera
from engine.things import Draggable, Shadow

import simulator


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
                self.held = None

        # TODO: figure out why the shadow is jank during creation
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


class Pipe(Draggable):
    def __init__(self, pipelayer, begin, end):
        Draggable.__init__(
            self,
            pipelayer.scene,
            group=pipelayer.scene.pipes,
            float_group=pipelayer.scene.floating_components
        )
        self.pipelayer = pipelayer
        self.grid = self.pipelayer.scene.grid

        self.begin = begin
        self.end = end

        self.image = pygame.Surface((0, 0))
        self.rect = pygame.Rect(0, 0, 0, 0)
        # self.update_image()

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
        rect = self.calc_rect()
        if self.held:
            rect.center = camera.untranslate(pygame.mouse.get_pos())

        self.rect = pygame.Rect(*camera.translate(rect.topleft), *rect.size)

        if self.shadow is not None:
            offset = 8 if self.held else 3
            self.shadow.rect.center = camera.translate((rect.centerx + offset, rect.centery + offset))

    def update_image(self, camera):
        rect = self.calc_rect()
        t = self.grid.tile_size
        w, h = rect.size

        self.image = pygame.Surface((w, h), pygame.SRCALPHA)

        # Draw a vertical line if the width is 1
        if abs(self.begin[0] - self.end[0]) + 1 == 1:
            pygame.draw.line(self.image, colors.black, (t // 2, t // 2), (t // 2, h - t // 2), 3)
        else:  # Otherwise a horizontal line
            pygame.draw.line(self.image, colors.black, (t // 2, t // 2), (w - t // 2, t // 2), 3)

        self.shadow.reload(rect)

    def handle_events(self, events, panel=None, **kwargs):
        mouse = pygame.mouse.get_pos()

        for event in events:
            if event.type == pygame.MOUSEBUTTONUP and panel is not None:
                if panel.rect.collidepoint(*mouse):
                    self.kill()
                elif self.held:
                    w, h = abs(self.begin[0] - self.end[0]) + 1, abs(self.begin[1] - self.end[1]) + 1
                    dx = (self.grid.tile_size // 2) if w % 2 == 0 else 0
                    dy = (self.grid.tile_size // 2) if h % 2 == 0 else 0

                    drop_point = panel.scene.camera.untranslate(self.rect.center)
                    drop_point = drop_point[0] + dx, drop_point[1] + dy
                    gx, gy = self.grid.tile_coord(drop_point)

                    self.begin = gx - (w // 2), gy - (h // 2)
                    self.end = (gx + (w // 2) - (0 if w % 2 else 1),
                                gy + (h // 2) - (0 if h % 2 else 1))

        Draggable.handle_events(self, events, **kwargs)

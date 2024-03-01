import sys

import pygame
import pygame.freetype

from engine import colors, things
from engine.scene import Scene, Camera
from engine.grid import Grid

from simulator.panel import Panel


class SimulationScene(Scene):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # All the things in the scene
        self.components = pygame.sprite.Group()
        self.pipes = pygame.sprite.Group()
        self.shadows = pygame.sprite.Group()
        self.floating_components = pygame.sprite.Group()

        # The background grid, for lines and for snapping things
        self.grid = Grid(tile_size=20)

        # The control panel on the left side
        w, h = pygame.display.get_surface().get_size()
        self.panel = Panel(self, (w // 5) + 7.5, h)

        # The camera, for moving around the scene
        self.camera = Camera(
            pos=(0, 0),
            screen_size=(w, h)
        )

    def handle_events(self, events):
        mouse = pygame.mouse.get_pos()

        try:
            if self.panel.rect.collidepoint(*mouse):
                self.panel.handle_events(events)
            else:
                for thing in self.components:
                    thing.handle_events(events, groups=(self.floating_components, self.components), panel=self.panel)
            for thing in self.floating_components:
                thing.handle_events(events, groups=(self.floating_components, self.components), panel=self.panel)
        except things.IgnoreOtherThings:
            pass

        if pygame.key.get_pressed()[pygame.K_w]:
            self.camera.move(0, -6)
        if pygame.key.get_pressed()[pygame.K_a]:
            self.camera.move(-6, 0)
        if pygame.key.get_pressed()[pygame.K_s]:
            self.camera.move(0, 6)
        if pygame.key.get_pressed()[pygame.K_d]:
            self.camera.move(6, 0)

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    pygame.quit()
                    sys.exit()

    def update(self):
        self.panel.update()

        self.floating_components.update(self.camera)
        self.components.update(self.camera, grid=self.grid)
        self.shadows.update(self.camera)

    def render(self, surface: pygame.Surface, fonts: {str: pygame.freetype.SysFont}):
        surface.fill(colors.gainsboro)

        self.grid.render(surface, self.camera)

        self.shadows.draw(surface)
        self.components.draw(surface)

        self.panel.render(surface, fonts)

        self.floating_components.draw(surface)

    def add_component(self, comp):
        pygame.sprite.Sprite.add(comp, self.floating_components)
        pygame.sprite.Sprite.add(things.Shadow(comp), self.shadows)

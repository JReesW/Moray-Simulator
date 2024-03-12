import sys

import pygame
import pygame.freetype

from engine import colors, things
from engine.scene import Scene, Camera
from engine.grid import Grid

from simulator.panel import Panel
from simulator.pipe import PipeLayer


class SimulationScene(Scene):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # The background grid, for lines and for snapping things
        self.grid = Grid(tile_size=20)

        # All the things in the scene
        self.components = pygame.sprite.Group()
        self.pipelayer = PipeLayer(self)
        self.pipes = pygame.sprite.Group()
        self.shadows = pygame.sprite.Group()
        self.floating_components = pygame.sprite.Group()

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
            # If the mouse is on the panel, handle events there
            if self.panel.rect.collidepoint(*mouse):
                self.panel.handle_events(events)
            elif self.panel.mode == "cursor":
                # Otherwise handle components on the grid
                for component in self.components:
                    component.handle_events(events, self.panel)

                for pipe in self.pipes:
                    pipe.handle_events(events, self.panel)
            elif self.panel.mode == "pipe":
                self.pipelayer.handle_events(events, self.camera)
            # TODO: add component/pipe deleter mode
            # elif self.panel.mode == "delete":
            #     for component in self.components:
            #         if component.rect.collidepoint(*mouse):

            # Always handle floating components
            for component in self.floating_components:
                component.handle_events(events, self.panel)

        # When a thing has reacted to an input event, we stop other things from handling events
        except things.IgnoreOtherThings:
            pass

        # Move the camera with WASD
        if pygame.key.get_pressed()[pygame.K_w]:
            self.camera.move(0, -6)
        if pygame.key.get_pressed()[pygame.K_a]:
            self.camera.move(-6, 0)
        if pygame.key.get_pressed()[pygame.K_s]:
            self.camera.move(0, 6)
        if pygame.key.get_pressed()[pygame.K_d]:
            self.camera.move(6, 0)

        # Quit the game when pressing Ctrl + Q
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    pygame.quit()
                    sys.exit()

    def update(self):
        # Update the panel
        self.panel.update()

        # Update the sprite groups
        show_connectors = len(self.floating_components) > 0 or self.pipelayer.held is not None
        self.floating_components.update(self.camera, show_connectors=show_connectors)
        self.pipes.update(self.camera)
        self.components.update(self.camera, show_connectors=show_connectors)
        self.shadows.update(self.camera)

    def render(self, surface: pygame.Surface, fonts: {str: pygame.freetype.SysFont}):
        surface.fill(colors.gainsboro)

        self.grid.render(surface, self.camera)

        self.shadows.draw(surface)
        self.components.draw(surface)
        self.pipes.draw(surface)

        self.panel.render(surface, fonts)

        self.floating_components.draw(surface)

    def add_component(self, comp):
        pygame.sprite.Sprite.add(comp, self.floating_components)
        pygame.sprite.Sprite.add(things.Shadow(comp), self.shadows)

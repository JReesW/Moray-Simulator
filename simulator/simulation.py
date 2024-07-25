import sys

import pygame
import pygame.freetype

from engine import audio, colors, things, particle, debug
from engine.things import Group
from engine.scene import Scene, Camera
from engine.grid import Grid

from simulator.panel import Panel
from simulator.pipe import PipeLayer
from simulator.inspectable import Inspectable


class SimulationScene(Scene):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # The background grid, for lines and for snapping things
        self.grid = Grid(tile_size=20)

        # All the things in the scene
        self.components = Group()
        self.pipelayer = PipeLayer(self)
        self.pipes = Group()
        self.shadows = Group()
        self.floating_components = Group()

        # The control panel on the left side
        w, h = pygame.display.get_surface().get_size()
        self.panel = Panel(self, (w // 5) + 7.5, h)

        # The component inspector
        self.inspect_focus = None

        # The camera, for moving around the scene
        self.camera = Camera(
            pos=(0, 0),
            screen_size=(w, h)
        )
        self.audio = audio.AudioManager()
        self.audio.add_sound("pickup", "sounds/202313__7778__click-2.mp3")
        self.audio.add_sound("drop", "sounds/202314__7778__click-1.mp3")
        self.audio.add_sound("connect", "sounds/202312__7778__dbl-click.mp3")
        self.audio.add_sound("delete", "sounds/508597__drooler__crumple-06.ogg")

        self.conn_particles = particle.ParticleManager()

    def handle_events(self, events):
        mouse = pygame.mouse.get_pos()

        # debug.debug("Mouse screen", mouse)
        # debug.debug("Mouse world", self.camera.untranslate(mouse))
        # debug.debug("Mouse grid", self.grid.tile_coord(self.camera.untranslate(mouse)))

        try:
            self.panel.handle_events(events)

            if self.panel.mode == "cursor":
                # Otherwise handle components on the grid
                for component in self.components:
                    component.handle_events(events)

                for pipe in self.pipes:
                    pipe.handle_events(events)
            elif self.panel.mode == "pipe" and not self.panel.rect.collidepoint(*mouse):
                self.pipelayer.handle_events(events, self.camera)
            elif self.panel.mode == "inspect":
                if self.inspect_focus is not None:
                    self.inspect_focus.events(events)

            # Always handle floating components
            for component in self.floating_components:
                component.handle_events(events)

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
                elif event.key == pygame.K_p:
                    for pipe in self.pipes:
                        print(f"pos: {pipe.pos}")
                        print(f"rect: {pipe.rect}")
                        print(f"begin: {pipe.begin}")
                        print(f"end: {pipe.end}")
                elif event.key == pygame.K_BACKQUOTE:
                    if debug.is_active():
                        debug.disable()
                    else:
                        debug.enable()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.panel.mode == "inspect":
                    if self.inspect_focus is not None and self.inspect_focus.i_rect.collidepoint(*mouse):
                        continue

                    for component in self.components:
                        if isinstance(component, Inspectable):
                            if component.rect.collidepoint(*mouse):
                                self.inspect_focus = component
                                break
                    else:
                        self.inspect_focus = None

    def update(self):
        # Update the panel  - TODO: is this necessary?
        self.panel.update()

        debug.debug("components", self.components)
        debug.debug("pipes", self.pipes)

        self.components.early_update()

        # Update the sprite groups
        show_connectors = len(self.floating_components) > 0 or self.panel.mode == "pipe"
        self.floating_components.update(self.camera, show_connectors=show_connectors)
        self.pipes.update(self.camera, show_connectors=show_connectors)
        self.components.update(self.camera, show_connectors=show_connectors)
        self.shadows.update(self.camera)

        self.audio.execute()
        self.conn_particles.update()

    def render(self, surface: pygame.Surface):
        surface.fill(colors.gainsboro)

        self.grid.render(surface, self.camera)

        self.shadows.draw(surface)
        self.components.draw(surface)
        if self.panel.mode == "inspect" and self.inspect_focus is not None:
            self.draw_focus_border(surface)
        self.pipes.draw(surface)

        self.conn_particles.render(surface, self.camera)

        self.panel.render(surface)

        if self.panel.mode == "inspect" and self.inspect_focus is not None:
            self.inspect_focus.render(surface)

        self.floating_components.draw(surface)

    def add_component(self, comp):
        pygame.sprite.Sprite.add(comp, self.floating_components)
        pygame.sprite.Sprite.add(things.Shadow(comp), self.shadows)

    def draw_focus_border(self, surface: pygame.Surface):
        border_surf = pygame.Surface((20, 20), pygame.SRCALPHA)
        border_rect = border_surf.get_rect()
        points = (1, 1), (border_rect.w - 2, 1), (border_rect.w - 2, border_rect.h - 2), (1, border_rect.h - 2)
        pygame.draw.lines(border_surf, colors.orange, True, points, 1)
        pygame.draw.rect(border_surf, (0, 0, 0, 0), (6, 0, 8, 20))
        pygame.draw.rect(border_surf, (0, 0, 0, 0), (0, 6, 20, 8))
        scaled = pygame.transform.smoothscale(border_surf, self.inspect_focus.rect.size)
        surface.blit(scaled, self.inspect_focus.rect)

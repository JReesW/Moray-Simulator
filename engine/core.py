import sys
import ctypes
from typing import Type

import pygame
import pygame.freetype

from engine.scene import Director, Scene


class Game:
    def __init__(self, starting_scene: Type[Scene], *, starting_scene_args: dict = None, caption="A Pygame App"):
        if starting_scene_args is None:
            starting_scene_args = {}

        pygame.init()
        pygame.freetype.init()
        self.fonts = {
            "default": pygame.freetype.SysFont("Arial", 14),
            "bold": pygame.freetype.SysFont("Arial", 14, bold=True),
            "title": pygame.freetype.SysFont("Arial", 40, bold=True)
        }
        self.screen = pygame.display.set_mode((0, 0), pygame.RESIZABLE)
        pygame.display.set_caption(caption)
        self.clock = pygame.time.Clock()

        # https://stackoverflow.com/questions/2790825/how-can-i-maximize-a-specific-window-with-python
        # What about MacOS/Linux?
        user32 = ctypes.WinDLL('user32')
        h_wnd = user32.GetForegroundWindow()
        user32.ShowWindow(h_wnd, 3)

        self.director = Director()
        self.director.set_scene(starting_scene(**starting_scene_args))

    def frame(self):
        self.clock.tick(60)

        surface = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)

        events = pygame.event.get()

        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # Call the necessary scene functions of the active scene
        self.director.scene.handle_events(events)
        self.director.scene.update()
        self.director.scene.render(surface, self.fonts)

        self.screen.blit(surface, (0, 0))

        # Draw the surface to the screen
        pygame.display.flip()

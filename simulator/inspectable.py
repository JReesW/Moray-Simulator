"""
Everything to do with the inspection system.

Due to the limited scope of the project, some things are more "hardcoded" than you'd expect.
The only inspectable components are the Gate Valve, the Three-way Valve, and the Pump.
These all need at least a single numeric input box, for either resistance or pressure.
So for that reason, all inspectable components have a numeric input box with variable label (and unit probably).
"""


import pygame
from pygame import Surface, Rect

from engine import colors, text, ui, maths, debug


class Inspectable:
    """
    Parent class for components that can be inspected
    """

    def __init__(self, title: str, text_label: str, text_unit: str, rect_size: (int, int)):
        self.title = title
        self.text_label = text_label
        self.text_unit = text_unit
        self.text_value = 1

        # i_rect because components already have a property named rect
        self.i_rect = Rect(0, 0, *rect_size)
        screen_rect = pygame.display.get_surface().get_rect()
        self.i_rect.right, self.i_rect.top = screen_rect.right + 5, screen_rect.top - 5

        self.input = ui.Input(
            Rect(0, 0, 100, 30),
            self.input_change,
            default_text="1",
            allowed_chars=".-0123456789",
            validate=maths.is_numeric
        )

    def events(self, events):
        """
        Handle events, not named handle_events to prevent conflicts with Component etc
        """
        self.input.handle_events(events)

    def render(self, surface: Surface):
        debug.debug("rect", self.i_rect)

        # Background and border
        pygame.draw.rect(surface, colors.gainsboro, self.i_rect)
        pygame.draw.rect(surface, colors.dim_gray, self.i_rect, 4)

        # Title
        surf, rect = text.render(self.title, colors.black, "Arial", 24)
        rect.left, rect.top = self.i_rect.left + 15, self.i_rect.top + 15
        surface.blit(surf, rect)

        # Unit text
        surf, rect = text.render(self.text_unit, colors.black, "Arial", 16)
        rect.right = self.i_rect.right - 15

        # Input box
        self.input.rect.right, self.input.rect.top = rect.left - 10, self.i_rect.top + 45
        rect.centery = self.input.rect.centery

        surface.blit(surf, rect)
        self.input.render(surface)

        # Input label
        surf, rect = text.render(self.text_label, colors.black, "Arial", 16)
        rect.left, rect.centery = self.i_rect.left + 15, self.input.rect.centery
        surface.blit(surf, rect)

    def input_change(self):
        if maths.is_numeric(self.input.text) and self.input.text:
            self.text_value = float(self.input.text)

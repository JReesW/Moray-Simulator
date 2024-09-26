import pygame
from pygame import Surface, Rect

from engine import text, colors, maths

from simulator import Connection, Inspectable
from simulator.component import Component

from math import dist


class ThreewayValve(Component, Inspectable):
    def __init__(self, pos: (int, int) = (0, 0)):
        Component.__init__(self, (3, 3), [
            Connection("N", 1),
            Connection("S", 1),
            Connection("W", 1)
        ], pos=pos)
        Inspectable.__init__(self, "Three-way Valve", "Resistance", "Ω", (300, 250))
        self.load_image("images/threewayvalve.png")

        l, t = self.i_rect.left + 25, self.i_rect.top + 125
        self.triangles = {
            "N": ((l + 50, t + 50), (l + 17, t + 4), (l + 83, t + 4)),
            "E": ((l + 50, t + 50), (l + 96, t + 17), (l + 96, t + 83)),
            "S": ((l + 50, t + 50), (l + 17, t + 96), (l + 83, t + 96)),
            "W": ((l + 50, t + 50), (l + 4, t + 17), (l + 4, t + 83))
        }
        self.open_side = "N"

        self.slider_rect = Rect(l + 120, t + 40, 135, 20)
        self.blue_part = 0.5  # TODO: rename
        self.slider_dragging = False

        self.circuit_red_valve = None
        self.circuit_blue_valve = None

    def open_blue_red_connections(self) -> (Connection, Connection, Connection):
        """
        Return the open connection, the blue connection, and the red connection, in that order
        """
        sides = {conn.direction for conn in self.connections}
        one, two = [conn for conn in self.connections if conn.direction in sides and conn.direction != self.open_side]
        open_conn = [conn for conn in self.connections if conn.direction in sides and conn.direction == self.open_side]
        return open_conn[0], *sorted([one, two], key=lambda c: "NESW".index(c.direction))

    def rotate(self, clockwise=True):
        Component.rotate(self, clockwise)

        # Rotate the open side
        cw = 1 if clockwise else -1
        self.open_side = "NESW"[("NESW".index(self.open_side) + cw) % 4]

    def events(self, events):
        Inspectable.events(self, events)

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse = pygame.mouse.get_pos()

                # Open side selection
                sides = {conn.direction for conn in self.connections}
                for side, triangle in self.triangles.items():
                    if side in sides:
                        if maths.point_in_triangle(mouse, triangle):
                            self.open_side = side

                # Slider
                if self.slider_rect.collidepoint(*mouse):
                    self.slider_dragging = True
            elif event.type == pygame.MOUSEBUTTONUP:
                self.slider_dragging = False

    def update(self, camera, *args, **kwargs):
        Component.update(self, camera, *args, **kwargs)

        if self.slider_dragging:
            x = pygame.mouse.get_pos()[0]
            x = maths.clamp(x, self.slider_rect.left, self.slider_rect.right)
            d1 = self.slider_rect.right - self.slider_rect.left
            d2 = x - self.slider_rect.left
            # clamp to prevent division by zero errors
            self.blue_part = maths.clamp(d2 / d1, 0.01, 0.99)

    def render(self, surface: Surface):
        Inspectable.render(self, surface)

        # Text
        surf, rect = text.render("Select side without resistance", colors.black, "Arial", 18, bold=True)
        rect.left, rect.top = self.i_rect.left + 15, self.i_rect.top + 95
        surface.blit(surf, rect)

        # Three-way Valve image and open side visualisation
        image = pygame.transform.smoothscale(self.image, (100, 100))
        rect = image.get_rect()
        rect.topleft = self.i_rect.left + 25, self.i_rect.top + 125
        surface.blit(image, rect)
        pygame.draw.polygon(surface, colors.black, self.triangles[self.open_side])

        # Colors for closed sides
        sides = {conn.direction for conn in self.connections}
        blue, red = [side for side in self.triangles if side in sides and side != self.open_side]
        pygame.draw.circle(surface, colors.blue, maths.triangle_centroid(self.triangles[blue]), 5)
        pygame.draw.circle(surface, colors.red, maths.triangle_centroid(self.triangles[red]), 5)

        # Slider
        pygame.draw.line(surface, colors.black, self.slider_rect.midleft, self.slider_rect.midright, 3)
        pygame.draw.line(surface, colors.blue, self.slider_rect.topleft, self.slider_rect.bottomleft, 4)
        pygame.draw.line(surface, colors.red, self.slider_rect.topright, self.slider_rect.bottomright, 4)
        pygame.draw.circle(surface, colors.white, maths.between_points(self.slider_rect.midleft, self.slider_rect.midright, self.blue_part), 7)
        pygame.draw.circle(surface, colors.black, maths.between_points(self.slider_rect.midleft, self.slider_rect.midright, self.blue_part), 7, 2)

        # Slider text
        surf, rect = text.render("Divide resistance", colors.black, "Arial", 14, bold=True)
        rect.centerx, rect.bottom = self.slider_rect.centerx, self.slider_rect.top - 10
        surface.blit(surf, rect)

        surf, rect = text.render(f"{self.blue_part * self.text_value: .2f}{self.text_unit}", colors.black, "Arial", 14)
        rect.left, rect.top = self.slider_rect.left, self.slider_rect.bottom + 5
        surface.blit(surf, rect)

        surf, rect = text.render(f"{(1 - self.blue_part) * self.text_value: .2f}{self.text_unit}", colors.black, "Arial", 14)
        rect.right, rect.top = self.slider_rect.right, self.slider_rect.bottom + 5
        surface.blit(surf, rect)

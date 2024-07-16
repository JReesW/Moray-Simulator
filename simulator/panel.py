import pygame
from pygame import Rect, Surface
from pygame.event import Event

from engine import colors, text, director, maths, debug

from simulator.components import GateValve, ThreewayValve, Pump, Fitting


# Hard coded data
data = {
    "inspect": {
        "title": "Inspect",
        "description": "Click on components to\ninspect their properties"
    },
    "cursor": {
        "title": "Move components",
        "description": "Grab components to\nmove them around"
    },
    "pipe": {
        "title": "Draw pipes",
        "description": "Connect components by\ndragging pipes"
    },
    "components": [
        {
            "title": "Gate Valve",
            "description": "A simple resistor",
            "name": "gatevalve",
            "object": GateValve
        },
        {
            "title": "Three-way Valve",
            "description": "A resistor connecting ...",
            "name": "threewayvalve",
            "object": ThreewayValve
        },
        {
            "title": "Pump",
            "description": "Generates pressure",
            "name": "pump",
            "object": Pump
        },
        {
            "title": "Fitting",
            "description": "Used for turns and\nsplits in pipes",
            "name": "fitting",
            "object": Fitting
        }
    ]
}


class ModeSelector:
    """
    Handles the buttons that switch between editing modes
    """

    def __init__(self, panel: "Panel", rect: Rect):
        self.panel = panel
        self.rect = rect

        self.images = {
            name: pygame.image.load(f"images/{name}.png").convert_alpha()
            for name in ["inspect", "cursor", "pipe"]
        }
        self.button_rects = self.generate_button_rects()

    def generate_button_rects(self) -> {Rect}:
        """
        Prepares the rects of the settings buttons
        """
        buttons = ["inspect", "cursor", "pipe"]
        return {
            name: Rect(20, self.rect.top + i * (self.rect.h // 3), self.rect.w, self.rect.h // 3)
            for i, name in enumerate(buttons)
        }

    def click(self, pos: (int, int)):
        """
        Check if a click landed on one of the buttons
        """
        for name, rect in self.button_rects.items():
            if rect.collidepoint(*pos):
                self.panel.mode = name
                self.panel.redraw()

    def render(self, surface: Surface):
        """
        Draw the mode selector on the given surface
        """
        for i, (name, rect) in enumerate(self.button_rects.items()):
            # Mode logo
            size = rect.height - 10
            scaled = pygame.transform.smoothscale(self.images[name], (size, size))
            topleft = self.rect.left + 5, self.rect.top + 5 + (rect.height * i)
            surface.blit(scaled, topleft)

            # Title
            surf, _rect = text.render(data[name]["title"], colors.black, "Arial", 18, True)
            _rect.bottom, _rect.left = rect.centery - 5, self.rect.left + 15 + size
            surface.blit(surf, _rect)

            # Description
            for j, line in enumerate(data[name]["description"].splitlines()):
                surf, _rect = text.render(line, colors.dim_gray, "Arial", 12, True)
                _rect.top, _rect.left = rect.centery - 1 + j * 13, self.rect.left + 15 + size
                surface.blit(surf, _rect)

            # Border if this mode is selected
            if name == self.panel.mode:
                border_surf = Surface((rect.width // 3, rect.height // 3), pygame.SRCALPHA)
                border_rect = border_surf.get_rect()
                points = (1, 1), (border_rect.w - 2, 1), (border_rect.w - 2, border_rect.h - 2), (1, border_rect.h - 2)
                pygame.draw.lines(border_surf, colors.yellow, True, points, 1)
                scaled = pygame.transform.smoothscale(border_surf, rect.size)
                surface.blit(scaled, rect)

            # Dividing lines
            if name != "pipe":
                bottomright = rect.right - 1, rect.bottom
                pygame.draw.line(surface, colors.light_slate_gray, rect.bottomleft, bottomright, 1)


class ComponentSelector:
    def __init__(self, panel: "Panel", rect: Rect):
        self.panel = panel
        self.rect = rect

        self.images = {
            name: pygame.image.load(f"images/{name}.png").convert_alpha()
            for name in ["gatevalve", "threewayvalve", "pump", "fitting"]
        }
        self.button_rects = self.generate_button_rects()

    def generate_button_rects(self) -> {str: Rect}:
        """
        Prepares the rects of the component buttons
        """
        h = self.rect.h // 4
        rects = {}
        for i, comp in enumerate(data["components"]):
            rect = Rect(self.rect.left, self.rect.top + h * i, h, h)
            rects[comp["name"]] = rect
        return rects

    def click(self, pos: (int, int)):
        """
        Check if a click landed on one of the components
        """
        for comp in data["components"]:
            if self.button_rects[comp["name"]].collidepoint(*pos):
                # If a component is clicked, spawn a held component
                director.scene.add_component(comp["object"]())
                self.panel.mode = "cursor"
                self.panel.redraw()
                director.scene.audio.play_sound("pickup")

    def render(self, surface: Surface):
        """
        Draw the component selector on the given surface
        """
        for comp in data["components"]:
            rect = self.button_rects[comp["name"]]

            # Component image
            t = director.scene.grid.tile_size
            if comp["name"] == "fitting":
                scaled = pygame.transform.smoothscale(self.images[comp["name"]], (t, t))
            else:
                scaled = pygame.transform.smoothscale(self.images[comp["name"]], (3 * t, 3 * t))
            _rect = scaled.get_rect()
            _rect.center = rect.center
            surface.blit(scaled, _rect)

            # Title
            surf, _rect = text.render(comp["title"], colors.black, "Arial", 18, True)
            _rect.bottom, _rect.left = rect.centery - 5, rect.right + 15
            surface.blit(surf, _rect)

            # Description
            for j, line in enumerate(comp["description"].splitlines()):
                surf, _rect = text.render(line, colors.dim_gray, "Arial", 12, True)
                _rect.top, _rect.left = rect.centery - 1 + j * 13, rect.right + 15
                surface.blit(surf, _rect)


class Panel:
    def __init__(self, scene, w, h):
        self.scene = scene
        self.w, self.h = w, h
        self.rect = Rect(0, 0, w, h)
        self.out = True

        self.components = {}

        self.mode_selector = ModeSelector(self, Rect(20, 40, w - 40, (2 * h // 7)))
        self.mode = "inspect"
        self.component_selector = ComponentSelector(self, Rect(20, 80 + (2 * h // 7), w - 40, (3 * h // 8)))

        self.images = {
            name: pygame.image.load(f"images/{name}.png").convert_alpha() for name in ["close_panel", "open_panel"]
        }

        self.image = None

    def generate_button_rects(self) -> {Rect}:
        """
        Prepares the rects of the settings buttons
        """
        w = self.rect.w - 40
        return {name: Rect(20, 20 + (i * 20), w, 50) for i, name in enumerate(["inspect", "cursor", "pipe"])}

    def handle_events(self, events: [Event]) -> None:
        mouse = pygame.mouse.get_pos()

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                # If the expand/collapse bar is clicked
                if Rect(self.rect.right, 0, 30, 30).collidepoint(*mouse):
                    self.out = not self.out
                    if self.out:
                        self.rect.left = 0
                    else:
                        self.rect.left = -self.w

                if self.out:
                    self.mode_selector.click(mouse)
                    self.component_selector.click(mouse)

    def update(self):
        pass

    def redraw(self):
        surface = Surface(self.rect.size)

        # Render the panel background
        pygame.draw.rect(surface, colors.gainsboro, self.rect)
        x = self.rect.right - 2.5
        pygame.draw.line(surface, colors.dim_gray, (x, 26), (x, self.rect.bottom), 5)

        # Render the settings buttons
        surf, rect = text.render("Edit modes", colors.black, "Arial", 24)
        rect.left, rect.bottom = self.mode_selector.rect.left, self.mode_selector.rect.top - 5
        surface.blit(surf, rect)
        self.mode_selector.render(surface)

        # Render the components
        surf, rect = text.render("Components", colors.black, "Arial", 24)
        rect.left, rect.bottom = self.component_selector.rect.left, self.component_selector.rect.top
        surface.blit(surf, rect)
        self.component_selector.render(surface)

        between = maths.between(rect.top, self.mode_selector.rect.bottom, 0.4)
        pygame.draw.line(surface, colors.grey, (self.rect.left + 10, between), (self.rect.right - 15, between), 2)

        self.image = surface

    def render(self, surface: Surface):
        debug.debug("mode", self.mode)

        if self.image is None:
            self.redraw()

        # Extension button
        x = self.rect.right - 2.5
        surf = Surface((30, 30), pygame.SRCALPHA)
        surf.fill(colors.gainsboro)
        surface.blit(surf, (self.rect.right, 0))
        pygame.draw.line(surface, colors.dim_gray, (x, 28), (x + 32, 28), 5)
        pygame.draw.line(surface, colors.dim_gray, (x + 30, 30), (x + 30, 0), 5)

        surface.blit(self.images["close_panel" if self.out else "open_panel"], (self.rect.right + 5, 5))

        if self.out:
            surface.blit(self.image, (0, 0))

import pygame
from pygame import Rect, Surface
from pygame.event import Event
from pygame.freetype import Font

from engine import colors

from simulator.component import components_list


buttons = [
    "cursor",
    "pipe",
    *["button"] * 8
]


class Panel:
    def __init__(self, scene, w, h):
        self.scene = scene
        self.w, self.h = w, h
        self.rect = Rect(0, 0, w, h)
        self.out = True

        self.component_types = components_list()
        self.components = {}
        self.parse_components()
        self.component_rects = self.generate_component_rects()

        self.button_images = {b: (pygame.image.load(f"images/{b}.png").convert_alpha(),
                                  pygame.image.load(f"images/{b}pressed.png").convert_alpha()) for b in buttons}

        self.button_rects = self.generate_button_rects()
        self.mode = "cursor"

    def parse_components(self) -> None:
        """
        Set up basic instances of components for drawing
        """
        for comp in self.component_types:
            self.components[comp] = self.component_types[comp](self.scene, self.scene.grid.tile_size)

    def generate_component_rects(self) -> {str: Rect}:
        """
        Prepares the rects of the component creators
        """
        # TODO: generate the positions automatically
        return {
            "Gate Valve": Rect(20, 160, *self.components["Gate Valve"].rect.size),
            "Globe Valve": Rect(100, 160, *self.components["Globe Valve"].rect.size),
            "Ball Valve": Rect(180, 160, *self.components["Ball Valve"].rect.size),
            "Diaphragm": Rect(20, 270, *self.components["Diaphragm"].rect.size),
            "Three-Way Valve": Rect(100, 270, *self.components["Three-Way Valve"].rect.size),
            "Pump": Rect(180, 270, *self.components["Pump"].rect.size)
        }

    def generate_button_rects(self) -> [Rect]:
        """
        Prepares the rects of the settings buttons
        """
        w = (self.rect.w - 15) / 5
        return [Rect(w * (i % 5), w * (i // 5), w + 1, w) for i in range(10)]

    def handle_events(self, events: [Event]) -> None:
        mouse = pygame.mouse.get_pos()

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                # If the expand/collapse bar is clicked
                if Rect(self.rect.right - 15, 0, 15, self.rect.h).collidepoint(*mouse):
                    self.out = not self.out
                    if self.out:
                        self.rect.left = 0
                    else:
                        self.rect.left = -self.w + 15

                if self.out:
                    for i in range(10):
                        rect = self.button_rects[i]
                        if rect.collidepoint(*mouse):
                            self.mode = buttons[i]

                    # If one of the components is clicked, add said component to the scene
                    # TODO: Set up a global list of positions
                    for i, (name, comp) in enumerate(self.components.items()):
                        if self.component_rects[name].collidepoint(*mouse):
                            self.scene.add_component(self.component_types[name](self.scene, self.scene.grid.tile_size))
                            self.mode = "cursor"
                            self.scene.audio.play_sound("pickup")

    def update(self):
        pass

    def render(self, surface: Surface, fonts: [Font]):
        # Render the panel background and extension bar
        pygame.draw.rect(surface, colors.cornflower_blue, self.rect)
        pygame.draw.line(surface, colors.dark_slate_blue, (self.rect.right - 7.5, 0),
                         (self.rect.right - 7.5, self.rect.bottom), 15)
        surf, rect = fonts['bold'].render("VVV", colors.white)
        surf = pygame.transform.rotate(surf, 270 if self.out else 90)
        rect.w, rect.h = rect.h, rect.w
        rect.center = (self.rect.right - 7.5, self.rect.centery)
        surface.blit(surf, rect)

        # Render things on the panel if it is extended
        if self.out:
            # Render the settings buttons
            for i in range(10):
                image = self.button_images[buttons[i]][1 if buttons[i] == self.mode else 0]
                rect = self.button_rects[i].copy()
                rect.left = self.button_rects[i].left + self.rect.left
                surface.blit(pygame.transform.smoothscale(image, rect.size), rect)

            # Render the components
            for i, (name, comp) in enumerate(self.components.items()):
                surface.blit(comp.image, self.component_rects[name])
                comp_rect = self.component_rects[name]

                surf, rect = fonts['bold'].render(name, colors.black)
                rect.centerx = comp_rect.centerx
                rect.top = comp_rect.bottom + 15
                surface.blit(surf, rect)

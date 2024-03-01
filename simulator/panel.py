import pygame

from engine import colors

from simulator.component import components_list


class Panel:
    def __init__(self, scene, w, h):
        self.scene = scene
        self.w, self.h = w, h
        self.rect = pygame.Rect(0, 0, w, h)
        self.out = True

        self.component_types = components_list()
        self.components = {}
        self.parse_components()

    def parse_components(self):
        for comp in self.component_types:
            self.components[comp] = self.component_types[comp](self.scene.grid.tile_size)

    def handle_events(self, events):
        mouse = pygame.mouse.get_pos()

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if pygame.Rect(self.rect.right - 15, 0, 15, self.rect.h).collidepoint(*mouse):
                    self.out = not self.out

                for i, (name, comp) in enumerate(self.components.items()):
                    if pygame.Rect(20, 20 + (comp.rect.h + 30) * i, *comp.rect.size).collidepoint(*mouse):
                        self.scene.add_component(self.component_types[name](self.scene.grid.tile_size))

    def update(self):
        if self.out:
            self.rect.left = 0
        else:
            w, h = pygame.display.get_surface().get_size()
            self.rect.left = (-w // 5) + 7.5

    def render(self, surface: pygame.Surface, fonts):
        pygame.draw.rect(surface, colors.cornflower_blue, self.rect)
        pygame.draw.line(surface, colors.dark_slate_blue, (self.rect.right - 7.5, 0),
                         (self.rect.right - 7.5, self.rect.bottom), 15)
        surf, rect = fonts['bold'].render("VVV", colors.white)
        surf = pygame.transform.rotate(surf, 270 if self.out else 90)
        rect.w, rect.h = rect.h, rect.w
        rect.center = (self.rect.right - 7.5, self.rect.centery)
        surface.blit(surf, rect)

        for i, (name, comp) in enumerate(self.components.items()):
            surface.blit(comp.image, pygame.Rect(self.rect.left + 20, 20 + (comp.rect.h + 30) * i, *comp.rect.size))

            surf, rect = fonts['bold'].render(name, colors.black)
            rect.centerx = self.rect.left + comp.rect.centerx + 20
            rect.top = comp.rect.bottom + 25 + (comp.rect.h + 30) * i
            surface.blit(surf, rect)

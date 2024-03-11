import pygame.mouse
from pygame.sprite import Sprite, Group
from pygame import Surface, Rect
import pygame

from engine import colors
from engine.scene import Scene


class IgnoreOtherThings(Exception):
    """
    For stopping other things from handling events
    """


class Thing(Sprite):
    """
    The basic actor of a scene
    """

    def __init__(self, scene: Scene, image: Surface = None, rect: Rect = None, pos: (int, int) = (0, 0)):
        Sprite.__init__(self)

        self.scene = scene

        self.rect = rect if rect is not None else Rect(50, 50, 10, 10)
        self.pos = pos

        self.shadow = None

        if image is None:
            self.image = Surface(self.rect.size)
            self.image.fill(colors.red)
        else:
            self.image = image

    def handle_events(self, events, **kwargs):
        """
        Handle user input
        """
        pass

    def update(self, *args, **kwargs):
        """
        Update the image and the rect (and other properties if needed)
        """
        if self.shadow is not None:
            self.shadow.rect.center = (self.rect.centerx + 5, self.rect.centery + 5)

    def kill(self):
        """
        Kill the thing and its shadow
        """
        Sprite.kill(self)
        if self.shadow is not None:
            Sprite.kill(self.shadow)


class Draggable(Thing):
    """
    A thing that can be dragged using the mouse
    """

    def __init__(self, scene: Scene, image: Surface = None, rect: Rect = None, pos: (int, int) = (0, 0),
                 group: Group = None, float_group: Group = None):
        Thing.__init__(self, scene, image, rect, pos)

        # Whether the mouse is dragging the thing
        self.held = True

        self.group = group if group is not None else []
        self.float_group = float_group if float_group is not None else []

    def handle_events(self, events, **kwargs):
        mouse = pygame.mouse.get_pos()

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(*mouse):
                # Set __held to true if the mouse is clicking while on top of the thing
                self.held = True
                Sprite.add(self, self.float_group)
                Sprite.remove(self, self.group)
                raise IgnoreOtherThings
            elif self.held and event.type == pygame.MOUSEBUTTONUP:
                # Revert __held back to false if it was true and the mouse has been released
                self.held = False
                Sprite.add(self, self.group)
                Sprite.remove(self, self.float_group)

    def update(self, camera, *args, **kwargs):
        # Update mouse pos if the thing is being dragged
        if self.held:
            self.pos = camera.untranslate(pygame.mouse.get_pos())

        # Set the rect center by translating the world coords to screen coords
        self.rect.center = camera.translate(self.pos)

        if self.shadow is not None:
            offset = 8 if self.held else 3
            self.shadow.rect.center = (self.rect.centerx + offset, self.rect.centery + offset)

    def kill(self):
        Thing.kill(self)
        self.held = False


class Shadow(Sprite):
    """
    The shadow of a thing
    """

    def __init__(self, thing: Thing):
        Sprite.__init__(self)

        self.thing = thing
        self.thing.shadow = self

        self.image = None
        self.rect = None

        self.reload()

    def reload(self, image=None, rect=None):
        """
        Generate the shadow's image
        """
        if image is None:
            self.image = self.thing.image.copy()
        else:
            self.image = image.copy()
        self.image.fill((0, 0, 0, 78), None, pygame.BLEND_RGBA_MULT)

        if rect is None:
            self.rect = self.thing.rect.copy()
            self.rect.center = (self.thing.rect.centerx + 10, self.thing.rect.centery + 10)
        else:
            self.rect = rect

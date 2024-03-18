from typing import Any
import re

import pygame.draw

from engine.particle import Particle
from engine import colors


class Connectable:
    """
    Defines a thing's connections, one for each cardinal direction NESW
    """

    opposites = {
        'N': 'S',
        'S': 'N',
        'E': 'W',
        'W': 'E'
    }

    def __init__(self, open_sides: str, name: str = "---"):
        if not re.match(r"^(?!.*(.).*\1)[NESW]*$", open_sides):
            raise Exception("Invalid sides string given to Connectable. Only use one of each of NESW")

        self.connections: dict[str, Any] = {c: None for c in open_sides}
        self.name = name

    def rotate_connections(self, clockwise=True):
        """
        Rotate the connections.
        Removes all connections because only held components can rotate, but held components have no connections
        """
        cw = -1 if clockwise else 1
        self.connections = {"NESW"[i]: None for i in range(4) if "NESW"[(i + cw) % 4] in self.connections}

    def connect(self, other: "Connectable", connection: str):
        """
        Connect this connectable with a given connectable on a given connection.
        Will use the opposite connection on the other connectable.
        """
        # opposite = "NESW"[("NESW".index(connection) + 2) % 4]
        self.connections[connection] = other
        other.connections[self.opposites[connection]] = self

    def disconnect(self):
        """
        Disconnects this connectable from all of its connections
        """
        for c in "NESW":
            if c in self.connections and self.connections[c] is not None:
                self.connections[c].connections[self.opposites[c]] = None
                self.connections[c] = None


class ConnectionParticle(Particle):
    def __init__(self, pos: (int, int)):
        Particle.__init__(self, pos, 30)
        self.radius = 7
        self.width = 3

    def update(self):
        self.radius += 0.2
        self.width += 0.1

    def render(self, surface: pygame.Surface, camera):
        surf = pygame.Surface((self.radius*2, self.radius*2), pygame.SRCALPHA)
        alpha = 255 - int(255 * (self.age / self.lifespan))
        pygame.draw.circle(surf, colors.lime, (self.radius, self.radius), int(self.radius), int(self.width))
        surf.set_alpha(alpha)
        rect = surf.get_rect()
        rect.center = camera.translate(self.pos)
        surface.blit(surf, rect)

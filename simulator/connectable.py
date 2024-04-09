import pygame.draw

from engine.particle import Particle
from engine import colors


class Connection:
    """
    Describes a connection, pointing in a certain direction, placed on a certain offset
    """

    def __init__(self, direction: str, offset: int = 0):
        if len(direction) == 1 and direction in "NESW":
            self.direction = direction
        else:
            raise Exception("Direction given to Connection is not one character of \"NESW\"")
        self.offset = offset
        self.connectable = None  # The Connectable this connection is a part of
        self.connection = None  # The connection of another Connectable that this connectable is connected to

    def opposes(self, other: "Connection"):
        """
        Return whether this connection is opposing a given connection in direction only
        """
        return "NESW".index(self.direction) == "SWNE".index(other.direction)

    def connect(self, other: "Connection"):
        """
        Connect this connection with another given connection
        """
        self.connection = other
        other.connection = self

    def __hash__(self):
        return hash(f"{self.direction}{self.offset}")

    def __repr__(self):
        return f"{self.direction}{self.offset}"


class Connectable:
    """
    Allows a thing to have connections and to connect with others
    """

    def __init__(self, dimensions: (int, int), connections: [Connection], name=""):
        self.dimensions = dimensions
        self.connections = connections
        for connection in self.connections:
            connection.connectable = self
        self.possible_connections = []
        self.name = name

    def rotate_connections(self, clockwise=True):
        """
        Rotate the connections.
        """
        cw = 1 if clockwise else -1
        for connection in self.connections:
            connection.direction = "NESW"[("NESW".index(connection.direction) + cw) % 4]

    def flip_horizontally(self):
        """
        Flip the connections horizontally
        """
        for connection in self.connections:
            if connection.direction in "EW":
                connection.direction = "W" if connection.direction == "E" else "E"
            connection.offset = self.dimensions[0] - connection.offset - 1

    def flip_vertically(self):
        """
        Flip the connections vertically
        """
        for connection in self.connections:
            if connection.direction in "NS":
                connection.direction = "S" if connection.direction == "N" else "N"
            connection.offset = self.dimensions[1] - connection.offset - 1

    def disconnect(self):
        """
        Disconnect all of this connectable's connections
        """
        for connection in self.connections:
            # TODO: maybe rename some things lmao
            if connection.connection is not None:
                connection.connection.connection = None
                connection.connection = None

    def __repr__(self):
        res = "<\n"
        for connection in self.connections:
            res += f"    {str(connection)} ["
            if connection.connection is not None:
                res += f"{connection.connection.connectable.name}: {connection.connection}"
            res += "]\n"
        res += ">"
        return res

    def draw(self):
        # For fun
        c = {d: [cn.offset for cn in self.connections if cn.direction == d] for d in "NESW"}
        w, h = self.dimensions
        res = f"┌{'┬'.join(['───'] * w)}┐\n"
        for y in range(h):
            if y > 0:
                res += f"├{'┼'.join(['───'] * w)}┤\n"
            res += f"│{'│'.join([f' {'↑' if x in c['N'] and y == 0 else ' '} ' for x in range(w)])}│\n"
            res += f"│{'│'.join([f'{'←' if (h - y - 1) in c['W'] and x == 0 else ' '} {'→' if y in c['E'] and x == w-1 else ' '}' for x in range(w)])}│\n"
            res += f"│{'│'.join([f' {'↓' if (w - x - 1) in c['S'] and y == h-1 else ' '} ' for x in range(w)])}│\n"

        res += f"└{'┴'.join(['───'] * w)}┘\n"
        return res


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


if __name__ == '__main__':
    A = Connectable((3, 3), [
        Connection('N', 0),
        Connection('N', 1),
        Connection('E', 0),
        Connection('E', 2),
        Connection('S', 1),
        Connection('W', 2),
    ], name="A")
    B = Connectable((3, 3), [
        Connection('S', 2)
    ], name="B")
    A.connections[0].connect(B.connections[0])
    print(A)
    print(A.draw())

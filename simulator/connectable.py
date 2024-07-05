import pygame.draw

from engine.things import Draggable
from engine.particle import Particle
from engine import colors, debug
import simulator

from math import dist


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


class Connectable(Draggable):
    """
    Allows a thing to have connections and to connect with others
    """

    def __init__(self, scene: "simulator.SimulationScene", dimensions: (int, int), image=None, rect=None, pos=None, connections: [Connection] = None, name=""):
        Draggable.__init__(self, scene, image, rect, pos, scene.components, scene.floating_components)

        self.dimensions = dimensions
        if connections is not None:
            self.connections = connections
            for connection in self.connections:
                connection.connectable = self
        else:
            self.connections = []
        self.possible_connections = []
        self.name = name  # TODO: remove name, or utilize it
        self.scene = scene
        self.grid = scene.grid

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

    def on_connect(self):
        """
        Called when being connected to something that got dropped
        """
        # TODO: probably delete this function
        pass

    def disconnect(self):
        """
        Disconnect all of this connectable's connections
        """
        for connection in self.connections:
            # if this connection is connected to another
            if connection.connection is not None:
                # remove the connection on both sides, first the other, then self
                connection.connection.connection = None
                connection.connection = None

    @property
    def snapped_rect(self):
        """
        Return the rect of this object were it snapped to the grid
        """
        snapped_rect = self.rect.copy()
        snapped_rect.center = self.grid.snap(self.pos, self.dimensions)
        return snapped_rect

    def connector_coords(self) -> {Connection: ((int, int), bool)}:
        """
        Get world coords of the component's connections, alongside bools whether they are connected or not
        """
        res = {}
        t = self.grid.tile_size
        for connection in self.connections:
            if connection.direction == "N":
                pos = (self.snapped_rect.left + t * connection.offset + t // 2, self.snapped_rect.top)
            elif connection.direction == "S":
                pos = (self.snapped_rect.right - t * connection.offset - t // 2, self.snapped_rect.bottom)
            elif connection.direction == "E":
                pos = (self.snapped_rect.right, self.snapped_rect.top + t * connection.offset + t // 2)
            else:  # if connection.direction == "W"
                pos = (self.snapped_rect.left, self.snapped_rect.bottom - t * connection.offset - t // 2)
            res[connection] = (pos, connection.connection is not None)
        return res

    def get_touching_side(self, other: "Connectable") -> str:
        """
        Checks whether the middles of two components are touching based on their grid coordinates.
        Returns the touching side, or None if they don't connect
        """
        half_t = self.grid.tile_size // 2
        w, h = self.dimensions

        # Get tile coords of the top-left corners
        ax, ay = self.grid.tile_coord((self.snapped_rect.left + half_t, self.snapped_rect.top + half_t))
        bx, by = self.grid.tile_coord((other.snapped_rect.left + half_t, other.snapped_rect.top + half_t))

        # Create a tile coord rect of B
        rect_b = pygame.Rect(bx, by, *other.dimensions)

        if rect_b.colliderect((ax, ay, w+1, h)):
            return "E"
        elif rect_b.colliderect((ax, ay, w, h+1)):
            return "S"
        elif rect_b.colliderect((ax-1, ay, w, h)):
            return "W"
        elif rect_b.colliderect((ax, ay-1, w, h)):
            return "N"

    def get_connections_on_side(self, other: "Connectable", side: str) -> {Connection: Connection}:
        """
        Return a dict of connections that connect to the connections of a given component
        """
        res = {}
        coords_a = self.connector_coords()
        coords_b = other.connector_coords()
        for a in self.connections:
            if a.direction == side:
                for b in other.connections:
                    if a.opposes(b) and dist(coords_a[a][0], coords_b[b][0]) < self.grid.tile_size // 2:
                        res[a] = b
        return res

    def grid_overlap(self, other: "Connectable"):
        """
        Return whether this component overlaps another on the grid
        """
        # Take this object's Rect as if it were snapped to the grid
        rect = pygame.Rect(0, 0, *self.rect.size)
        rect.center = self.grid.snap(self.pos, self.dimensions)

        # Take the other object's Rect as if it were snapped to the grid
        other_rect = pygame.Rect(0, 0, *other.rect.size)
        other_rect.center = self.grid.snap(other.pos, other.dimensions)

        # Check if they would collide, were they snapped to the grid
        return rect.colliderect(other_rect)

    def early_update(self, *args, **kwargs):
        if self.scene.components.has(self):
            for comp in self.scene.floating_components:
                if touching := self.get_touching_side(comp):
                    for a, b in self.get_connections_on_side(comp, touching).items():
                        self.possible_connections.append(a)
                        comp.possible_connections.append(b)

    def on_drop(self):
        if self.scene.panel.rect.collidepoint(*self.scene.camera.translate(self.pos)):
            self.kill()
            self.scene.audio.play_sound("delete")
        else:
            colliding = any([self.grid_overlap(comp) for comp in self.scene.components if self is not comp])

            if not colliding:
                # Snap the component to the grid
                self.pos = self.grid.snap(self.pos, self.dimensions)
            else:
                # Snap the component back to the last valid spot, or kill it if there is none
                if self.prev_pos is None:
                    self.kill()
                    return
                else:
                    self.pos = self.prev_pos

            connection_made = False
            for comp in [*self.scene.components, *self.scene.pipes]:
                if comp is not self and (side := self.get_touching_side(comp)):
                    for a, b in self.get_connections_on_side(comp, side).items():
                        a.connect(b)
                        connection_made = True

            if connection_made:
                for pos, b in self.connector_coords().values():
                    if b:
                        self.scene.conn_particles.add(simulator.connectable.ConnectionParticle(pos))
                self.scene.audio.play_sound("connect")
            else:
                self.scene.audio.play_sound("drop")

    def on_pickup(self):
        self.disconnect()
        self.scene.audio.play_sound("pickup")


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

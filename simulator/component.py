import pygame.image
from pygame import Surface, Rect

import simulator
from simulator import Connection, Connectable, Pipe
from engine.things import Draggable
from engine.grid import Grid
from engine import colors

from math import dist


def components_list():
    return {
        "Gate Valve": GateValve,
        "Globe Valve": GlobeValve,
        "Ball Valve": BallValve,
        "Diaphragm": Diaphragm,
        "Three-Way Valve": ThreeWayValve,
        "Pump": Pump,
        "Fourway Valve": FourwayValve,
        "And Valve": AndValve
    }


class Component(Draggable, Connectable):
    def __init__(self,
                 scene: "simulator.SimulationScene",
                 dimensions: (int, int),
                 tile_size: int,
                 connections: [Connection],
                 image: Surface = None,
                 rect: Rect = None,
                 pos: (int, int) = (0, 0)
                 ):
        Draggable.__init__(self, scene, image, rect, pos, scene.components, scene.floating_components)
        Connectable.__init__(self, dimensions, connections)

        self.bg_image = None
        self.dim = dimensions
        self.w, self.h = tile_size * self.dim[0], tile_size * self.dim[1]
        self.tile_size = tile_size
        self.rect = Rect(*pos, self.w, self.h)

        # TODO: perhaps remove scene from Thing, as this might be the only need for it atm
        self.scene = scene
        self.grid = scene.grid

    def load_image(self, path: str):
        """
        Load the component's image from its given path
        """
        self.bg_image = pygame.transform.smoothscale(pygame.image.load(path).convert_alpha(), (self.w, self.h))
        self.image = self.bg_image.copy()

    @property
    def snapped_rect(self):
        snapped_rect = self.rect.copy()
        snapped_rect.center = self.grid.snap(self.pos, self.dim)
        return snapped_rect

    def grid_overlap(self, other: "Component"):
        """
        Return whether this component overlaps another on the grid
        """
        rect = Rect(0, 0, *self.dim)
        rect.center = self.grid.tile_coord(self.pos)
        other_rect = Rect(0, 0, *other.dim)
        other_rect.center = self.grid.tile_coord(other.pos)
        return rect.colliderect(other_rect)

    def get_touching_side(self, other: "Component | Pipe") -> str:
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

    def get_connections_on_side(self, other: "Component", side: str) -> {Connection: Connection}:
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

    def rotate(self, clockwise=True):
        """
        Rotate the component by a 90-degree rotation
        """
        self.bg_image = pygame.transform.rotate(self.bg_image, -90 if clockwise else 90)
        self.shadow.image = pygame.transform.rotate(self.shadow.image, -90 if clockwise else 90)
        self.rotate_connections(clockwise)

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

    def on_drop(self):
        if self.scene.panel.rect.collidepoint(*self.pos):
            self.kill()
            self.scene.audio.play_sound("delete")
        else:
            colliding = any([self.grid_overlap(comp) for comp in self.scene.components if self is not comp])

            if not colliding:
                # Snap the component to the grid
                self.pos = self.grid.snap(self.pos, self.dim)
            else:
                # Snap the component back to the last valid spot, or kill it if there is none
                if self.prev_pos is None:
                    self.kill()
                    return
                else:
                    self.pos = self.prev_pos

            connection_made = False
            # TODO: Connections for pipes
            for comp in [*self.scene.components]:  # , *self.scene.pipes]:
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

    def handle_events(self, events, **kwargs):
        Draggable.handle_events(self, events, **kwargs)

        for event in events:
            if event.type == pygame.KEYDOWN:
                if self.held and event.key == pygame.K_r:
                    if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                        self.rotate(False)
                    else:
                        self.rotate()

    def early_update(self, *args, **kwargs):
        if self.scene.components.has(self):
            for comp in self.scene.floating_components:
                if not isinstance(comp, Pipe) and (touching := self.get_touching_side(comp)):
                    for a, b in self.get_connections_on_side(comp, touching).items():
                        self.possible_connections.append(a)
                        comp.possible_connections.append(b)

    def update(self, camera, *args, **kwargs):
        Draggable.update(self, camera, *args, **kwargs)

        self.image = self.bg_image.copy()

        if self.scene.components.has(self):
            # Draw red if a dragging component is overlapping this component
            if any([self.grid_overlap(comp) for comp in self.scene.floating_components if not isinstance(comp, Pipe)]):
                red = Surface(self.rect.size, pygame.SRCALPHA)
                red.fill((*colors.red, 75))
                self.image.blit(red, (0, 0))

        # Draw connectors
        if "show_connectors" in kwargs and kwargs["show_connectors"]:
            conn_image = Surface(self.rect.size, pygame.SRCALPHA)
            for k, (coord, connected) in self.connector_coords().items():
                color = colors.lime if connected or k in self.possible_connections else colors.dark_orange
                coord = coord[0] - self.snapped_rect.left, coord[1] - self.snapped_rect.top
                pygame.draw.circle(conn_image, color, coord, 7, 3)
            self.image.blit(conn_image, (0, 0))

        self.possible_connections = []


# TODO: Move these to their own files
class GateValve(Component):
    def __init__(self, scene: "simulator.SimulationScene", tile_size: int, pos: (int, int) = (0, 0)):
        Component.__init__(self, scene, (3, 3), tile_size, [
            Connection("N", 1),
            Connection("S", 1)
        ], pos=pos)
        self.load_image("images/gatevalve.png")


class GlobeValve(Component):
    def __init__(self, scene: "simulator.SimulationScene", tile_size: int, pos: (int, int) = (0, 0)):
        Component.__init__(self, scene, (3, 3), tile_size, [
            Connection("N", 1),
            Connection("S", 1)
        ], pos=pos)
        self.load_image("images/globevalve.png")


class BallValve(Component):
    def __init__(self, scene: "simulator.SimulationScene", tile_size: int, pos: (int, int) = (0, 0)):
        Component.__init__(self, scene, (3, 3), tile_size, [
            Connection("N", 1),
            Connection("S", 1)
        ], pos=pos)
        self.load_image("images/ballvalve.png")


class Diaphragm(Component):
    def __init__(self, scene: "simulator.SimulationScene", tile_size: int, pos: (int, int) = (0, 0)):
        Component.__init__(self, scene, (3, 3), tile_size, [
            Connection("N", 1),
            Connection("S", 1)
        ], pos=pos)
        self.load_image("images/diaphragm.png")


class ThreeWayValve(Component):
    def __init__(self, scene: "simulator.SimulationScene", tile_size: int, pos: (int, int) = (0, 0)):
        Component.__init__(self, scene, (3, 3), tile_size, [
            Connection("N", 1),
            Connection("S", 1),
            Connection("W", 1)
        ], pos=pos)
        self.load_image("images/threewayvalve.png")


class Pump(Component):
    def __init__(self, scene: "simulator.SimulationScene", tile_size: int, pos: (int, int) = (0, 0)):
        Component.__init__(self, scene, (3, 3), tile_size, [
            Connection("E", 1),
            Connection("W", 1)
        ], pos=pos)
        self.load_image("images/pump.png")


class FourwayValve(Component):
    def __init__(self, scene: "simulator.SimulationScene", tile_size: int, pos: (int, int) = (0, 0)):
        Component.__init__(self, scene, (3, 3), tile_size, [
            Connection("N", 1),
            Connection("E", 1),
            Connection("S", 1),
            Connection("W", 1)
        ], pos=pos)
        self.load_image("images/fourwayvalve.png")


class AndValve(Component):
    def __init__(self, scene: "simulator.SimulationScene", tile_size: int, pos: (int, int) = (0, 0)):
        Component.__init__(self, scene, (3, 3), tile_size, [
            Connection("W", 0),
            Connection("W", 2),
            Connection("E", 1)
        ], pos=pos)
        self.load_image("images/andvalve.png")

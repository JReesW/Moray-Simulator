import pygame.image
from pygame import Surface, Rect

import simulator
from simulator import Connectable
from engine.things import Draggable
from engine.grid import Grid
from engine import colors


def components_list():
    return {
        "Gate Valve": GateValve,
        "Globe Valve": GlobeValve,
        "Ball Valve": BallValve,
        "Diaphragm": Diaphragm,
        "Three-Way Valve": ThreeWayValve,
        "Pump": Pump
    }


class Component(Draggable, Connectable):
    def __init__(self,
                 scene: "simulator.SimulationScene",
                 dimensions: (int, int),
                 tile_size: int,
                 image: Surface = None,
                 rect: Rect = None,
                 pos: (int, int) = (0, 0)
                 ):
        Draggable.__init__(self, scene, image, rect, pos, scene.components, scene.floating_components)

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

    def drop(self):
        """
        Handle what happens when the component is dropped
        """
        colliding = any([self.grid_overlap(comp) for comp in self.scene.components if self is not comp])

        if not colliding:
            # Snap the component to the grid
            self.pos = self.grid.snap(self.pos, self.dim)
        else:
            # Snap the component back to the last valid spot, or kill it if there is none
            if self.prev_pos is None:
                self.kill()
            else:
                self.pos = self.prev_pos

    def grid_overlap(self, other: "Component"):
        """
        Return whether this component overlaps another on the grid
        """
        rect = Rect(0, 0, *self.dim)
        rect.center = self.grid.tile_coord(self.pos)
        other_rect = Rect(0, 0, *other.dim)
        other_rect.center = self.grid.tile_coord(other.pos)
        return rect.colliderect(other_rect)

    def rotate(self, clockwise=True):
        """
        Rotate the component by a 90-degree rotation
        """
        self.bg_image = pygame.transform.rotate(self.bg_image, -90 if clockwise else 90)
        self.shadow.image = pygame.transform.rotate(self.shadow.image, -90 if clockwise else 90)
        self.rotate_connections(clockwise)

    def connector_coords(self) -> ((int, int), bool):
        """
        Get screencoords of the component's connectors, alongside bools whether they are connected or not
        """
        res = []
        cx, cy = self.w / 2, self.h / 2
        if "N" in self.connections:
            res.append(((cx, 0), self.connections["N"] is not None))
        if "E" in self.connections:
            res.append(((self.w, cy), self.connections["E"] is not None))
        if "S" in self.connections:
            res.append(((cx, self.h), self.connections["S"] is not None))
        if "W" in self.connections:
            res.append(((0, cy), self.connections["W"] is not None))
        return res

    def handle_events(self, events, panel=None, **kwargs):
        Draggable.handle_events(self, events, **kwargs)
        mouse = pygame.mouse.get_pos()

        for event in events:
            if event.type == pygame.MOUSEBUTTONUP and panel is not None:
                if panel.rect.collidepoint(*mouse):
                    self.kill()
                else:
                    self.drop()

            elif event.type == pygame.KEYDOWN:
                if self.held and event.key == pygame.K_r:
                    if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                        self.rotate(False)
                    else:
                        self.rotate()

    def update(self, camera, *args, **kwargs):
        Draggable.update(self, camera, *args, **kwargs)

        self.image = self.bg_image.copy()

        # Draw red if a dragging component is overlapping this component
        if any([self.grid_overlap(comp) for comp in self.scene.floating_components if self is not comp]):
            red = Surface(self.rect.size, pygame.SRCALPHA)
            red.fill((*colors.red, 100))
            self.image.blit(red, (0, 0))

        # Draw connectors
        if "show_connectors" in kwargs and kwargs["show_connectors"]:
            conn_image = Surface(self.rect.size, pygame.SRCALPHA)
            for coord, connected in self.connector_coords():
                color = colors.green if connected else colors.dark_orange
                pygame.draw.circle(conn_image, color, coord, 7, 3)
            self.image.blit(conn_image, (0, 0))


class GateValve(Component):
    def __init__(self, scene: "simulator.SimulationScene", tile_size: int, pos: (int, int) = (0, 0)):
        Component.__init__(self, scene, (3, 3), tile_size, pos=pos)
        Connectable.__init__(self, "NS")
        self.load_image("images/gatevalve.png")


class GlobeValve(Component):
    def __init__(self, scene: "simulator.SimulationScene", tile_size: int, pos: (int, int) = (0, 0)):
        Component.__init__(self, scene, (3, 3), tile_size, pos=pos)
        Connectable.__init__(self, "NS")
        self.load_image("images/globevalve.png")


class BallValve(Component):
    def __init__(self, scene: "simulator.SimulationScene", tile_size: int, pos: (int, int) = (0, 0)):
        Component.__init__(self, scene, (3, 3), tile_size, pos=pos)
        Connectable.__init__(self, "NS")
        self.load_image("images/ballvalve.png")


class Diaphragm(Component):
    def __init__(self, scene: "simulator.SimulationScene", tile_size: int, pos: (int, int) = (0, 0)):
        Component.__init__(self, scene, (3, 3), tile_size, pos=pos)
        Connectable.__init__(self, "NS")
        self.load_image("images/diaphragm.png")


class ThreeWayValve(Component):
    def __init__(self, scene: "simulator.SimulationScene", tile_size: int, pos: (int, int) = (0, 0)):
        Component.__init__(self, scene, (3, 3), tile_size, pos=pos)
        Connectable.__init__(self, "NSW")
        self.load_image("images/threewayvalve.png")


class Pump(Component):
    def __init__(self, scene: "simulator.SimulationScene", tile_size: int, pos: (int, int) = (0, 0)):
        Component.__init__(self, scene, (3, 3), tile_size, pos=pos)
        Connectable.__init__(self, "EW")
        self.load_image("images/pump.png")

import pygame

from engine import colors


class Grid:
    def __init__(self, tile_size: int = 1):
        self.tile_size = tile_size

    def tile_coord(self, coord: (int, int)) -> (int, int):
        """
        Return the grid coord a given coord is located in
        """
        x, y = coord
        return x // self.tile_size, y // self.tile_size

    def world_coord(self, coord: (int, int)) -> (int, int):
        """
        Return the world coord of a given tile coord's topleft corner
        """
        x, y = coord
        return x * self.tile_size, y * self.tile_size

    def snap(self, coord: (int, int), dim: (int, int)) -> (int, int):
        """
        Snap a given coord to the grid based on its center.
        Uneven dimensions will snap to a tile center while even dimensions snap to gridlines.
        """
        x, y = coord
        dx = (self.tile_size // 2) if dim[0] % 2 == 0 else 0
        dy = (self.tile_size // 2) if dim[1] % 2 == 0 else 0
        nx = ((x + dx) // self.tile_size) * self.tile_size + (self.tile_size / 2) - dx
        ny = ((y + dy) // self.tile_size) * self.tile_size + (self.tile_size / 2) - dy
        return nx, ny

    def render(self, surface, camera):
        """
        Draw gridlines on a surface, only those in view of the camera
        """
        w, h = camera.screen_size

        for y in range(h // self.tile_size + 1):
            y_val = (-camera.top % self.tile_size) + (y * self.tile_size)
            pygame.draw.line(surface, colors.light_steel_blue, (0, y_val), (w, y_val))

        for x in range(w // self.tile_size + 1):
            x_val = (-camera.left % self.tile_size) + (x * self.tile_size)
            pygame.draw.line(surface, colors.light_steel_blue, (x_val, 0), (x_val, h))

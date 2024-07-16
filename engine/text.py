"""
Text rendering module

TODO:
 - Write a function that handles multiline text rendering
"""


from pygame import Surface, Rect
import pygame.freetype

from engine.colors import Color


if not pygame.freetype.get_init():
    pygame.freetype.init()


__fonts = {}


def render(text: str, color: Color, font: str, size: int, bold=False, italic=False) -> (Surface, Rect):
    if (font, size) not in __fonts:
        __fonts[(font, size)] = pygame.freetype.SysFont(font, size, bold=bold, italic=italic)

    return __fonts[(font, size)].render(text, color)


def multiline_render(surface: Surface, pos: (int, int), text: str, color: Color, font: str, size: int, bold=False, italic=False) -> (Surface, Rect):
    if (font, size) not in __fonts:
        __fonts[(font, size)] = pygame.freetype.SysFont(font, size, bold=bold, italic=italic)

    f = __fonts[(font, size)]

    # https://stackoverflow.com/a/42015712
    words = [word.split(' ') for word in text.splitlines()]
    space = f.render(' ', (0, 0, 0))[0].get_size()[0]
    print(space)
    max_width, max_height = surface.get_size()
    x, y = pos
    word_height = 0
    for line in words:
        for word in line:
            word_surface, _ = f.render(word, color)
            word_width, word_height = word_surface.get_size()
            if x + word_width >= max_width:
                x = pos[0]  # Reset the x.
                y += word_height  # Start on new row.
            surface.blit(word_surface, (x, y))
            x += word_width + space
        x = pos[0]  # Reset the x.
        y += word_height  # Start on new row.

    return surface, surface.get_rect()


# def multiline_render(surface: Surface, pos: (int, int), text: str, color: Color, font: str, size: int, bold=False, italic=False) -> (Surface, Rect):
#     if (font, size) not in __fonts:
#         __fonts[(font, size)] = pygame.freetype.SysFont(font, size, bold=bold, italic=italic)
#
#     f = __fonts[(font, size)]
#
#     # https://stackoverflow.com/a/42015712
#     words = [word.split(' ') for word in text.splitlines()]
#     space = f.render(' ', (0, 0, 0))[0].get_size()[0]
#     print(space)
#     max_width, max_height = surface.get_size()
#     x, y = pos
#     word_height = 0
#     for line in words:
#         for word in line:
#             word_surface, _ = f.render(word, color)
#             word_width, word_height = word_surface.get_size()
#             if x + word_width >= max_width:
#                 x = pos[0]  # Reset the x.
#                 y += word_height  # Start on new row.
#             surface.blit(word_surface, (x, y))
#             x += word_width + space
#         x = pos[0]  # Reset the x.
#         y += word_height  # Start on new row.
#
#     return surface, surface.get_rect()


if __name__ == '__main__':
    for word in ["ee", "___", "lllllll"]:
        _, rect = render(word, (0, 0, 0), "Arial", 24)
        print(rect)

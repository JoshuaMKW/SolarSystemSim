from abc import abstractmethod, ABC
import pygame

class PygameUILayer(ABC):
    """
    Pygame UI Layer
    """
    
    @abstractmethod
    def draw(self, screen: pygame.Surface, delta: float, rect: pygame.Rect, is_hovered: bool = False):
        """
        Draw the layer
        """
        pass

    @abstractmethod
    def intersects(self, rect: pygame.Rect) -> bool:
        """
        Check if the layer intersects with the rect
        """
        pass

    @abstractmethod
    def on_event(self, event: pygame.event.Event, rect: pygame.Rect) -> bool:
        """
        Handle the event
        """
        pass

_circle_cache = {}
def _circlepoints(r):
    r = int(round(r))
    if r in _circle_cache:
        return _circle_cache[r]
    x, y, e = r, 0, 1 - r
    _circle_cache[r] = points = []
    while x >= y:
        points.append((x, y))
        y += 1
        if e < 0:
            e += 2 * y - 1
        else:
            x -= 1
            e += 2 * (y - x) - 1
    points += [(y, x) for x, y in points if x > y]
    points += [(-x, y) for x, y in points if x]
    points += [(x, -y) for x, y in points if y]
    points.sort()
    return points

def render_text(text, font, gfcolor=pygame.Color('white'), ocolor=pygame.Color('black'), opx=2):
    """
    Render a text with an outline using circular rendering techniques
    """

    textsurface = font.render(text, True, gfcolor).convert_alpha()
    w = textsurface.get_width() + 2 * opx
    h = font.get_height()

    osurf = pygame.Surface((w, h + 2 * opx)).convert_alpha()
    osurf.fill((0, 0, 0, 0))

    surf = osurf.copy()

    osurf.blit(font.render(text, True, ocolor).convert_alpha(), (0, 0))

    for dx, dy in _circlepoints(opx):
        surf.blit(osurf, (dx + opx, dy + opx))

    surf.blit(textsurface, (opx, opx))
    return surf

DELTA_TIME_CUR: float = 0.0
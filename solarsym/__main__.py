__doc__ = 'Solar System simulation'

import pygame
from pygame.locals import *

from solarsym.system_viewer import RenderView

from . import PLANET_FONT, SYSTEM_FONT
from .system.body import SystemBody
from .system.system import SystemBodyPool
from .drawer import BodyDrawerUI
import solarsym.pygame_ui as pygame_ui

PLANET_FONT = None
SYSTEM_FONT = None

def main():
    # Screen initialization
    screen = pygame.display.set_mode((1600, 900))
    pygame.display.set_caption('Solar System')

    # Background fill
    background = pygame.Surface(screen.get_size())
    background = background.convert()
    background.fill((0, 0, 0))

    system: SystemBodyPool = SystemBodyPool()

    drawer = BodyDrawerUI()
    renderer = RenderView()
    renderer.set_system(system)
    drawer.set_system_viewer(renderer)

    speedup = 1.0

    delta = 0.1
    expected_delta = 0.0

    clock = pygame.time.Clock()

    # Main loop
    while True:
        delta = clock.tick(165) * 0.1 * speedup
        pygame_ui.DELTA_TIME_CUR = delta
        if (expected_delta == 0.0):
            expected_delta = delta * 1.1
        
        # Pause if the delta is too high
        if (delta > expected_delta):
            continue

        for event in pygame.event.get():
            if event.type == QUIT:
                return
            
            if drawer.on_event(event, pygame.Rect(0, 0, 500, 900)):
                continue

            if renderer.on_event(event, pygame.Rect(0, 0, 1600, 900)):
                continue
            
        renderer.pre_draw(delta, pygame.Rect(0, 0, 1600, 900))
        renderer.draw(screen, delta, pygame.Rect(0, 0, 1600, 900), False)
        renderer.post_draw(delta)
        
        drawer.draw(screen, delta, pygame.Rect(0, 0, 500, 900), False)
        pygame.display.update()

        screen.blit(background, (0, 0))
        # pygame.display.flip()

if __name__ == '__main__':
    main()
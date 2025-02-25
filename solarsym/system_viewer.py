import math
from enum import IntEnum
from io import BytesIO
from typing import override

import matplotlib.pyplot as plt
import numpy as np
import pygame
from matplotlib.colors import LinearSegmentedColormap
from pygame.locals import *

from . import PLANET_FONT, SYSTEM_FONT
from .pygame_ui import DELTA_TIME_CUR, PygameUILayer
from .system.body import SystemBody
from .system.system import SystemBodyPool
import solarsym.pygame_ui as pygame_ui

def ease_in_out(t: float) -> float:
    """
    Easing function
    """
    return 3 * t ** 2 - 2 * t ** 3

class RenderView(PygameUILayer):
    """
    A class to represent a body drawer
    """

    class ControlState(IntEnum):
        """
        An enum of different control states
        """
        STATE_NONE = 0
        STATE_SELECTED = 1
        STATE_DROPPED = 2

    _system: SystemBodyPool
    _view_pos: list[float, float]
    _zoom: float
    _drag_view_active: bool
    _drag_last_pos: list[float, float]
    _control_state: ControlState
    _drop_pos: list[float, float]
    _drag_body: SystemBody | None

    def __init__(self):
        self._system = SystemBodyPool()
        self._view_pos = [0.0, 0.0]
        self._zoom = 1.0
        self._drag_view_active = False
        self._drag_last_pos = [0.0, 0.0]
        self._control_state = RenderView.ControlState.STATE_NONE
        self._drop_pos = [0.0, 0.0]

    def set_system(self, system: SystemBodyPool):
        """
        Set the system to render
        """
        self._system = system

    def start_drag_body(self, body: SystemBody):
        """
        Start dragging the body
        """
        self._control_state = RenderView.ControlState.STATE_SELECTED
        self._drag_body = body

    def toggle_heatmap(self, state: bool):
        """
        Toggle if the underlying system
        should generate heatmaps
        """
        self._system.toggle_heatmap(state)

    def pre_draw(self, delta: float, view_rect: pygame.Rect):
        """
        Update the system physics and such
        """
        self._system.update_system()
        self._system.update_heatmap(delta, self._zoom, pygame.Rect(self._view_pos[0], self._view_pos[1], 1600, 900))

        if self._drag_view_active:
            mouse_pos = pygame.mouse.get_pos()
            self._view_pos[0] += (self._drag_last_pos[0] - mouse_pos[0]) * 100 * (1 / self._zoom)
            self._view_pos[1] += (self._drag_last_pos[1] - mouse_pos[1]) * 100 * (1 / self._zoom)
            self._system.set_center(self._view_pos)
            self._drag_last_pos = mouse_pos

        if self._control_state == RenderView.ControlState.STATE_SELECTED:
            mouse_pos = pygame.mouse.get_pos()
            self._drop_pos = mouse_pos
            self._drag_body.position = [
                (mouse_pos[0] - view_rect.centerx) / (SystemBody.SYSTEM_SCALE * self._zoom) + self._view_pos[0],
                (mouse_pos[1] - view_rect.centery) / (SystemBody.SYSTEM_SCALE * self._zoom) + self._view_pos[1]
            ]

    def post_draw(self, delta: float):
        """
        Post draw
        """
        self._system.move_all(delta)

    @override
    def intersects(self, rect: pygame.Rect) -> bool:
        """
        Check if the position intersects with the textbox
        """
        return True

    @override
    def draw(self, screen: pygame.Surface, delta: float, rect: pygame.Rect, is_hovered: bool = False):
        """
        Draw the body on the screen
        """
        self._system.draw_all(screen, delta, self._view_pos, self._zoom)

        if self._control_state == RenderView.ControlState.STATE_SELECTED:
            self._drag_body.draw(screen, delta, self._zoom, self._view_pos, True)

        elif self._control_state == RenderView.ControlState.STATE_DROPPED:
            mouse_pos = pygame.mouse.get_pos()

            self._drag_body.draw(screen, delta, self._zoom, self._view_pos, False)

            # Draw the arrow outline
            pygame.draw.line(screen, (0, 0, 0), self._drop_pos, mouse_pos, 4)
            pygame.draw.circle(screen, (0, 0, 0), self._drop_pos, 5)
            pygame.draw.circle(screen, (0, 0, 0), mouse_pos, 5)

            pygame.draw.line(screen, (255, 0, 0), self._drop_pos, mouse_pos, 2)
            pygame.draw.circle(screen, (255, 0, 0), self._drop_pos, 3)
            pygame.draw.circle(screen, (255, 0, 0), mouse_pos, 3)




    @override
    def on_event(self, event: pygame.event.Event, rect: pygame.Rect) -> bool:
        """
        Handle the event
        """
        mouse_pos = pygame.mouse.get_pos()

        if event.type == MOUSEWHEEL:
            if event.y > 0:
                self._zoom *= 0.9
            else:
                self._zoom *= 1.1
            return True

        if event.type == MOUSEBUTTONDOWN:
            if not rect.collidepoint(mouse_pos):
                return False
            if self._control_state == RenderView.ControlState.STATE_DROPPED and event.button == BUTTON_LEFT:
                self._control_state = RenderView.ControlState.STATE_NONE
                self._drag_body.velocity = [
                    ((mouse_pos[0] - self._drop_pos[0]) * pygame_ui.DELTA_TIME_CUR * 0.1) / (SystemBody.SYSTEM_SCALE * self._zoom),
                    ((mouse_pos[1] - self._drop_pos[1]) * pygame_ui.DELTA_TIME_CUR * 0.1) / (SystemBody.SYSTEM_SCALE * self._zoom),
                ]
                self._system.add_body(self._drag_body)
                self._drag_body = None
                return True

            if event.button == BUTTON_MIDDLE or event.button == BUTTON_LEFT:
                self._drag_view_active = True
                self._drag_last_pos = mouse_pos
                return True
        elif event.type == MOUSEBUTTONUP:
            if self._control_state == RenderView.ControlState.STATE_SELECTED and event.button == BUTTON_LEFT:
                self._control_state = RenderView.ControlState.STATE_DROPPED
                return True
            
            if event.button == BUTTON_MIDDLE or event.button == BUTTON_LEFT:
                self._drag_view_active = False
                return True
            
        return False
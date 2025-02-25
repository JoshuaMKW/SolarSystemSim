import math
from typing import override
import pygame
from pygame.locals import *

from solarsym.system_viewer import RenderView

from . import PLANET_FONT, SYSTEM_FONT
from .pygame_ui import PygameUILayer
from .system.body import SystemBody
from .system.system import SystemBodyPool

def ease_in_out(t: float) -> float:
    """
    Easing function
    """
    return 3 * t ** 2 - 2 * t ** 3

class BodyPreviewUI(PygameUILayer):
    """
    A class to represent a body preview
    """

    BACKGROUND_COLOR = (100, 100, 150)
    FRAME_COLOR = (80, 80, 140)

    _body: SystemBody
    _system_viewer: RenderView

    def __init__(self):
        self._body = SystemBody('Earth', 500.972, 800, (0, 0, 255), (0, 0))
        self._system_viewer = None

    def get_body(self) -> SystemBody:
        """
        Get the body preview
        """
        return self._body

    def set_body(self, body: SystemBody):
        """
        Set the body to preview
        """
        self._body = body
        
    def set_system_viewer(self, system_viewer: RenderView):
        """
        Set the system viewer
        """
        self._system_viewer = system_viewer

    @override
    def draw(self, screen: pygame.Surface, delta: float, rect: pygame.Rect, is_hovered: bool = False):
        """
        Draw the body preview
        """
        pygame.draw.rect(screen, BodyPreviewUI.BACKGROUND_COLOR, rect, border_radius=10)
        pygame.draw.rect(screen, BodyPreviewUI.FRAME_COLOR, rect, 5, border_radius=10)

        if self._body is not None:
            pygame.draw.circle(screen, (0, 0, 0, 180), (rect.centerx, rect.centery), rect.width // 4)
            pygame.draw.circle(screen, self._body.color, (rect.centerx, rect.centery), rect.width // 4)

        text = SYSTEM_FONT.render(self._body.name, True, (255, 255, 255), (0, 0, 0, 180))
        text_rect = text.get_rect()
        text_rect.center = [
            rect.centerx,
            rect.top + 30
        ]
        screen.blit(text, text_rect)

    @override
    def intersects(self, rect: pygame.Rect) -> bool:
        """
        Check if the layer intersects with the rect
        """
        return True
    
    @override
    def on_event(self, event: pygame.event.Event, rect: pygame.Rect) -> bool:
        """
        Handle the event
        """
        if event.type == MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            if rect.collidepoint(mouse_pos):
                self._system_viewer.start_drag_body(self._body)
                self._body = SystemBody(
                    self._body.name,
                    self._body.mass,
                    self._body.radius,
                    self._body.color,
                    (0, 0)
                )
                return True
                
        return False

class BodyDrawerTextbox(PygameUILayer):
    """
    A class to represent a body drawer textbox
    """

    LABEL_PADDING = 5
    FIELD_INNER_PADDING = 5
    BACKGROUND_COLOR = (100, 100, 150)
    FRAME_COLOR = (80, 80, 140)

    
    _label: str
    _hint: str
    _value: str
    _focused: bool
    _focused_counter: float

    def __init__(self, label: str, hint: str = ''):
        self._label = label
        self._hint = hint
        self._value = ''
        self._focused = False
        self._focused_counter = 0.0

    @property
    def value(self) -> str:
        """
        Get the value of the textbox
        """
        return self._value
    
    @value.setter
    def value(self, value: str):
        """
        Set the value of the textbox
        """
        self._value = value

    def focus(self):
        """
        Focus the textbox
        """
        self._focused = True
        self._focused_counter = 0.0

    def unfocus(self):
        """
        Unfocus the textbox
        """
        self._focused = False

    def is_focused(self):
        """
        Check if the textbox is focused
        """
        return self._focused
    
    @override
    def intersects(self, rect: pygame.Rect) -> bool:
        """
        Check if the position intersects with the textbox
        """
        text_height = SYSTEM_FONT.get_height()
        textbox_height = rect.height
        if textbox_height == 0:
            textbox_height = text_height

        label = SYSTEM_FONT.render(self._label, True, (255, 255, 255))
        label_rect = label.get_rect()
        label_rect.centery = rect.top + (text_height // 2) + BodyDrawerTextbox.FIELD_INNER_PADDING
        label_rect.left = rect.left + BodyDrawerTextbox.LABEL_PADDING

        label_width = label_rect.width + (BodyDrawerTextbox.LABEL_PADDING * 2)

        textbox_height += (BodyDrawerTextbox.FIELD_INNER_PADDING * 2)
        textbox_rect = pygame.Rect(rect.left + label_width, rect.top, rect.width, textbox_height)
        return textbox_rect.collidepoint(pygame.mouse.get_pos())

    @override
    def draw(self, screen: pygame.Surface, delta: float, rect: pygame.Rect, is_hovered: bool = False):
        """
        Draw the textbox
        """
        text_height = SYSTEM_FONT.get_height()
        textbox_height = rect.height
        if textbox_height == 0:
            textbox_height = text_height

        textbox_height += (BodyDrawerTextbox.FIELD_INNER_PADDING * 2)
        textbox_rect = pygame.Rect(rect.left, rect.top, rect.width, textbox_height)
        if not screen.get_clip().colliderect(textbox_rect):
            return

        label = SYSTEM_FONT.render(self._label, True, (255, 255, 255))
        label_rect = label.get_rect()
        label_rect.centery = rect.top + (text_height // 2) + BodyDrawerTextbox.FIELD_INNER_PADDING
        label_rect.left = rect.left + BodyDrawerTextbox.LABEL_PADDING

        label_width = label_rect.width + (BodyDrawerTextbox.LABEL_PADDING * 2)

        screen.blit(label, label_rect)

        field_rect = pygame.Rect(rect.left + label_width, rect.top, max(rect.width - label_width, 100), 30)

        pygame.draw.rect(screen, BodyDrawerTextbox.BACKGROUND_COLOR, field_rect, border_radius=5)
        pygame.draw.rect(screen, BodyDrawerTextbox.FRAME_COLOR, field_rect, 2, border_radius=5)

        if self._value != "":
            text = SYSTEM_FONT.render(self._value, True, (255, 255, 255))
            text_rect = text.get_rect()
            text_rect.centery = rect.top + (text_height // 2) + BodyDrawerTextbox.FIELD_INNER_PADDING
            text_rect.left = field_rect.left + BodyDrawerTextbox.FIELD_INNER_PADDING
            text_rect.right = min(text_rect.right, field_rect.right - BodyDrawerTextbox.FIELD_INNER_PADDING)

            screen.blit(text, text_rect)

            if self._focused and math.fmod(self._focused_counter, 120) < 60.0:
                pygame.draw.line(screen, (255, 255, 255), (text_rect.right + 2, text_rect.top), (text_rect.right + 2, text_rect.bottom))

        elif self._hint != "":
            text = SYSTEM_FONT.render(self._hint, True, (200, 200, 200))
            text_rect = text.get_rect()
            text_rect.centery = rect.top + (text_height // 2) + BodyDrawerTextbox.FIELD_INNER_PADDING
            text_rect.left = field_rect.left + BodyDrawerTextbox.FIELD_INNER_PADDING
            text_rect.right = min(text_rect.right, field_rect.right - BodyDrawerTextbox.FIELD_INNER_PADDING)

            screen.blit(text, text_rect)

            if self._focused and math.fmod(self._focused_counter, 120) < 60.0:
                pygame.draw.line(screen, (255, 255, 255), (text_rect.left, text_rect.top), (text_rect.left, text_rect.bottom))
            
        else:
            if self._focused and math.fmod(self._focused_counter, 120) < 60.0:
                pygame.draw.line(screen, (255, 255, 255), (text_rect.left, text_rect.top), (text_rect.left, text_rect.bottom))

        self._focused_counter += 1 * delta

    @override
    def on_event(self, event: pygame.event.Event, rect: pygame.Rect) -> bool:
        """
        Handle the event
        """
        if event.type == KEYDOWN and self._focused:
            if event.key == K_BACKSPACE:
                self._value = self._value[:-1]
            elif event.key == K_RETURN:
                self._focused = False
            else:
                self._value += event.unicode
            return True
        elif event.type == MOUSEBUTTONDOWN:
            self._focused = self.intersects(rect)
            if self._focused:
                return True
            
        return False

class BodyDrawerUI(PygameUILayer):
    """
    A class to represent a body drawer
    """

    DRAWER_CLOSED_X = -490
    DRAWER_OPEN_X = 0

    _presets: list[SystemBody]
    _body_preview: BodyPreviewUI
    _input_name: BodyDrawerTextbox
    _input_mass: BodyDrawerTextbox
    _input_radius: BodyDrawerTextbox
    _input_color: BodyDrawerTextbox

    _drawer_x_current: int
    _drawer_lerping: bool
    _drawer_lerp: float
    _drawer_x_begin: int
    _drawer_x_end: int
    _drawer_closing: bool
    _drawer_opening: bool

    def __init__(self):
        self._presets = []
        self._input_name = BodyDrawerTextbox('Name', 'Enter the name of the body')
        self._input_mass = BodyDrawerTextbox('Mass', 'Enter the mass of the body')
        self._input_radius = BodyDrawerTextbox('Radius', 'Enter the radius of the body')
        self._input_color = BodyDrawerTextbox('Color', 'Enter the color of the body')
        self._body_preview = BodyPreviewUI()
        self._drawer_lerp = 0.0
        self._drawer_x_current = BodyDrawerUI.DRAWER_CLOSED_X
        self._drawer_x_begin = 0
        self._drawer_x_end = 0
        self._drawer_lerping = False
        self._drawer_closing = False
        self._drawer_opening = False

    def set_system_viewer(self, system_viewer: RenderView):
        """
        Set the system viewer
        """
        self._body_preview.set_system_viewer(system_viewer)

    def set_presets(self, presets: list[SystemBody]):
        """
        Set the presets
        """
        self._presets = presets

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
        dyn_rect = pygame.Rect(self._drawer_x_current, 0, 500, 900)

        pygame.draw.rect(screen, (100, 100, 150), dyn_rect, border_radius=10)
        pygame.draw.rect(screen, (80, 80, 140), dyn_rect, 5, border_radius=10)

        self._body_preview.draw(screen, delta, pygame.Rect(dyn_rect.left + 10, dyn_rect.top + 10, dyn_rect.width - 20, 400))

        self._input_name.draw(screen, delta, pygame.Rect(dyn_rect.left + 10, dyn_rect.top + 420, dyn_rect.width - 20, 30))
        self._input_mass.draw(screen, delta, pygame.Rect(dyn_rect.left + 10, dyn_rect.top + 460, dyn_rect.width - 20, 30))
        self._input_radius.draw(screen, delta, pygame.Rect(dyn_rect.left + 10, dyn_rect.top + 500, dyn_rect.width - 20, 30))
        self._input_color.draw(screen, delta, pygame.Rect(dyn_rect.left + 10, dyn_rect.top + 540, dyn_rect.width - 20, 30))

        # Calculate the drawer position
        mouse_pos = pygame.mouse.get_pos()
        drawer_rect = pygame.Rect(self._drawer_x_current, 0, 500, 900)

        drawer_diff = math.fabs(BodyDrawerUI.DRAWER_OPEN_X - BodyDrawerUI.DRAWER_CLOSED_X)

        if not self._drawer_opening and drawer_rect.collidepoint(mouse_pos) and self._drawer_lerp < 1.0:
            self._drawer_lerping = True
            self._drawer_opening = True
            self._drawer_closing = False
            self._drawer_x_begin = BodyDrawerUI.DRAWER_CLOSED_X
            self._drawer_x_end = BodyDrawerUI.DRAWER_OPEN_X
            self._drawer_lerp = math.fabs((self._drawer_x_current - BodyDrawerUI.DRAWER_CLOSED_X) / drawer_diff)
        elif not self._drawer_closing and not drawer_rect.collidepoint(mouse_pos) and self._drawer_lerp < 1.0:
            self._drawer_lerping = True
            self._drawer_opening = False
            self._drawer_closing = True
            self._drawer_x_begin = BodyDrawerUI.DRAWER_OPEN_X
            self._drawer_x_end = BodyDrawerUI.DRAWER_CLOSED_X
            self._drawer_lerp = math.fabs((self._drawer_x_current - BodyDrawerUI.DRAWER_OPEN_X) / drawer_diff)

        if (self._drawer_lerping):
            self._drawer_x_current = int(self._drawer_x_begin + (self._drawer_x_end - self._drawer_x_begin) * ease_in_out(self._drawer_lerp))
            self._drawer_lerp += 0.02 * delta
            if (self._drawer_lerp >= 1.0):
                self._drawer_lerping = False
                self._drawer_lerp = 0.0

    @override
    def on_event(self, event: pygame.event.Event, rect: pygame.Rect) -> bool:
        """
        Handle the event
        """
        dyn_rect = pygame.Rect(self._drawer_x_current, rect.top, rect.width, rect.height)

        if self._body_preview.on_event(event, pygame.Rect(dyn_rect.left + 10, dyn_rect.top + 10, dyn_rect.width - 20, 400)):
            return True
        
        if self._input_name.on_event(event, pygame.Rect(dyn_rect.left + 10, dyn_rect.top + 420, dyn_rect.width - 20, 30)):
            if (event.type == KEYDOWN and event.key == K_RETURN):
                self._body_preview.get_body().name = self._input_name.value
            return True
        
        if self._input_mass.on_event(event, pygame.Rect(dyn_rect.left + 10, dyn_rect.top + 460, dyn_rect.width - 20, 30)):
            if (event.type == KEYDOWN and event.key == K_RETURN):
                try:
                    self._body_preview.get_body().mass = float(self._input_mass.value)
                except ValueError:
                    pass
            return True

        if self._input_radius.on_event(event, pygame.Rect(dyn_rect.left + 10, dyn_rect.top + 500, dyn_rect.width - 20, 30)):
            if (event.type == KEYDOWN and event.key == K_RETURN):
                try:
                    self._body_preview.get_body().radius = float(self._input_radius.value)
                except ValueError:
                    pass
            return True

        if self._input_color.on_event(event, pygame.Rect(dyn_rect.left + 10, dyn_rect.top + 540, dyn_rect.width - 20, 30)):
            if (event.type == KEYDOWN and event.key == K_RETURN):
                try:
                    color = self._input_color.value.split(',')
                    self._body_preview.get_body().color = (int(color[0]), int(color[1]), int(color[2]))
                except ValueError:
                    pass
            return True
            
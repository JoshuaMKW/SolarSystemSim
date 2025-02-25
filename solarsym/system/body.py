from __future__ import annotations
from dataclasses import dataclass
import math

import pygame
from pygame.locals import *

from solarsym.pygame_ui import render_text

from .. import PLANET_FONT


class SystemBody:
    """A class to represent a body in the solar system"""

    # GRAVITY_CONSTANT = 6.67430e-11
    GRAVITY_CONSTANT = 6.67430e3
    SYSTEM_SCALE = 0.01
    COLLISION_DAMPENING = 0.01

    _name: str
    _mass: float
    _radius: int
    _color: list[float, float]
    _position: list[float, float]
    _velocity: list[float, float]
    _acceleration: list[float, float]

    @dataclass
    class CollisionInfo:
        """
        Collision information for a body
        """

        granularity: int
        bias: float
        impulse: float
        reflect_dir: list[float, float]

    @dataclass
    class GravityInfo:
        """
        Gravity information for a body
        """

        force: float
        direction: list[float, float]

    def __init__(self, name, mass, radius, color, position, velocity=(0, 0)):
        self._name = name
        self._mass = mass
        self._radius = radius
        self._color = color
        self._position = [position[0], position[1]]
        self._velocity = [velocity[0], velocity[1]]
        self._acceleration = [0, 0]

    @property
    def name(self) -> str:
        """
        Get the name of the body
        """
        return self._name

    @name.setter
    def name(self, name: str):
        """
        Set the name of the body
        """
        self._name = name

    @property
    def position(self) -> list[float, float]:
        """
        Get the position of the body
        """
        return self._position

    @position.setter
    def position(self, position: list[float, float]):
        """
        Set the position of the body
        """
        self._position = position

    @property
    def velocity(self) -> list[float, float]:
        """
        Get the velocity of the body
        """
        return self._velocity

    @velocity.setter
    def velocity(self, velocity: list[float, float]):
        """
        Set the velocity of the body
        """
        self._velocity = velocity

    @property
    def acceleration(self) -> list[float, float]:
        """
        Get the acceleration of the body
        """
        return self._acceleration

    @acceleration.setter
    def acceleration(self, acceleration: list[float, float]):
        """
        Set the acceleration of the body
        """
        self._acceleration = acceleration

    @property
    def mass(self) -> float:
        """
        Get the mass of the body
        """
        return self._mass

    @mass.setter
    def mass(self, mass: float):
        """
        Set the mass of the body
        """
        self._mass = mass

    @property
    def radius(self) -> float:
        """
        Get the radius of the body
        """
        return self._radius

    @radius.setter
    def radius(self, radius: float):
        """
        Set the radius of the body
        """
        self._radius = radius

    @property
    def color(self) -> float:
        """
        Get the color of the body
        """
        return self._color

    @color.setter
    def color(self, color: float):
        """
        Set the color of the body
        """
        self._color = color

    def draw(
        self,
        screen,
        delta: float,
        zoom: float,
        center: list[float, float],
        is_hovered: bool = False,
    ):
        """
        Draw the body on the screen
        """
        # Normalize the postition
        screen_pos = [
            (self._position[0] - center[0]) * SystemBody.SYSTEM_SCALE * zoom
            + screen.get_width() / 2,
            (self._position[1] - center[1]) * SystemBody.SYSTEM_SCALE * zoom
            + screen.get_height() / 2,
        ]
        screen_radius = self._radius * SystemBody.SYSTEM_SCALE * zoom

        color = list(self._color)

        if is_hovered:
            color[0] = min(255, color[0] + 50)
            color[1] = min(255, color[1] + 50)
            color[2] = min(255, color[2] + 50)

            self._draw_info(screen, screen_pos, screen_radius)

        pygame.draw.circle(screen, (0, 0, 0), screen_pos, screen_radius + 2)
        pygame.draw.circle(screen, color, screen_pos, screen_radius)

    def move(self, delta: float):
        """
        Update the position of the body based on its velocity
        """
        self._velocity[0] += self._acceleration[0] * delta
        self._velocity[1] += self._acceleration[1] * delta
        self._position[0] += self._velocity[0] * delta
        self._position[1] += self._velocity[1] * delta
        self._acceleration = [0, 0]

    def add_acceleration(self, acceleration: tuple):
        """
        Add an acceleration to the body
        """
        self._acceleration[0] += acceleration[0]
        self._acceleration[1] += acceleration[1]

    def add_force(self, force: tuple):
        """
        Add a force to the body
        """
        self._acceleration[0] += force[0] / self._mass
        self._acceleration[1] += force[1] / self._mass

    def calc_gravity_acceleration(self, other: SystemBody) -> float:
        """
        Calculate the gravitational acceleration caused by the other body
        """
        dist_x = other.position[0] - self._position[0]
        dist_y = other.position[1] - self._position[1]
        dist_sqr = dist_x**2 + dist_y**2
        mass_x = other.mass
        force = (SystemBody.GRAVITY_CONSTANT * mass_x) / dist_sqr
        return force

    def calc_gravity_at_point(
        self, point: list[float, float]
    ) -> SystemBody.GravityInfo:
        """
        Calculate the gravitational acceleration caused by a point
        """
        dist_x = point[0] - self._position[0]
        dist_y = point[1] - self._position[1]
        dist_sqr = dist_x**2 + dist_y**2
        dist_sqr = max(dist_sqr, self._radius**2)
        dist = math.sqrt(dist_sqr)
        force = (SystemBody.GRAVITY_CONSTANT) / dist_sqr
        return SystemBody.GravityInfo(
            force=force, direction=[dist_x / dist, dist_y / dist]
        )

    def calc_collision_bias(self, other: SystemBody) -> CollisionInfo | None:
        """
        Calculates the bias for collision resolution between 0 and 1
        1 means no mass is lost, 1 means no mass is lost
        """

        # Calculate the relative velocity
        rel_vel = [
            self._velocity[0] - other.velocity[0],
            self._velocity[1] - other.velocity[1],
        ]

        # Calculate the relative position
        rel_pos = [
            self._position[0] - other.position[0],
            self._position[1] - other.position[1],
        ]

        rel_pos_mag = rel_pos[0] ** 2 + rel_pos[1] ** 2

        # Determine intersection depth using radius
        distance = math.sqrt(rel_pos_mag)
        intersection = self._radius + other.radius - distance

        if intersection < 0:
            return None

        # rel_pos is the normal vector
        col_normal = [rel_pos[0] / rel_pos_mag, rel_pos[1] / rel_pos_mag]

        # Calculate the relative velocity in the normal direction
        rel_vel_n = rel_vel[0] * col_normal[0] + rel_vel[1] * col_normal[1]
        if rel_vel_n >= 0:
            return None

        # Calculate the impulse
        impulse = -2 * rel_vel_n / (1 / self._mass + 1 / other.mass)
        impulse *= other.mass / self._mass
        impulse *= SystemBody.COLLISION_DAMPENING
        impulse /= SystemBody.SYSTEM_SCALE

        rel_vel_mag = math.sqrt(rel_vel[0] ** 2 + rel_vel[1] ** 2)

        # Calculate the reflection vector
        rel_vel_normalized = [rel_vel[0] / rel_vel_mag, rel_vel[1] / rel_vel_mag]

        reflection = [
            -rel_vel_normalized[0] + 2 * rel_vel_n * col_normal[0],
            -rel_vel_normalized[1] + 2 * rel_vel_n * col_normal[1],
        ]

        # Bias is the density of the body compared to the other body
        bias = self._mass / (self._mass + other.mass)

        info = SystemBody.CollisionInfo(
            granularity=10, bias=bias, impulse=impulse, reflect_dir=reflection
        )

        return info

    def calc_blended_color(
        self, other: SystemBody, bias: float = 0.5
    ) -> list[float, float, float]:
        """
        Calculate the blended color of the body with another body
        """

        # Convert RGB to HSL
        hsl_self = pygame.Color(self._color).hsva
        hsl_other = pygame.Color(other.color).hsva

        # Calculate the average hue
        hue = hsl_self[0] * bias + hsl_other[0] * (1.0 - bias)

        # Calculate the average saturation
        sat = hsl_self[1] * bias + hsl_other[1] * (1.0 - bias)

        # Calculate the average lightness
        light = hsl_self[2] * bias + hsl_other[2] * (1.0 - bias)

        # Convert HSL to RGB
        color = pygame.Color(0)
        color.hsva = (hue, sat, light)
        return color

    def _draw_info(self, screen, position: list[float, float], radius: float):
        """
        Draw the body's information on the screen
        """

        # text = PLANET_FONT.render(f'{self._name} - {self._mass:.2e} kg', True, (255, 255, 255))
        # text_rect = text.get_rect()
        # text_rect.center = position
        # text_rect.y -= (20 + int(radius))
        # screen.blit(text, text_rect)

        text_surf = render_text(f"{self._name} - {self._mass:.2e} kg", PLANET_FONT)
        text_rect = text_surf.get_rect()
        text_rect.center = position
        text_rect.y -= 20 + int(radius)
        screen.blit(text_surf, text_rect)

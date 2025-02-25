from __future__ import annotations
from dataclasses import dataclass
import math

import matplotlib.pyplot as plt
import numpy as np
import pygame
from matplotlib.colors import Normalize
from pygame.locals import *

from io import BytesIO

from .body import SystemBody

class SystemBodyPool:
    """A class to represent a pool of bodies in the solar system"""

    HEATMAP_CELL_SIZE = 10
    HEATMAP_UPDATE_INTERVAL = 15.0

    bodies: list[SystemBody]
    center: list[float, float]
    _heatmap: np.ndarray
    _heatmap_active: bool
    _heatmap_update_time: float
    _heatmap_surface: pygame.Surface | None

    @dataclass
    class _UpdateInfo:
        """
        Information about a collision update
        """
        new_color: list[int, int, int]
        new_mass: float
        new_radius: int
        new_position: list[float, float]
        due_acceleration: list[float, float]
        affectors: list[list[SystemBody, SystemBody.CollisionInfo]]
        affected: SystemBody

        def apply(self):
            """
            Apply the update to the affected body
            """
            self.affected.color = self.new_color
            self.affected.mass = self.new_mass
            self.affected.radius = self.new_radius
            self.affected.acceleration = self.due_acceleration
        

    def __init__(self):
        self.bodies = []
        self.center = [0, 0]
        self._heatmap = []
        self._heatmap_active = True
        self._heatmap_update_time = 0.0
        self._heatmap_surface = None

    def intersects_point(self, point: list[float, float]) -> bool:
        """
        Check if a point intersects any body in the pool
        """
        for body in self.bodies:
            dist_sqr = (point[0] - body.position[0]) ** 2 + (point[1] - body.position[1]) ** 2
            if dist_sqr <= body.radius ** 2:
                return True

        return False
    
    def intersects_body(self, body: SystemBody, point: list[float, float]) -> bool:
        """
        Check if a point intersects a specific body in the pool
        """
        dist_sqr = (point[0] - body.position[0]) ** 2 + (point[1] - body.position[1]) ** 2
        return dist_sqr <= body.radius ** 2

    def set_center(self, center: list[float, float]):
        """
        Set the center of the pool
        """
        self.center = center

    def add_body(self, body: SystemBody):
        """
        Add a body to the pool
        """
        self.bodies.append(body)

    def draw_all(self, screen, delta: float, view_pos: list[float, float], zoom: float):
        """
        Draw all bodies in the pool on the screen
        """
        mouse_pos = pygame.mouse.get_pos()

        click_point = [
            view_pos[0] + (mouse_pos[0] / (SystemBody.SYSTEM_SCALE * zoom)),
            view_pos[1] + (mouse_pos[1] / (SystemBody.SYSTEM_SCALE * zoom))
        ]

        abs_point = [
            view_pos[0] + ((mouse_pos[0] + screen.get_width() / 2) / (SystemBody.SYSTEM_SCALE * zoom)),
            view_pos[1] + ((mouse_pos[1] + screen.get_height() / 2) / (SystemBody.SYSTEM_SCALE * zoom))
        ]

        if (self._heatmap_active and self._heatmap_surface is not None):
            screen.blit(self._heatmap_surface, (0, 0))

        for body in self.bodies:
            body.draw(screen, delta, zoom, view_pos, self.intersects_body(body, abs_point))

    def move_all(self, delta: float):
        """
        Update the position of all bodies in the pool based on their velocity
        """
        for body in self.bodies:
            body.move(delta)

    def update_system(self):
        """
        Apply gravitational forces between all bodies
        """
        bodies_to_remove = set()
        bodies_to_add = set()
        bodies_to_merge = set()
        body_merge_info = []
        pending_updates: list[SystemBodyPool._UpdateInfo] = []

        for affected in self.bodies:
            update_info = SystemBodyPool._UpdateInfo(
                new_color=affected.color,
                new_mass=affected.mass,
                new_radius=affected.radius,
                new_position=affected.position,
                due_acceleration=[0, 0],
                affectors=[],
                affected=affected,
            )

            for affector in self.bodies:
                if affected == affector:
                    continue

                # Calculate the gravitational acceleration
                acceleration = affected.calc_gravity_acceleration(affector)

                affect_angle = math.atan2(affected.position[1] - affector.position[1], affected.position[0] - affector.position[0])

                accel_vector = [
                    -acceleration * math.cos(affect_angle),
                    -acceleration * math.sin(affect_angle)
                ]
                affected.add_acceleration(accel_vector)

                # Calculate a collision
                col_info = affected.calc_collision_bias(affector)
                if (col_info is None):
                    continue

                update_info.affectors.append([affector, col_info])

            if (len(update_info.affectors) > 0):
                pending_updates.append(update_info)


        for this_update in pending_updates:
            for affector, col_info in this_update.affectors:
                if (this_update.affected == affector):
                    continue

                # Absorb the smaller body
                if (col_info.bias < 0.1):
                    bodies_to_remove.add(this_update.affected)
                    continue
                
                # Merge the bodies if the reflection isn't strong enough
                reflection_theta = math.atan2(col_info.reflect_dir[1], col_info.reflect_dir[0])
                if math.fabs(reflection_theta) >= math.pi - 0.05 or math.fabs(reflection_theta) < 0.05 or col_info.impulse < 10:
                    if (this_update.affected in bodies_to_merge):
                        continue
                    bodies_to_merge.add(this_update.affected)
                    bodies_to_merge.add(affector)
                    body_merge_info.append([this_update.affected, affector])

                # Apply the collision bias to reduce mass
                this_update.new_mass *= col_info.bias
                this_update.new_radius *= col_info.bias

                # Apply the affector bias to increase mass
                this_update.new_mass += affector.mass * (1 - col_info.bias)
                this_update.new_radius += affector.radius * (1 - col_info.bias)

                this_update.due_acceleration = [
                    this_update.due_acceleration[0] + col_info.impulse * col_info.reflect_dir[0],
                    this_update.due_acceleration[1] + col_info.impulse * col_info.reflect_dir[1]
                ]

                this_update.new_color = this_update.affected.calc_blended_color(affector, col_info.bias)

                if (col_info.bias >= 0.9):
                    continue

                continue

                # # Create new bodies
                # particle_mass = (affected.mass * (1 - col_info.bias)) / col_info.granularity
                # particle_radius = (affected.radius * (1 - col_info.bias)) / col_info.granularity
                # particle_position = [
                #     affected.position[0] + col_info.reflect_dir[0] * affected.radius,
                #     affected.position[1] + col_info.reflect_dir[1] * affected.radius
                # ]
                # particle_velocity = [
                #     affected.velocity[0] + col_info.reflect_dir[0] * col_info.impulse,
                #     affected.velocity[1] + col_info.reflect_dir[1] * col_info.impulse
                # ]
                # for i in range(col_info.granularity):
                #     particle = SystemBody(f'_col_{affected.name}{i}', particle_mass, particle_radius, affected.color, particle_position, particle_velocity)
                #     bodies_to_add.append(particle)

                #     particle_position[0] += col_info.reflect_dir[0] * particle_radius
                #     particle_position[1] += col_info.reflect_dir[1] * particle_radius
                #     particle_velocity[0] *= 1.1
                #     particle_velocity[1] *= 1.1

        for update in pending_updates:
            if (update.affected in bodies_to_merge):
                continue
            update.apply()

        for body1, body2 in body_merge_info:
            new_mass = body1.mass + body2.mass
            new_radius = body1.radius + body2.radius
            new_color = body1.calc_blended_color(body2)
            new_position = [
                (body1.position[0] * body1.mass + body2.position[0] * body2.mass) / new_mass,
                (body1.position[1] * body1.mass + body2.position[1] * body2.mass) / new_mass
            ]
            new_velocity = [
                (body1.velocity[0] * body1.mass + body2.velocity[0] * body2.mass) / new_mass,
                (body1.velocity[1] * body1.mass + body2.velocity[1] * body2.mass) / new_mass
            ]
            new_body = SystemBody(f'{body1.name}_{body2.name}', new_mass, new_radius, new_color, new_position, new_velocity)
            bodies_to_remove.add(body1)
            bodies_to_remove.add(body2)
            bodies_to_add.add(new_body)

        for body in bodies_to_remove:
            self.bodies.remove(body)

        for body in bodies_to_add:
            self.bodies.append(body)

    def toggle_heatmap(self, state: bool):
        """
        Toggle the heatmap state
        """
        self._heatmap_active = state

    def update_heatmap(self, delta: float, scale: float, view_rect: pygame.Rect):
        """
        Update the calculated heatmap for the gravity at each point
        """
        if not self._heatmap_active:
            return
        
        if (self._heatmap_update_time < SystemBodyPool.HEATMAP_UPDATE_INTERVAL):
            self._heatmap_update_time += delta
            return
        
        self._heatmap_update_time = 0.0
        
        self._heatmap = []

        for y in range(SystemBodyPool.HEATMAP_CELL_SIZE // 2, view_rect.height + SystemBodyPool.HEATMAP_CELL_SIZE // 2, SystemBodyPool.HEATMAP_CELL_SIZE):
            row = []
            for x in range(SystemBodyPool.HEATMAP_CELL_SIZE // 2, view_rect.width + SystemBodyPool.HEATMAP_CELL_SIZE // 2, SystemBodyPool.HEATMAP_CELL_SIZE):
                point = [
                    (x - view_rect.width // 2) / (SystemBody.SYSTEM_SCALE * scale) + view_rect.x,
                    (y - view_rect.height // 2) / (SystemBody.SYSTEM_SCALE * scale) + view_rect.y,
                ]
                
                total_accel = 0
                for body in self.bodies:
                    new_info = body.calc_gravity_at_point(point)
                    total_accel += new_info.force

                row.append(total_accel)
            self._heatmap.append(row)

        self._heatmap_surface = self.create_heatmap_surface(view_rect)

    def create_heatmap_surface(self, view_rect: pygame.Rect) -> pygame.Surface:
        """
        Generate a pygame surface from a heatmap
        """

        # # Normalize the heatmap
        # norm = Normalize(vmin=np.min(data), vmax=np.max(data))

        # plt.figure(None, figsize=(16, 9), dpi=100, frameon=False)
        # plt.imshow(data, cmap='hot', norm=norm, interpolation='nearest')
        # plt.axis('off')

        # # Save to memory buffer
        # buf = BytesIO()
        # plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0)
        # plt.close()
        # buf.seek(0)

        # # Load the buffer into a pygame image
        # surface = pygame.image.load(buf).convert()
        # buf.close()

        # surface = pygame.transform.scale(surface, (1600, 900))
        # return surface

        surface = pygame.Surface((1600, 900))

        accel_max = 0
        accel_min = 1e20
        for y, row in enumerate(self._heatmap):
            for x, value in enumerate(row):
                accel_max = max(accel_max, value)
                accel_min = min(accel_min, value)

        if (accel_min - accel_max) == 0:
            return surface

        data_range = math.log(accel_max / accel_min)

        accel_max /= data_range
        accel_min /= data_range

        scaled_range = accel_max - accel_min

        for y, row in enumerate(self._heatmap):
            for x, value in enumerate(row):
                value = ((math.log(value) / data_range - accel_min) / scaled_range)
                color = int(value * 255)
                pygame.draw.rect(
                    surface,
                    (color, color, color),
                    (
                        x * SystemBodyPool.HEATMAP_CELL_SIZE,
                        y * SystemBodyPool.HEATMAP_CELL_SIZE,
                        SystemBodyPool.HEATMAP_CELL_SIZE,
                        SystemBodyPool.HEATMAP_CELL_SIZE
                    )
                )

        return surface
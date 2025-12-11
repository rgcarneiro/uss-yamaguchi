import math
import random
import sys
import time
from dataclasses import dataclass
from functools import partial

import pygame
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *


@dataclass(frozen=True)
class CameraConfig:
    """Camera projection and orbital parameters.

    Attributes:
        fov (float): Field of view in degrees for the perspective projection.
        aspect_ratio (float): Window width divided by height.
        near_plane (float): Near clipping plane distance in coordinate units.
        far_plane (float): Far clipping plane distance in coordinate units.
        look_at_eye (tuple[float, float, float]): Camera position in world space.
        look_at_center (tuple[float, float, float]): Target point the camera faces.
        look_at_up (tuple[float, float, float]): Up vector used for orientation.
        camera_radius (float): Distance of the orbiting camera from the origin.
    """

    fov: float = 50.0
    aspect_ratio: float = 1000 / 650
    near_plane: float = 1.0
    far_plane: float = 200.0
    look_at_eye: tuple[float, float, float] = (8.25, -12.25, 20.0)
    look_at_center: tuple[float, float, float] = (0.0, 0.0, 0.0)
    look_at_up: tuple[float, float, float] = (-0.07, 1.0, 0.0)
    camera_radius: float = 25.0


@dataclass(frozen=True)
class AccelerationConfig:
    """Timing and motion thresholds used during the animation.

    All values are expressed in seconds or units consistent with the scene's
    coordinate system.
    """

    acceleration_duration: float = 12.0
    angle_start_time: float = 3.0
    color_change_time: float = 15.0
    warp_time: float = 28.0
    angle_increment_deg: float = 0.2
    max_angle_deg: float = 520.0
    acceleration_increment: float = 0.1
    position_scale: float = 0.01
    warp_reset_threshold: float = 10.0
    timer_interval_ms: int = 16


@dataclass(frozen=True)
class ColorPalette:
    """Default hull and lighting colors using normalized RGB values."""

    nacelle_blue: tuple[float, float, float] = (0.5, 0.7, 0.9)
    nacelle_red: tuple[float, float, float] = (0.9, 0.2, 0.4)
    background: tuple[float, float, float] = (0.0, 0.0, 0.0)


def draw_disc():
    y_axis = 7.0
    radius = 5.0
    cond = True
    while cond:
        if y_axis > 6.5:
            glPushMatrix()
            glColor3f(0.6, 0.6, 0.6)
            glTranslatef(0, y_axis, 6)
            glRotatef(240, 1, 1, 1)
            draw_saucer(radius, -3, 20)
            glPopMatrix()

            y_axis -= 0.01
            radius += 0.01

        elif y_axis > 6.0:
            glPushMatrix()
            glColor3f(0.4, 0.4, 0.4)
            glTranslatef(0, y_axis, 6)
            glRotatef(240, 1, 1, 1)
            draw_saucer(radius, -3, 20)
            glPopMatrix()

            y_axis -= 0.01
            radius -= 0.01
        else:
            cond = False


def draw_main_bridge(height):
    glBegin(GL_QUADS)

    glVertex3f(-0.5, -0.5, height)
    glVertex3f(0.5, -0.5, height)
    glVertex3f(0.8, 0.5, height)
    glVertex3f(-0.2, 0.5, height)

    glVertex3f(-0.5, -0.5, -height)
    glVertex3f(0.5, -0.5, -height)
    glVertex3f(0.8, 0.5, -height)
    glVertex3f(-0.2, 0.5, -height)

    glVertex3f(-0.5, -0.5, height)
    glVertex3f(-0.2, 0.5, height)
    glVertex3f(-0.2, 0.5, -height)
    glVertex3f(-0.5, -0.5, -height)

    glVertex3f(0.5, -0.5, height)
    glVertex3f(0.8, 0.5, height)
    glVertex3f(0.8, 0.5, -height)
    glVertex3f(0.5, -0.5, -height)

    glVertex3f(-0.2, 0.5, height)
    glVertex3f(0.8, 0.5, height)
    glVertex3f(0.8, 0.5, -height)
    glVertex3f(-0.2, 0.5, -height)

    glVertex3f(-0.5, -0.5, height)
    glVertex3f(0.5, -0.5, height)
    glVertex3f(0.5, -0.5, -height)
    glVertex3f(-0.5, -0.5, -height)

    glEnd()


def draw_saucer(radius, height, slices):
    glBegin(GL_POLYGON)
    for i in range(slices):
        angle = 2 * math.pi * i / slices
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        glVertex3f(x, y, height)
    glEnd()


def draw_nacelle(length, radius, slices):
    for i in range(slices):
        angle = 2 * math.pi * i / slices
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        glBegin(GL_POLYGON)
        glVertex3f(x, y, 0)
        glVertex3f(x, y, length)
        glVertex3f(
            radius * math.cos(angle + 2 * math.pi / slices),
            radius * math.sin(angle + 2 * math.pi / slices),
            length,
        )
        glVertex3f(
            radius * math.cos(angle + 2 * math.pi / slices),
            radius * math.sin(angle + 2 * math.pi / slices),
            0,
        )
        glEnd()


def draw_nacelle_with_lights(position, length, radius, slices, front_color, back_color):
    """Draw a nacelle and its lights at the given position.

    Args:
        position (tuple[float, float, float]): Translation coordinates for the
            nacelle's base (x, y, z).
        length (float): Length of the nacelle along the z-axis.
        radius (float): Radius used for the nacelle body and lights.
        slices (int): Number of slices used to approximate circular geometry.
        front_color (tuple[float, float, float]): RGB color for the nacelle's
            front light.
        back_color (tuple[float, float, float]): RGB color for the nacelle's
            back light.
    """

    x_pos, y_pos, z_pos = position

    glPushMatrix()
    glColor3f(0.5, 0.5, 0.5)
    glTranslatef(x_pos, y_pos, z_pos)
    draw_nacelle(length, radius, slices)
    glPopMatrix()

    glPushMatrix()
    glColor3f(*back_color)
    glTranslatef(x_pos, y_pos, z_pos)
    draw_circle(radius, 100, 0)
    glPopMatrix()

    glPushMatrix()
    glColor3f(*front_color)
    glTranslatef(x_pos, y_pos, z_pos + length)
    draw_circle(radius, 100, 0)
    glPopMatrix()


def draw_plank(x, y, z):
    glBegin(GL_QUADS)
    glVertex3f(x, -y, -z)
    glVertex3f(x, y, -z)
    glVertex3f(-x, y, -z)
    glVertex3f(-x, -y, -z)

    glVertex3f(x, -y, z)
    glVertex3f(x, y, z)
    glVertex3f(x, y, -z)
    glVertex3f(x, -y, -z)

    glVertex3f(-x, -y, z)
    glVertex3f(-x, y, z)
    glVertex3f(x, y, z)
    glVertex3f(x, -y, z)

    glVertex3f(-x, -y, -z)
    glVertex3f(-x, y, -z)
    glVertex3f(-x, y, z)
    glVertex3f(-x, -y, z)

    glVertex3f(x, y, -z)
    glVertex3f(x, y, z)
    glVertex3f(-x, y, z)
    glVertex3f(-x, y, -z)

    glVertex3f(x, -y, -z)
    glVertex3f(x, -y, z)
    glVertex3f(-x, -y, z)
    glVertex3f(-x, -y, -z)
    glEnd()


def draw_circle(radius, slices, height):
    glBegin(GL_TRIANGLE_FAN)
    glVertex3f(0, 0, 0)
    for i in range(slices + 1):
        angle = 2 * math.pi * i / slices
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        glVertex3f(x, y, height)
    glEnd()


def draw_circle_outline(radius, slices, height):
    glBegin(GL_LINE_LOOP)
    for i in range(slices):
        angle = 2 * math.pi * i / slices
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        glVertex3f(x, y, height)
    glEnd()


def draw_solid_sphere(radius, slices, stacks):
    for i in range(stacks):
        theta1 = i * math.pi / stacks
        theta2 = (i + 1) * math.pi / stacks

        glBegin(GL_TRIANGLE_STRIP)
        for j in range(slices + 1):
            phi = j * 2 * math.pi / slices

            x1 = radius * math.sin(theta1) * math.cos(phi)
            y1 = radius * math.cos(theta1)
            z1 = radius * math.sin(theta1) * math.sin(phi)
            glVertex3f(x1, y1, z1)

            x2 = radius * math.sin(theta2) * math.cos(phi)
            y2 = radius * math.cos(theta2)
            z2 = radius * math.sin(theta2) * math.sin(phi)
            glVertex3f(x2, y2, z2)
        glEnd()


def draw_stars():
    num_stars = 600
    stars_back = [
        (
            random.uniform(-100, 100),
            random.uniform(-100, 100),
            random.uniform(-300, -50),
        )
        for _ in range(num_stars)
    ]

    stars_middle = [
        (
            random.uniform(50, -50),
            random.uniform(-50, 50),
            random.uniform(150, -25),
        )
        for _ in range(num_stars)
    ]

    stars_front = [
        (
            random.uniform(100, -100),
            random.uniform(100, -100),
            random.uniform(300, 50),
        )
        for _ in range(num_stars)
    ]

    glBegin(GL_POINTS)
    glColor3f(1.0, 1.0, 1.0)

    for back in stars_back:
        glVertex3f(*back)
    for middle in stars_middle:
        glVertex3f(*middle)
    for front in stars_front:
        glVertex3f(*front)

    glEnd()


def draw_yamaguchi(colors_blue, colors_red):
    # =========================================================================
    #   UPPER PART DISC
    # =========================================================================

    draw_disc()

    # =========================================================================
    #   TOP SPHERE
    # =========================================================================

    glPushMatrix()
    glColor3f(0.47, 0.47, 0.47)
    glTranslatef(0, 4, 6)
    draw_solid_sphere(0.5, 10, 10)
    glPopMatrix()

    # =========================================================================
    #   UPPER PART DISC CIRCLE OUTLINES
    # =========================================================================

    glPushMatrix()
    glColor3f(0.3, 0.3, 0.3)
    glTranslatef(0, 4.1, 6)
    glRotatef(240, 1, 1, 1)
    draw_circle_outline(1, 100, 0)
    glPopMatrix()

    glPushMatrix()
    glColor3f(0.3, 0.3, 0.3)
    glTranslatef(0, 4.1, 6)
    glRotatef(240, 1, 1, 1)
    draw_circle_outline(3, 100, 0)
    glPopMatrix()

    glPushMatrix()
    glColor3f(0.3, 0.3, 0.3)
    glTranslatef(0, 4, 6)
    glRotatef(240, 1, 1, 1)
    draw_circle_outline(5, 100, 0)
    glPopMatrix()

    # =========================================================================
    #   MAIN BRIDGE
    # =========================================================================

    glPushMatrix()
    glColor3f(0.5, 0.5, 0.5)
    glTranslatef(0, 2, 4)
    glRotatef(240, 1, 1, 1)
    draw_main_bridge(1.5)
    glPopMatrix()

    # =========================================================================
    #   MIDDLE NACELLE
    # =========================================================================

    glPushMatrix()
    glColor3f(0.48, 0.48, 0.48)
    glTranslatef(0, 0.5, 0)
    draw_nacelle(5, 0.5, 20)
    glPopMatrix()

    glPushMatrix()
    glColor3f(0.5, 0.5, 0.5)
    glTranslatef(0, 1, -5)
    draw_nacelle(10, 0.5, 20)
    glPopMatrix()

    # =========================================================================
    #   MIDDLE NACELLE ENGINE FRONTLIGHT
    # =========================================================================

    glPushMatrix()
    glColor3f(colors_blue[0], colors_blue[1], colors_blue[2])
    glTranslatef(0, 0.5, 5)
    draw_circle(0.5, 100, 0)
    glPopMatrix()

    glPushMatrix()
    glColor3f(0.5, 0.5, 0.5)
    glTranslatef(0, 0.5, 0)
    draw_circle(0.5, 100, 0)
    glPopMatrix()

    # =========================================================================
    #   LEFT NACELLE
    # =========================================================================

    nacelles = [
        {
            "position": (-3, 3, -5.5),
            "length": 6,
            "radius": 0.5,
            "slices": 20,
            "front_color": tuple(colors_red),
            "back_color": tuple(colors_blue),
        },
        {
            "position": (3, 3, -5.5),
            "length": 6,
            "radius": 0.5,
            "slices": 20,
            "front_color": tuple(colors_red),
            "back_color": tuple(colors_blue),
        },
    ]

    for nacelle in nacelles:
        draw_nacelle_with_lights(
            nacelle["position"],
            nacelle["length"],
            nacelle["radius"],
            nacelle["slices"],
            nacelle["front_color"],
            nacelle["back_color"],
        )

    # =========================================================================
    #   HORIZONTAL PLANK
    # =========================================================================

    glPushMatrix()
    glColor3f(0.45, 0.45, 0.45)
    glTranslatef(0, 0, 0.5)
    draw_plank(2, 0.2, 0.5)
    glPopMatrix()

    # =========================================================================
    #   VERTICAL LEFT PLANK
    # =========================================================================

    glPushMatrix()
    glColor3f(0.47, 0.47, 0.47)
    glTranslatef(2.3, 1.4, 0.2)
    glRotatef(-110, 0, 0, 1)
    draw_plank(1.5, 0.25, 0.25)
    glPopMatrix()

    # =========================================================================
    #   VERTICAL RIGHT PLANK
    # =========================================================================

    glPushMatrix()
    glColor3f(0.47, 0.47, 0.47)
    glTranslatef(-2.3, 1.4, 0.2)
    glRotatef(110, 0, 0, 1)
    draw_plank(1.5, 0.25, 0.25)
    glPopMatrix()

class SceneState:
    def __init__(
        self,
        camera_config: CameraConfig = CameraConfig(),
        acceleration_config: AccelerationConfig = AccelerationConfig(),
        colors: ColorPalette = ColorPalette(),
    ):
        self.initial_position = [-2, -1, -3]
        self.camera_config = camera_config
        self.acceleration = acceleration_config
        self.angle = 0

        self.z_position = 0
        self.speed = 0
        self.velocity = 0
        self.start_time = None
        self.colors_blue = list(colors.nacelle_blue)
        self.colors_red = list(colors.nacelle_red)

    def accelerate(self, value):
        if self.start_time is None:
            self.start_time = time.time()
        elapsed_time = time.time() - self.start_time

        if elapsed_time < self.acceleration.acceleration_duration:
            self.speed += self.acceleration.acceleration_increment

        self.z_position -= self.speed * self.acceleration.position_scale
        glutPostRedisplay()
        glutTimerFunc(
            self.acceleration.timer_interval_ms,
            partial(SceneState.accelerate, self),
            0,
        )

    def animation_camera(self):
        glTranslatef(0, 0, -self.camera_config.camera_radius)
        glRotatef(self.angle, -1, 1, 1)

    def display(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        self.animation_camera()

        glPushMatrix()
        glRotatef(30, 1, 1, 0)
        glTranslatef(
            self.initial_position[0],
            self.initial_position[1],
            self.initial_position[2],
        )

        draw_yamaguchi(self.colors_blue, self.colors_red)
        draw_stars()

        glPopMatrix()
        glutSwapBuffers()

        if self.start_time is None:
            self.start_time = time.time()
        elapsed_time = time.time() - self.start_time

        if elapsed_time > self.acceleration.angle_start_time:
            self.angle += self.acceleration.angle_increment_deg
            if self.angle > self.acceleration.max_angle_deg:
                self.angle = self.acceleration.max_angle_deg

        if elapsed_time > self.acceleration.color_change_time:
            self.colors_blue[0] = random.uniform(0, 1)
            self.colors_blue[1] = random.uniform(0, 1)
            self.colors_blue[2] = random.uniform(0, 1)
            self.colors_red[0] = random.uniform(0, 1)
            self.colors_red[1] = random.uniform(0, 1)
            self.colors_red[2] = random.uniform(0, 1)

        if elapsed_time > self.acceleration.warp_time:
            self.velocity += self.speed
            self.initial_position[0] += self.velocity
            self.initial_position[1] = 0
            self.initial_position[2] = 0

            if self.initial_position[0] > self.acceleration.warp_reset_threshold:
                self.initial_position[0] = self.acceleration.warp_reset_threshold * 10
                self.velocity = 0

        return


CLEAR_COLOR_ALPHA = 1.0


def main():
    camera_config = CameraConfig()
    acceleration_config = AccelerationConfig()
    color_palette = ColorPalette()
    scene = SceneState(camera_config, acceleration_config, color_palette)

    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1280, 720)
    glutInitWindowPosition(0, 0)
    glutCreateWindow("USS YAMAGUCHI")
    glClearColor(*color_palette.background, CLEAR_COLOR_ALPHA)
    glShadeModel(GL_SMOOTH)
    glFrontFace(GL_CCW)
    glEnable(GL_DEPTH_TEST)

    glutDisplayFunc(partial(SceneState.display, scene))
    glutTimerFunc(
        scene.acceleration.timer_interval_ms,
        partial(SceneState.accelerate, scene),
        0,
    )

    glMatrixMode(GL_PROJECTION)
    gluPerspective(
        camera_config.fov,
        camera_config.aspect_ratio,
        camera_config.near_plane,
        camera_config.far_plane,
    )
    glMatrixMode(GL_MODELVIEW)
    gluLookAt(
        *camera_config.look_at_eye,
        *camera_config.look_at_center,
        *camera_config.look_at_up,
    )
    glPushMatrix()
    glutMainLoop()

    return


if __name__ == "__main__":
    main()

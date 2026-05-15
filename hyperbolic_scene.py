import math
import random
from dataclasses import dataclass
from typing import List, Tuple

import pygame
from pygame.locals import DOUBLEBUF, OPENGL
from OpenGL.GL import (
    GL_COLOR_BUFFER_BIT,
    GL_DEPTH_BUFFER_BIT,
    GL_DEPTH_TEST,
    GL_LINES,
    GL_MODELVIEW,
    GL_PROJECTION,
    glBegin,
    glClear,
    glClearColor,
    glColor3f,
    glEnable,
    glEnd,
    glLoadIdentity,
    glMatrixMode,
    glVertex3f,
)
from OpenGL.GLU import gluPerspective

Vec3 = Tuple[float, float, float]


@dataclass
class Polyhedron:
    center: Vec3
    vertices: List[Vec3]
    edges: List[Tuple[int, int]]
    color: Vec3


def dot(a: Vec3, b: Vec3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def norm2(v: Vec3) -> float:
    return dot(v, v)


def add(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def scale(s: float, v: Vec3) -> Vec3:
    return (s * v[0], s * v[1], s * v[2])


def mat_rot_y(v: Vec3, ang: float) -> Vec3:
    c, s = math.cos(ang), math.sin(ang)
    return (c * v[0] + s * v[2], v[1], -s * v[0] + c * v[2])


def forward_from_yaw(yaw: float) -> Vec3:
    return (math.sin(yaw), 0.0, -math.cos(yaw))


def mobius_add(a: Vec3, b: Vec3) -> Vec3:
    """Möbius addition in the 3D Poincaré ball (curvature -1)."""
    aa = norm2(a)
    bb = norm2(b)
    ab = dot(a, b)
    denom = 1.0 + 2.0 * ab + aa * bb
    if denom <= 1e-8:
        denom = 1e-8

    part1 = scale(1.0 + 2.0 * ab + bb, a)
    part2 = scale(1.0 - aa, b)
    out = scale(1.0 / denom, add(part1, part2))

    r2 = norm2(out)
    if r2 >= 0.9995:
        r = math.sqrt(r2)
        out = scale(0.999 / r, out)
    return out


def map_to_ball_render(p: Vec3) -> Vec3:
    """Rendering map: keep points strictly inside visible unit sphere."""
    r2 = norm2(p)
    if r2 >= 1.0:
        r = math.sqrt(r2)
        return scale(0.999 / r, p)
    return p


def make_tetra(scale_: float) -> Tuple[List[Vec3], List[Tuple[int, int]]]:
    verts = [
        (scale_, scale_, scale_),
        (-scale_, -scale_, scale_),
        (-scale_, scale_, -scale_),
        (scale_, -scale_, -scale_),
    ]
    edges = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]
    return verts, edges


def make_cube(scale_: float) -> Tuple[List[Vec3], List[Tuple[int, int]]]:
    v = []
    for x in (-scale_, scale_):
        for y in (-scale_, scale_):
            for z in (-scale_, scale_):
                v.append((x, y, z))
    edges = []
    for i in range(8):
        for j in range(i + 1, 8):
            a, b = v[i], v[j]
            diff = sum(1 for k in range(3) if abs(a[k] - b[k]) > 1e-6)
            if diff == 1:
                edges.append((i, j))
    return v, edges


def make_octa(scale_: float) -> Tuple[List[Vec3], List[Tuple[int, int]]]:
    verts = [
        (scale_, 0.0, 0.0),
        (-scale_, 0.0, 0.0),
        (0.0, scale_, 0.0),
        (0.0, -scale_, 0.0),
        (0.0, 0.0, scale_),
        (0.0, 0.0, -scale_),
    ]
    edges = []
    for i in range(6):
        for j in range(i + 1, 6):
            if i + j in (1, 5, 9):
                continue
            edges.append((i, j))
    return verts, edges


def spawn_polyhedra(n: int = 14) -> List[Polyhedron]:
    out: List[Polyhedron] = []
    factories = [make_tetra, make_cube, make_octa]
    for _ in range(n):
        r = random.uniform(0.2, 0.85)
        theta = random.uniform(0.0, 2.0 * math.pi)
        phi = math.acos(random.uniform(-1.0, 1.0))
        center = (
            r * math.sin(phi) * math.cos(theta),
            r * math.cos(phi),
            r * math.sin(phi) * math.sin(theta),
        )
        sc = random.uniform(0.03, 0.08)
        verts, edges = random.choice(factories)(sc)
        col = (random.uniform(0.3, 1.0), random.uniform(0.3, 1.0), random.uniform(0.3, 1.0))
        out.append(Polyhedron(center=center, vertices=verts, edges=edges, color=col))
    return out


def draw_wire_sphere(radius: float = 1.0, slices: int = 18, stacks: int = 10) -> None:
    glColor3f(0.2, 0.35, 0.55)
    for i in range(1, stacks):
        phi = math.pi * i / stacks
        y = radius * math.cos(phi)
        rr = radius * math.sin(phi)
        glBegin(GL_LINES)
        for j in range(slices):
            a = 2.0 * math.pi * j / slices
            b = 2.0 * math.pi * (j + 1) / slices
            glVertex3f(rr * math.cos(a), y, rr * math.sin(a))
            glVertex3f(rr * math.cos(b), y, rr * math.sin(b))
        glEnd()

    for j in range(slices):
        th = 2.0 * math.pi * j / slices
        glBegin(GL_LINES)
        for i in range(stacks):
            pa = math.pi * i / stacks
            pb = math.pi * (i + 1) / stacks
            glVertex3f(radius * math.sin(pa) * math.cos(th), radius * math.cos(pa), radius * math.sin(pa) * math.sin(th))
            glVertex3f(radius * math.sin(pb) * math.cos(th), radius * math.cos(pb), radius * math.sin(pb) * math.sin(th))
        glEnd()


def render_poly(poly: Polyhedron) -> None:
    glColor3f(*poly.color)
    transformed: List[Vec3] = []
    for v in poly.vertices:
        pv = add(poly.center, v)
        transformed.append(map_to_ball_render(pv))

    glBegin(GL_LINES)
    for a, b in poly.edges:
        va = transformed[a]
        vb = transformed[b]
        glVertex3f(va[0], va[1], va[2])
        glVertex3f(vb[0], vb[1], vb[2])
    glEnd()


def main() -> None:
    pygame.init()
    pygame.display.set_mode((1280, 720), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("PyOpenGL 3D Hyperbolic Space (Poincare Ball)")

    glEnable(GL_DEPTH_TEST)
    glClearColor(0.02, 0.02, 0.03, 1.0)

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(65.0, 1280 / 720, 0.01, 100.0)

    glMatrixMode(GL_MODELVIEW)

    polys = spawn_polyhedra(16)
    clock = pygame.time.Clock()

    running = True
    move_speed = 0.55
    turn_speed = 1.4
    yaw = 0.0

    while running:
        dt = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()

        move_z = 0.0
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            move_z -= move_speed * dt
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            move_z += move_speed * dt

        turn_y = 0.0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            turn_y += turn_speed * dt
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            turn_y -= turn_speed * dt

        if abs(turn_y) > 1e-8:
            yaw += turn_y
            for poly in polys:
                poly.center = mat_rot_y(poly.center, turn_y)

        if abs(move_z) > 1e-8:
            fwd = forward_from_yaw(yaw)
            cam_step = (fwd[0] * (-move_z), 0.0, fwd[2] * (-move_z))
            inv_step = (-cam_step[0], -cam_step[1], -cam_step[2])
            for poly in polys:
                poly.center = mobius_add(inv_step, poly.center)

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        # First-person observer pinned at the origin of the Poincare ball.
        # Motion is represented by world Möbius transforms; camera coordinates stay fixed.
        from OpenGL.GLU import gluLookAt

        look = forward_from_yaw(yaw)
        gluLookAt(0.0, 0.0, 0.0, look[0], look[1], look[2], 0.0, 1.0, 0.0)

        draw_wire_sphere(1.0)
        for poly in polys:
            render_poly(poly)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()

"""Constructor de mundos 3D controlado con las manos.

Mano derecha (puntero):
    - Punta del índice ............ mueve el cursor 3D
    - Pellizco pulgar + índice .... pone un bloque / pulsa botones y colores
    - Pellizco pulgar + medio ..... quita el bloque señalado
Mano izquierda (cámara):
    - Pellizco pulgar + índice y mover ....... gira la cámara
    - Pellizco pulgar + medio y subir/bajar .. zoom
"""
import collections
import ctypes
import math
import os
import time

import numpy as np
import pygame
from pygame.locals import (DOUBLEBUF, OPENGL, QUIT, KEYDOWN, MOUSEBUTTONDOWN, MOUSEBUTTONUP,
                           MOUSEMOTION, MOUSEWHEEL, K_ESCAPE, K_LEFT, K_RIGHT, K_UP, K_DOWN,
                           K_PAGEUP, K_PAGEDOWN, K_F1)
from OpenGL.GL import *
from OpenGL.GLU import gluPerspective, gluLookAt

from clima import SEGUNDOS_DIA, estado_cielo, hora_reloj, campo_estrellas
from fauna import Fauna, MUERTO
from hand_tracker import HandTracker, PUNTAS
from mundo import Mundo, PALETA, NOMBRES, CARAS
from shaders import (
    SOLIDO_VERT, SOLIDO_FRAG, AGUA_VERT, AGUA_FRAG, ANIMAL_VERT, ANIMAL_FRAG,
    ATRIBUTOS, UNIFORMES, LOC_POS, LOC_NRM, LOC_COL, LOC_AUX,
    compilar, uniforms,
)
from texturas import atlas_rgba

ANCHO, ALTO = 1280, 720
FOV = 55
MARGEN_MANO = 0.12
PELLIZCO_ON, PELLIZCO_OFF = 0.28, 0.40
RETARDO_ACCION = 0.12
ARCHIVO_MUNDO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mundo_guardado.npy")

COLOR_PUNTA = [(1.0, 0.85, 0.2), (0.2, 0.9, 1.0), (1.0, 0.4, 0.9), (0.4, 1.0, 0.4), (1.0, 0.6, 0.2)]

_CIRCULO = [(math.cos(a), math.sin(a)) for a in np.linspace(0, 2 * math.pi, 33)]
_ARISTAS = [(0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7), (7, 4), (0, 4), (1, 5), (2, 6), (3, 7)]
_VERTICES_CUBO = [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1), (0, 1, 0), (1, 1, 0), (1, 1, 1), (0, 1, 1)]
_PTR0 = ctypes.c_void_p(0)


class OneEuro:
    """Filtro One Euro: suaviza el temblor sin agregar retraso en movimientos rápidos."""

    def __init__(self, min_cutoff=1.0, beta=0.006, d_cutoff=1.0):
        self.min_cutoff, self.beta, self.d_cutoff = min_cutoff, beta, d_cutoff
        self.reiniciar()

    def reiniciar(self):
        self.x = self.dx = self.t = None

    @staticmethod
    def _alfa(dt, corte):
        tau = 1.0 / (2 * math.pi * corte)
        return 1.0 / (1.0 + tau / dt)

    def __call__(self, x, t):
        if self.x is None:
            self.x, self.dx, self.t = x, np.zeros_like(x), t
            return x
        dt = max(t - self.t, 1e-3)
        dx = (x - self.x) / dt
        a_d = self._alfa(dt, self.d_cutoff)
        self.dx = a_d * dx + (1 - a_d) * self.dx
        corte = self.min_cutoff + self.beta * float(np.linalg.norm(self.dx))
        a = self._alfa(dt, corte)
        self.x = a * x + (1 - a) * self.x
        self.t = t
        return self.x


def a_pantalla(nx, ny):
    m = MARGEN_MANO
    sx = (nx - m) / (1 - 2 * m) * ANCHO
    sy = (ny - m) / (1 - 2 * m) * ALTO
    return min(max(sx, 0), ANCHO - 1), min(max(sy, 0), ALTO - 1)


class EstadoMano:
    def __init__(self):
        self.filtro = OneEuro()
        self.historial = collections.deque(maxlen=40)
        self.reiniciar()

    def reiniciar(self):
        self.visible = False
        self.pinza_indice = self.pinza_medio = False
        self.ratio_indice = self.ratio_medio = 1.0
        self.cursor = None
        self.puntas = []
        self.palma = None
        self.filtro.reiniciar()
        self.historial.clear()

    def soltar(self):
        eventos = []
        if self.pinza_indice:
            eventos.append("indice_off")
        if self.pinza_medio:
            eventos.append("medio_off")
        self.reiniciar()
        return eventos

    def actualizar(self, mano, aspecto, t):
        if mano is None:
            return self.soltar() if self.visible else []

        self.visible = True
        pts = mano.puntos
        self.cursor = self.filtro(np.array(a_pantalla(pts[8, 0], pts[8, 1])), t)
        self.historial.append((t, float(self.cursor[0]), float(self.cursor[1])))
        self.puntas = [a_pantalla(pts[i, 0], pts[i, 1]) for i in PUNTAS]
        self.palma = pts[9, :2].copy()

        p = pts[:, :2] * (aspecto, 1.0)
        escala = float(np.linalg.norm(p[0] - p[9])) + 1e-6
        self.ratio_indice = float(np.linalg.norm(p[4] - p[8])) / escala
        self.ratio_medio = float(np.linalg.norm(p[4] - p[12])) / escala

        eventos = []
        if not self.pinza_indice and not self.pinza_medio:
            if self.ratio_indice < PELLIZCO_ON and self.ratio_indice <= self.ratio_medio:
                self.pinza_indice = True
                eventos.append("indice_on")
            elif self.ratio_medio < PELLIZCO_ON:
                self.pinza_medio = True
                eventos.append("medio_on")
        elif self.pinza_indice and self.ratio_indice > PELLIZCO_OFF:
            self.pinza_indice = False
            eventos.append("indice_off")
        elif self.pinza_medio and self.ratio_medio > PELLIZCO_OFF:
            self.pinza_medio = False
            eventos.append("medio_off")
        return eventos

    def pos_pasada(self, retardo):
        if not self.historial:
            return None
        limite = self.historial[-1][0] - retardo
        for t, x, y in reversed(self.historial):
            if t <= limite:
                return x, y
        return self.historial[0][1:]


class MallaGPU:
    """Vértices en VRAM: estáticos para el terreno, dinámicos para la fauna."""

    def __init__(self, nbuf=4, dinamico=False):
        self.ids = glGenBuffers(nbuf)
        self.n = 0
        self.uso = GL_DYNAMIC_DRAW if dinamico else GL_STATIC_DRAW
        self.sizes = (3, 3, 3, 2)[:nbuf]
        self.locs = (LOC_POS, LOC_NRM, LOC_COL, LOC_AUX)[:nbuf]

    def cargar(self, *datos):
        self.n = int(len(datos[0]))
        for buf, arr in zip(self.ids, datos):
            buf_arr = np.ascontiguousarray(arr, dtype=np.float32)
            glBindBuffer(GL_ARRAY_BUFFER, int(buf))
            glBufferData(GL_ARRAY_BUFFER, buf_arr.nbytes, buf_arr, self.uso)
        glBindBuffer(GL_ARRAY_BUFFER, 0)

    def enlazar(self):
        for buf, loc, n in zip(self.ids, self.locs, self.sizes):
            glBindBuffer(GL_ARRAY_BUFFER, int(buf))
            glEnableVertexAttribArray(loc)
            glVertexAttribPointer(loc, n, GL_FLOAT, GL_FALSE, 0, _PTR0)

    def dibujar(self):
        if self.n:
            glDrawArrays(GL_TRIANGLES, 0, self.n)

    @staticmethod
    def desenlazar():
        for loc in (LOC_POS, LOC_NRM, LOC_COL, LOC_AUX):
            glDisableVertexAttribArray(loc)
        glBindBuffer(GL_ARRAY_BUFFER, 0)


def _juntar(a, b):
    if len(a[0]) == 0:
        return b
    if len(b[0]) == 0:
        return a
    return tuple(np.ascontiguousarray(np.concatenate([x, y])) for x, y in zip(a, b))


class App:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Mundo 3D con las manos")
        pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE, 24)
        try:
            pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLEBUFFERS, 1)
            pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLESAMPLES, 4)
            pygame.display.set_mode((ANCHO, ALTO), DOUBLEBUF | OPENGL)
        except pygame.error:
            pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLEBUFFERS, 0)
            pygame.display.set_mode((ANCHO, ALTO), DOUBLEBUF | OPENGL)

        self.reloj = pygame.time.Clock()
        self.fuente = pygame.font.SysFont("segoeui", 17)
        self.fuente_bold = pygame.font.SysFont("segoeui", 19, bold=True)
        self.fuente_grande = pygame.font.SysFont("segoeui", 24, bold=True)
        self._textos = {}

        self.mundo = Mundo()
        self.mundo.generar_terreno(registrar=False)
        self.fauna = Fauna(self.mundo)
        self.color = 8
        self.malla_version = -1
        self.gpu_solido = MallaGPU()
        self.gpu_agua = MallaGPU()
        self.gpu_fauna = MallaGPU(nbuf=3, dinamico=True)

        w, _, d = self.mundo.tam
        self.objetivo = np.array([w / 2, 4.0, d / 2], dtype=np.float32)
        self.yaw, self.pitch, self.dist = math.radians(35), math.radians(40), 92.0

        self.hora = 0.34
        self.ciclo_activo = True
        self.vel_ciclo = 1.0
        self.t_agua = 0.0
        self.cielo = estado_cielo(self.hora)
        self.estrellas_pts, self.estrellas_brillo, self.estrellas_tam, self.estrellas_2d = campo_estrellas(
            ancho=ANCHO, alto=ALTO
        )

        self.tracker = HandTracker()
        self.tracker.start()
        self.ultimo_frame = -1
        self.preview_frame = -1
        self.mano_puntero = "Right"
        self.puntero = EstadoMano()
        self.camara = EstadoMano()
        self.ancla_orbita = self.ancla_zoom = None
        self.raton_orbita = None

        self.hover = (None, None)
        self.mensaje, self.mensaje_t = "", 0.0
        self.mostrar_ayuda = True
        self.mostrar_preview = True
        self.corriendo = True
        self.shaders_ok = False
        self.prog_solido = self.prog_agua = self.prog_fauna = None
        self.u_solido = self.u_agua = self.u_fauna = {}
        self.tex_atlas = None

        self.botones = []
        for i, (texto, accion) in enumerate([
            ("Nuevo terreno", self.nuevo_terreno),
            ("Deshacer", self.deshacer),
            ("Limpiar", self.limpiar),
            ("Guardar", self.guardar),
            ("Cargar", self.cargar),
            ("Cambiar manos", self.cambiar_manos),
            ("Pausar cielo", self.pausar_cielo),
            ("Avanzar hora", self.avanzar_hora),
        ]):
            self.botones.append([texto, pygame.Rect(ANCHO - 186, 16 + i * 46, 170, 40), accion])

        n, lado, sep = len(PALETA) - 1, 52, 8
        x0 = (ANCHO - (n * lado + (n - 1) * sep)) // 2
        self.rect_colores = [pygame.Rect(x0 + i * (lado + sep), ALTO - lado - 18, lado, lado) for i in range(n)]

        self.init_gl()

    # ------------------------------------------------------------------ acciones
    def avisar(self, texto):
        self.mensaje, self.mensaje_t = texto, time.perf_counter()

    def nuevo_terreno(self):
        self.mundo.generar_terreno()
        self.fauna = Fauna(self.mundo)
        self.avisar("Terreno nuevo y fauna nueva")

    def deshacer(self):
        self.avisar("Deshecho" if self.mundo.deshacer() else "Nada que deshacer")

    def limpiar(self):
        self.mundo.limpiar()
        self.fauna = Fauna(self.mundo)
        self.fauna.vivo[:] = False
        self.avisar("Mundo vacío: ¡a construir!")

    def guardar(self):
        self.mundo.guardar(ARCHIVO_MUNDO)
        self.avisar("Mundo guardado en mundo_guardado.npy")

    def cargar(self):
        try:
            self.mundo.cargar(ARCHIVO_MUNDO)
            self.fauna = Fauna(self.mundo)
            self.avisar("Mundo cargado")
        except FileNotFoundError:
            self.avisar("Todavía no hay un mundo guardado")
        except Exception as e:
            self.avisar(f"No se pudo cargar: {e}")

    def cambiar_manos(self):
        self.mano_puntero = "Left" if self.mano_puntero == "Right" else "Right"
        self.puntero.reiniciar()
        self.camara.reiniciar()
        self.ancla_orbita = self.ancla_zoom = None
        nombre = "derecha" if self.mano_puntero == "Right" else "izquierda"
        self.avisar(f"Ahora el puntero es la mano {nombre}")

    def pausar_cielo(self):
        self.ciclo_activo = not self.ciclo_activo
        self.botones[6][0] = "Reanudar cielo" if not self.ciclo_activo else "Pausar cielo"
        self.avisar("Cielo en pausa" if not self.ciclo_activo else "El día vuelve a correr")

    def avanzar_hora(self):
        self.hora = (self.hora + 0.25) % 1.0
        self.cielo = estado_cielo(self.hora)
        self.avisar(self.cielo.nombre)

    def ui_en(self, pos):
        if pos is None:
            return None
        for i, (_, rect, _) in enumerate(self.botones):
            if rect.collidepoint(pos):
                return ("boton", i)
        for i, rect in enumerate(self.rect_colores):
            if rect.collidepoint(pos):
                return ("color", i + 1)
        return None

    def poner_en(self, pos):
        ui = self.ui_en(pos)
        if ui:
            if ui[0] == "boton":
                self.botones[ui[1]][2]()
            else:
                self.color = ui[1]
                self.avisar(f"Color: {NOMBRES[self.color]}")
            return
        _, celda = self.raycast_pantalla(pos)
        self.mundo.poner(celda, self.color)

    def quitar_en(self, pos):
        if self.ui_en(pos):
            return
        bloque, _ = self.raycast_pantalla(pos)
        self.mundo.quitar(bloque)

    # ------------------------------------------------------------------ cámara
    def base_camara(self):
        cp = math.cos(self.pitch)
        ojo = self.objetivo + self.dist * np.array([cp * math.sin(self.yaw), math.sin(self.pitch),
                                                    cp * math.cos(self.yaw)], dtype=np.float32)
        f = self.objetivo - ojo
        f /= np.linalg.norm(f)
        r = np.cross(f, (0.0, 1.0, 0.0))
        r /= np.linalg.norm(r)
        return ojo, f, r, np.cross(r, f)

    def raycast_pantalla(self, pos):
        if pos is None:
            return None, None
        ojo, f, r, u = self.base_camara()
        nx = 2 * pos[0] / ANCHO - 1
        ny = 1 - 2 * pos[1] / ALTO
        th = math.tan(math.radians(FOV) / 2)
        d = f + r * nx * th * (ANCHO / ALTO) + u * ny * th
        return self.mundo.raycast(ojo, d / np.linalg.norm(d))

    def limitar_camara(self):
        self.pitch = min(max(self.pitch, math.radians(5)), math.radians(85))
        self.dist = min(max(self.dist, 10.0), 240.0)

    # ------------------------------------------------------------------ entrada
    def cursor_actual(self):
        if self.puntero.visible and self.puntero.cursor is not None:
            return float(self.puntero.cursor[0]), float(self.puntero.cursor[1])
        return pygame.mouse.get_pos() if pygame.mouse.get_focused() else None

    def procesar_eventos(self, dt):
        for ev in pygame.event.get():
            if ev.type == QUIT:
                self.corriendo = False
            elif ev.type == KEYDOWN:
                self.tecla(ev)
            elif ev.type == MOUSEBUTTONDOWN:
                if ev.button == 1:
                    self.poner_en(ev.pos)
                elif ev.button == 3:
                    self.quitar_en(ev.pos)
                elif ev.button == 2:
                    self.raton_orbita = ev.pos
            elif ev.type == MOUSEBUTTONUP and ev.button == 2:
                self.raton_orbita = None
            elif ev.type == MOUSEMOTION and self.raton_orbita:
                dx, dy = ev.rel
                self.yaw -= dx * 0.008
                self.pitch += dy * 0.008
            elif ev.type == MOUSEWHEEL:
                self.dist *= 0.9 ** ev.y

        teclas = pygame.key.get_pressed()
        self.yaw += (teclas[K_LEFT] - teclas[K_RIGHT]) * 1.6 * dt
        self.pitch += (teclas[K_UP] - teclas[K_DOWN]) * 1.2 * dt
        self.dist *= 1.0 + (teclas[K_PAGEDOWN] - teclas[K_PAGEUP]) * 1.2 * dt
        self.limitar_camara()

    def tecla(self, ev):
        k = ev.key
        if k == K_ESCAPE:
            self.corriendo = False
        elif pygame.K_1 <= k <= pygame.K_9:
            self.color = k - pygame.K_0
            self.avisar(f"Color: {NOMBRES[self.color]}")
        elif k == pygame.K_t:
            self.nuevo_terreno()
        elif k == pygame.K_z:
            self.deshacer()
        elif k == pygame.K_c:
            self.limpiar()
        elif k == pygame.K_g:
            self.guardar()
        elif k == pygame.K_l:
            self.cargar()
        elif k == pygame.K_m:
            self.cambiar_manos()
        elif k == pygame.K_p:
            self.mostrar_preview = not self.mostrar_preview
        elif k == pygame.K_n:
            self.pausar_cielo()
        elif k == pygame.K_v:
            self.hora = 0.50
            self.cielo = estado_cielo(self.hora)
            self.avisar("Mediodía")
        elif k == pygame.K_b:
            self.hora = 0.02
            self.cielo = estado_cielo(self.hora)
            self.avisar("Noche")
        elif k in (pygame.K_COMMA, pygame.K_MINUS):
            self.vel_ciclo = max(0.25, self.vel_ciclo / 2)
            self.avisar(f"Velocidad del cielo ×{self.vel_ciclo:g}")
        elif k in (pygame.K_PERIOD, pygame.K_PLUS, pygame.K_EQUALS):
            self.vel_ciclo = min(16.0, self.vel_ciclo * 2)
            self.avisar(f"Velocidad del cielo ×{self.vel_ciclo:g}")
        elif k in (K_F1, pygame.K_h):
            self.mostrar_ayuda = not self.mostrar_ayuda

    def procesar_manos(self, t):
        manos, frame = self.tracker.manos()
        if frame == self.ultimo_frame:
            return
        self.ultimo_frame = frame

        punt = cam = None
        for m in sorted(manos, key=lambda m: -m.confianza):
            if m.etiqueta == self.mano_puntero and punt is None:
                punt = m
            elif cam is None:
                cam = m
            elif punt is None:
                punt = m

        aspecto = self.tracker.aspecto
        for ev in self.puntero.actualizar(punt, aspecto, t):
            if ev == "indice_on":
                self.poner_en(self.puntero.pos_pasada(RETARDO_ACCION))
            elif ev == "medio_on":
                self.quitar_en(self.puntero.pos_pasada(RETARDO_ACCION))

        for ev in self.camara.actualizar(cam, aspecto, t):
            if ev == "indice_on":
                self.ancla_orbita = (self.camara.palma.copy(), self.yaw, self.pitch)
            elif ev == "indice_off":
                self.ancla_orbita = None
            elif ev == "medio_on":
                self.ancla_zoom = (self.camara.palma.copy(), self.dist)
            elif ev == "medio_off":
                self.ancla_zoom = None

        if self.ancla_orbita and self.camara.pinza_indice:
            p0, yaw0, pitch0 = self.ancla_orbita
            dx, dy = self.camara.palma - p0
            self.yaw = yaw0 - dx * 4.5
            self.pitch = pitch0 + dy * 3.0
        if self.ancla_zoom and self.camara.pinza_medio:
            p0, dist0 = self.ancla_zoom
            self.dist = dist0 * math.exp((self.camara.palma[1] - p0[1]) * 3.0)
        self.limitar_camara()

    def modo_quitar(self):
        p = self.puntero
        return p.visible and (p.pinza_medio or (not p.pinza_indice and p.ratio_medio < p.ratio_indice
                                                 and p.ratio_medio < 0.6))

    # ------------------------------------------------------------------ OpenGL
    def init_gl(self):
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_LINE_SMOOTH)
        glEnable(GL_CULL_FACE)
        glCullFace(GL_BACK)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glFogi(GL_FOG_MODE, GL_LINEAR)
        self.tex_preview = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.tex_preview)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        atlas = atlas_rgba()
        self.tex_atlas = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.tex_atlas)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, atlas.shape[1], atlas.shape[0], 0,
                     GL_RGBA, GL_UNSIGNED_BYTE, atlas)
        try:
            self.prog_solido = compilar(SOLIDO_VERT, SOLIDO_FRAG, ATRIBUTOS)
            self.prog_agua = compilar(AGUA_VERT, AGUA_FRAG, ATRIBUTOS)
            self.prog_fauna = compilar(ANIMAL_VERT, ANIMAL_FRAG, ATRIBUTOS)
            self.u_solido = uniforms(self.prog_solido, UNIFORMES)
            self.u_agua = uniforms(self.prog_agua, UNIFORMES)
            self.u_fauna = uniforms(self.prog_fauna, UNIFORMES)
            self.shaders_ok = True
        except Exception as e:
            print("No se pudieron cargar los shaders, uso el render básico:", e)
            self.shaders_ok = False

    def modo_3d(self):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(FOV, ANCHO / ALTO, 0.15, 900.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        ojo = self.base_camara()[0]
        gluLookAt(*ojo, *self.objetivo, 0, 1, 0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_FOG)
        glFogfv(GL_FOG_COLOR, (*self.cielo.niebla, 1.0))
        glFogf(GL_FOG_START, self.dist * 0.85)
        glFogf(GL_FOG_END, min(420.0, self.dist * 2.4))

    def modo_2d(self):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, ANCHO, ALTO, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_FOG)
        glDisable(GL_CULL_FACE)

    def _luz_uniforms(self, prog_u):
        c = self.cielo
        ojo = self.base_camara()[0]
        glUniform3f(prog_u["u_sun_dir"], *c.sol_dir)
        glUniform3f(prog_u["u_sun_color"], *c.sol_color)
        glUniform3f(prog_u["u_ambient"], *c.ambiente)
        glUniform3f(prog_u["u_luna_dir"], *c.luna_dir)
        glUniform1f(prog_u["u_sun_fuerza"], c.sol_fuerza)
        glUniform1f(prog_u["u_luna_fuerza"], c.luna_fuerza)
        glUniform3f(prog_u["u_cam_pos"], *ojo)
        glUniform1f(prog_u["u_time"], self.t_agua)
        if prog_u.get("u_atlas", -1) >= 0:
            glUniform1i(prog_u["u_atlas"], 0)

    def actualizar_mallas(self):
        if self.malla_version == self.mundo.version:
            return
        solido, lados, superficie = self.mundo.construir_mallas()
        self.gpu_solido.cargar(*solido)
        self.gpu_agua.cargar(*_juntar(lados, superficie))
        self.malla_version = self.mundo.version

    def dibujar(self):
        glViewport(0, 0, ANCHO, ALTO)
        glClearColor(*self.cielo.cielo_abajo, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.modo_2d()
        self.dibujar_cielo()
        self.modo_3d()
        self.dibujar_cielo_3d()
        self.dibujar_suelo()
        self.actualizar_mallas()
        self.dibujar_mundo()
        self.dibujar_fauna()
        self.dibujar_seleccion()
        self.modo_2d()
        self.dibujar_hud()
        pygame.display.flip()

    def dibujar_cielo(self):
        glBegin(GL_QUADS)
        glColor3f(*self.cielo.cielo_arriba)
        glVertex2f(0, 0)
        glVertex2f(ANCHO, 0)
        glColor3f(*self.cielo.cielo_abajo)
        glVertex2f(ANCHO, ALTO)
        glVertex2f(0, ALTO)
        glEnd()
        if self.cielo.estrellas > 0.02:
            glEnable(GL_POINT_SMOOTH)
            glPointSize(2.8)
            glBegin(GL_POINTS)
            a = self.cielo.estrellas
            for x, y, b in self.estrellas_2d:
                glColor4f(0.92, 0.95, 1.0, min(1.0, float(b) * a * 1.35))
                glVertex2f(float(x), float(y))
            glEnd()
            glPointSize(1.0)

    def _disco(self, centro, radio, color, segmentos=28):
        _, _f, r, u = self.base_camara()
        glBegin(GL_TRIANGLE_FAN)
        glColor4f(*color)
        glVertex3f(*centro)
        for i in range(segmentos + 1):
            a = i / segmentos * math.tau
            glVertex3f(*(centro + (math.cos(a) * r + math.sin(a) * u) * radio))
        glEnd()

    def dibujar_cielo_3d(self):
        ojo = self.base_camara()[0]
        glDisable(GL_FOG)
        glDepthMask(GL_FALSE)
        glDisable(GL_CULL_FACE)

        if self.cielo.estrellas > 0.02:
            glEnable(GL_POINT_SMOOTH)
            glPointSize(2.2)
            glBegin(GL_POINTS)
            a = self.cielo.estrellas
            for p, b in zip(self.estrellas_pts, self.estrellas_brillo):
                glColor4f(0.85, 0.9, 1.0, float(b) * a)
                glVertex3f(*(self.objetivo + p * 210.0))
            glEnd()
            glPointSize(1.0)

        if self.cielo.sol_fuerza > 0.02:
            pos = ojo + self.cielo.sol_dir * 190.0
            self._disco(pos, 18.0 + 10.0 * self.cielo.sol_fuerza, (*self.cielo.sol_color, 0.18))
            self._disco(pos, 6.5, (1.0, 0.96, 0.78, 1.0))
        if self.cielo.luna_fuerza > 0.05:
            pos = ojo + self.cielo.luna_dir * 175.0
            self._disco(pos, 8.0, (0.55, 0.62, 0.78, 0.16))
            self._disco(pos, 3.6, (0.86, 0.90, 0.96, 0.95))

        glDepthMask(GL_TRUE)
        glEnable(GL_FOG)

    def dibujar_suelo(self):
        w, _, d = self.mundo.tam
        s = self.cielo.suelo
        glDisable(GL_CULL_FACE)
        glBegin(GL_QUADS)
        glColor3f(s[0] * 0.72, s[1] * 0.72, s[2] * 0.72)
        for x, z in ((-400, -400), (400 + w, -400), (400 + w, 400 + d), (-400, 400 + d)):
            glVertex3f(x, -0.05, z)
        glColor3f(*s)
        for x, z in ((0, 0), (w, 0), (w, d), (0, d)):
            glVertex3f(x, 0, z)
        glEnd()

    def dibujar_mundo(self):
        if self.shaders_ok:
            glActiveTexture(GL_TEXTURE0)
            glBindTexture(GL_TEXTURE_2D, self.tex_atlas)
            glUseProgram(self.prog_solido)
            self._luz_uniforms(self.u_solido)
            glEnable(GL_CULL_FACE)
            glEnable(GL_ALPHA_TEST)
            glAlphaFunc(GL_GREATER, 0.35)
            self.gpu_solido.enlazar()
            self.gpu_solido.dibujar()
            MallaGPU.desenlazar()
            glDisable(GL_ALPHA_TEST)

            if self.gpu_agua.n:
                glUseProgram(self.prog_agua)
                self._luz_uniforms(self.u_agua)
                glDisable(GL_CULL_FACE)
                glEnable(GL_BLEND)
                glDepthMask(GL_FALSE)
                self.gpu_agua.enlazar()
                self.gpu_agua.dibujar()
                MallaGPU.desenlazar()
                glDepthMask(GL_TRUE)
            glUseProgram(0)
            return

        self._dibujar_malla_basica(self.gpu_solido, opaco=True)
        self._dibujar_malla_basica(self.gpu_agua, opaco=False)

    def dibujar_fauna(self):
        if not self.gpu_fauna.n:
            return
        if self.shaders_ok and self.prog_fauna:
            glUseProgram(self.prog_fauna)
            self._luz_uniforms(self.u_fauna)
            glEnable(GL_CULL_FACE)
            self.gpu_fauna.enlazar()
            self.gpu_fauna.dibujar()
            MallaGPU.desenlazar()
            glUseProgram(0)
            return
        self._dibujar_malla_basica(self.gpu_fauna, opaco=True)

    def _dibujar_malla_basica(self, malla, opaco):
        if not malla.n:
            return
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_COLOR_ARRAY)
        glBindBuffer(GL_ARRAY_BUFFER, int(malla.ids[0]))
        glVertexPointer(3, GL_FLOAT, 0, _PTR0)
        glBindBuffer(GL_ARRAY_BUFFER, int(malla.ids[2]))
        glColorPointer(3, GL_FLOAT, 0, _PTR0)
        if not opaco:
            glDepthMask(GL_FALSE)
            glColor4f(0.15, 0.45, 0.7, 0.65)
        glDrawArrays(GL_TRIANGLES, 0, malla.n)
        if not opaco:
            glDepthMask(GL_TRUE)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glDisableClientState(GL_COLOR_ARRAY)
        glDisableClientState(GL_VERTEX_ARRAY)

    def cubo_alambre(self, celda, color, grosor=3.0, margen=0.02):
        x, y, z = celda
        s = 1 + 2 * margen
        glLineWidth(grosor)
        glColor4f(*color)
        glBegin(GL_LINES)
        for a, b in _ARISTAS:
            for vx, vy, vz in (_VERTICES_CUBO[a], _VERTICES_CUBO[b]):
                glVertex3f(x - margen + vx * s, y - margen + vy * s, z - margen + vz * s)
        glEnd()
        glLineWidth(1.0)

    def cubo_solido(self, celda, color):
        x, y, z = celda
        glBegin(GL_QUADS)
        for _, esquinas, sombra in CARAS:
            glColor4f(color[0] * sombra, color[1] * sombra, color[2] * sombra, color[3])
            for ex, ey, ez in esquinas:
                glVertex3f(x + ex, y + ey, z + ez)
        glEnd()

    def dibujar_seleccion(self):
        glUseProgram(0)
        glDisable(GL_CULL_FACE)
        bloque, celda = self.hover
        if self.modo_quitar():
            if bloque:
                glDepthMask(GL_FALSE)
                self.cubo_solido(bloque, (1.0, 0.2, 0.2, 0.35))
                glDepthMask(GL_TRUE)
                self.cubo_alambre(bloque, (1.0, 0.25, 0.25, 1.0))
            return
        if bloque:
            self.cubo_alambre(bloque, (1, 1, 1, 0.9), grosor=2.0)
        if celda and self.mundo.dentro(*celda):
            glDepthMask(GL_FALSE)
            self.cubo_solido(celda, (*PALETA[self.color], 0.5))
            glDepthMask(GL_TRUE)
            self.cubo_alambre(celda, (1, 1, 0.3, 1.0), grosor=2.0, margen=0.0)

    # ------------------------------------------------------------------ HUD
    def rect(self, x, y, w, h, color):
        glColor4f(*color)
        glBegin(GL_QUADS)
        glVertex2f(x, y)
        glVertex2f(x + w, y)
        glVertex2f(x + w, y + h)
        glVertex2f(x, y + h)
        glEnd()

    def marco(self, x, y, w, h, color, grosor=2.0):
        glLineWidth(grosor)
        glColor4f(*color)
        glBegin(GL_LINE_LOOP)
        glVertex2f(x, y)
        glVertex2f(x + w, y)
        glVertex2f(x + w, y + h)
        glVertex2f(x, y + h)
        glEnd()
        glLineWidth(1.0)

    def circulo(self, x, y, r, color, relleno=True, grosor=2.0):
        glColor4f(*color)
        if relleno:
            glBegin(GL_TRIANGLE_FAN)
            glVertex2f(x, y)
        else:
            glLineWidth(grosor)
            glBegin(GL_LINE_STRIP)
        for cx, cy in _CIRCULO:
            glVertex2f(x + cx * r, y + cy * r)
        glEnd()
        glLineWidth(1.0)

    def texto(self, s, x, y, color=(255, 255, 255), fuente=None, centro=False):
        fuente = fuente or self.fuente
        clave = (s, color, id(fuente))
        if clave not in self._textos:
            if len(self._textos) > 400:
                glDeleteTextures([t for t, _, _ in self._textos.values()])
                self._textos.clear()
            sup = fuente.render(s, True, color)
            w, h = sup.get_size()
            tex = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, tex)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE,
                         pygame.image.tobytes(sup, "RGBA", False))
            self._textos[clave] = (tex, w, h)
        tex, w, h = self._textos[clave]
        if centro:
            x, y = x - w / 2, y - h / 2
        self.textura(tex, x, y, w, h)
        return w, h

    def textura(self, tex, x, y, w, h):
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, tex)
        glColor4f(1, 1, 1, 1)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0)
        glVertex2f(x, y)
        glTexCoord2f(1, 0)
        glVertex2f(x + w, y)
        glTexCoord2f(1, 1)
        glVertex2f(x + w, y + h)
        glTexCoord2f(0, 1)
        glVertex2f(x, y + h)
        glEnd()
        glDisable(GL_TEXTURE_2D)

    def dibujar_hud(self):
        cursor = self.cursor_actual()
        ui_hover = self.ui_en(cursor)

        if self.mostrar_ayuda:
            lineas = [
                ("MANO DERECHA  (puntero)" if self.mano_puntero == "Right" else "MANO IZQUIERDA  (puntero)", True),
                ("  Punta del índice: mueve el cursor", False),
                ("  Pellizco pulgar + índice: poner bloque / botón", False),
                ("  Pellizco pulgar + medio: quitar bloque", False),
                ("MANO IZQUIERDA  (cámara)" if self.mano_puntero == "Right" else "MANO DERECHA  (cámara)", True),
                ("  Pellizco pulgar + índice y mover: girar", False),
                ("  Pellizco pulgar + medio y subir/bajar: zoom", False),
                ("Cielo: N pausa  V día  B noche  ,/. velocidad", False),
                ("12 animales: comen, cazan, huyen y se reproducen", False),
                ("Teclas: 1-9 color  T terreno  Z deshacer  C limpiar", False),
                ("G guardar  L cargar  M manos  P cámara  H ayuda", False),
            ]
            self.rect(12, 12, 430, 16 + len(lineas) * 23, (0, 0, 0, 0.45))
            for i, (linea, titulo) in enumerate(lineas):
                self.texto(linea, 22, 18 + i * 23, (255, 230, 120) if titulo else (235, 235, 235),
                           self.fuente_bold if titulo else self.fuente)

        for i, (nombre, r, _) in enumerate(self.botones):
            activo = ui_hover == ("boton", i)
            self.rect(r.x, r.y, r.w, r.h, (0.15, 0.45, 0.95, 0.85) if activo else (0, 0, 0, 0.5))
            self.marco(r.x, r.y, r.w, r.h, (1, 1, 1, 0.6 if activo else 0.25))
            self.texto(nombre, r.centerx, r.centery, fuente=self.fuente_bold, centro=True)

        for i, r in enumerate(self.rect_colores):
            c = i + 1
            elegido = c == self.color
            crece = 6 if elegido else (3 if ui_hover == ("color", c) else 0)
            self.rect(r.x - crece, r.y - crece, r.w + 2 * crece, r.h + 2 * crece, (*PALETA[c], 1.0))
            self.marco(r.x - crece, r.y - crece, r.w + 2 * crece, r.h + 2 * crece,
                       (1, 1, 1, 1) if elegido else (0, 0, 0, 0.5), 3.0 if elegido else 1.5)
            self.texto(str(c), r.x + 4 - crece, r.y + 1 - crece, (0, 0, 0))
        r0 = self.rect_colores[0]
        self.texto(f"Bloque: {NOMBRES[self.color]}", ANCHO / 2, r0.y - 22, fuente=self.fuente_bold, centro=True)

        reloj = f"{hora_reloj(self.hora)}  {self.cielo.nombre}"
        if not self.ciclo_activo:
            reloj += "  (pausa)"
        self.texto(reloj, ANCHO / 2, 18, (255, 230, 160), self.fuente_bold, centro=True)

        if self.mostrar_preview:
            img, fid = self.tracker.preview()
            if img is not None:
                h, w = img.shape[:2]
                if fid != self.preview_frame:
                    glBindTexture(GL_TEXTURE_2D, self.tex_preview)
                    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, w, h, 0, GL_RGB, GL_UNSIGNED_BYTE, img)
                    self.preview_frame = fid
                pw, ph = 256, 192
                px, py = 14, ALTO - ph - 14
                self.textura(self.tex_preview, px, py, pw, ph)
                self.marco(px, py, pw, ph, (1, 1, 1, 0.7))

        self.dibujar_manos()

        if self.tracker.error:
            self.texto(self.tracker.error + "  (puedes usar el ratón)", ANCHO / 2, 20, (255, 120, 120),
                       self.fuente_bold, centro=True)
        elif not self.tracker.listo:
            self.texto("Iniciando cámara y modelo de manos...", ANCHO / 2, 20, (255, 255, 255),
                       self.fuente_bold, centro=True)
        if self.mensaje and time.perf_counter() - self.mensaje_t < 2.5:
            w = self.fuente_grande.size(self.mensaje)[0]
            self.rect(ANCHO / 2 - w / 2 - 16, 44, w + 32, 40, (0, 0, 0, 0.55))
            self.texto(self.mensaje, ANCHO / 2, 64, fuente=self.fuente_grande, centro=True)

        vivos = int(np.sum(self.fauna.vivo & (self.fauna.estado != MUERTO)))
        manos = int(self.puntero.visible) + int(self.camara.visible)
        self.texto(f"{self.reloj.get_fps():.0f} FPS  |  {vivos} animales  |  manos: {manos}",
                   ANCHO - 16 - 310, ALTO - 26, (230, 230, 230))
        if self.mostrar_ayuda:
            lineas_f = self.fauna.conteo()
            self.rect(12, 268, 210, 16 + len(lineas_f) * 18, (0, 0, 0, 0.42))
            self.texto("CADENA ALIMENTICIA", 20, 272, (255, 210, 120), self.fuente_bold)
            for i, (nom, n) in enumerate(lineas_f):
                self.texto(f"{nom}: {n}", 22, 292 + i * 18, (220, 220, 220))

    def dibujar_manos(self):
        for estado, rol in ((self.camara, "Cámara"), (self.puntero, "Puntero")):
            if not estado.visible:
                continue
            for i, (x, y) in enumerate(estado.puntas):
                if estado is self.puntero and i == 1:
                    continue
                self.circulo(x, y, 7, (*COLOR_PUNTA[i], 0.9))
                self.circulo(x, y, 7, (0, 0, 0, 0.6), relleno=False, grosor=1.5)
            if estado is self.camara:
                x, y = estado.puntas[1]
                if self.camara.pinza_indice:
                    self.texto("Girando", x + 14, y - 10, (255, 200, 80), self.fuente_bold)
                elif self.camara.pinza_medio:
                    self.texto("Zoom", x + 14, y - 10, (255, 200, 80), self.fuente_bold)
                else:
                    self.texto(rol, x + 14, y - 10, (255, 255, 255))

        p = self.puntero
        if p.visible and p.cursor is not None:
            x, y = p.cursor
            quitar = self.modo_quitar()
            ratio = p.ratio_medio if quitar else p.ratio_indice
            if p.pinza_indice or p.pinza_medio:
                self.circulo(x, y, 14, (1.0, 0.25, 0.25, 0.9) if p.pinza_medio else (0.2, 1.0, 0.4, 0.9))
            else:
                progreso = min(max((ratio - PELLIZCO_ON) / (0.9 - PELLIZCO_ON), 0.0), 1.0)
                self.circulo(x, y, 12 + 26 * progreso,
                             (1.0, 0.35, 0.35, 0.9) if quitar else (0.3, 0.95, 1.0, 0.9), relleno=False, grosor=3)
            self.circulo(x, y, 5, (1, 1, 1, 1))
            self.texto("Quitar" if quitar else "Puntero", x + 18, y + 8, (255, 255, 255))

    # ------------------------------------------------------------------ bucle
    def actualizar_hover(self):
        cursor = self.cursor_actual()
        self.hover = (None, None) if (cursor is None or self.ui_en(cursor)) else self.raycast_pantalla(cursor)

    def ejecutar(self):
        try:
            while self.corriendo:
                dt = self.reloj.tick(60) / 1000.0
                self.t_agua += dt
                if self.ciclo_activo:
                    self.hora = (self.hora + dt / SEGUNDOS_DIA * self.vel_ciclo) % 1.0
                self.cielo = estado_cielo(self.hora)
                self.procesar_eventos(dt)
                self.procesar_manos(time.perf_counter())
                ojo = self.base_camara()[0]
                self.fauna.actualizar(dt, cam=ojo)
                self.gpu_fauna.cargar(*self.fauna.malla_visible(ojo, radio=max(70.0, self.dist * 1.15)))
                self.actualizar_hover()
                self.dibujar()
        finally:
            self.tracker.detener()
            self.tracker.join(timeout=2)
            pygame.quit()


if __name__ == "__main__":
    App().ejecutar()

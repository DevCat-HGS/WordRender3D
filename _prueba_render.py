import math

import numpy as np
import pygame
from OpenGL.GL import glReadPixels, GL_RGB, GL_UNSIGNED_BYTE

import main
from fauna import CIERVO, MUERTO
from tiempo import LLUVIA, NEVADO, TORNADO


class TrackerFalso:
    listo, error, fps, aspecto = True, None, 30.0, 4 / 3

    def start(self): pass
    def detener(self): pass
    def join(self, timeout=None): pass
    def manos(self): return [], 0
    def preview(self): return None, 0


def leer(nombre):
    datos = glReadPixels(0, 0, main.ANCHO, main.ALTO, GL_RGB, GL_UNSIGNED_BYTE)
    img = np.frombuffer(datos, np.uint8).reshape(main.ALTO, main.ANCHO, 3)[::-1]
    pygame.image.save(pygame.surfarray.make_surface(img.swapaxes(0, 1)), nombre)


def tick(app, n=10):
    for i in range(n):
        dt = 0.05
        app.t_agua += dt
        app.clima_est = app.tiempo.actualizar(dt)
        app.tiempo.teñir(app.cielo)
        ojo = app.base_camara()[0]
        app.fauna.actualizar(dt, cam=ojo, clima=app.clima_est)
        app.frutas.actualizar(dt, app.clima_est, app.fauna)
        app.gpu_fauna.cargar(*app.fauna.malla_visible(ojo, 130))
        app.gpu_frutas.cargar(*app.frutas.malla_visible(ojo, 130))
        app.dibujar()


main.HandTracker = TrackerFalso
app = main.App()
app.mundo.generar_terreno(semilla=2, registrar=False)
app.fauna = main.Fauna(app.mundo, semilla=2)
app.frutas = main.Frutas(app.mundo, semilla=2)
app.malla_version = -1
app.mostrar_ayuda = False
app.ciclo_activo = False
app.hora = 0.45
app.cielo = main.estado_cielo(app.hora)
app.elegir_clima(LLUVIA)
tick(app, 12)
leer("captura.png")

vivos = np.nonzero(app.fauna.vivo & (app.fauna.estado != MUERTO) & (app.fauna.esp == CIERVO))[0]
if len(vivos):
    app.objetivo = app.fauna.pos[vivos[0]].copy()
    app.dist, app.pitch = 11.0, math.radians(18)
    tick(app, 6)
    leer("captura_fauna.png")

app.objetivo = np.array([app.mundo.tam[0] / 2, 4, app.mundo.tam[2] / 2], np.float32)
app.dist, app.pitch = 92.0, math.radians(40)
app.elegir_clima(NEVADO)
app.cielo = main.estado_cielo(0.45)
tick(app, 8)
leer("captura_noche.png")
pygame.quit()
print("ok", app.frutas.conteo())

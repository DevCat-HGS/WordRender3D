"""Convierte lo que hacen las manos en órdenes: apuntar, pellizcar, arrastrar, girar, zoom y contar dedos."""
from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass

from . import config
from .manos import Mano

ESPERA_DOS_MANOS = 0.12   # s de margen para distinguir "pellizco con una mano" de "zoom con las dos"
RETRASO_BLOQUEO = 0.15    # s: al pellizcar, el índice se mueve hacia el pulgar; se usa donde apuntaba antes


def a_pantalla(punto) -> tuple[float, float]:
    """De coordenadas de la cámara a coordenadas de la ventana (0-1, origen arriba a la izquierda)."""
    x0, y0, x1, y1 = config.ZONA_ACTIVA
    return (punto[0] - x0) / (x1 - x0), (punto[1] - y0) / (y1 - y0)


def _dentro(p: tuple[float, float]) -> tuple[float, float]:
    return min(max(p[0], 0.0), 1.0), min(max(p[1], 0.0), 1.0)


@dataclass
class Lectura:
    """Lo que pidieron las manos en este cuadro."""
    principal: Mano | None = None
    secundaria: Mano | None = None
    cursor: tuple[float, float] | None = None     # a dónde apunta el índice de la mano principal
    clic: tuple[float, float] | None = None       # empezó un pellizco (en la posición de antes de pellizcar)
    arrastrando: bool = False                     # el pellizco sigue cerrado
    soltar: bool = False                          # se abrió el pellizco
    giro: tuple[float, float] = (0.0, 0.0)        # cuánto se movió la mano que gira el mundo
    zoom: float = 1.0                             # >1 aleja la cámara, <1 la acerca
    conteo: tuple[int, float] | None = None       # dedos que muestra la mano secundaria y progreso (0-1)
    herramienta: int | None = None                # herramienta elegida al terminar de contar dedos


class Gestos:
    def __init__(self):
        self._historial: deque[tuple[float, tuple[float, float]]] = deque(maxlen=30)
        self._estado = "libre"        # libre | pendiente | trazo | zoom | esperar_soltar
        self._inicio_pendiente = 0.0
        self._clic_guardado: tuple[float, float] | None = None
        self._giro_anterior: tuple[float, float] | None = None
        self._distancia_zoom: float | None = None
        self._conteo: tuple[int, float] | None = None   # (dedos, desde cuándo)
        self._conteo_usado = False

    def actualizar(self, manos: tuple[Mano, ...], ahora: float) -> Lectura:
        principal = next((m for m in manos if m.lado == config.MANO_PRINCIPAL), None)
        secundaria = next((m for m in manos if m.lado != config.MANO_PRINCIPAL), None)
        lectura = Lectura(principal=principal, secundaria=secundaria)
        if principal is not None:
            lectura.cursor = _dentro(a_pantalla(principal.indice))
            self._historial.append((ahora, lectura.cursor))
        else:
            self._historial.clear()
        self._pellizco_principal(lectura, ahora)
        self._zoom(lectura)
        self._mano_secundaria(lectura, ahora)
        return lectura

    def _pellizco_principal(self, lectura: Lectura, ahora: float):
        pellizca = lectura.principal is not None and lectura.principal.pellizcando
        otra = lectura.secundaria is not None and lectura.secundaria.pellizcando
        estado = self._estado
        if estado == "libre":
            if pellizca:
                self._estado = "zoom" if otra else "pendiente"
                self._inicio_pendiente = ahora
                self._clic_guardado = self._cursor_en(ahora - RETRASO_BLOQUEO)
        elif estado == "pendiente":
            if otra:
                self._estado = "zoom"
            elif not pellizca:
                lectura.clic, lectura.soltar = self._clic_guardado, True   # pellizco rápido: un clic
                self._estado = "libre"
            elif ahora - self._inicio_pendiente >= ESPERA_DOS_MANOS:
                lectura.clic, lectura.arrastrando = self._clic_guardado, True
                self._estado = "trazo"
        elif estado == "trazo":
            if not pellizca or otra:
                lectura.soltar = True
                self._estado = "zoom" if pellizca else "libre"
            else:
                lectura.arrastrando = True
        elif estado == "zoom":
            if not pellizca:
                self._estado = "libre"
            elif not otra:
                self._estado = "esperar_soltar"
        elif estado == "esperar_soltar" and not pellizca:
            self._estado = "libre"

    def _zoom(self, lectura: Lectura):
        if self._estado != "zoom" or lectura.secundaria is None or not lectura.secundaria.pellizcando:
            self._distancia_zoom = None
            return
        distancia = math.dist(a_pantalla(lectura.principal.punto_pellizco), a_pantalla(lectura.secundaria.punto_pellizco))
        if self._distancia_zoom:
            lectura.zoom = self._distancia_zoom / max(distancia, 1e-3)
        self._distancia_zoom = distancia

    def _mano_secundaria(self, lectura: Lectura, ahora: float):
        mano = lectura.secundaria
        if mano is None:
            self._giro_anterior, self._conteo = None, None
            return
        if mano.pellizcando:
            self._conteo = None
            if self._estado == "zoom":
                self._giro_anterior = None
                return
            punto = a_pantalla(mano.punto_pellizco)
            if self._giro_anterior is not None:
                lectura.giro = (punto[0] - self._giro_anterior[0], punto[1] - self._giro_anterior[1])
            self._giro_anterior = punto
            return
        self._giro_anterior = None
        dedos = mano.cuenta_dedos
        if dedos not in (1, 2, 3):
            self._conteo, self._conteo_usado = None, False
            return
        if self._conteo is None or self._conteo[0] != dedos:
            self._conteo, self._conteo_usado = (dedos, ahora), False
        if self._conteo_usado:
            return
        progreso = min((ahora - self._conteo[1]) / config.SEGUNDOS_CONTAR_DEDOS, 1.0)
        lectura.conteo = (dedos, progreso)
        if progreso >= 1.0:
            lectura.herramienta = dedos - 1
            self._conteo_usado = True

    def _cursor_en(self, momento: float) -> tuple[float, float] | None:
        elegido = self._historial[0][1] if self._historial else None
        for tiempo, cursor in self._historial:
            if tiempo > momento:
                break
            elegido = cursor
        return elegido

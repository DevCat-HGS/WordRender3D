"""Cámara + MediaPipe: encuentra hasta dos manos y lee las puntas de los dedos."""
from __future__ import annotations

import sys
import threading
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks.python import BaseOptions, vision

from . import config
from .filtros import FiltroEuro

PUNTAS = (4, 8, 12, 16, 20)   # pulgar, índice, medio, anular, meñique
CONEXIONES = (
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20), (0, 17),
)
_DEDOS = ((5, 6, 7, 8), (9, 10, 11, 12), (13, 14, 15, 16), (17, 18, 19, 20))   # mcp, pip, dip, punta
COLOR_VISTA = {"Derecha": (255, 210, 60), "Izquierda": (220, 110, 255)}         # BGR


@dataclass(frozen=True, eq=False)
class Mano:
    lado: str                 # "Derecha" o "Izquierda": la mano real de la persona
    puntos: np.ndarray        # (21, 3) suavizados: x, y en 0-1 sobre la imagen espejada; z relativo
    pellizco: float           # distancia pulgar-índice dividida por el tamaño de la palma
    pellizcando: bool
    dedos: tuple[bool, ...]   # levantados: pulgar, índice, medio, anular, meñique

    @property
    def indice(self) -> np.ndarray:
        return self.puntos[8, :2]

    @property
    def punto_pellizco(self) -> np.ndarray:
        return (self.puntos[4, :2] + self.puntos[8, :2]) / 2

    @property
    def cuenta_dedos(self) -> int:
        return sum(self.dedos)


def dedos_levantados(px: np.ndarray) -> tuple[bool, ...]:
    """px: los 21 puntos en píxeles. Un dedo cuenta como levantado si está estirado y alejado de la muñeca."""
    distancia = np.linalg.norm
    pulgar = distancia(px[4] - px[9]) > distancia(px[2] - px[9]) * 1.1
    otros = []
    for mcp, pip, dip, punta in _DEDOS:
        largo = distancia(px[pip] - px[mcp]) + distancia(px[dip] - px[pip]) + distancia(px[punta] - px[dip])
        recto = distancia(px[punta] - px[mcp]) > 0.8 * largo
        lejos = distancia(px[punta] - px[0]) > distancia(px[pip] - px[0])
        otros.append(bool(recto and lejos))
    return (bool(pulgar), *otros)


def abrir_camara():
    backends = (cv2.CAP_DSHOW, cv2.CAP_ANY) if sys.platform == "win32" else (cv2.CAP_ANY,)
    for backend in backends:
        camara = cv2.VideoCapture(config.INDICE_CAMARA, backend)
        if camara.isOpened():
            ancho, alto = config.RESOLUCION_CAMARA
            camara.set(cv2.CAP_PROP_FRAME_WIDTH, ancho)
            camara.set(cv2.CAP_PROP_FRAME_HEIGHT, alto)
            if camara.read()[0]:
                return camara
        camara.release()
    return None


def dibujar_vista(cuadro: np.ndarray, manos, ancho=320) -> np.ndarray:
    """Imagen pequeña de la cámara con el esqueleto de cada mano, para verla dentro del mundo."""
    alto = round(cuadro.shape[0] * ancho / cuadro.shape[1])
    vista = cv2.resize(cuadro, (ancho, alto), interpolation=cv2.INTER_AREA)
    x0, y0, x1, y1 = config.ZONA_ACTIVA
    cv2.rectangle(vista, (round(x0 * ancho), round(y0 * alto)), (round(x1 * ancho), round(y1 * alto)), (120, 120, 120), 1)
    for mano in manos:
        tinte = COLOR_VISTA[mano.lado]
        pts = np.round(mano.puntos[:, :2] * (ancho, alto)).astype(int)
        for a, b in CONEXIONES:
            cv2.line(vista, tuple(pts[a]), tuple(pts[b]), tinte, 2, cv2.LINE_AA)
        for i, p in enumerate(pts):
            if i in PUNTAS:
                relleno = (90, 255, 90) if mano.pellizcando and i in (4, 8) else (255, 255, 255)
                cv2.circle(vista, tuple(p), 5, relleno, -1, cv2.LINE_AA)
                cv2.circle(vista, tuple(p), 5, tinte, 1, cv2.LINE_AA)
            else:
                cv2.circle(vista, tuple(p), 2, tinte, -1, cv2.LINE_AA)
    return vista


class Rastreador:
    """Hilo que lee la cámara y publica las manos del último cuadro."""

    def __init__(self, ruta_modelo: Path):
        self._ruta_modelo = ruta_modelo
        self._candado = threading.Lock()
        self._manos: tuple[Mano, ...] = ()
        self._vista: np.ndarray | None = None
        self._cuadro = 0
        self._parar = threading.Event()
        self._filtros: dict[str, FiltroEuro] = {}
        self._pellizcos: dict[str, bool] = {}
        self.error: str | None = None
        self.fps = 0.0
        self._hilo = threading.Thread(target=self._bucle, name="manos", daemon=True)

    def iniciar(self):
        self._hilo.start()

    def detener(self):
        self._parar.set()
        if self._hilo.is_alive():
            self._hilo.join(timeout=3)

    def leer(self) -> tuple[int, tuple[Mano, ...], np.ndarray | None]:
        """Número de cuadro (sirve para saber si hay datos nuevos), manos e imagen de la cámara."""
        with self._candado:
            return self._cuadro, self._manos, self._vista

    def _bucle(self):
        try:
            detector = vision.HandLandmarker.create_from_options(vision.HandLandmarkerOptions(
                base_options=BaseOptions(model_asset_buffer=self._ruta_modelo.read_bytes()),
                running_mode=vision.RunningMode.VIDEO,
                num_hands=2,
                min_hand_detection_confidence=0.6,
                min_hand_presence_confidence=0.5,
                min_tracking_confidence=0.5,
            ))
        except Exception as exc:
            self.error = f"no se pudo cargar el modelo de manos ({exc})"
            return
        camara = abrir_camara()
        if camara is None:
            self.error = "no se pudo abrir la cámara (¿la usa otra aplicación?)"
            detector.close()
            return
        inicio = time.monotonic()
        ultimo_ms = -1
        fallos = 0
        tiempos = deque(maxlen=30)
        try:
            while not self._parar.is_set():
                ok, cuadro = camara.read()
                if not ok:
                    fallos += 1
                    if fallos > 100:
                        self.error = "la cámara dejó de enviar imágenes"
                        return
                    time.sleep(0.02)
                    continue
                fallos = 0
                ahora = time.monotonic()
                cuadro = cv2.flip(cuadro, 1)   # como un espejo: tu mano derecha aparece a la derecha
                imagen = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(cuadro, cv2.COLOR_BGR2RGB))
                ultimo_ms = max(int((ahora - inicio) * 1000), ultimo_ms + 1)
                resultado = detector.detect_for_video(imagen, ultimo_ms)
                manos = self._interpretar(resultado, cuadro.shape[1], cuadro.shape[0], ahora)
                vista = dibujar_vista(cuadro, manos)
                tiempos.append(ahora)
                if len(tiempos) > 1:
                    self.fps = (len(tiempos) - 1) / (tiempos[-1] - tiempos[0])
                with self._candado:
                    self._manos, self._vista = manos, vista
                    self._cuadro += 1
        finally:
            camara.release()
            detector.close()

    def _interpretar(self, resultado, ancho, alto, ahora) -> tuple[Mano, ...]:
        detectadas = []
        for puntos, lateralidad in zip(resultado.hand_landmarks, resultado.handedness):
            lado = "Derecha" if lateralidad[0].category_name == "Right" else "Izquierda"
            if config.INVERTIR_LADOS:
                lado = "Izquierda" if lado == "Derecha" else "Derecha"
            detectadas.append([lado, np.array([(p.x, p.y, p.z) for p in puntos])])
        if len(detectadas) == 2 and detectadas[0][0] == detectadas[1][0]:
            # A veces MediaPipe etiqueta igual las dos manos: en la imagen espejada la derecha queda a la derecha.
            detectadas.sort(key=lambda d: d[1][0, 0])
            detectadas[0][0], detectadas[1][0] = "Izquierda", "Derecha"

        escala = np.array([ancho, alto, ancho], dtype=float)
        manos = []
        for lado, crudos in detectadas:
            px = crudos * escala
            palma = np.linalg.norm(px[0] - px[9]) + 1e-6
            pellizco = float(np.linalg.norm(px[4] - px[8]) / palma)
            umbral = config.PELLIZCO_ABRIR if self._pellizcos.get(lado) else config.PELLIZCO_CERRAR
            self._pellizcos[lado] = pellizco < umbral
            suaves = self._filtros.setdefault(lado, FiltroEuro())(crudos, ahora)
            manos.append(Mano(lado, suaves, pellizco, self._pellizcos[lado], dedos_levantados(px)))
        for lado in self._pellizcos.keys() - {m.lado for m in manos}:
            self._pellizcos[lado] = False
        return tuple(manos)

"""Seguimiento de manos con la cámara web usando MediaPipe (Tasks API).

Corre en un hilo aparte para que el render 3D no se congele mientras
MediaPipe procesa cada fotograma.
"""
import os
import threading
import time
import urllib.request
from dataclasses import dataclass

import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions, vision

MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/1/hand_landmarker.task"
)
MODEL_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "modelos", "hand_landmarker.task"
)

# Índices de MediaPipe: pulgar, índice, medio, anular, meñique
PUNTAS = (4, 8, 12, 16, 20)
CONEXIONES = [(c.start, c.end) for c in vision.HandLandmarksConnections.HAND_CONNECTIONS]
NOMBRE_MANO = {"Left": "Izquierda", "Right": "Derecha"}


@dataclass
class Mano:
    etiqueta: str        # "Left" o "Right"
    confianza: float
    puntos: np.ndarray   # (21, 3) normalizados sobre la imagen en espejo


def asegurar_modelo():
    if os.path.exists(MODEL_PATH):
        return MODEL_PATH
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    print("Descargando modelo de manos de MediaPipe...")
    tmp = MODEL_PATH + ".part"
    urllib.request.urlretrieve(MODEL_URL, tmp)
    os.replace(tmp, MODEL_PATH)
    return MODEL_PATH


class HandTracker(threading.Thread):
    def __init__(self, camara=0, ancho=640, alto=480, tam_preview=(320, 240)):
        super().__init__(daemon=True)
        self.camara = camara
        self.ancho = ancho
        self.alto = alto
        self.tam_preview = tam_preview
        self.aspecto = ancho / alto
        self.listo = False
        self.error = None
        self.fps = 0.0
        self._corriendo = True
        self._lock = threading.Lock()
        self._manos = []
        self._preview = None
        self._frame_id = 0

    def manos(self):
        with self._lock:
            return list(self._manos), self._frame_id

    def preview(self):
        with self._lock:
            return self._preview, self._frame_id

    def detener(self):
        self._corriendo = False

    def run(self):
        try:
            opciones = vision.HandLandmarkerOptions(
                base_options=BaseOptions(model_asset_path=asegurar_modelo()),
                running_mode=vision.RunningMode.VIDEO,
                num_hands=2,
                min_hand_detection_confidence=0.6,
                min_hand_presence_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            detector = vision.HandLandmarker.create_from_options(opciones)
        except Exception as e:
            self.error = f"No se pudo cargar MediaPipe: {e}"
            return

        cap = cv2.VideoCapture(self.camara, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap = cv2.VideoCapture(self.camara)
        if not cap.isOpened():
            self.error = "No se encontró ninguna cámara web"
            detector.close()
            return
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.ancho)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.alto)

        self.listo = True
        t0 = time.perf_counter()
        ultimo_ts = -1
        cuadros, t_fps = 0, t0
        try:
            while self._corriendo:
                ok, frame = cap.read()
                if not ok:
                    time.sleep(0.01)
                    continue
                frame = cv2.flip(frame, 1)
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w = rgb.shape[:2]
                self.aspecto = w / h

                ts = int((time.perf_counter() - t0) * 1000)
                if ts <= ultimo_ts:
                    ts = ultimo_ts + 1
                ultimo_ts = ts
                res = detector.detect_for_video(
                    mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb), ts
                )

                manos = []
                for lms, lado in zip(res.hand_landmarks, res.handedness):
                    pts = np.array([[p.x, p.y, p.z] for p in lms], dtype=np.float32)
                    manos.append(Mano(lado[0].category_name, lado[0].score, pts))

                preview = self._dibujar_preview(rgb, manos)
                with self._lock:
                    self._manos = manos
                    self._preview = preview
                    self._frame_id += 1

                cuadros += 1
                ahora = time.perf_counter()
                if ahora - t_fps >= 1.0:
                    self.fps = cuadros / (ahora - t_fps)
                    cuadros, t_fps = 0, ahora
        except Exception as e:
            self.error = f"Error en el seguimiento de manos: {e}"
        finally:
            cap.release()
            detector.close()

    def _dibujar_preview(self, rgb, manos):
        pw, ph = self.tam_preview
        img = cv2.resize(rgb, (pw, ph))
        for m in manos:
            pts = (m.puntos[:, :2] * (pw, ph)).astype(int)
            for a, b in CONEXIONES:
                cv2.line(img, tuple(pts[a]), tuple(pts[b]), (255, 255, 255), 1, cv2.LINE_AA)
            for i in PUNTAS:
                cv2.circle(img, tuple(pts[i]), 4, (0, 220, 255), -1, cv2.LINE_AA)
            x, y = pts[0]
            cv2.putText(img, NOMBRE_MANO.get(m.etiqueta, m.etiqueta), (x - 30, min(y + 18, ph - 4)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 0), 1, cv2.LINE_AA)
        return np.ascontiguousarray(img)

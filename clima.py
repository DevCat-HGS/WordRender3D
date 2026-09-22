"""Ciclo de día y noche: cielo, sol, luna, estrellas y luz ambiental."""
import math
from dataclasses import dataclass

import numpy as np


# Un día completo en segundos reales (se puede acelerar en la app).
SEGUNDOS_DIA = 90.0

# (hora 0-1, cielo arriba, horizonte, ambiente, color del sol)
_CLAVES = [
    (0.00, (0.02, 0.03, 0.10), (0.04, 0.05, 0.12), (0.16, 0.18, 0.28), (0.18, 0.22, 0.38)),
    (0.18, (0.08, 0.06, 0.16), (0.16, 0.08, 0.12), (0.18, 0.14, 0.20), (0.40, 0.22, 0.18)),
    (0.23, (0.55, 0.22, 0.24), (0.96, 0.48, 0.24), (0.32, 0.18, 0.14), (1.00, 0.48, 0.20)),
    (0.28, (0.62, 0.38, 0.32), (0.98, 0.66, 0.36), (0.40, 0.26, 0.18), (1.00, 0.68, 0.32)),
    (0.34, (0.34, 0.54, 0.92), (0.74, 0.84, 0.97), (0.46, 0.48, 0.52), (1.00, 0.93, 0.74)),
    (0.50, (0.28, 0.56, 0.97), (0.76, 0.88, 1.00), (0.52, 0.54, 0.58), (1.00, 0.97, 0.84)),
    (0.68, (0.42, 0.48, 0.82), (0.86, 0.70, 0.52), (0.46, 0.40, 0.38), (1.00, 0.82, 0.52)),
    (0.74, (0.72, 0.30, 0.20), (0.98, 0.52, 0.24), (0.42, 0.24, 0.16), (1.00, 0.52, 0.20)),
    (0.80, (0.28, 0.12, 0.22), (0.50, 0.20, 0.16), (0.22, 0.16, 0.20), (0.70, 0.28, 0.16)),
    (0.88, (0.04, 0.04, 0.12), (0.08, 0.06, 0.12), (0.16, 0.17, 0.26), (0.20, 0.24, 0.40)),
    (1.00, (0.02, 0.03, 0.10), (0.04, 0.05, 0.12), (0.16, 0.18, 0.28), (0.18, 0.22, 0.38)),
]


def _mezcla(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def _muestra(hora):
    h = hora % 1.0
    for i in range(len(_CLAVES) - 1):
        h0, *a = _CLAVES[i]
        h1, *b = _CLAVES[i + 1]
        if h0 <= h <= h1:
            t = 0.0 if h1 == h0 else (h - h0) / (h1 - h0)
            t = t * t * (3.0 - 2.0 * t)
            return [_mezcla(x, y, t) for x, y in zip(a, b)]
    return list(_CLAVES[0][1:])


@dataclass
class EstadoCielo:
    hora: float
    nombre: str
    cielo_arriba: tuple
    cielo_abajo: tuple
    ambiente: np.ndarray
    sol_color: np.ndarray
    sol_dir: np.ndarray
    luna_dir: np.ndarray
    sol_fuerza: float
    luna_fuerza: float
    estrellas: float
    niebla: tuple
    suelo: tuple


def nombre_hora(hora):
    h = hora % 1.0
    if 0.22 <= h < 0.32:
        return "Amanecer"
    if 0.32 <= h < 0.70:
        return "Día"
    if 0.70 <= h < 0.82:
        return "Atardecer"
    return "Noche"


def hora_reloj(hora):
    minutos = int((hora % 1.0) * 24 * 60)
    return f"{minutos // 60:02d}:{minutos % 60:02d}"


def estado_cielo(hora):
    cielo_arriba, cielo_abajo, ambiente, sol_col = _muestra(hora)
    ang = (hora % 1.0 - 0.25) * math.tau
    sol = np.array([math.cos(ang), math.sin(ang), 0.28], dtype=np.float32)
    sol /= max(float(np.linalg.norm(sol)), 1e-6)
    luna = -sol
    if luna[1] < 0.08:
        luna = luna.copy()
        luna[1] = 0.08
        luna /= np.linalg.norm(luna)

    elev = float(sol[1])
    # El sol sigue iluminando un rato después de tocar el horizonte.
    sol_fuerza = max(0.0, elev + 0.18) ** 0.55
    luna_fuerza = max(0.0, 0.62 - max(elev, 0.0)) * 0.70
    estrellas = max(0.0, min(1.0, (0.16 - elev) / 0.30))

    suelo_dia = (0.42, 0.55, 0.38)
    suelo_noche = (0.08, 0.10, 0.14)
    t_suelo = 0.15 + 0.85 * sol_fuerza
    suelo = _mezcla(suelo_noche, suelo_dia, t_suelo)

    return EstadoCielo(
        hora=hora % 1.0,
        nombre=nombre_hora(hora),
        cielo_arriba=cielo_arriba,
        cielo_abajo=cielo_abajo,
        ambiente=np.array(ambiente, dtype=np.float32),
        sol_color=np.array(sol_col, dtype=np.float32),
        sol_dir=sol,
        luna_dir=luna.astype(np.float32),
        sol_fuerza=sol_fuerza,
        luna_fuerza=luna_fuerza,
        estrellas=estrellas,
        niebla=cielo_abajo,
        suelo=suelo,
    )


def campo_estrellas(n=280, semilla=11, ancho=1280, alto=720):
    rng = np.random.default_rng(semilla)
    u = rng.random(n)
    v = rng.random(n)
    theta = u * math.tau
    y = 0.08 + 0.92 * (v ** 0.55)
    r = np.sqrt(np.maximum(1.0 - y * y, 0.0))
    pts = np.stack([r * np.cos(theta), y, r * np.sin(theta)], axis=1).astype(np.float32)
    brillo = (0.45 + 0.55 * rng.random(n)).astype(np.float32)
    tam = (1.2 + 2.4 * rng.random(n) ** 2).astype(np.float32)
    pantalla = np.stack([
        rng.random(n) * ancho,
        rng.random(n) * alto * 0.28,
        brillo,
    ], axis=1).astype(np.float32)
    return pts, brillo, tam, pantalla

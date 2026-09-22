"""Climas que el jugador elige: partículas, viento, cielo y un tornado."""
import math
from dataclasses import dataclass

import numpy as np

BRISA, LLUVIA, TORMENTA, SEQUIA, NEVADO, TORNADO = range(6)

CLIMAS = [
    {"id": BRISA, "nombre": "Brisa", "color": (0.52, 0.78, 0.95), "desc": "Viento suave y hojas"},
    {"id": LLUVIA, "nombre": "Lluvia", "color": (0.30, 0.48, 0.78), "desc": "Llueve y crecen frutas"},
    {"id": TORMENTA, "nombre": "Tormenta", "color": (0.22, 0.20, 0.38), "desc": "Rayos, viento y miedo"},
    {"id": SEQUIA, "nombre": "Sequía", "color": (0.86, 0.62, 0.22), "desc": "Polvo, hambre y sed"},
    {"id": NEVADO, "nombre": "Nevado", "color": (0.90, 0.94, 1.00), "desc": "Nieve y frío"},
    {"id": TORNADO, "nombre": "Tornado", "color": (0.45, 0.42, 0.38), "desc": "Un remolino que empuja"},
]


def _mezcla(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


@dataclass
class EstadoTiempo:
    viento: np.ndarray
    frio: float
    sequia: float
    lluvia: float
    peligro: float
    tornado: np.ndarray | None
    relampago: float


class Tiempo:
    def __init__(self, mundo, n=1400):
        self.mundo = mundo
        self.clima = BRISA
        self.n = n
        rng = np.random.default_rng(5)
        w, _, d = mundo.tam
        self.pos = np.column_stack([
            rng.uniform(-8, w + 8, n),
            rng.uniform(2, 28, n),
            rng.uniform(-8, d + 8, n),
        ]).astype(np.float32)
        self.vel = np.zeros((n, 3), np.float32)
        self.col = np.ones((n, 4), np.float32)
        self.tornado = np.array([w * 0.35, 0.0, d * 0.4], np.float32)
        self.ang = 0.0
        self.flash = 0.0
        self.t = 0.0
        self.rng = rng

    def activar(self, clima_id):
        self.clima = int(np.clip(clima_id, 0, 5))
        return CLIMAS[self.clima]["nombre"]

    @property
    def nombre(self):
        return CLIMAS[self.clima]["nombre"]

    def estado(self):
        c = self.clima
        viento = {
            BRISA: (1.6, 0.0, 0.4),
            LLUVIA: (0.8, 0.0, 0.2),
            TORMENTA: (5.5, 0.0, 2.2),
            SEQUIA: (2.4, 0.0, 0.3),
            NEVADO: (1.2, 0.0, 0.8),
            TORNADO: (3.0, 0.0, 1.2),
        }[c]
        return EstadoTiempo(
            viento=np.array(viento, np.float32),
            frio=1.0 if c == NEVADO else 0.0,
            sequia=1.0 if c == SEQUIA else 0.0,
            lluvia=1.0 if c in (LLUVIA, TORMENTA) else 0.0,
            peligro=1.0 if c in (TORMENTA, TORNADO) else 0.0,
            tornado=self.tornado.copy() if c == TORNADO else None,
            relampago=self.flash,
        )

    def teñir(self, cielo):
        c = self.clima
        if c == LLUVIA:
            cielo.cielo_arriba = _mezcla(cielo.cielo_arriba, (0.28, 0.34, 0.42), 0.55)
            cielo.cielo_abajo = _mezcla(cielo.cielo_abajo, (0.38, 0.42, 0.48), 0.5)
            cielo.niebla = _mezcla(cielo.niebla, (0.40, 0.44, 0.50), 0.55)
            cielo.sol_fuerza *= 0.55
        elif c == TORMENTA:
            cielo.cielo_arriba = _mezcla(cielo.cielo_arriba, (0.08, 0.09, 0.14), 0.75)
            cielo.cielo_abajo = _mezcla(cielo.cielo_abajo, (0.16, 0.16, 0.20), 0.7)
            cielo.niebla = (0.14, 0.15, 0.18)
            cielo.sol_fuerza *= 0.22
            if self.flash > 0.4:
                cielo.cielo_arriba = (0.85, 0.88, 1.0)
                cielo.cielo_abajo = (0.70, 0.74, 0.86)
        elif c == SEQUIA:
            cielo.cielo_arriba = _mezcla(cielo.cielo_arriba, (0.72, 0.52, 0.22), 0.45)
            cielo.cielo_abajo = _mezcla(cielo.cielo_abajo, (0.86, 0.68, 0.32), 0.5)
            cielo.suelo = _mezcla(cielo.suelo, (0.55, 0.40, 0.18), 0.4)
            cielo.sol_color = cielo.sol_color * np.array([1.0, 0.85, 0.55], np.float32)
        elif c == NEVADO:
            cielo.cielo_arriba = _mezcla(cielo.cielo_arriba, (0.70, 0.78, 0.90), 0.5)
            cielo.cielo_abajo = _mezcla(cielo.cielo_abajo, (0.86, 0.90, 0.96), 0.55)
            cielo.niebla = (0.78, 0.84, 0.92)
            cielo.suelo = _mezcla(cielo.suelo, (0.82, 0.86, 0.92), 0.45)
        elif c == TORNADO:
            cielo.cielo_arriba = _mezcla(cielo.cielo_arriba, (0.32, 0.30, 0.28), 0.55)
            cielo.cielo_abajo = _mezcla(cielo.cielo_abajo, (0.42, 0.38, 0.32), 0.5)
            cielo.niebla = (0.40, 0.36, 0.30)
            cielo.sol_fuerza *= 0.4
        return cielo

    def actualizar(self, dt):
        self.t += dt
        w, _, d = self.mundo.tam
        c = self.clima
        if c == TORMENTA and self.rng.random() < 0.012:
            self.flash = 1.0
        self.flash = max(0.0, self.flash - dt * 3.5)

        if c == TORNADO:
            self.ang += dt * 2.4
            self.tornado[0] = w * 0.5 + math.cos(self.ang * 0.35) * w * 0.28
            self.tornado[2] = d * 0.5 + math.sin(self.ang * 0.28) * d * 0.28

        p = self.pos
        if c == LLUVIA or c == TORMENTA:
            rap = 22.0 if c == TORMENTA else 14.0
            p[:, 1] -= rap * dt
            p[:, 0] += (3.5 if c == TORMENTA else 1.2) * dt
            self.col[:] = (0.55, 0.70, 0.95, 0.45 if c == LLUVIA else 0.65)
        elif c == NEVADO:
            p[:, 1] -= 2.8 * dt
            p[:, 0] += np.sin(self.t * 1.4 + p[:, 2] * 0.2) * 1.6 * dt
            self.col[:] = (0.95, 0.97, 1.0, 0.85)
        elif c == SEQUIA:
            p[:, 1] += np.sin(self.t + p[:, 0]) * 0.4 * dt
            p[:, 0] += 2.2 * dt
            self.col[:] = (0.78, 0.58, 0.22, 0.28)
        elif c == TORNADO:
            dx = p[:, 0] - self.tornado[0]
            dz = p[:, 2] - self.tornado[2]
            ang = np.arctan2(dz, dx) + 4.5 * dt
            r = np.sqrt(dx * dx + dz * dz) * 0.96 + 0.15
            p[:, 0] = self.tornado[0] + np.cos(ang) * r
            p[:, 2] = self.tornado[2] + np.sin(ang) * r
            p[:, 1] += 3.2 * dt
            self.col[:] = (0.45, 0.38, 0.28, 0.55)
        else:
            p[:, 0] += 1.8 * dt
            p[:, 1] += np.sin(self.t * 2 + p[:, 2]) * 0.5 * dt
            self.col[:] = (0.42, 0.72, 0.28, 0.40)

        caen = p[:, 1] < 0.2
        salen = (p[:, 0] < -10) | (p[:, 0] > w + 10) | (p[:, 2] < -10) | (p[:, 2] > d + 10) | (p[:, 1] > 32)
        reset = caen | salen
        k = int(reset.sum())
        if k:
            p[reset, 0] = self.rng.uniform(-4, w + 4, k)
            p[reset, 1] = self.rng.uniform(12, 30, k)
            p[reset, 2] = self.rng.uniform(-4, d + 4, k)
        return self.estado()

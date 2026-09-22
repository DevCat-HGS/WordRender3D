"""Cadena alimenticia: 12 especies, IA en lotes y mallas low-poly reutilizables."""
from dataclasses import dataclass

import numpy as np

WANDER, COMER, HUIR, CAZAR, ATACAR, MUERTO = range(6)
CELDA = 8.0

# ids
MARIPOSA, RANA, RATON, CONEJO, PEZ, PATO = range(6)
CIERVO, JABALI, ZORRO, LOBO, AGUILA, OSO = range(6, 12)
NOMBRES = [
    "Mariposa", "Rana", "Ratón", "Conejo", "Pez", "Pato",
    "Ciervo", "Jabalí", "Zorro", "Lobo", "Águila", "Oso",
]


@dataclass(frozen=True)
class Especie:
    nombre: str
    cuerpo: tuple
    extra: tuple
    escala: float
    vel: float
    vision: float
    hambre_t: float
    vida: float
    dano: float
    dieta: str          # hierba, carne, omni, nectar
    presas: tuple
    vuela: bool
    nada: bool
    poblacion: int


ESPECIES = [
    Especie("Mariposa", (0.98, 0.62, 0.12), (0.20, 0.12, 0.08), 0.38, 2.4, 6, 40, 4, 0.0, "nectar", (), True, False, 26),
    Especie("Rana", (0.18, 0.62, 0.18), (0.10, 0.32, 0.10), 0.48, 1.6, 7, 28, 8, 1.2, "carne", (MARIPOSA,), False, True, 14),
    Especie("Ratón", (0.48, 0.34, 0.22), (0.28, 0.18, 0.12), 0.46, 2.2, 8, 26, 7, 0.8, "hierba", (), False, False, 22),
    Especie("Conejo", (0.86, 0.80, 0.70), (0.58, 0.40, 0.30), 0.62, 2.6, 9, 30, 10, 0.5, "hierba", (), False, False, 20),
    Especie("Pez", (0.12, 0.48, 0.82), (0.95, 0.62, 0.10), 0.50, 2.0, 6, 32, 6, 0.0, "nectar", (), False, True, 18),
    Especie("Pato", (0.18, 0.32, 0.18), (0.90, 0.58, 0.08), 0.64, 1.8, 8, 28, 12, 1.4, "omni", (PEZ,), False, True, 10),
    Especie("Ciervo", (0.62, 0.40, 0.20), (0.90, 0.86, 0.78), 0.98, 2.8, 12, 34, 22, 1.0, "hierba", (), False, False, 12),
    Especie("Jabalí", (0.36, 0.24, 0.14), (0.16, 0.10, 0.06), 0.84, 2.0, 9, 30, 20, 2.2, "omni", (RATON,), False, False, 8),
    Especie("Zorro", (0.90, 0.42, 0.10), (0.95, 0.92, 0.88), 0.72, 3.2, 11, 24, 16, 3.0, "carne", (CONEJO, RATON, RANA, PATO), False, False, 7),
    Especie("Lobo", (0.40, 0.42, 0.48), (0.16, 0.16, 0.18), 0.88, 3.4, 14, 26, 24, 4.2, "carne", (CIERVO, CONEJO, JABALI), False, False, 5),
    Especie("Águila", (0.46, 0.28, 0.14), (0.92, 0.88, 0.82), 0.78, 3.6, 16, 28, 14, 3.4, "carne", (CONEJO, RATON, PEZ, PATO), True, False, 5),
    Especie("Oso", (0.30, 0.18, 0.08), (0.10, 0.06, 0.04), 1.15, 2.2, 12, 32, 36, 5.0, "omni", (PEZ, CIERVO, JABALI), False, True, 3),
]


def _caja(x0, y0, z0, x1, y1, z1, color):
    caras = [
        ((1, 0, 0), [(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)]),
        ((-1, 0, 0), [(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)]),
        ((0, 1, 0), [(x0, y1, z0), (x0, y1, z1), (x1, y1, z1), (x1, y1, z0)]),
        ((0, -1, 0), [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)]),
        ((0, 0, 1), [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]),
        ((0, 0, -1), [(x0, y0, z0), (x0, y1, z0), (x1, y1, z0), (x1, y0, z0)]),
    ]
    tri = (0, 1, 2, 0, 2, 3)
    pos, nrm, col = [], [], []
    for n, qs in caras:
        for i in tri:
            pos.append(qs[i])
            nrm.append(n)
            col.append(color)
    return pos, nrm, col


def _modelo(esp: Especie):
    """Cada especie tiene silueta propia: orejas, cola, pico, cuernos, alas."""
    c, e = esp.cuerpo, esp.extra
    pos, nrm, col = [], [], []

    def add(*args):
        pos.extend(args[0])
        nrm.extend(args[1])
        col.extend(args[2])

    def patas(pts, y1=0.14, gro=0.035, color=None):
        color = color or e
        for sx, sz in pts:
            add(*_caja(sx - gro, 0.0, sz - gro, sx + gro, y1, sz + gro, color))

    nombre = esp.nombre
    if nombre == "Mariposa":
        add(*_caja(-0.04, 0.10, -0.14, 0.04, 0.18, 0.14, e))
        add(*_caja(-0.03, 0.12, 0.12, 0.03, 0.16, 0.22, (0.15, 0.10, 0.08)))
        add(*_caja(-0.40, 0.12, -0.02, -0.04, 0.15, 0.18, c))
        add(*_caja(-0.34, 0.11, -0.16, -0.06, 0.14, 0.00, (0.15, 0.08, 0.08)))
        add(*_caja(0.04, 0.12, -0.02, 0.40, 0.15, 0.18, c))
        add(*_caja(0.06, 0.11, -0.16, 0.34, 0.14, 0.00, (0.15, 0.08, 0.08)))
        add(*_caja(-0.02, 0.16, 0.18, -0.01, 0.28, 0.22, (0.10, 0.08, 0.06)))
        add(*_caja(0.01, 0.16, 0.18, 0.02, 0.28, 0.22, (0.10, 0.08, 0.06)))
    elif nombre == "Rana":
        add(*_caja(-0.16, 0.06, -0.14, 0.16, 0.22, 0.16, c))
        add(*_caja(-0.12, 0.18, 0.10, -0.04, 0.28, 0.20, c))
        add(*_caja(0.04, 0.18, 0.10, 0.12, 0.28, 0.20, c))
        add(*_caja(-0.10, 0.24, 0.14, -0.06, 0.30, 0.20, (0.95, 0.90, 0.20)))
        add(*_caja(0.06, 0.24, 0.14, 0.10, 0.30, 0.20, (0.95, 0.90, 0.20)))
        add(*_caja(-0.22, 0.00, -0.16, -0.10, 0.08, 0.02, e))
        add(*_caja(0.10, 0.00, -0.16, 0.22, 0.08, 0.02, e))
        add(*_caja(-0.14, 0.00, 0.08, -0.06, 0.07, 0.18, e))
        add(*_caja(0.06, 0.00, 0.08, 0.14, 0.07, 0.18, e))
    elif nombre == "Ratón":
        add(*_caja(-0.10, 0.06, -0.12, 0.10, 0.20, 0.14, c))
        add(*_caja(-0.08, 0.10, 0.12, 0.08, 0.20, 0.22, c))
        add(*_caja(-0.14, 0.18, 0.10, -0.06, 0.30, 0.18, e))
        add(*_caja(0.06, 0.18, 0.10, 0.14, 0.30, 0.18, e))
        add(*_caja(-0.03, 0.12, 0.20, 0.03, 0.16, 0.26, (0.90, 0.55, 0.55)))
        add(*_caja(-0.02, 0.10, -0.28, 0.02, 0.14, -0.12, e))
        patas(((-0.07, -0.08), (0.07, -0.08), (-0.07, 0.08), (0.07, 0.08)), 0.07, 0.025)
    elif nombre == "Conejo":
        add(*_caja(-0.14, 0.08, -0.14, 0.14, 0.28, 0.16, c))
        add(*_caja(-0.10, 0.14, 0.12, 0.10, 0.28, 0.26, c))
        add(*_caja(-0.10, 0.28, 0.14, -0.04, 0.52, 0.20, e))
        add(*_caja(0.04, 0.28, 0.14, 0.10, 0.52, 0.20, e))
        add(*_caja(-0.08, 0.10, -0.20, 0.08, 0.22, -0.14, (0.95, 0.92, 0.90)))
        add(*_caja(-0.03, 0.16, 0.24, 0.03, 0.20, 0.30, (0.90, 0.60, 0.60)))
        patas(((-0.09, -0.10), (0.09, -0.10), (-0.09, 0.10), (0.09, 0.10)), 0.09, 0.03)
    elif nombre == "Pez":
        add(*_caja(-0.08, 0.04, -0.20, 0.08, 0.18, 0.16, c))
        add(*_caja(-0.05, 0.08, 0.16, 0.05, 0.16, 0.24, c))
        add(*_caja(-0.02, 0.06, 0.22, 0.02, 0.18, 0.34, e))
        add(*_caja(-0.01, 0.18, -0.04, 0.01, 0.28, 0.08, e))
        add(*_caja(-0.16, 0.08, -0.04, -0.08, 0.14, 0.08, e))
        add(*_caja(0.08, 0.08, -0.04, 0.16, 0.14, 0.08, e))
        add(*_caja(0.03, 0.12, 0.18, 0.06, 0.15, 0.22, (0.05, 0.05, 0.05)))
    elif nombre == "Pato":
        add(*_caja(-0.12, 0.10, -0.16, 0.12, 0.26, 0.14, (0.92, 0.92, 0.90)))
        add(*_caja(-0.08, 0.18, 0.12, 0.08, 0.30, 0.24, (0.90, 0.90, 0.88)))
        add(*_caja(-0.03, 0.20, 0.22, 0.03, 0.24, 0.36, (0.95, 0.55, 0.08)))
        add(*_caja(-0.10, 0.22, -0.06, 0.10, 0.28, 0.08, (0.12, 0.12, 0.14)))
        patas(((-0.07, -0.06), (0.07, -0.06), (-0.07, 0.08), (0.07, 0.08)), 0.10, 0.03, (0.95, 0.55, 0.08))
    elif nombre == "Ciervo":
        add(*_caja(-0.12, 0.22, -0.28, 0.12, 0.40, 0.16, c))
        add(*_caja(-0.09, 0.26, 0.14, 0.09, 0.42, 0.30, c))
        add(*_caja(-0.10, 0.40, 0.20, -0.05, 0.62, 0.24, e))
        add(*_caja(-0.16, 0.52, 0.18, -0.05, 0.56, 0.26, e))
        add(*_caja(0.05, 0.40, 0.20, 0.10, 0.62, 0.24, e))
        add(*_caja(0.05, 0.52, 0.18, 0.16, 0.56, 0.26, e))
        add(*_caja(-0.04, 0.28, -0.36, 0.04, 0.34, -0.28, e))
        patas(((-0.08, -0.20), (0.08, -0.20), (-0.08, 0.10), (0.08, 0.10)), 0.22, 0.03)
    elif nombre == "Jabalí":
        add(*_caja(-0.16, 0.12, -0.22, 0.16, 0.34, 0.16, c))
        add(*_caja(-0.10, 0.14, 0.14, 0.10, 0.28, 0.32, c))
        add(*_caja(-0.06, 0.16, 0.30, 0.06, 0.22, 0.40, e))
        add(*_caja(-0.10, 0.14, 0.34, -0.06, 0.18, 0.42, (0.92, 0.90, 0.82)))
        add(*_caja(0.06, 0.14, 0.34, 0.10, 0.18, 0.42, (0.92, 0.90, 0.82)))
        add(*_caja(-0.12, 0.30, 0.18, -0.06, 0.40, 0.24, e))
        add(*_caja(0.06, 0.30, 0.18, 0.12, 0.40, 0.24, e))
        add(*_caja(-0.04, 0.18, -0.30, 0.04, 0.26, -0.22, e))
        patas(((-0.10, -0.14), (0.10, -0.14), (-0.10, 0.08), (0.10, 0.08)), 0.12, 0.04)
    elif nombre == "Zorro":
        add(*_caja(-0.10, 0.12, -0.20, 0.10, 0.28, 0.14, c))
        add(*_caja(-0.08, 0.14, 0.12, 0.08, 0.28, 0.26, c))
        add(*_caja(-0.08, 0.14, 0.10, 0.08, 0.24, 0.22, (0.96, 0.94, 0.90)))
        add(*_caja(-0.12, 0.26, 0.16, -0.04, 0.40, 0.22, c))
        add(*_caja(0.04, 0.26, 0.16, 0.12, 0.40, 0.22, c))
        add(*_caja(-0.06, 0.10, -0.38, 0.06, 0.22, -0.20, c))
        add(*_caja(-0.04, 0.12, -0.42, 0.04, 0.20, -0.36, (0.96, 0.94, 0.90)))
        add(*_caja(-0.02, 0.16, 0.24, 0.02, 0.20, 0.30, (0.15, 0.10, 0.08)))
        patas(((-0.07, -0.12), (0.07, -0.12), (-0.07, 0.08), (0.07, 0.08)), 0.12, 0.03)
    elif nombre == "Lobo":
        add(*_caja(-0.12, 0.16, -0.24, 0.12, 0.34, 0.14, c))
        add(*_caja(-0.09, 0.18, 0.12, 0.09, 0.34, 0.28, c))
        add(*_caja(-0.05, 0.20, 0.26, 0.05, 0.28, 0.36, e))
        add(*_caja(-0.12, 0.32, 0.16, -0.04, 0.46, 0.22, e))
        add(*_caja(0.04, 0.32, 0.16, 0.12, 0.46, 0.22, e))
        add(*_caja(-0.05, 0.18, -0.38, 0.05, 0.28, -0.24, c))
        add(*_caja(-0.03, 0.22, 0.32, 0.03, 0.26, 0.38, (0.08, 0.08, 0.08)))
        patas(((-0.08, -0.16), (0.08, -0.16), (-0.08, 0.08), (0.08, 0.08)), 0.16, 0.035)
    elif nombre == "Águila":
        add(*_caja(-0.08, 0.14, -0.16, 0.08, 0.24, 0.14, c))
        add(*_caja(-0.07, 0.16, 0.12, 0.07, 0.26, 0.26, (0.92, 0.90, 0.86)))
        add(*_caja(-0.03, 0.16, 0.24, 0.03, 0.20, 0.34, (0.95, 0.72, 0.12)))
        add(*_caja(-0.48, 0.16, -0.08, -0.08, 0.20, 0.12, e))
        add(*_caja(0.08, 0.16, -0.08, 0.48, 0.20, 0.12, e))
        add(*_caja(-0.04, 0.14, -0.28, 0.04, 0.22, -0.16, c))
        add(*_caja(-0.05, 0.10, 0.06, -0.02, 0.14, 0.12, (0.90, 0.70, 0.15)))
        add(*_caja(0.02, 0.10, 0.06, 0.05, 0.14, 0.12, (0.90, 0.70, 0.15)))
    else:  # Oso
        add(*_caja(-0.20, 0.12, -0.22, 0.20, 0.40, 0.16, c))
        add(*_caja(-0.14, 0.16, 0.14, 0.14, 0.38, 0.32, c))
        add(*_caja(-0.06, 0.18, 0.30, 0.06, 0.26, 0.40, e))
        add(*_caja(-0.16, 0.36, 0.18, -0.08, 0.48, 0.26, c))
        add(*_caja(0.08, 0.36, 0.18, 0.16, 0.48, 0.26, c))
        add(*_caja(-0.08, 0.20, -0.30, 0.08, 0.32, -0.22, c))
        patas(((-0.12, -0.14), (0.12, -0.14), (-0.12, 0.08), (0.12, 0.08)), 0.13, 0.05)

    return (
        np.array(pos, dtype=np.float32),
        np.array(nrm, dtype=np.float32),
        np.array(col, dtype=np.float32),
    )


MODELOS = [_modelo(e) for e in ESPECIES]

# Vértices de alas (índices) no hacen falta: el aleteo se hace por altura y balanceo.


def _lerp_ang(a, b, t):
    d = (b - a + np.pi) % (2 * np.pi) - np.pi
    return float(a + d * t)


class Fauna:
    def __init__(self, mundo, semilla=None):
        self.mundo = mundo
        self.rng = np.random.default_rng(semilla)
        self.poblar()

    def poblar(self):
        partes = []
        for i, e in enumerate(ESPECIES):
            partes.append(np.full(e.poblacion, i, dtype=np.int32))
        self.esp = np.concatenate(partes) if partes else np.zeros(0, np.int32)
        n = len(self.esp)
        self.n = n
        self.pos = np.zeros((n, 3), np.float32)
        self.vel = np.zeros((n, 3), np.float32)
        self.yaw = self.rng.random(n).astype(np.float32) * np.float32(np.pi * 2)
        self.yaw_obj = self.yaw.copy()
        self.wander_ang = self.rng.random(n).astype(np.float32) * np.float32(np.pi * 2)
        self.hambre = self.rng.uniform(4, 12, n).astype(np.float32)
        self.vida = np.array([ESPECIES[int(i)].vida for i in self.esp], np.float32)
        self.estado = np.zeros(n, np.int32)
        self.fase = self.rng.random(n).astype(np.float32) * 20
        self.cd = np.zeros(n, np.float32)
        self.objetivo = np.full(n, -1, np.int32)
        self.vivo = np.ones(n, np.bool_)
        self.rapidez = np.zeros(n, np.float32)
        self.y_suelo = np.zeros(n, np.float32)
        self.salto = np.zeros(n, np.float32)
        self._colocar()

    def _colocar(self):
        w, _h, d = self.mundo.tam
        agua = self.mundo.agua_sup
        suelo = self.mundo.altura
        for i in range(self.n):
            e = ESPECIES[int(self.esp[i])]
            for _ in range(40):
                x = float(self.rng.uniform(2, w - 3))
                z = float(self.rng.uniform(2, d - 3))
                xi, zi = int(x), int(z)
                if e.nada and not e.vuela:
                    if agua[xi, zi] <= 0:
                        continue
                    y = float(suelo[xi, zi]) + 0.35
                    if e.nombre == "Pez":
                        y = max(float(suelo[xi, zi]) - 0.2, 0.4)
                    break
                if agua[xi, zi] > 0 and not e.nada:
                    continue
                y = float(suelo[xi, zi])
                if e.vuela:
                    y += 3.5 + float(self.rng.random()) * 2.5
                break
            else:
                x, z, y = w * 0.5, d * 0.5, 4.0
            self.pos[i] = (x, y, z)
            self.y_suelo[i] = y

    def _hash(self):
        celdas = {}
        ix = np.clip((self.pos[:, 0] / CELDA).astype(np.int32), 0, 512)
        iz = np.clip((self.pos[:, 2] / CELDA).astype(np.int32), 0, 512)
        for i in range(self.n):
            if not self.vivo[i] and self.estado[i] != MUERTO:
                continue
            clave = (int(ix[i]), int(iz[i]))
            celdas.setdefault(clave, []).append(i)
        return celdas, ix, iz

    def _cerca(self, celdas, ix, iz, i, radio):
        cx, cz = int(ix[i]), int(iz[i])
        r2 = radio * radio
        p = self.pos[i]
        out = []
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                for j in celdas.get((cx + dx, cz + dz), ()):
                    if j == i:
                        continue
                    d2 = float(np.sum((self.pos[j] - p) ** 2))
                    if d2 <= r2:
                        out.append((d2, j))
        out.sort()
        return out

    def actualizar(self, dt, cam=None, clima=None):
        if self.n == 0:
            return
        dt = min(dt, 0.05)
        celdas, ix, iz = self._hash()
        w, _h, d = self.mundo.tam
        suelo = self.mundo.altura
        agua = self.mundo.agua_sup
        rng = self.rng
        vel_clima = 0.62 if (clima and clima.frio) else 1.0
        hambre_extra = 0.55 if (clima and clima.sequia) else 0.0
        if clima is not None:
            vivos = self.vivo & (self.estado != MUERTO)
            self.pos[vivos, 0] += clima.viento[0] * dt * 0.12
            self.pos[vivos, 2] += clima.viento[2] * dt * 0.12
            if clima.tornado is not None:
                dlt = self.pos[vivos] - clima.tornado
                r2 = dlt[:, 0] ** 2 + dlt[:, 2] ** 2
                near = r2 < 64.0
                if np.any(near):
                    idx = np.nonzero(vivos)[0][near]
                    pull = clima.tornado - self.pos[idx]
                    self.pos[idx, 0] += pull[:, 0] * dt * 1.8
                    self.pos[idx, 2] += pull[:, 2] * dt * 1.8
                    self.pos[idx, 1] += dt * 2.4
                    self.vida[idx] -= dt * 4.0

        # Los lejanos a la cámara se actualizan más barato.
        if cam is not None:
            dist2 = np.sum((self.pos - cam) ** 2, axis=1)
            activos = dist2 < (95.0 ** 2)
        else:
            activos = np.ones(self.n, np.bool_)

        self.cd = np.maximum(self.cd - dt, 0.0)
        self.salto = np.maximum(self.salto - dt, 0.0)

        for i in range(self.n):
            e = ESPECIES[int(self.esp[i])]
            if self.estado[i] == MUERTO:
                self.vel[i] *= 0.2
                self.hambre[i] += dt
                if self.hambre[i] > 18:
                    self.vivo[i] = False
                    self.pos[i, 1] = -50
                else:
                    self._asentar(i, e, suelo, agua, dt)
                continue
            if not self.vivo[i]:
                continue

            self.hambre[i] += dt * ((0.9 if e.dieta == "carne" else 0.55) + hambre_extra)
            if self.vida[i] <= 0 or self.hambre[i] > e.hambre_t:
                self.estado[i] = MUERTO
                self.vida[i] = 0
                self.hambre[i] = 0
                self.vel[i] = 0
                continue

            if not activos[i]:
                self.wander_ang[i] += (rng.random() - 0.5) * 1.8 * dt
                self.yaw[i] += (self.wander_ang[i] - self.yaw[i]) * 0.4 * dt
                self.pos[i, 0] = np.clip(self.pos[i, 0] + np.cos(self.yaw[i]) * e.vel * 0.18 * dt, 1.2, w - 2.2)
                self.pos[i, 2] = np.clip(self.pos[i, 2] + np.sin(self.yaw[i]) * e.vel * 0.18 * dt, 1.2, d - 2.2)
                self._asentar(i, e, suelo, agua, dt)
                continue

            cerca = self._cerca(celdas, ix, iz, i, e.vision)
            depredador = None
            presa = None
            carroña = None
            for d2, j in cerca:
                je = int(self.esp[j])
                if self.estado[j] == MUERTO:
                    if e.dieta in ("carne", "omni"):
                        carroña = j
                    continue
                if not self.vivo[j]:
                    continue
                if int(self.esp[i]) in ESPECIES[je].presas:
                    depredador = j
                    break
                if je in e.presas and presa is None:
                    presa = j

            dest = None
            rap_obj = e.vel * vel_clima
            if clima is not None and clima.peligro and rng.random() < 0.04 and not e.vuela:
                dest = self.pos[i] + rng.normal(0, 8, 3)
                self.estado[i] = HUIR
                rap_obj *= 1.45
            elif depredador is not None:
                self.estado[i] = HUIR
                away = self.pos[i] - self.pos[depredador]
                dest = self.pos[i] + away
                rap_obj *= 1.55
            elif e.dieta in ("carne", "omni") and self.hambre[i] > e.hambre_t * 0.35 and presa is not None:
                self.estado[i] = CAZAR
                dest = self.pos[presa]
                self.objetivo[i] = presa
                rap_obj *= 1.15
                if np.linalg.norm(self.pos[presa] - self.pos[i]) < 0.55 + e.escala:
                    self.estado[i] = ATACAR
                    rap_obj *= 0.35
                    if self.cd[i] <= 0:
                        self.vida[presa] -= e.dano
                        self.cd[i] = 0.45
                        self.hambre[i] = max(0.0, self.hambre[i] - 2.5)
                        if self.vida[presa] <= 0:
                            self.estado[presa] = MUERTO
                            self.hambre[i] = max(0.0, self.hambre[i] - 10)
                            self._reproducir(i)
            elif carroña is not None and self.hambre[i] > 6:
                dest = self.pos[carroña]
                self.estado[i] = CAZAR
                if np.linalg.norm(self.pos[carroña] - self.pos[i]) < 0.7:
                    self.hambre[i] = max(0.0, self.hambre[i] - 12)
                    self.vivo[carroña] = False
                    self.pos[carroña, 1] = -50
                    self.estado[i] = COMER
                    rap_obj = 0.0
            elif e.dieta in ("hierba", "nectar", "omni") and self.hambre[i] > 5:
                self.estado[i] = COMER
                self.hambre[i] = max(0.0, self.hambre[i] - dt * 7.0)
                if rng.random() < 0.004:
                    self._reproducir(i)
                # Pastan: se quedan, miran y dan un paso de vez en cuando.
                if rng.random() < 0.015:
                    dest = self.pos[i] + rng.normal(0, 1.4, 3)
                    rap_obj *= 0.35
                else:
                    rap_obj = 0.0
                    self.yaw_obj[i] += (rng.random() - 0.5) * 1.6 * dt
            else:
                self.estado[i] = WANDER
                if self.cd[i] <= 0 and rng.random() < 0.012:
                    self.cd[i] = float(rng.uniform(0.6, 1.8))
                    rap_obj = 0.0
                    self.yaw_obj[i] += (rng.random() - 0.5) * 2.4
                else:
                    self.wander_ang[i] += (rng.random() - 0.5) * 3.4 * dt
                    fx, fz = float(np.cos(self.yaw[i])), float(np.sin(self.yaw[i]))
                    dest = self.pos[i] + np.array(
                        (fx * 3.8 + np.cos(self.wander_ang[i]) * 1.8,
                         0.0,
                         fz * 3.8 + np.sin(self.wander_ang[i]) * 1.8),
                        np.float32,
                    )
                    rap_obj *= 0.72

            deseada = np.zeros(3, np.float32)
            if dest is not None and rap_obj > 0.02:
                dir3 = np.asarray(dest, np.float32) - self.pos[i]
                dir3[1] = 0
                nrm = float(np.linalg.norm(dir3))
                if nrm > 0.08:
                    dir3 /= nrm
                    self.yaw_obj[i] = float(np.arctan2(dir3[2], dir3[0]))
                    deseada[0] = dir3[0] * rap_obj
                    deseada[2] = dir3[2] * rap_obj

            # Inercia: no arrancan ni frenan de golpe.
            accel = 5.5 if self.estado[i] == HUIR else 3.2
            self.vel[i] += (deseada - self.vel[i]) * min(1.0, accel * dt)
            if e.nombre in ("Rana", "Conejo", "Ratón"):
                # Saltos: impulsos cortos, no un desliz continuo.
                impulso = 1.75 if e.nombre == "Rana" else 1.42
                espera = 0.58 if e.nombre == "Rana" else 0.36
                if self.salto[i] <= 0 and float(np.linalg.norm(deseada)) > 0.15:
                    self.vel[i] = deseada * impulso
                    self.salto[i] = espera
                elif self.salto[i] > espera * 0.45:
                    self.vel[i] *= 0.90
                else:
                    self.vel[i] *= 0.48

            self.pos[i, 0] = float(np.clip(self.pos[i, 0] + self.vel[i, 0] * dt, 1.2, w - 2.2))
            self.pos[i, 2] = float(np.clip(self.pos[i, 2] + self.vel[i, 2] * dt, 1.2, d - 2.2))
            self.rapidez[i] = float(np.hypot(self.vel[i, 0], self.vel[i, 2]))
            self.yaw[i] = _lerp_ang(self.yaw[i], self.yaw_obj[i], min(1.0, 7.0 * dt))
            self.yaw[i] = (self.yaw[i] + np.pi) % (2 * np.pi) - np.pi
            self.fase[i] += dt * (2.4 + self.rapidez[i] * 3.6)
            self._asentar(i, e, suelo, agua, dt)

    def _asentar(self, i, e, suelo, agua, dt):
        xi = int(np.clip(self.pos[i, 0], 0, suelo.shape[0] - 1))
        zi = int(np.clip(self.pos[i, 2], 0, suelo.shape[1] - 1))
        base = float(suelo[xi, zi])
        if self.estado[i] == MUERTO:
            objetivo = base + 0.02
        elif e.vuela:
            oleaje = 0.45 * np.sin(self.fase[i] * 0.7) + 0.18 * np.sin(self.fase[i] * 1.7)
            objetivo = float(np.clip(base + 3.6 + oleaje, base + 1.6, base + 5.4))
        elif e.nombre == "Pez":
            if agua[xi, zi] > 0:
                objetivo = max(base - 0.15, 0.35) + 0.18 * np.sin(self.fase[i])
            else:
                objetivo = base + 0.05
        elif e.nada and agua[xi, zi] > 0:
            objetivo = max(base, float(agua[xi, zi]) - 0.12) + 0.06 * np.sin(self.fase[i] * 0.8)
        else:
            objetivo = base
        if e.nombre in ("Rana", "Conejo", "Ratón") and self.estado[i] != MUERTO and self.salto[i] > 0:
            dur = 0.58 if e.nombre == "Rana" else 0.36
            arco = float(np.sin(np.clip(1.0 - self.salto[i] / dur, 0.0, 1.0) * np.pi))
            objetivo += arco * (0.30 if e.nombre == "Rana" else 0.14)
        self.y_suelo[i] = objetivo
        k = 14.0 if not e.vuela else 3.2
        self.pos[i, 1] += (objetivo - self.pos[i, 1]) * min(1.0, k * dt)

    def _reproducir(self, i):
        e = ESPECIES[int(self.esp[i])]
        vivos = int(np.sum(self.vivo & (self.esp == self.esp[i]) & (self.estado != MUERTO)))
        if vivos >= e.poblacion + 6:
            return
        if self.n > 340:
            return
        self._agregar(int(self.esp[i]), self.pos[i] + self.rng.normal(0, 0.6, 3))

    def _agregar(self, tipo, pos):
        e = ESPECIES[tipo]
        yaw0 = np.float32(self.rng.random() * 6.28)
        self.esp = np.append(self.esp, np.int32(tipo))
        self.pos = np.vstack([self.pos, pos.astype(np.float32)])
        self.vel = np.vstack([self.vel, np.zeros(3, np.float32)])
        self.yaw = np.append(self.yaw, yaw0)
        self.yaw_obj = np.append(self.yaw_obj, yaw0)
        self.wander_ang = np.append(self.wander_ang, yaw0)
        self.hambre = np.append(self.hambre, np.float32(3.0))
        self.vida = np.append(self.vida, np.float32(e.vida))
        self.estado = np.append(self.estado, np.int32(WANDER))
        self.fase = np.append(self.fase, np.float32(0.0))
        self.cd = np.append(self.cd, np.float32(2.0))
        self.objetivo = np.append(self.objetivo, np.int32(-1))
        self.vivo = np.append(self.vivo, True)
        self.rapidez = np.append(self.rapidez, np.float32(0.0))
        self.y_suelo = np.append(self.y_suelo, np.float32(pos.astype(np.float32)[1]))
        self.salto = np.append(self.salto, np.float32(0.0))
        self.n = len(self.esp)

    def conteo(self):
        out = []
        for i, e in enumerate(ESPECIES):
            n = int(np.sum(self.vivo & (self.esp == i) & (self.estado != MUERTO)))
            out.append((e.nombre, n))
        return out

    def malla_visible(self, cam, radio=90.0):
        """Una sola malla con todos los animales cercanos, ya transformados."""
        if self.n == 0:
            return (np.zeros((0, 3), np.float32),) * 3
        d2 = np.sum((self.pos - cam) ** 2, axis=1)
        vis = (d2 < radio * radio) & (self.vivo | (self.estado == MUERTO))
        if not np.any(vis):
            return (np.zeros((0, 3), np.float32),) * 3

        ps, ns, cs = [], [], []
        for tipo in range(len(ESPECIES)):
            idx = np.nonzero(vis & (self.esp == tipo))[0]
            if len(idx) == 0:
                continue
            base_p, base_n, base_c = MODELOS[tipo]
            e = ESPECIES[tipo]
            P = self.pos[idx]
            yaw = self.yaw[idx]
            muerto = self.estado[idx] == MUERTO
            fase = self.fase[idx]
            c, s = np.cos(yaw), np.sin(yaw)
            esc = e.escala * np.where(muerto, 0.35, 1.0)
            rap = self.rapidez[idx]
            # Paso: trote, salto o aleteo según la especie.
            if e.nombre in ("Conejo", "Rana", "Ratón"):
                ciclo = np.abs(np.sin(fase))
                bob = np.where(muerto, 0.0, ciclo * np.clip(rap * 0.12, 0.02, 0.16))
            elif e.vuela:
                bob = np.where(muerto, 0.0, 0.08 * np.sin(fase * 2.2) + 0.03 * np.sin(fase * 5.1))
            elif e.nombre == "Pez":
                bob = np.where(muerto, 0.0, 0.04 * np.sin(fase * 2.0))
            else:
                bob = np.where(muerto, 0.0, 0.045 * np.sin(fase * 2.0) * np.clip(rap * 0.35, 0.15, 1.2))
            roll = np.where(muerto, 0.0, 0.07 * np.sin(fase) * np.clip(rap * 0.25, 0.0, 1.0))
            # (N, V, 3)
            bp = base_p[None, :, :] * esc[:, None, None]
            # Ligero balanceo al caminar (eje X local).
            y_loc = bp[..., 1] + bp[..., 0] * roll[:, None]
            x = bp[..., 0] * c[:, None] - bp[..., 2] * s[:, None]
            z = bp[..., 0] * s[:, None] + bp[..., 2] * c[:, None]
            y = y_loc + P[:, 1, None] + bob[:, None]
            x = x + P[:, 0, None]
            z = z + P[:, 2, None]
            world = np.stack([x, y, z], axis=-1).reshape(-1, 3)
            bn = np.broadcast_to(base_n[None, :, :], (len(idx), len(base_n), 3))
            nx = bn[..., 0] * c[:, None] - bn[..., 2] * s[:, None]
            nz = bn[..., 0] * s[:, None] + bn[..., 2] * c[:, None]
            nrm = np.stack([nx, bn[..., 1], nz], axis=-1).reshape(-1, 3)
            col = np.broadcast_to(base_c[None, :, :], (len(idx), len(base_c), 3)).reshape(-1, 3).copy()
            if np.any(muerto):
                mask = np.repeat(muerto, len(base_c))
                col[mask] *= 0.35
            ps.append(world)
            ns.append(nrm)
            cs.append(col)
        return (
            np.ascontiguousarray(np.concatenate(ps), np.float32),
            np.ascontiguousarray(np.concatenate(ns), np.float32),
            np.ascontiguousarray(np.concatenate(cs), np.float32),
        )

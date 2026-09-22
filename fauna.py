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
    c, e = esp.cuerpo, esp.extra
    s = 1.0
    pos, nrm, col = [], [], []

    def add(p, n, k):
        pos.extend(p)
        nrm.extend(n)
        col.extend(k)

    if esp.nombre == "Mariposa":
        add(*_caja(-0.05, 0.08, -0.12, 0.05, 0.16, 0.12, e))
        add(*_caja(-0.32, 0.10, -0.08, -0.05, 0.14, 0.08, c))
        add(*_caja(0.05, 0.10, -0.08, 0.32, 0.14, 0.08, c))
    elif esp.nombre == "Pez":
        add(*_caja(-0.08, 0.02, -0.22, 0.08, 0.16, 0.18, c))
        add(*_caja(-0.04, 0.06, 0.18, 0.04, 0.14, 0.28, e))
        add(*_caja(-0.02, 0.16, -0.04, 0.02, 0.24, 0.06, e))
    elif esp.nombre == "Águila":
        add(*_caja(-0.08, 0.10, -0.18, 0.08, 0.20, 0.16, c))
        add(*_caja(-0.06, 0.12, 0.16, 0.06, 0.22, 0.28, c))
        add(*_caja(-0.42, 0.14, -0.06, -0.08, 0.17, 0.10, e))
        add(*_caja(0.08, 0.14, -0.06, 0.42, 0.17, 0.10, e))
    else:
        largo = 0.38 if esp.nombre in ("Ciervo", "Lobo", "Oso", "Jabalí") else 0.30
        alto = 0.22 if esp.nombre != "Oso" else 0.26
        add(*_caja(-0.14, 0.12, -largo, 0.14, 0.12 + alto, largo * 0.55, c))
        add(*_caja(-0.10, 0.16, largo * 0.50, 0.10, 0.16 + alto * 0.85, largo * 0.95, e if esp.nombre == "Pato" else c))
        if esp.nombre == "Conejo":
            add(*_caja(-0.08, 0.34, 0.18, -0.03, 0.50, 0.24, e))
            add(*_caja(0.03, 0.34, 0.18, 0.08, 0.50, 0.24, e))
        if esp.nombre == "Ciervo":
            add(*_caja(-0.08, 0.38, 0.22, -0.04, 0.58, 0.26, e))
            add(*_caja(0.04, 0.38, 0.22, 0.08, 0.58, 0.26, e))
        if esp.nombre == "Pato":
            add(*_caja(-0.03, 0.28, 0.28, 0.03, 0.32, 0.42, (0.80, 0.50, 0.10)))
        pata_y1 = 0.12
        for sx, sz in ((-0.09, -largo * 0.6), (0.09, -largo * 0.6), (-0.09, largo * 0.25), (0.09, largo * 0.25)):
            add(*_caja(sx - 0.03, 0.0, sz - 0.03, sx + 0.03, pata_y1, sz + 0.03, e))
        add(*_caja(-0.03, 0.16, -largo - 0.12, 0.03, 0.22, -largo, e))

    p = np.array(pos, dtype=np.float32) * s
    n = np.array(nrm, dtype=np.float32)
    k = np.array(col, dtype=np.float32)
    return p, n, k


MODELOS = [_modelo(e) for e in ESPECIES]


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
        self.hambre = self.rng.uniform(4, 12, n).astype(np.float32)
        self.vida = np.array([ESPECIES[int(i)].vida for i in self.esp], np.float32)
        self.estado = np.zeros(n, np.int32)
        self.fase = self.rng.random(n).astype(np.float32) * 20
        self.cd = np.zeros(n, np.float32)
        self.objetivo = np.full(n, -1, np.int32)
        self.vivo = np.ones(n, np.bool_)
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

    def actualizar(self, dt, cam=None):
        if self.n == 0:
            return
        dt = min(dt, 0.05)
        celdas, ix, iz = self._hash()
        w, _h, d = self.mundo.tam
        suelo = self.mundo.altura
        agua = self.mundo.agua_sup
        rng = self.rng

        # Los lejanos a la cámara se actualizan más barato.
        if cam is not None:
            dist2 = np.sum((self.pos - cam) ** 2, axis=1)
            activos = dist2 < (95.0 ** 2)
        else:
            activos = np.ones(self.n, np.bool_)

        self.fase += dt * 8.0
        self.cd = np.maximum(self.cd - dt, 0.0)

        for i in range(self.n):
            e = ESPECIES[int(self.esp[i])]
            if self.estado[i] == MUERTO:
                self.hambre[i] += dt
                if self.hambre[i] > 18:
                    self.vivo[i] = False
                    self.pos[i, 1] = -50
                continue
            if not self.vivo[i]:
                continue

            self.hambre[i] += dt * (0.9 if e.dieta == "carne" else 0.55)
            if self.vida[i] <= 0 or self.hambre[i] > e.hambre_t:
                self.estado[i] = MUERTO
                self.vida[i] = 0
                self.hambre[i] = 0
                continue

            if not activos[i]:
                self.pos[i, 0] = np.clip(self.pos[i, 0] + np.cos(self.yaw[i]) * e.vel * 0.25 * dt, 1.2, w - 2.2)
                self.pos[i, 2] = np.clip(self.pos[i, 2] + np.sin(self.yaw[i]) * e.vel * 0.25 * dt, 1.2, d - 2.2)
                self._poner_altura(i, e, suelo, agua)
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
            if depredador is not None:
                self.estado[i] = HUIR
                away = self.pos[i] - self.pos[depredador]
                dest = self.pos[i] + away
            elif e.dieta in ("carne", "omni") and self.hambre[i] > e.hambre_t * 0.35 and presa is not None:
                self.estado[i] = CAZAR
                dest = self.pos[presa]
                self.objetivo[i] = presa
                if np.linalg.norm(self.pos[presa] - self.pos[i]) < 0.55 + e.escala:
                    self.estado[i] = ATACAR
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
                if np.linalg.norm(self.pos[carroña] - self.pos[i]) < 0.7:
                    self.hambre[i] = max(0.0, self.hambre[i] - 12)
                    self.vivo[carroña] = False
                    self.pos[carroña, 1] = -50
                    self.estado[i] = COMER
            elif e.dieta in ("hierba", "nectar", "omni") and self.hambre[i] > 5:
                self.estado[i] = COMER
                self.hambre[i] = max(0.0, self.hambre[i] - dt * 7.0)
                if rng.random() < 0.004:
                    self._reproducir(i)
                if rng.random() < 0.35:
                    dest = self.pos[i] + rng.normal(0, 2.5, 3)
            else:
                self.estado[i] = WANDER
                if self.cd[i] <= 0:
                    dest = self.pos[i] + rng.normal(0, 6, 3)
                    self.cd[i] = float(rng.uniform(1.2, 3.0))

            if dest is not None:
                dir3 = dest - self.pos[i]
                dir3[1] = 0
                nrm = float(np.linalg.norm(dir3))
                if nrm > 0.05:
                    dir3 /= nrm
                    self.yaw[i] = float(np.arctan2(dir3[2], dir3[0]))
                    rap = e.vel * (1.45 if self.estado[i] == HUIR else 1.0)
                    self.pos[i, 0] += dir3[0] * rap * dt
                    self.pos[i, 2] += dir3[2] * rap * dt

            self.pos[i, 0] = float(np.clip(self.pos[i, 0], 1.2, w - 2.2))
            self.pos[i, 2] = float(np.clip(self.pos[i, 2], 1.2, d - 2.2))
            self._poner_altura(i, e, suelo, agua)

    def _poner_altura(self, i, e, suelo, agua):
        xi = int(np.clip(self.pos[i, 0], 0, suelo.shape[0] - 1))
        zi = int(np.clip(self.pos[i, 2], 0, suelo.shape[1] - 1))
        base = float(suelo[xi, zi])
        if self.estado[i] == MUERTO:
            self.pos[i, 1] = base + 0.02
            return
        if e.vuela:
            techo = base + 5.2
            self.pos[i, 1] += (techo - 1.2 - self.pos[i, 1]) * 0.04
            self.pos[i, 1] = float(np.clip(self.pos[i, 1], base + 1.4, techo))
        elif e.nombre == "Pez":
            if agua[xi, zi] > 0:
                self.pos[i, 1] = max(base - 0.15, 0.35) + 0.25 * np.sin(self.fase[i])
            else:
                self.pos[i, 1] = base + 0.05
        elif e.nada and agua[xi, zi] > 0:
            self.pos[i, 1] = max(base, float(agua[xi, zi]) - 0.15)
        else:
            self.pos[i, 1] = base

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
        self.esp = np.append(self.esp, np.int32(tipo))
        self.pos = np.vstack([self.pos, pos.astype(np.float32)])
        self.vel = np.vstack([self.vel, np.zeros(3, np.float32)])
        self.yaw = np.append(self.yaw, np.float32(self.rng.random() * 6.28))
        self.hambre = np.append(self.hambre, np.float32(3.0))
        self.vida = np.append(self.vida, np.float32(e.vida))
        self.estado = np.append(self.estado, np.int32(WANDER))
        self.fase = np.append(self.fase, np.float32(0.0))
        self.cd = np.append(self.cd, np.float32(2.0))
        self.objetivo = np.append(self.objetivo, np.int32(-1))
        self.vivo = np.append(self.vivo, True)
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
            bob = np.where(muerto, 0.0, 0.03 * np.sin(fase))
            # (N, V, 3)
            bp = base_p[None, :, :] * esc[:, None, None]
            x = bp[..., 0] * c[:, None] - bp[..., 2] * s[:, None]
            z = bp[..., 0] * s[:, None] + bp[..., 2] * c[:, None]
            y = bp[..., 1]
            y = y + P[:, 1, None] + bob[:, None]
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

"""Frutas en los árboles: manzana, naranja y baya. Los herbívoros las comen."""
import numpy as np

from mundo import HOJAS, MADERA

MANZANA, NARANJA, BAYA = 0, 1, 2
COLORES = np.array([
    (0.86, 0.12, 0.10),
    (0.95, 0.52, 0.08),
    (0.55, 0.12, 0.62),
], dtype=np.float32)
NOMBRES_FRUTA = ["Manzana", "Naranja", "Baya"]


def _octaedro(r, color):
    verts = np.array([
        [0, r, 0], [r, 0, 0], [0, 0, r],
        [0, r, 0], [0, 0, r], [-r, 0, 0],
        [0, r, 0], [-r, 0, 0], [0, 0, -r],
        [0, r, 0], [0, 0, -r], [r, 0, 0],
        [0, -r, 0], [0, 0, r], [r, 0, 0],
        [0, -r, 0], [-r, 0, 0], [0, 0, r],
        [0, -r, 0], [0, 0, -r], [-r, 0, 0],
        [0, -r, 0], [r, 0, 0], [0, 0, -r],
    ], dtype=np.float32)
    nrm = np.repeat([[0, 1, 0], [1, 0, 0], [0, 0, 1], [-1, 0, 0],
                     [0, -1, 0], [0, 0, 1], [0, 0, -1], [1, 0, 0]], 3, axis=0).astype(np.float32)
    col = np.repeat(np.array([color], np.float32), len(verts), axis=0)
    return verts, nrm, col


_MODELOS = [_octaedro(0.16, COLORES[i]) for i in range(3)]


class Frutas:
    def __init__(self, mundo, semilla=None):
        self.mundo = mundo
        self.rng = np.random.default_rng(semilla)
        self.poblar()

    def poblar(self, extra=0):
        hojas = np.argwhere(self.mundo.grid == HOJAS)
        if len(hojas) == 0:
            self.n = 0
            self.pos = np.zeros((0, 3), np.float32)
            self.tipo = np.zeros(0, np.int32)
            self.vivo = np.zeros(0, np.bool_)
            return
        k = min(len(hojas), 70 + extra)
        idx = self.rng.choice(len(hojas), size=k, replace=False)
        celdas = hojas[idx]
        self.pos = (celdas.astype(np.float32) + self.rng.uniform(0.15, 0.85, celdas.shape)).astype(np.float32)
        self.pos[:, 1] -= 0.15
        self.tipo = self.rng.integers(0, 3, k).astype(np.int32)
        self.vivo = np.ones(k, np.bool_)
        self.n = k

    def actualizar(self, dt, clima, fauna=None):
        if self.n == 0:
            return
        # Sequía pudre, lluvia hace brotar, tornado tira.
        if clima.sequia and self.rng.random() < 0.08 * dt:
            vivos = np.nonzero(self.vivo)[0]
            if len(vivos):
                self.vivo[int(self.rng.choice(vivos))] = False
        if clima.lluvia and self.rng.random() < 0.35 * dt:
            self._brotar()
        if clima.tornado is not None:
            d = self.pos - clima.tornado
            cerca = self.vivo & (d[:, 0] ** 2 + d[:, 2] ** 2 < 36)
            self.pos[cerca, 1] -= 6 * dt
            caen = cerca & (self.pos[:, 1] < self.mundo.altura[
                np.clip(self.pos[:, 0].astype(int), 0, self.mundo.tam[0] - 1),
                np.clip(self.pos[:, 2].astype(int), 0, self.mundo.tam[2] - 1),
            ] + 0.2)
            self.vivo[caen] = False

        if fauna is None or fauna.n == 0:
            return
        from fauna import ESPECIES, MUERTO
        herb = np.nonzero(fauna.vivo & (fauna.estado != MUERTO))[0]
        for i in herb:
            if ESPECIES[int(fauna.esp[i])].dieta not in ("hierba", "nectar", "omni"):
                continue
            if fauna.hambre[i] < 4:
                continue
            delta = self.pos - fauna.pos[i]
            d2 = np.sum(delta * delta, axis=1)
            hit = self.vivo & (d2 < 0.85)
            if np.any(hit):
                j = int(np.argmin(np.where(hit, d2, 1e9)))
                self.vivo[j] = False
                fauna.hambre[i] = max(0.0, fauna.hambre[i] - 9.0)

    def _brotar(self):
        hojas = np.argwhere(self.mundo.grid == HOJAS)
        if len(hojas) == 0:
            return
        celda = hojas[int(self.rng.integers(0, len(hojas)))]
        pos = celda.astype(np.float32) + self.rng.uniform(0.2, 0.8, 3)
        pos[1] -= 0.1
        if self.n == 0:
            self.pos = pos[None, :].astype(np.float32)
            self.tipo = np.array([int(self.rng.integers(0, 3))], np.int32)
            self.vivo = np.array([True])
        else:
            self.pos = np.vstack([self.pos, pos])
            self.tipo = np.append(self.tipo, np.int32(self.rng.integers(0, 3)))
            self.vivo = np.append(self.vivo, True)
        self.n = len(self.tipo)
        if self.n > 160:
            # recicla las muertas
            muertos = np.nonzero(~self.vivo)[0]
            if len(muertos):
                self.pos = np.delete(self.pos, muertos[:20], axis=0)
                self.tipo = np.delete(self.tipo, muertos[:20])
                self.vivo = np.delete(self.vivo, muertos[:20])
                self.n = len(self.tipo)

    def malla_visible(self, cam, radio=90.0):
        if self.n == 0 or not np.any(self.vivo):
            return (np.zeros((0, 3), np.float32),) * 3
        d2 = np.sum((self.pos - cam) ** 2, axis=1)
        vis = self.vivo & (d2 < radio * radio)
        if not np.any(vis):
            return (np.zeros((0, 3), np.float32),) * 3
        ps, ns, cs = [], [], []
        for t in range(3):
            idx = np.nonzero(vis & (self.tipo == t))[0]
            if len(idx) == 0:
                continue
            bp, bn, bc = _MODELOS[t]
            P = self.pos[idx]
            world = (bp[None, :, :] + P[:, None, :]).reshape(-1, 3)
            nrm = np.broadcast_to(bn[None, :, :], (len(idx), len(bn), 3)).reshape(-1, 3)
            col = np.broadcast_to(bc[None, :, :], (len(idx), len(bc), 3)).reshape(-1, 3)
            ps.append(world)
            ns.append(nrm)
            cs.append(col)
        return (
            np.ascontiguousarray(np.concatenate(ps), np.float32),
            np.ascontiguousarray(np.concatenate(ns), np.float32),
            np.ascontiguousarray(np.concatenate(cs), np.float32),
        )

    def conteo(self):
        return int(np.sum(self.vivo)) if self.n else 0

"""Mundo de bloques grande: chunks, texturas por cara, altura para la fauna."""
import math

import cv2
import numpy as np

from texturas import TILES_BLOQUE

PALETA = [
    (0.0, 0.0, 0.0),
    (0.36, 0.72, 0.30),
    (0.55, 0.38, 0.22),
    (0.55, 0.55, 0.58),
    (0.25, 0.50, 0.90),
    (0.92, 0.84, 0.58),
    (0.45, 0.29, 0.15),
    (0.18, 0.52, 0.20),
    (0.90, 0.25, 0.25),
    (0.96, 0.96, 0.98),
]
NOMBRES = ["", "Pasto", "Tierra", "Piedra", "Agua", "Arena", "Madera", "Hojas", "Ladrillo", "Nieve"]
PASTO, TIERRA, PIEDRA, AGUA, ARENA, MADERA, HOJAS, LADRILLO, NIEVE = range(1, 10)
_PALETA_NP = np.array(PALETA, dtype=np.float32)
_TILE_LUT = np.zeros((10, 3), dtype=np.float32)
for _tipo, (_top, _side, _bot) in TILES_BLOQUE.items():
    _TILE_LUT[_tipo] = (_bot, _side, _top)

CARAS = [
    ((1, 0, 0), [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)], 0.80),
    ((-1, 0, 0), [(0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0)], 0.80),
    ((0, 1, 0), [(0, 1, 0), (0, 1, 1), (1, 1, 1), (1, 1, 0)], 1.00),
    ((0, -1, 0), [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)], 0.50),
    ((0, 0, 1), [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)], 0.65),
    ((0, 0, -1), [(0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 0)], 0.65),
]
_TRI = np.array([0, 1, 2, 0, 2, 3], dtype=np.intp)
_VACIO = (
    np.zeros((0, 3), np.float32),
    np.zeros((0, 3), np.float32),
    np.zeros((0, 3), np.float32),
    np.zeros((0, 2), np.float32),
)

MAX_HISTORIAL = 24
SUBDIV_AGUA = 2
CHUNK = 16
ANCHO_MUNDO, ALTO_MUNDO, FONDO_MUNDO = 128, 30, 128


class Mundo:
    def __init__(self, ancho=ANCHO_MUNDO, alto=ALTO_MUNDO, fondo=FONDO_MUNDO):
        self.tam = (ancho, alto, fondo)
        self.grid = np.zeros(self.tam, dtype=np.uint8)
        self.historial = []
        self.version = 0
        self.cx = (ancho + CHUNK - 1) // CHUNK
        self.cz = (fondo + CHUNK - 1) // CHUNK
        self.chunk_dirty = np.ones((self.cx, self.cz), dtype=bool)
        self._cache_s = {}
        self._cache_a = {}
        self.altura = np.zeros((ancho, fondo), dtype=np.int32)
        self.agua_sup = np.zeros((ancho, fondo), dtype=np.int32)

    def dentro(self, x, y, z):
        w, h, d = self.tam
        return 0 <= x < w and 0 <= y < h and 0 <= z < d

    def _registrar(self):
        self.historial.append(self.grid.copy())
        if len(self.historial) > MAX_HISTORIAL:
            self.historial.pop(0)

    def _ensuciar_celda(self, x, z):
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                ci = (x + dx) // CHUNK
                cj = (z + dz) // CHUNK
                if 0 <= ci < self.cx and 0 <= cj < self.cz:
                    self.chunk_dirty[ci, cj] = True

    def _ensuciar_todo(self):
        self.chunk_dirty[:] = True
        self._cache_s.clear()
        self._cache_a.clear()

    def _cambio(self, celda=None):
        self.version += 1
        if celda is None:
            self._ensuciar_todo()
            self._recalcular_altura()
        else:
            x, y, z = celda
            self._ensuciar_celda(x, z)
            self._recalcular_altura_col(x, z)

    def _recalcular_altura_col(self, x, z):
        col = self.grid[x, :, z]
        sol = (col > 0) & (col != AGUA)
        ys = np.nonzero(sol)[0]
        self.altura[x, z] = int(ys[-1] + 1) if len(ys) else 0
        wa = np.nonzero(col == AGUA)[0]
        self.agua_sup[x, z] = int(wa[-1] + 1) if len(wa) else 0

    def _recalcular_altura(self):
        solido = (self.grid > 0) & (self.grid != AGUA)
        ys = np.where(solido, np.arange(self.tam[1], dtype=np.int32)[None, :, None] + 1, 0)
        self.altura = ys.max(axis=1)
        agua = self.grid == AGUA
        ya = np.where(agua, np.arange(self.tam[1], dtype=np.int32)[None, :, None] + 1, 0)
        self.agua_sup = ya.max(axis=1)

    def poner(self, celda, color):
        if celda is None or not self.dentro(*celda) or self.grid[celda]:
            return False
        self._registrar()
        self.grid[celda] = color
        self._cambio(celda)
        return True

    def quitar(self, celda):
        if celda is None or not self.dentro(*celda) or not self.grid[celda]:
            return False
        self._registrar()
        self.grid[celda] = 0
        self._cambio(celda)
        return True

    def deshacer(self):
        if not self.historial:
            return False
        self.grid = self.historial.pop()
        self._cambio()
        return True

    def limpiar(self):
        self._registrar()
        self.grid[:] = 0
        self._cambio()

    def guardar(self, ruta):
        np.save(ruta, self.grid)

    def cargar(self, ruta):
        datos = np.load(ruta)
        if datos.shape != self.tam:
            raise ValueError(f"tamaño {datos.shape} distinto de {self.tam}")
        self._registrar()
        self.grid = datos.astype(np.uint8)
        self._cambio()

    def generar_terreno(self, semilla=None, registrar=True):
        if registrar:
            self._registrar()
        w, h, d = self.tam
        rng = np.random.default_rng(semilla)

        def ruido(celdas):
            base = rng.random((celdas + 1, celdas + 1)).astype(np.float32)
            return cv2.resize(base, (d, w), interpolation=cv2.INTER_CUBIC)

        v = 0.42 * ruido(3) + 0.28 * ruido(7) + 0.18 * ruido(14) + 0.12 * ruido(28)
        v = (v - v.min()) / (v.max() - v.min() + 1e-6)
        alturas = (2 + v * min(h - 10, 16)).astype(np.int32)
        nivel_agua = 6

        Y = np.arange(h, dtype=np.int32).reshape(1, h, 1)
        A = alturas[:, None, :]
        g = np.zeros(self.tam, dtype=np.uint8)
        g[Y < A] = PIEDRA
        g[(Y >= np.maximum(A - 3, 0)) & (Y < A)] = TIERRA

        bajo = A <= nivel_agua
        g[bajo & (Y >= np.maximum(A - 2, 0)) & (Y < A)] = ARENA
        g[bajo & (Y >= A) & (Y < nivel_agua)] = AGUA

        xs, zs = np.indices((w, d))
        ys = np.maximum(alturas - 1, 0)
        tope = np.where(alturas <= nivel_agua, ARENA, np.where(alturas >= 15, NIEVE, PASTO))
        g[xs, ys, zs] = tope

        n_arboles = int(w * d * 0.0035)
        for _ in range(n_arboles):
            x, z = int(rng.integers(3, w - 3)), int(rng.integers(3, d - 3))
            a = int(alturas[x, z])
            if g[x, a - 1, z] != PASTO:
                continue
            tronco = int(rng.integers(3, 5))
            if a + tronco + 2 >= h:
                continue
            copa = a + tronco
            hojas = g[x - 2:x + 3, copa - 2:copa + 1, z - 2:z + 3]
            hojas[hojas == 0] = HOJAS
            g[x - 1:x + 2, copa + 1, z - 1:z + 2][g[x - 1:x + 2, copa + 1, z - 1:z + 2] == 0] = HOJAS
            g[x, a:copa, z] = MADERA

        self.grid = g
        self._cambio()

    def raycast(self, origen, direccion, max_pasos=2200):
        w, h, d = self.tam
        celda = [int(math.floor(c)) for c in origen]
        paso, t_max, t_delta = [0, 0, 0], [math.inf] * 3, [math.inf] * 3
        for i in range(3):
            if direccion[i] > 0:
                paso[i] = 1
                t_max[i] = (celda[i] + 1 - origen[i]) / direccion[i]
                t_delta[i] = 1 / direccion[i]
            elif direccion[i] < 0:
                paso[i] = -1
                t_max[i] = (celda[i] - origen[i]) / direccion[i]
                t_delta[i] = -1 / direccion[i]

        previa = None
        for _ in range(max_pasos):
            x, y, z = celda
            if y < 0:
                if previa is not None and 0 <= x < w and 0 <= z < d:
                    return None, previa
                if paso[1] <= 0:
                    return None, None
            elif y >= h and paso[1] >= 0:
                return None, None
            elif 0 <= x < w and y < h and 0 <= z < d and self.grid[x, y, z]:
                return (x, y, z), previa
            previa = (x, y, z)
            eje = 0 if t_max[0] < t_max[1] else 1
            if t_max[2] < t_max[eje]:
                eje = 2
            celda[eje] += paso[eje]
            t_max[eje] += t_delta[eje]
        return None, None

    def _emitir_caras(self, mask, pad, ocupado, olas=None, profundidades=None):
        w, h, d = self.tam
        verts, nrms, cols, auxs = [], [], [], []
        tipos = self.grid
        ncount = (
            ocupado[0:w, 1:h + 1, 1:d + 1].astype(np.float32)
            + ocupado[2:w + 2, 1:h + 1, 1:d + 1]
            + ocupado[1:w + 1, 0:h, 1:d + 1]
            + ocupado[1:w + 1, 2:h + 2, 1:d + 1]
            + ocupado[1:w + 1, 1:h + 1, 0:d]
            + ocupado[1:w + 1, 1:h + 1, 2:d + 2]
        )
        ao_vol = np.clip(1.0 - 0.08 * ncount, 0.52, 1.0)

        for (nx, ny, nz), esquinas, _sombra in CARAS:
            if olas is not None and ny > 0:
                continue
            tapada = pad[1 + nx:1 + nx + w, 1 + ny:1 + ny + h, 1 + nz:1 + nz + d]
            idx = np.argwhere(mask & ~tapada)
            if len(idx) == 0:
                continue
            v = (idx[:, None, :] + np.array(esquinas, dtype=np.float32)[None, :, :]).astype(np.float32)
            v = v[:, _TRI, :].reshape(-1, 3)
            n = np.broadcast_to(np.array([nx, ny, nz], dtype=np.float32), (len(v), 3)).copy()
            tipo = tipos[idx[:, 0], idx[:, 1], idx[:, 2]]
            c = _PALETA_NP[tipo]
            ruido = ((idx[:, 0] * 73856093) ^ (idx[:, 1] * 19349663) ^ (idx[:, 2] * 83492791)) % 1000
            tint = (0.90 + 0.14 * ruido / 1000.0).astype(np.float32)
            c = np.clip(c * tint[:, None], 0, 1)
            c = np.repeat(c, 6, axis=0)

            ao = ao_vol[idx[:, 0], idx[:, 1], idx[:, 2]]
            if ny > 0:
                ao = np.clip(ao + 0.08, 0, 1)
            elif ny < 0:
                ao = ao * 0.72
            ao = np.repeat(ao, 6)

            if olas is None:
                cara = 2 if ny > 0 else (0 if ny < 0 else 1)
                tiles = np.repeat(_TILE_LUT[tipo, cara], 6)
                a = np.stack([ao, tiles], axis=1)
            else:
                ola = np.repeat(olas[idx[:, 0], idx[:, 1], idx[:, 2]], 6)
                if ny == 0:
                    ola = ola * (v[:, 1] >= (np.repeat(idx[:, 1], 6) + 0.99)).astype(np.float32)
                else:
                    ola = np.zeros(len(v), dtype=np.float32)
                prof = np.repeat(profundidades[idx[:, 0], idx[:, 1], idx[:, 2]], 6)
                a = np.stack([ola, prof], axis=1).astype(np.float32)

            verts.append(v)
            nrms.append(n)
            cols.append(c.astype(np.float32))
            auxs.append(a.astype(np.float32))
        if not verts:
            return _VACIO
        return (
            np.ascontiguousarray(np.concatenate(verts), dtype=np.float32),
            np.ascontiguousarray(np.concatenate(nrms), dtype=np.float32),
            np.ascontiguousarray(np.concatenate(cols), dtype=np.float32),
            np.ascontiguousarray(np.concatenate(auxs), dtype=np.float32),
        )

    def _superficie_agua(self, agua, profundidades, xlim, zlim, subdiv=SUBDIV_AGUA):
        w, h, d = self.tam
        x0, x1 = xlim
        z0, z1 = zlim
        pad = np.pad(agua, 1, constant_values=False)
        tope = agua & ~pad[1:w + 1, 2:h + 2, 1:d + 1]
        tope[:x0] = False
        tope[x1:] = False
        tope[:, :, :z0] = False
        tope[:, :, z1:] = False
        tops = np.argwhere(tope)
        if len(tops) == 0:
            return _VACIO

        s = subdiv
        ii, jj = np.meshgrid(np.arange(s, dtype=np.float32), np.arange(s, dtype=np.float32), indexing="ij")
        ii, jj = ii.reshape(-1), jj.reshape(-1)
        u = np.stack([ii, ii + 1, ii + 1, ii], axis=1) / s
        v = np.stack([jj, jj, jj + 1, jj + 1], axis=1) / s
        x = tops[:, 0, None, None].astype(np.float32) + u
        z = tops[:, 2, None, None].astype(np.float32) + v
        y = (tops[:, 1, None, None] + 1.0).astype(np.float32) * np.ones_like(x)
        pos = np.stack([x, y, z], axis=-1)[:, :, _TRI, :].reshape(-1, 3)
        nrm = np.zeros_like(pos)
        nrm[:, 1] = 1.0
        col = np.repeat(np.array([(0.12, 0.42, 0.72)], dtype=np.float32), len(pos), axis=0)
        prof = profundidades[tops[:, 0], tops[:, 1], tops[:, 2]].astype(np.float32)
        prof = np.repeat(prof, s * s * 6)
        aux = np.stack([np.ones(len(pos), dtype=np.float32), prof], axis=1)
        return (
            np.ascontiguousarray(pos, dtype=np.float32),
            np.ascontiguousarray(nrm, dtype=np.float32),
            np.ascontiguousarray(col, dtype=np.float32),
            np.ascontiguousarray(aux, dtype=np.float32),
        )

    def _malla_region(self, x0, x1, z0, z1):
        grid = self.grid
        w, h, d = self.tam
        solido = (grid > 0) & (grid != AGUA)
        agua = grid == AGUA
        region = np.zeros_like(solido)
        region[x0:x1, :, z0:z1] = True

        pad_s = np.pad(solido, 1, constant_values=False)
        pad_s[:, 0, :] = True
        ocupado = pad_s.copy()
        malla_solido = self._emitir_caras(solido & region, pad_s, ocupado)

        if not (agua & region).any():
            return malla_solido, _VACIO

        tapado_agua = np.pad(agua | solido, 1, constant_values=False)
        profundidades = np.zeros(self.tam, dtype=np.float32)
        for y in range(h):
            if y == 0:
                profundidades[:, 0, :] = agua[:, 0, :].astype(np.float32)
            else:
                profundidades[:, y, :] = (profundidades[:, y - 1, :] + 1.0) * agua[:, y, :]
        olas = agua.astype(np.float32)
        lados = self._emitir_caras(agua & region, tapado_agua, ocupado, olas, profundidades)
        superficie = self._superficie_agua(agua, profundidades, (x0, x1), (z0, z1))
        if len(lados[0]) and len(superficie[0]):
            agua_m = tuple(np.ascontiguousarray(np.concatenate([a, b])) for a, b in zip(lados, superficie))
        else:
            agua_m = lados if len(lados[0]) else superficie
        return malla_solido, agua_m

    def construir_mallas(self):
        w, _h, d = self.tam
        solido, agua = self._malla_region(0, w, 0, d)
        self.chunk_dirty[:] = False
        return solido, _VACIO, agua

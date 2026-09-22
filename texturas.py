"""Atlas procedural 4×4: cada bloque tiene tapa, lado y base distintas."""
import numpy as np

TILE = 32
COLS, FILAS = 4, 4
#  0 pasto tapa   1 pasto lado   2 tierra    3 piedra
#  4 arena        5 madera lado  6 madera tapa 7 hojas
#  8 ladrillo     9 nieve        10 gravilla  11 musgo
PASTO_TOP, PASTO_LADO, TIERRA_T, PIEDRA_T = 0, 1, 2, 3
ARENA_T, MADERA_LADO, MADERA_TOP, HOJAS_T = 4, 5, 6, 7
LADRILLO_T, NIEVE_T, GRAVA_T, MUSGO_T = 8, 9, 10, 11

# tipo de bloque -> (tapa, lado, base)
TILES_BLOQUE = {
    1: (PASTO_TOP, PASTO_LADO, TIERRA_T),
    2: (TIERRA_T, TIERRA_T, TIERRA_T),
    3: (PIEDRA_T, PIEDRA_T, PIEDRA_T),
    5: (ARENA_T, ARENA_T, ARENA_T),
    6: (MADERA_TOP, MADERA_LADO, MADERA_TOP),
    7: (HOJAS_T, HOJAS_T, HOJAS_T),
    8: (LADRILLO_T, LADRILLO_T, LADRILLO_T),
    9: (NIEVE_T, NIEVE_T, TIERRA_T),
}


def _n2(shape, rng, escala=8):
    gy, gx = max(shape[0] // escala, 2), max(shape[1] // escala, 2)
    base = rng.random((gy, gx)).astype(np.float32)
    y = np.linspace(0, gy - 1, shape[0])
    x = np.linspace(0, gx - 1, shape[1])
    yy, xx = np.meshgrid(y, x, indexing="ij")
    y0 = np.clip(yy.astype(int), 0, gy - 2)
    x0 = np.clip(xx.astype(int), 0, gx - 2)
    fy, fx = yy - y0, xx - x0
    fy = fy * fy * (3 - 2 * fy)
    fx = fx * fx * (3 - 2 * fx)
    v = (
        base[y0, x0] * (1 - fy) * (1 - fx)
        + base[y0, x0 + 1] * (1 - fy) * fx
        + base[y0 + 1, x0] * fy * (1 - fx)
        + base[y0 + 1, x0 + 1] * fy * fx
    )
    return v


def _tile(rng):
    return np.ones((TILE, TILE, 4), dtype=np.float32)


def _pasto_tapa(rng):
    t = _tile(rng)
    n = 0.55 * _n2((TILE, TILE), rng, 6) + 0.45 * _n2((TILE, TILE), rng, 3)
    t[..., 0] = 0.22 + 0.18 * n
    t[..., 1] = 0.48 + 0.38 * n
    t[..., 2] = 0.12 + 0.14 * n
    brizna = rng.random((TILE, TILE)) > 0.82
    t[brizna, 1] += 0.12
    t[..., 3] = 1.0
    return np.clip(t, 0, 1)


def _pasto_lado(rng):
    t = _tile(rng)
    n = _n2((TILE, TILE), rng, 5)
    yy = np.linspace(0, 1, TILE)[:, None]
    pasto = np.clip((0.28 - yy) / 0.28, 0, 1)
    t[..., 0] = 0.42 + 0.12 * n
    t[..., 1] = 0.30 + 0.10 * n
    t[..., 2] = 0.16 + 0.06 * n
    t[..., 0] = t[..., 0] * (1 - pasto) + (0.28 + 0.15 * n) * pasto
    t[..., 1] = t[..., 1] * (1 - pasto) + (0.55 + 0.22 * n) * pasto
    t[..., 2] = t[..., 2] * (1 - pasto) + (0.16 + 0.08 * n) * pasto
    t[..., 3] = 1.0
    return np.clip(t, 0, 1)


def _tierra(rng):
    t = _tile(rng)
    n = 0.6 * _n2((TILE, TILE), rng, 5) + 0.4 * rng.random((TILE, TILE)).astype(np.float32)
    t[..., 0] = 0.40 + 0.18 * n
    t[..., 1] = 0.26 + 0.12 * n
    t[..., 2] = 0.13 + 0.07 * n
    t[..., 3] = 1.0
    return np.clip(t, 0, 1)


def _piedra(rng):
    t = _tile(rng)
    n = 0.7 * _n2((TILE, TILE), rng, 6) + 0.3 * _n2((TILE, TILE), rng, 2)
    g = 0.42 + 0.28 * n
    t[..., :3] = g[..., None]
    grieta = (np.abs(_n2((TILE, TILE), rng, 4) - 0.5) < 0.03)
    t[grieta, :3] *= 0.55
    t[..., 3] = 1.0
    return np.clip(t, 0, 1)


def _arena(rng):
    t = _tile(rng)
    n = 0.5 * _n2((TILE, TILE), rng, 7) + 0.5 * rng.random((TILE, TILE)).astype(np.float32)
    t[..., 0] = 0.84 + 0.12 * n
    t[..., 1] = 0.74 + 0.12 * n
    t[..., 2] = 0.48 + 0.10 * n
    t[..., 3] = 1.0
    return np.clip(t, 0, 1)


def _madera_lado(rng):
    t = _tile(rng)
    xx = np.arange(TILE)[None, :]
    anillo = 0.5 + 0.5 * np.sin(xx * 0.9 + 0.4 * np.sin(np.arange(TILE)[:, None] * 0.35))
    n = _n2((TILE, TILE), rng, 8)
    t[..., 0] = 0.42 + 0.18 * anillo + 0.06 * n
    t[..., 1] = 0.26 + 0.10 * anillo
    t[..., 2] = 0.12 + 0.05 * anillo
    t[..., 3] = 1.0
    return np.clip(t, 0, 1)


def _madera_tapa(rng):
    t = _tile(rng)
    cy, cx = (np.arange(TILE)[:, None] - 15.5), (np.arange(TILE)[None, :] - 15.5)
    r = np.sqrt(cx * cx + cy * cy)
    anillo = 0.5 + 0.5 * np.sin(r * 1.3)
    t[..., 0] = 0.50 + 0.16 * anillo
    t[..., 1] = 0.32 + 0.10 * anillo
    t[..., 2] = 0.16 + 0.05 * anillo
    t[..., 3] = 1.0
    return np.clip(t, 0, 1)


def _hojas(rng):
    t = _tile(rng)
    n = _n2((TILE, TILE), rng, 4)
    t[..., 0] = 0.16 + 0.14 * n
    t[..., 1] = 0.42 + 0.32 * n
    t[..., 2] = 0.12 + 0.10 * n
    hueco = rng.random((TILE, TILE)) > 0.78
    t[hueco, 3] = 0.0
    t[~hueco, 3] = 1.0
    return np.clip(t, 0, 1)


def _ladrillo(rng):
    t = _tile(rng)
    y, x = np.indices((TILE, TILE))
    fila = y // 8
    ox = (fila % 2) * 8
    junta = ((x + ox) % 16 < 2) | (y % 8 < 2)
    n = rng.random((TILE, TILE)).astype(np.float32)
    t[..., 0] = 0.62 + 0.16 * n
    t[..., 1] = 0.18 + 0.08 * n
    t[..., 2] = 0.14 + 0.06 * n
    t[junta, :3] = (0.72, 0.68, 0.62)
    t[..., 3] = 1.0
    return np.clip(t, 0, 1)


def _nieve(rng):
    t = _tile(rng)
    n = _n2((TILE, TILE), rng, 6)
    t[..., 0] = 0.88 + 0.10 * n
    t[..., 1] = 0.91 + 0.08 * n
    t[..., 2] = 0.95 + 0.05 * n
    t[..., 3] = 1.0
    return np.clip(t, 0, 1)


def _grava(rng):
    t = _piedra(rng)
    t[..., :3] *= 0.85
    return t


def _musgo(rng):
    t = _tierra(rng)
    n = _n2((TILE, TILE), rng, 4)
    t[..., 1] = np.clip(t[..., 1] + 0.22 * n, 0, 1)
    return t


def atlas_rgba():
    rng = np.random.default_rng(17)
    makers = [
        _pasto_tapa, _pasto_lado, _tierra, _piedra,
        _arena, _madera_lado, _madera_tapa, _hojas,
        _ladrillo, _nieve, _grava, _musgo,
        _tierra, _tierra, _tierra, _tierra,
    ]
    img = np.zeros((FILAS * TILE, COLS * TILE, 4), dtype=np.uint8)
    for i, fn in enumerate(makers):
        ty, tx = divmod(i, COLS)
        tile = (np.clip(fn(rng), 0, 1) * 255).astype(np.uint8)
        img[ty * TILE:(ty + 1) * TILE, tx * TILE:(tx + 1) * TILE] = tile
    return np.ascontiguousarray(img)


def tile_cara(tipo, ny):
    top, side, bot = TILES_BLOQUE.get(int(tipo), (PIEDRA_T, PIEDRA_T, PIEDRA_T))
    if ny > 0:
        return top
    if ny < 0:
        return bot
    return side

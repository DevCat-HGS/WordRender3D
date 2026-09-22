# Mundo y render

El valle es un volumen de voxeles. La GPU no dibuja cubos sueltos: dibuja **mallas de triángulos** con caras tapadas eliminadas, un atlas de texturas y tres programas GLSL 1.20.

## Volumen

| Dato | Valor |
| --- | --- |
| Tamaño | 128 × 30 × 128 |
| Tipo | `uint8` por celda |
| 0 | Vacío |
| 1–9 | Pasto, tierra, piedra, agua, arena, madera, hojas, ladrillo, nieve |
| Chunk | 16×16 en XZ (el dirty-flag existe; el rebuild actual es de una pasada) |

`mundo.altura[x, z]` es la primera celda vacía sobre el sólido (sin contar agua). `mundo.agua_sup[x, z]` es la tapa del agua. La fauna pisa esas alturas.

API de `Mundo`:

| Método | Efecto |
| --- | --- |
| `poner` / `quitar` | Cambia una celda y guarda historial |
| `deshacer` | Hasta 24 copias de la cuadrícula |
| `limpiar` | Todo a cero |
| `guardar` / `cargar` | `numpy.save` / `load` del grid |
| `generar_terreno` | Procedural |
| `raycast` | DDA de Amanatides & Woo |
| `construir_mallas` | Sólidos y agua listos para VBO |

La UI ya no coloca bloques, pero `poner`, `quitar` y el raycast siguen en el código.

## Terreno procedural

`generar_terreno` mezcla cuatro octavas de ruido (celdas 3, 7, 14, 28) reescaladas con `cv2.resize` cúbico. Eso da colinas en ~30–40 ms, no en cientos.

Luego:

1. Rellena piedra y, arriba, tierra.
2. Nivel de agua = 6. Debajo hay arena y agua.
3. Tapa: arena en orilla, nieve si altura ≥ 15, pasto en el resto.
4. Árboles (~0.35 % de las columnas): tronco de madera y copa de hojas solo sobre pasto.

Cada **Nuevo terreno** tira otra semilla, otra fauna y otras frutas.

## Mallas

`construir_mallas` recorre caras +X −X +Y −Y +Z −Z. Si el vecino tapa la cara, no se emite. Cada cara son dos triángulos.

- Sólidos: posición, normal, color de paleta, AO (vecinos ocupados) y tile del atlas.
- Agua: laterales como sólido; la superficie se subdivide (`SUBDIV_AGUA = 2`) para que las olas Gerstner no se vean como un plano rígido.

El resultado sube a VBOs. Solo se vuelve a subir cuando `mundo.version` cambia. Día/noche y clima **no** reconstruyen el terreno: cambian uniforms.

## Atlas

`texturas.py` fabrica en CPU un atlas 4×4 de tiles 32×32 (pasto, tierra, piedra, arena, madera, hojas, ladrillo, nieve, gravilla, musgo). Cada tipo de bloque elige tapa / lado / base. El fragment shader hace triplanar simple: según la normal usa XZ, ZY o XY.

No hay archivos PNG de bloques. El aspecto sale del ruido procedural.

## Shaders (`shaders.py`)

GLSL 1.20 a propósito: abre en GPUs viejas y en el perfil de pygame+PyOpenGL.

| Programa | Uso |
| --- | --- |
| Sólido | Terreno texturizado, sol + luna + AO |
| Agua | Olas Gerstner, albedo más oscuro, especular corto |
| Animal | Color vértice, misma luz, sin atlas |

El sol no se apaga al tocar el horizonte: `sol_fuerza = max(0, elev + 0.18)^0.55`. Así el atardecer no se pone negro. Las estrellas de fondo son un campo 2D en la franja alta del cielo, no puntos 3D detrás de la cámara cuando miras hacia abajo.

## Agua

Las olas se desplazan en el vertex shader (Gerstner: varias sinusoides que mueven XZ y Y). El tiempo `u_time` lo incrementa el bucle. La CPU no anima vértices de agua.

El especular está apretado para que el mediodía no deje el lago blanco a lo lejos.

## Cámara

Órbita alrededor del centro del mapa:

- `yaw`, `pitch`, `dist` (distancia inicial 92)
- Objetivo ≈ `(64, 4, 64)`
- Proyección perspectiva, FOV 55

Manos o teclado/ratón escriben los mismos tres ángulos.

## Dibujo por frame

1. Color de clear = cielo teñido por el clima.
2. Estrellas si `estrellas > 0`.
3. Terreno sólido.
4. Agua con blending.
5. Fauna y frutas (VBO dinámico, solo lo cercano a la cámara).
6. Partículas de clima (cada dos frames).
7. HUD en 2D (pygame → texturas de texto).

Siguiente: [Clima y cielo](clima-y-cielo.md) y [Arquitectura](arquitectura.md).

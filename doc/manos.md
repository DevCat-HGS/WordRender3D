# Manos

El seguimiento vive en `hand_tracker.py` y corre en un **hilo daemon** para no congelar el render. `main.py` solo lee el último resultado y mueve cursor, cámara o climas.

## Modelo

MediaPipe Tasks, `HandLandmarker`, modo `VIDEO`. El archivo `modelos/hand_landmarker.task` se descarga en el primer arranque desde:

`https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task`

Si la descarga se corta, queda un `.part`. Bórralo y vuelve a abrir el programa.

Umbrales del landmarker:

- Manos máximas: 2
- Detección: 0.6
- Presencia: 0.5
- Tracking: 0.5

## Cámara

1. Intenta `cv2.VideoCapture(0, CAP_DSHOW)` en Windows.
2. Si falla, reintenta sin `CAP_DSHOW`.
3. Si no hay dispositivo, `HandTracker.error` explica el fallo y la app sigue sin manos.

El frame se **espeja** (`flip` horizontal) para que mover la mano a la derecha mueva el cursor a la derecha. La miniatura de la esquina es ese mismo preview a 320×240.

## Qué llega a la app

`HandTracker.manos()` devuelve una lista de `Mano` y un `frame_id`:

| Campo | Significado |
| --- | --- |
| `etiqueta` | `"Left"` o `"Right"` según MediaPipe |
| `confianza` | Score de la mano |
| `puntos` | 21 landmarks normalizados (0–1) sobre la imagen en espejo |

Índices de puntas (`PUNTAS`): pulgar 4, índice 8, medio 12, anular 16, meñique 20.

`main.py` asigna la mano con etiqueta `mano_puntero` al cursor y la otra a la órbita. Si hay dos manos de la misma etiqueta, gana la de más confianza.

## De la punta al cursor

1. Se toma el landmark 8 (índice).
2. Se aplica un margen (`MARGEN_MANO = 0.12`) para no exigir el borde de la foto.
3. Se mapea a la ventana 1280×720.
4. Pasa por el filtro **One Euro** (`min_cutoff=1.0`, `beta=0.006`).

One Euro suaviza cuando la mano tiembla y deja pasar cuando se mueve rápido. Cada mano (puntero y cámara) tiene su propio filtro.

## Pellizco

Distancia 3D entre pulgar e índice (o pulgar y medio), en el espacio normalizado de la imagen.

| Estado | Umbral |
| --- | --- |
| Empieza el pellizco | distancia &lt; 0.28 |
| Se suelta | distancia &gt; 0.40 |

Sin histéresis el gesto parpadearía. Con ella, un pellizco estable lanza **una** acción; `RETARDO_ACCION = 0.12` evita dobles clics.

- Pellizco índice sobre un botón → ejecuta el botón.
- Pellizco índice sobre el mundo → activa el clima seleccionado.
- Pellizco medio → brisa.

## Órbita y zoom

Mientras el pellizco de cámara está activo se guarda un ancla (yaw/pitch o distancia). El desplazamiento de la punta desde esa ancla gira o acerca. Al soltar, el ancla se borra.

## Código que ya no se usa

La carpeta `mundo3d/` (`gestos.py`, `manos.py`, `filtros.py`, `modelos.py`, `config.py`) es un resto de un prototipo anterior. **La app no la importa.** El camino real es `hand_tracker.py` + la lógica de `App` en `main.py`.

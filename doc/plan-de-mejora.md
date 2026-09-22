# Plan de mejora

Prioridades concretas sobre el código de hoy. No es una lista de deseos: cada ítem dice **por qué**, **qué tocar** y **cómo saber que está hecho**.

Las visiones a largo plazo viven en [visiones.md](visiones.md). Esto es el camino para no romper el valle mientras crece.

## Principios

1. El control con las manos no se sacrifica por features nuevas.
2. Un cambio de simulación no puede multiplicar los draw calls.
3. Documentar en `doc/` lo que se añada; el README raíz se queda corto.
4. No commitear `.venv`, modelos `.task` ni partidas `.npy`.

## Ahora — higiene y verdad del repo

Deuda que ya está en el árbol y confunde a quien clona.

| Ítem | Por qué | Dónde | Hecho cuando |
| --- | --- | --- | --- |
| Retirar o marcar `ciclo.py` | Duplica el cielo y nadie lo importa | `ciclo.py` | El archivo no existe o el docstring dice “obsoleto” y el README lo lista |
| Retirar o marcar `mundo3d/` | Prototipo de gestos; el camino real es `hand_tracker.py` | `mundo3d/` | Igual que arriba |
| Fijar versiones en `requirements.txt` | Un pip fresco puede romper MediaPipe + Python 3.13 | `requirements.txt` | Pins probados en Windows |
| Tests de humo sin GPU | Hoy solo se prueba a mano | `tests/` o un script | `python -c` / pytest genera mundo, fauna 40 frames y malla finita |
| Guardar más que bloques | Cargar inventa fauna nueva; se pierde el ecosistema | `mundo.py`, `main.py` | Un `.npz` con grid + hora + clima, o documentar el límite en la UI |
| Capturas en el README | `captura.png` está en `.gitignore` | README, `.gitignore` | Una imagen de día y una de noche versionadas, o un enlace estable |

## Luego — simulación que se sienta viva

El movimiento ya tiene inercia, wander y saltos. Sigue viéndose de cajas.

| Ítem | Por qué | Dónde | Hecho cuando |
| --- | --- | --- | --- |
| Esqueletos mínimos (4–6 huesos) | Orejas, alas y patas fijas | `fauna.py` modelos + `malla_visible` | Alas que baten de verdad; patas en fase opuesta |
| Grupos (ciervos, lobos) | Hoy cada uno ignora a su especie | `fauna.actualizar` | 2–3 ciervos caminan juntos; los lobos flanquean |
| Territorio y bebedero | El mapa es homogéneo | `fauna` + `mundo.agua_sup` | Herbívoros bajan al agua; predadores patrullan |
| Transición de climas | El cielo salta de sequía a nieve | `tiempo.py` | 2–4 s de lerp entre estados |
| Estaciones lentas | El clima solo lo lanza el jugador | `clima.py`, `tiempo.py` | Un ciclo opcional de días que cambia el clima base |
| Audio | El valle es mudo | nuevo `audio.py` | Viento, lluvia, un relámpago; mute con tecla |
| Guardar fauna y frutas | La partida es solo geología | serializar SoA | Cargar restaura conteos y posiciones |

## Después — render y escala

| Ítem | Por qué | Dónde | Hecho cuando |
| --- | --- | --- | --- |
| Instancias de GPU | 50k vértices de fauna se suben cada frame | shaders + `glDrawArraysInstanced` | CPU manda solo pos/yaw/fase |
| LOD de terreno | 128³ entero siempre | `construir_mallas` | Chunks lejanos sin AO fino |
| Sombras baratas | La luz es plana | shader sólido | Un shadow map o AO direccional |
| Mundo más grande | 128 se acaba al orbitar | `mundo.py` | 256 con el mismo presupuesto de frame, o streaming |
| Biomas | Pasto / nieve / arena ya existen como tapa | `generar_terreno` | Tres recetas (bosque, costa, cima) con fauna distinta |
| Partículas en GPU | 1400 puntos en CPU + draw intercalado | `tiempo.py` | Transform feedback o un shader de puntos |

## Producto

| Ítem | Por qué | Hecho cuando |
| --- | --- | --- |
| Tutorial de 30 s en el HUD | La ayuda es un muro de texto | Primera sesión: 4 frases, una por gesto |
| Calibración de manos | El margen 0.12 no sirve en todas las webcams | Un botón “calibrar” mide el alcance |
| Idioma | Toda la UI está en español | `es` por defecto; `en` opcional |
| Empaquetado | Pedir Python + venv echa para atrás | Un `.zip` con runtime o un instalador |
| CI en GitHub Actions | Nadie ve si `fauna.py` se rompe | Lint + test de humo en cada push |
| Licencia explícita | El README dice “uso personal” | Un `LICENSE` (MIT o similar) y créditos MediaPipe |

## Orden sugerido (tres pases)

### Pase A — una semana

1. Marcar o borrar `ciclo.py` y `mundo3d/`.
2. Pins en `requirements.txt`.
3. Test de humo de mundo + fauna + frutas.
4. Una captura de día y una de noche en el README.

### Pase B — un mes

1. Guardado `.npz` (grid, hora, clima).
2. Transición de climas.
3. Manada de ciervos y pareja de lobos.
4. Tutorial corto y calibración de manos.

### Pase C — un trimestre

1. Instancing de fauna.
2. Un bioma extra (costa o cima).
3. Audio de clima.
4. CI + licencia.

## Fuera de alcance (por ahora)

No se meten en el plan hasta que A y B existan:

- Multijugador.
- VR / manos con depth camera.
- Editor de bloques otra vez como modo principal (el diseño actual es clima, no construcción).
- IA de animales con redes neuronales.
- Motor (Ursina, Godot, Unity). El venv puede tener Ursina instalado; **la app no lo usa**.

## Cómo proponer un cambio

1. ¿Rompe el hilo de las manos o el presupuesto de un VBO? Si sí, rediseñar.
2. Añadir o actualizar la página de `doc/` que corresponda.
3. Si el cambio es de UX, verificar en ventana real (cámara o ratón), no solo con un print.

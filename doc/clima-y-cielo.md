# Clima y cielo

Hay dos relojes distintos:

- **Cielo** (`clima.py`): hora del día, sol, luna, estrellas, luz ambiental.
- **Tiempo** (`tiempo.py`): el clima que tú eliges (lluvia, tornado…).

El cielo corre solo. El clima lo lanzas tú. Los dos se mezclan: una tormenta oscurece un mediodía; una sequía tiñe de ocre un atardecer.

## Ciclo de día y noche

Un día a velocidad ×1 dura **90 segundos** reales (`SEGUNDOS_DIA`). `,` y `.` lo parten o lo multiplican por dos (entre ×0.25 y ×16). `N` lo pausa. `V` salta a hora 0.50 (mediodía). `B` salta a 0.02 (noche). El botón **Avanzar hora** suma 0.25.

La hora es un float en `[0, 1)`. Se interpola una tabla de claves (noche, alba, día, ocaso) con un smoothstep. De ahí salen:

| Campo | Para qué sirve |
| --- | --- |
| `cielo_arriba` / `cielo_abajo` | Degradado de fondo |
| `ambiente` | Luz de relleno de los shaders |
| `sol_dir` / `sol_color` / `sol_fuerza` | Luz principal |
| `luna_dir` / `luna_fuerza` | Luz nocturna azulada |
| `estrellas` | Opacidad del campo de estrellas |
| `niebla` / `suelo` | Tintes de horizonte y piso |

Fases: Amanecer (0.22–0.32), Día (0.32–0.70), Atardecer (0.70–0.82), Noche (el resto). El HUD muestra también un reloj `HH:MM` de 24 horas ficticias.

`ciclo.py` es un prototipo anterior del mismo tema. **No se importa.** El camino real es `clima.estado_cielo`.

## Los seis climas

`Tiempo.activar(id)` cambia el clima. `Tiempo.estado()` publica un `EstadoTiempo` que leen fauna, frutas y el teñido del cielo.

| Id | Nombre | Viento | Señales | Partículas |
| --- | --- | --- | --- | --- |
| 0 | Brisa | (1.6, 0, 0.4) | — | Hojas verdes que flotan |
| 1 | Lluvia | (0.8, 0, 0.2) | `lluvia` | Gotas rápidas (14 u/s) |
| 2 | Tormenta | (5.5, 0, 2.2) | `lluvia`, `peligro` | Gotas más rápidas (22 u/s), destellos |
| 3 | Sequía | (2.4, 0, 0.3) | `sequia` | Polvo ocre |
| 4 | Nevado | (1.2, 0, 0.8) | `frio` | Copos lentos que derivan |
| 5 | Tornado | (3.0, 0, 1.2) | `peligro`, `tornado` | Polvo en espiral |

Hay ~1400 partículas. Se dibujan cada dos frames. Al salir del mapa o caer al piso se reciclan arriba.

### Efectos sobre el cielo (`teñir`)

- Lluvia: gris, sol al 55 %.
- Tormenta: casi de noche; un relámpago pinta el cielo de blanco un instante (`flash`, ~1.2 % por frame de chance).
- Sequía: ocre, sol más cálido, suelo seco.
- Nevado: blanco-azul, niebla clara.
- Tornado: marrón, sol al 40 %.

### Efectos sobre la vida

Leídos en `fauna.actualizar` y `frutas.actualizar`:

| Señal | Fauna | Frutas |
| --- | --- | --- |
| `viento` | Empuja un poco en XZ | — |
| `frio` | Velocidad ×0.62 | — |
| `sequia` | Más hambre | Algunas se pudren |
| `lluvia` | — | Brotes nuevos en hojas |
| `peligro` | A veces entran en HUIR | — |
| `tornado` | Atrae, levanta y resta vida si están a menos de 8 u | Las tira al suelo y las apaga |

El remolino del tornado recorre una elipse alrededor del centro del mapa.

## Cómo se lanza

1. Tecla `1`–`6`, clic en la barra, o pellizco sobre un recuadro → `elegir_clima`.
2. Pellizco o clic en el mundo → vuelve a activar el seleccionado (feedback en el aviso).
3. Pellizco del medio o clic derecho → brisa.

No hay clima “automático” todavía. El plan de mejora propone estaciones y transiciones. Ver [Plan de mejora](plan-de-mejora.md).

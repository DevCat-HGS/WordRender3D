# Guía de usuario

Esta página describe lo que ves en pantalla y cómo controlarlo. No hace falta leer código.

## Ventana

Resolución fija 1280×720, título **Mundo 3D con las manos**.

| Zona | Qué hay |
| --- | --- |
| Centro | El valle, el agua, los animales y las frutas |
| Arriba a la izquierda | Reloj, fase del día, clima, FPS y recuento de fauna si la ayuda está abierta |
| Arriba a la derecha | Botones: terreno, deshacer, limpiar, guardar, cargar, manos, cielo |
| Abajo al centro | Seis climas |
| Esquina | Miniatura de la cámara (se oculta con `P`) |

El cursor 3D sigue la punta del índice de la mano puntero, o el ratón si no hay manos.

## Manos

Por defecto la **derecha** es el puntero y la **izquierda** es la cámara. MediaPipe nombra las manos según el cuerpo, no según el espejo: si te las cruza, pulsa `M`.

| Mano | Gesto | Acción |
| --- | --- | --- |
| Puntero | Punta del índice | Mueve el cursor |
| Puntero | Pellizco pulgar + índice | Lanza el clima elegido o pulsa un botón |
| Puntero | Pellizco pulgar + medio | Vuelve a la brisa |
| Cámara | Pellizco pulgar + índice y mover | Gira el mundo (órbita) |
| Cámara | Pellizco pulgar + medio y subir o bajar | Zoom |

El pellizco tiene histéresis: se activa cerca (umbral 0.28) y se suelta más lejos (0.40) para que no tiemble. El movimiento de las puntas pasa por un filtro One Euro, que suaviza el temblor sin retrasar un gesto rápido. Hay un retardo corto (0.12 s) antes de repetir una acción.

Detalle técnico: [Manos](manos.md).

## Teclado y ratón

| Entrada | Acción |
| --- | --- |
| `1`–`6` | Elige un clima |
| Clic izquierdo | Igual que el pellizco del índice: clima o botón |
| Clic derecho | Vuelve a la brisa |
| Rueda / `RePág` `AvPág` | Zoom |
| Flechas | Órbita |
| Arrastrar con el ratón | Órbita (si no hay gesto de cámara) |
| `N` | Pausa o reanuda el ciclo día/noche |
| `V` / `B` | Mediodía / noche |
| `,` o `-` | Cielo más lento |
| `.` `+` `=` | Cielo más rápido |
| `T` | Nuevo terreno, fauna y frutas |
| `Z` | Deshacer el último cambio de bloques |
| `C` | Vaciar el mundo (también apaga fauna y frutas) |
| `G` / `L` | Guardar / cargar `mundo_guardado.npy` |
| `M` | Intercambia las manos |
| `P` | Muestra u oculta la vista de la cámara |
| `H` / `F1` | Ayuda y recuento de especies |
| `Esc` | Salir |

## Botones de la derecha

| Botón | Qué hace |
| --- | --- |
| Nuevo terreno | Regenera altura, agua, árboles, fauna y frutas |
| Deshacer | Restaura la cuadrícula anterior (hasta 24 pasos) |
| Limpiar | Deja el volumen vacío y oculta la vida |
| Guardar | Escribe solo los bloques, no los animales |
| Cargar | Lee el `.npy` y vuelve a poblar fauna y frutas |
| Cambiar manos | Invierte puntero y cámara |
| Pausar cielo | Congela la hora; el botón pasa a **Reanudar cielo** |
| Avanzar hora | Salta un cuarto de día |

## Climas

La barra inferior no coloca bloques. Elige el tiempo y, si pellizcas o haces clic fuera de un botón, **lanza** ese clima.

| Tecla | Clima | Lo que notas |
| --- | --- | --- |
| `1` | Brisa | Hojas en el aire, viento suave |
| `2` | Lluvia | Cielo gris, gotas, más frutas en las copas |
| `3` | Tormenta | Oscuro, viento fuerte, rayos, animales que huyen |
| `4` | Sequía | Polvo, más hambre, frutas que se secan |
| `5` | Nevado | Nieve, paso más lento, cielo pálido |
| `6` | Tornado | Remolino que empuja, levanta y hace daño |

Clic derecho o pellizco del dedo medio = brisa.

Explicación de física y cielo: [Clima y cielo](clima-y-cielo.md).

## Vida en el valle

Verás mariposas, ranas, ratones, conejos, peces, patos, ciervos, jabalíes, zorros, lobos, águilas y osos. No los controlas. Pastan, comen frutas, cazan, huyen, se reproducen con tope y mueren de hambre o de heridas.

- Conejo, rana y ratón **saltan**.
- Mariposa y águila **alean** y cambian de altura.
- El pez **ondea** bajo el agua.
- El resto **trotea** con inercia y giro suave.

Cadena, dietas y números: [Ecosistema](ecosistema.md).

## Guardar

**Guardar** escribe `mundo_guardado.npy` junto a `main.py`. Solo guarda bloques. Al **cargar**, el terreno vuelve y se crea fauna y frutas nuevas sobre él. Un archivo de otro tamaño no carga.

Ese `.npy` no se versiona. Es tu partida local.

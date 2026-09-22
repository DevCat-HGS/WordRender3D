# Visiones

Cuatro futuros distintos para el mismo valle. No son un roadmap: son **hacia dónde podría mirar** el proyecto si elige un público. El trabajo concreto está en el [plan de mejora](plan-de-mejora.md).

Cualquier visión conserva tres cosas:

1. Las manos como forma principal de estar en el mundo.
2. Un ecosistema que se entiende de un vistazo.
3. Un render que quepa en un portátil.

---

## Visión 1 — Laboratorio vivo

**Para quién:** quien quiere *ver* una cadena alimenticia, no leerla.

El valle se vuelve un instrumento. El clima ya es un dial; faltarían diales de población, de hambre y de estaciones. Un panel (también manejable con pellizco) mostraría: cuántos conejos quedan, cuánto tarda un lobo en cazar, qué hace la sequía a las frutas en diez días de simulación.

No es un simulador científico. Es un laboratorio de juguete honesto: las reglas caben en [ecosistema.md](ecosistema.md) y se pueden contradecir con un experimento (“quito la lluvia, ¿se acaba el ciervo?”).

**Se reconoce esta visión cuando:**

- Hay gráficas o un recuento que se puede seguir sin pulsar `H`.
- Se puede congelar el cielo y acelerar solo la fauna.
- Un docente puede plantear una pregunta y obtener una respuesta visible en menos de un minuto.

**Tensión:** más UI no puede tapar el valle. El laboratorio se mira, no se administra.

---

## Visión 2 — Patio de las manos

**Para quién:** ferias, aulas, alguien que no quiere un teclado.

Hoy las manos ya orbitan y lanzan clima, pero el primer minuto sigue pidiendo leer. Esta visión convierte el gesto en el tutorial: una mariposa sigue el índice; un pellizco “coge” una nube y la suelta sobre el bosque; separar las palmas hace zoom.

El teclado queda como accesibilidad, no como camino principal. La calibración se hace una vez, en silencio, con las dos manos abiertas.

**Se reconoce esta visión cuando:**

- Un extraño entiende lluvia y órbita sin que le expliquen teclas.
- El preview de la cámara es un espejo útil, no un debug.
- Fallar un pellizco no lanza un tornado a medias.

**Tensión:** MediaPipe se equivoca. La visión vive o muere en la histéresis, el One Euro y un modo “solo ratón” que no humille.

---

## Visión 3 — Mundo que crece solo

**Para quién:** quien deja la ventana abierta como un acuario.

El mapa deja de ser un stamp de 128 bloques. Aparecen orillas, un bosque denso, una cima nevada con otra fauna. Las estaciones cambian el clima base; tú solo *intervienes*. Los árboles tiran semilla; un incendio de sequía abre un claro; los peces suben río cuando llueve.

El guardado deja de ser un grid: es una semilla + un diario (hora, poblaciones, árboles caídos).

**Se reconoce esta visión cuando:**

- Volver al cabo de un rato no es ver el mismo frame con otro yaw.
- Hay al menos tres paisajes legibles desde la órbita.
- La población oscila y no se extingue en dos minutos ni explota a 340.

**Tensión:** escala vs. un solo VBO. Sin instancing y sin LOD esta visión se come el FPS.

---

## Visión 4 — Pieza para mostrar

**Para quién:** portfolio, charla, README que se entiende en diez segundos.

El valle ya es photogénico (día, agua, ocaso). Esta visión lo trata como una pieza: dos capturas oficiales, un vídeo de 20 s con manos en cuadro, una licencia clara, un instalador que no pide saber qué es un venv.

El código se queda legible —eso *es* parte de la pieza— pero el visitante de GitHub no tiene que abrir `fauna.py` para creerse el proyecto.

**Se reconoce esta visión cuando:**

- El README tiene prueba visual y un “clone and run” que funciona en una máquina limpia.
- Hay `LICENSE` y créditos de MediaPipe.
- Alguien puede citar WordRender3D en una charla sin disculparse por la instalación.

**Tensión:** empaquetar Python+OpenGL+cámara en Windows es sucio. Más vale un script `run.ps1` excelente que un instalador a medias.

---

## Qué visión no es

- Un Minecraft para construir con las manos. Esa etapa ya se cerró: las opciones son climas.
- Un motor generacional. Ursina u otro framework en el venv no son el destino.
- Un MMO. Doce especies en un portátil ya piden culling.

## Cómo elegir

Si el próximo mes solo hay tiempo para una apuesta:

| Si te importa… | Empuja la visión | Empieza por el plan |
| --- | --- | --- |
| Explicar el ecosistema | 1 Laboratorio | Recuentos, freeze de cielo, guardado de poblaciones |
| Que lo use tu familia | 2 Patio | Tutorial, calibrar, pellizco fiable |
| Que el mundo sorprenda | 3 Acuario | Transición de climas, bioma, instancing |
| Que GitHub se vea serio | 4 Pieza | Capturas, pins, CI, licencia |

Se pueden mezclar. Lo que no se puede es perseguir, las cuatro a la vez, sin el [pase A](plan-de-mejora.md#pase-a--una-semana).

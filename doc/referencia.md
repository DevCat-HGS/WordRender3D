# Referencia

Tablas para consultar sin recorrer el código. Si un número y el fuente discrepan, gana el fuente.

## Teclas

| Tecla | Acción |
| --- | --- |
| `1`–`6` | Brisa, lluvia, tormenta, sequía, nevado, tornado |
| `T` | Nuevo terreno |
| `Z` | Deshacer |
| `C` | Limpiar |
| `G` / `L` | Guardar / cargar |
| `M` | Cambiar manos |
| `P` | Preview de cámara |
| `N` | Pausar cielo |
| `V` / `B` | Mediodía / noche |
| `,` `-` | Cielo más lento |
| `.` `+` `=` | Cielo más rápido |
| `H` `F1` | Ayuda |
| Flechas | Órbita |
| `RePág` `AvPág` | Zoom |
| `Esc` | Salir |

## Bloques

| Id | Nombre | Notas |
| --- | --- | --- |
| 0 | Vacío | Aire |
| 1 | Pasto | Tapa verde, lado con tierra |
| 2 | Tierra | |
| 3 | Piedra | Núcleo de las colinas |
| 4 | Agua | Malla aparte, olas |
| 5 | Arena | Orillas |
| 6 | Madera | Troncos |
| 7 | Hojas | Copas; de aquí cuelgan frutas |
| 8 | Ladrillo | En paleta; el generador no lo usa |
| 9 | Nieve | Cimas ≥ 15 |

## Especies

Población = conteo al nacer. Velocidad en unidades mundo / s. Visión = radio de hash.

| Especie | Dieta | Presas | Vel | Visión | Hambre máx. | Vida | Daño | Vuela | Nada | Pob. |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Mariposa | néctar | — | 2.4 | 6 | 40 | 4 | 0 | sí | no | 26 |
| Rana | carne | Mariposa | 1.6 | 7 | 28 | 8 | 1.2 | no | sí | 14 |
| Ratón | hierba | — | 2.2 | 8 | 26 | 7 | 0.8 | no | no | 22 |
| Conejo | hierba | — | 2.6 | 9 | 30 | 10 | 0.5 | no | no | 20 |
| Pez | néctar | — | 2.0 | 6 | 32 | 6 | 0 | no | sí | 18 |
| Pato | omni | Pez | 1.8 | 8 | 28 | 12 | 1.4 | no | sí | 10 |
| Ciervo | hierba | — | 2.8 | 12 | 34 | 22 | 1.0 | no | no | 12 |
| Jabalí | omni | Ratón | 2.0 | 9 | 30 | 20 | 2.2 | no | no | 8 |
| Zorro | carne | Conejo, ratón, rana, pato | 3.2 | 11 | 24 | 16 | 3.0 | no | no | 7 |
| Lobo | carne | Ciervo, conejo, jabalí | 3.4 | 14 | 26 | 24 | 4.2 | no | no | 5 |
| Águila | carne | Conejo, ratón, pez, pato | 3.6 | 16 | 28 | 14 | 3.4 | sí | no | 5 |
| Oso | omni | Pez, ciervo, jabalí | 2.2 | 12 | 32 | 36 | 5.0 | no | sí | 3 |

Estados de IA: 0 wander, 1 comer, 2 huir, 3 cazar, 4 atacar, 5 muerto.

Andares especiales: rana / conejo / ratón saltan; mariposa y águila aletean; pez ondea.

## Frutas

| Id | Nombre | Color aproximado |
| --- | --- | --- |
| 0 | Manzana | rojo |
| 1 | Naranja | naranja |
| 2 | Baya | púrpura |

## Constantes útiles

| Símbolo | Valor | Dónde |
| --- | --- | --- |
| Ventana | 1280×720 | `main.py` |
| FOV | 55 | `main.py` |
| Día | 90 s | `clima.py` |
| Mundo | 128×30×128 | `mundo.py` |
| Chunk | 16 | `mundo.py` |
| Historial | 24 | `mundo.py` |
| Agua subdiv | 2 | `mundo.py` |
| Nivel agua | 6 | `generar_terreno` |
| Partículas | 1400 | `tiempo.py` |
| Celda fauna | 8 | `fauna.py` |
| Tope fauna | 340 | `fauna.py` |
| Radio mesh fauna | 90 | `fauna.py` |
| Radio IA barata | 95 | `fauna.py` |
| Frutas iniciales | ≤ 70 | `frutas.py` |
| Tope frutas | 160 | `frutas.py` |
| Pellizco on/off | 0.28 / 0.40 | `main.py` |
| Archivo guardado | `mundo_guardado.npy` | junto a `main.py` |

## Archivos del repo

```
WordRender3D/
├── main.py
├── hand_tracker.py
├── mundo.py
├── texturas.py
├── shaders.py
├── clima.py
├── tiempo.py
├── fauna.py
├── frutas.py
├── ciclo.py              # no usado
├── mundo3d/              # no usado
├── requirements.txt
├── README.md
├── .gitignore
├── doc/                  # esta documentación
└── modelos/              # se crea al arrancar
```

## Dependencias

```
mediapipe
opencv-python
numpy
pygame
PyOpenGL
```

Sin pins de versión en `requirements.txt`. El plan de mejora propone fijarlas.

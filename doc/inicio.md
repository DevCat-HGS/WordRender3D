# Inicio

WordRender3D es un simulador 3D de un ecosistema voxel que se controla con las manos. La cámara web lee las puntas de los dedos; el cielo recorre un ciclo de día y noche; el agua se anima en la GPU; y doce especies viven, comen, cazan y huyen. Tú eliges el clima.

El repositorio público es [DevCat-HGS/WordRender3D](https://github.com/DevCat-HGS/WordRender3D).

## Qué puedes hacer hoy

- Mirar un valle de 128×30×128 bloques con pasto, nieve, lagos y árboles.
- Girar y acercar la cámara con la mano izquierda o con el ratón.
- Lanzar brisa, lluvia, tormenta, sequía, nieve o tornado.
- Ver cómo llueve y brotan frutas, o cómo un tornado empuja a los animales.
- Pausar el cielo, saltar al mediodía o a la noche, guardar y cargar el terreno.

No construyes bloques con las manos. Las opciones de la barra inferior son **climas**, no materiales.

## Para quién es

| Perfil | Qué le aporta |
| --- | --- |
| Curioso o estudiante | Un mundo vivo que se toca con las manos |
| Desarrollador | Un ejemplo compacto de OpenGL, MediaPipe y simulación en NumPy |
| Docente | Una demo de cadena alimenticia, clima y ciclo día/noche |

## Requisitos

| Componente | Detalle |
| --- | --- |
| Sistema | Windows 10/11; también Linux y macOS |
| Runtime | Python 3.11 o superior (probado con 3.13) |
| Entrada | Cámara web. Si no hay, ratón y teclado cubren el mismo flujo |
| Gráficos | GPU con OpenGL 2.1 o superior |
| Disco | Unos 200 MB para el entorno virtual más ~8 MB del modelo de manos |

## Instalación

```powershell
git clone https://github.com/DevCat-HGS/WordRender3D.git
cd WordRender3D
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

En Linux o macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Dependencias: `mediapipe`, `opencv-python`, `numpy`, `pygame`, `PyOpenGL`.

La primera vez que arranca descarga sola `modelos/hand_landmarker.task` desde los servidores de MediaPipe. Ese archivo no se sube a Git.

## Arrancar

```powershell
.\.venv\Scripts\python.exe main.py
```

Se abre una ventana 1280×720. Si hay cámara, un hilo aparte empieza a leer las manos. Si no, el puntero del ratón y el teclado bastan: no se cierra la aplicación.

## Primeros cinco minutos

1. Deja que el terreno termine de generar (unos segundos).
2. Mueve la mano derecha: el cursor sigue la punta del índice.
3. Pellizca pulgar + índice sobre un clima de la barra inferior.
4. Con la mano izquierda, pellizca y arrastra para orbitar.
5. Pulsa `H` si quieres ocultar o volver a ver la ayuda.

Siguiente lectura: [Guía de usuario](guia-de-usuario.md).

## Si algo falla

| Síntoma | Qué probar |
| --- | --- |
| No hay cámara | El juego sigue; usa ratón. El aviso aparece en consola |
| MediaPipe no carga | Revisa la red en el primer arranque; borra `modelos/*.part` y reintenta |
| Ventana negra o crash de GL | La app baja el antialiasing si falla el MSAA; actualiza el driver |
| Manos cruzadas | Pulsa `M` o el botón **Cambiar manos** |
| El mundo no carga | El `.npy` tiene que ser 128×30×128; un tamaño distinto se rechaza |

## Qué no está en Git

El `.gitignore` deja fuera el entorno virtual, `__pycache__`, el modelo `.task`, `mundo_guardado.npy`, capturas `captura*.png` y carpetas de editores. Eso es deliberado: cada máquina genera esos archivos.

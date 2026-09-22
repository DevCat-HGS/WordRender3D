"""Parámetros ajustables del creador de mundos."""
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ARCHIVO_MUNDO = RAIZ / "mundos" / "mi_mundo.json"

MODELO_MANOS = RAIZ / "modelos" / "hand_landmarker.task"
URL_MODELO_MANOS = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/latest/hand_landmarker.task"
)

# Cámara
INDICE_CAMARA = 0
RESOLUCION_CAMARA = (640, 480)

# Manos
MANO_PRINCIPAL = "Derecha"   # con esta mano construyes; la otra gira el mundo y elige herramienta
INVERTIR_LADOS = False       # ponlo en True si el programa confunde tu mano derecha con la izquierda
# Parte de la imagen de la cámara (x0, y0, x1, y1) que se estira a toda la ventana,
# así no tienes que llevar la mano hasta el borde de lo que ve la cámara.
ZONA_ACTIVA = (0.12, 0.08, 0.88, 0.80)
PELLIZCO_CERRAR = 0.30       # distancia pulgar-índice / tamaño de la palma para detectar el pellizco
PELLIZCO_ABRIR = 0.45        # hay que separarlos más que esto para soltar (evita parpadeos)
SEGUNDOS_CONTAR_DEDOS = 1.0  # tiempo mostrando 1, 2 o 3 dedos para cambiar de herramienta
SENSIBILIDAD_GIRO = 220      # grados que gira el mundo al cruzar toda la ventana con la mano

# Mundo
TAMANO_MUNDO = 24            # bloques por lado
ALTURA_MAXIMA = 24
NIVEL_AGUA = 3

"""Descarga, solo la primera vez, el modelo de MediaPipe que detecta las manos."""
import urllib.request
from pathlib import Path

from . import config


def asegurar_modelo_manos() -> Path:
    ruta = config.MODELO_MANOS
    if ruta.exists() and ruta.stat().st_size > 1_000_000:
        return ruta
    ruta.parent.mkdir(parents=True, exist_ok=True)
    parcial = ruta.with_suffix(".part")
    print("Descargando el modelo de manos de MediaPipe (unos 8 MB)...")
    with urllib.request.urlopen(config.URL_MODELO_MANOS, timeout=60) as respuesta, open(parcial, "wb") as archivo:
        total = int(respuesta.headers.get("Content-Length") or 0)
        descargado = 0
        while bloque := respuesta.read(1 << 16):
            archivo.write(bloque)
            descargado += len(bloque)
            if total:
                print(f"\r  {descargado * 100 // total}%", end="", flush=True)
    print()
    parcial.replace(ruta)
    return ruta

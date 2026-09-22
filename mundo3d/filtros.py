"""Filtro One Euro (Casiez et al., 2012) para quitar el temblor de los puntos de la mano."""
import math

import numpy as np


class FiltroEuro:
    """Suaviza mucho cuando la mano está quieta y casi nada cuando se mueve rápido, así no se siente retraso."""

    def __init__(self, corte_minimo=1.2, beta=4.0, corte_derivada=1.0, reinicio=0.4):
        self.corte_minimo = corte_minimo
        self.beta = beta
        self.corte_derivada = corte_derivada
        self.reinicio = reinicio      # segundos sin datos tras los que se empieza de cero
        self._valor = None
        self._derivada = None
        self._tiempo = None

    @staticmethod
    def _alfa(corte, dt):
        tau = 1.0 / (2 * math.pi * corte)
        return 1.0 / (1.0 + tau / dt)

    def __call__(self, valor: np.ndarray, tiempo: float) -> np.ndarray:
        if self._tiempo is None or tiempo - self._tiempo > self.reinicio:
            self._valor, self._derivada, self._tiempo = valor.copy(), np.zeros_like(valor), tiempo
            return valor.copy()
        dt = max(tiempo - self._tiempo, 1e-3)
        a_d = self._alfa(self.corte_derivada, dt)
        self._derivada = a_d * (valor - self._valor) / dt + (1 - a_d) * self._derivada
        a = self._alfa(self.corte_minimo + self.beta * np.abs(self._derivada), dt)
        self._valor = a * valor + (1 - a) * self._valor
        self._tiempo = tiempo
        return self._valor.copy()

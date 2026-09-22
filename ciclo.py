"""Ciclo de día y noche: posición del sol y la luna, colores del cielo y de la luz."""
import math

SEGUNDOS_POR_HORA = 15.0    # a velocidad x1 un día completo dura 6 minutos
VELOCIDADES = [(1.0, "x1"), (15.0, "x15"), (0.0, "pausa")]
HORAS_POR_SEGUNDO_SALTO = 5.0

DIA_ARRIBA, DIA_HORIZONTE = (0.22, 0.48, 0.92), (0.70, 0.84, 1.0)
NOCHE_ARRIBA, NOCHE_HORIZONTE = (0.01, 0.02, 0.06), (0.05, 0.07, 0.15)
OCASO = (1.0, 0.52, 0.28)


def suave(a, b, x):
    t = min(max((x - a) / (b - a), 0.0), 1.0)
    return t * t * (3 - 2 * t)


def mezcla(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def escalar(c, k):
    return tuple(v * k for v in c)


class CicloDia:
    def __init__(self, hora=9.5):
        self.hora = hora
        self.i_velocidad = 0
        self.objetivo = None

    @property
    def velocidad(self):
        return VELOCIDADES[self.i_velocidad]

    def cambiar_velocidad(self):
        self.i_velocidad = (self.i_velocidad + 1) % len(VELOCIDADES)
        return self.velocidad[1]

    def es_de_dia(self):
        return 6.0 <= self.hora < 18.0

    def alternar(self):
        """Avanza el reloj rápidamente hasta la noche o hasta la mañana siguiente."""
        self.objetivo = 21.5 if self.es_de_dia() else 7.5

    def avanzar(self, dt):
        if self.objetivo is not None:
            falta = (self.objetivo - self.hora) % 24.0
            paso = min(falta, HORAS_POR_SEGUNDO_SALTO * dt)
            self.hora = (self.hora + paso) % 24.0
            if falta - paso <= 1e-6:
                self.objetivo = None
        else:
            self.hora = (self.hora + dt * self.velocidad[0] / SEGUNDOS_POR_HORA) % 24.0

    def texto_hora(self):
        h = int(self.hora)
        m = int((self.hora - h) * 60)
        return f"{'Día' if self.es_de_dia() else 'Noche'}  {h:02d}:{m:02d}"

    def estado(self):
        a = (self.hora - 6.0) / 24.0 * 2 * math.pi
        sx, sy, sz = math.cos(a) * 0.9, math.sin(a), 0.4
        n = math.sqrt(sx * sx + sy * sy + sz * sz)
        sol = (sx / n, sy / n, sz / n)
        luna = (-sol[0], -sol[1], -sol[2])
        y = sol[1]

        dia = suave(-0.12, 0.25, y)
        ocaso = math.exp(-(y / 0.22) ** 2)

        arriba = mezcla(mezcla(NOCHE_ARRIBA, DIA_ARRIBA, dia), (0.30, 0.30, 0.55), ocaso * 0.35)
        horizonte = mezcla(mezcla(NOCHE_HORIZONTE, DIA_HORIZONTE, dia), OCASO, ocaso * 0.7)
        color_sol = mezcla((1.0, 0.42, 0.18), (1.0, 0.96, 0.88), suave(0.0, 0.35, y))

        if y >= 0:
            k = suave(0.0, 0.15, y)
            luz_dir = sol
            luz_color = escalar(mezcla((1.0, 0.55, 0.30), (1.0, 0.96, 0.88), suave(0.0, 0.4, y)), 1.05 * k)
            fuerza_sombra = 0.85 * k
        else:
            k = suave(0.0, 0.15, -y)
            luz_dir = luna
            luz_color = escalar((0.42, 0.52, 0.80), 0.35 * k)
            fuerza_sombra = 0.6 * k

        ambiente = mezcla(mezcla((0.10, 0.12, 0.22), (0.40, 0.45, 0.55), dia), (0.45, 0.33, 0.30), ocaso * 0.3)
        nube = mezcla(mezcla((0.08, 0.09, 0.15), (0.96, 0.97, 1.0), dia), (1.0, 0.62, 0.45), ocaso * 0.6)

        return {
            "sol": sol, "luna": luna, "arriba": arriba, "horizonte": horizonte,
            "color_sol": color_sol, "luz_dir": luz_dir, "luz_color": luz_color,
            "ambiente": ambiente, "nube": nube, "noche": 1.0 - dia,
            "fuerza_sombra": fuerza_sombra,
        }

"""Cálculos sobre la salida del modelo: unidades, derivados, semáforo y ventanas.

Funciones puras (sin base de datos) para poder probarlas con casos conocidos.
"""
import math

import numpy as np

DIRECCIONES = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"]
NIVEL = {"verde": 0, "amarillo": 1, "gris": 2, "rojo": 3}
NOMBRES = {
    "temperatura": ("Temperatura", "°C"),
    "sensacion_termica": ("Sensación térmica", "°C"),
    "viento": ("Viento", "km/h"),
    "humedad": ("Humedad", "%"),
}


# --- Unidades -------------------------------------------------------------

def kelvin_a_c(t_k):
    return t_k - 273.15


def viento_kmh(u, v):
    return math.hypot(u, v) * 3.6


def viento_direccion(u, v):
    """Grados de donde viene el viento (0 = norte) y su nombre en 8 rumbos."""
    if u == 0 and v == 0:
        return None, None
    grados = (math.degrees(math.atan2(-u, -v)) + 360) % 360
    return round(grados), DIRECCIONES[int((grados + 22.5) // 45) % 8]


# --- Derivados (RF004, RF014) --------------------------------------------

def sensacion_termica(t_c, v_kmh):
    """Índice de enfriamiento por viento. Solo aplica con T <= 10 °C y viento > 4,8 km/h."""
    if t_c > 10 or v_kmh <= 4.8:
        return t_c
    f = v_kmh ** 0.16
    return 13.12 + 0.6215 * t_c - 11.37 * f + 0.3965 * t_c * f


def punto_rocio(t_c, rh):
    """Fórmula de Magnus."""
    rh = max(rh, 1.0)
    a, b = 17.62, 243.12
    g = math.log(rh / 100) + a * t_c / (b + t_c)
    return b * g / (a - g)


def ajuste_altitud(t_c, altitud_real, altitud_celda, gradiente_c_km):
    """La celda está a otra altura que el punto: se corrige T con el gradiente."""
    return t_c - gradiente_c_km * (altitud_real - altitud_celda) / 1000


def isoterma_cero(t_c, dem):
    """Altitud (m) donde la T cruza 0 °C en el dominio, o None si no hay cruce.

    Se ajusta una recta T = a + b * altitud con todas las celdas.
    """
    t = np.asarray(t_c, dtype=np.float64).ravel()
    z = np.asarray(dem, dtype=np.float64).ravel()
    if not (t.min() < 0 < t.max()):
        return None
    b, a = np.polyfit(z, t, 1)
    if b >= 0:
        return None
    return round(-a / b)


def transicion_termica(temperaturas):
    """Índice de la primera hora en que T pasa de negativa a >= 0 (RF019), o None."""
    for i in range(1, len(temperaturas)):
        anterior, actual = temperaturas[i - 1], temperaturas[i]
        if anterior is not None and actual is not None and anterior < 0 <= actual:
            return i
    return None


# --- Semáforo (RF006) -----------------------------------------------------

def _num(x):
    return f"{x:.1f}".rstrip("0").rstrip(".")


def evaluar_criterio(valor, criterio):
    """Color y motivo de una variable frente a su criterio."""
    nombre, unidad = NOMBRES[criterio["variable"]]
    if criterio["sentido"] == "max":
        for color in ("rojo", "amarillo"):
            umbral = criterio[f"umbral_{color}"]
            if valor >= umbral:
                return color, f"{nombre} {_num(valor)} {unidad} supera el umbral {color} de {_num(umbral)} {unidad}"
    else:
        for color in ("rojo", "amarillo"):
            umbral = criterio[f"umbral_{color}"]
            if valor <= umbral:
                return color, f"{nombre} {_num(valor)} {unidad} está por debajo del umbral {color} de {_num(umbral)} {unidad}"
    return "verde", None


def semaforo(valores, criterios):
    """valores: {variable: número o None}. criterios: lista de dicts de la zona.

    Gana el peor color; el motivo es el de esa variable.
    """
    if not criterios:
        return "gris", "Sin criterios configurados para esta zona"
    peor, motivo = "verde", "Todas las variables dentro de los umbrales"
    for c in criterios:
        valor = valores.get(c["variable"])
        if valor is None:
            color, texto = "gris", f"Sin dato de {NOMBRES[c['variable']][0].lower()}"
        else:
            color, texto = evaluar_criterio(valor, c)
        if NIVEL[color] > NIVEL[peor]:
            peor, motivo = color, texto
    return peor, motivo


# --- Ventanas favorables (RF007) -----------------------------------------

def ventanas(horas, duracion_h):
    """horas: lista ordenada de {hora_lima, fin_lima, colores: [(color, motivo)] de todas las zonas}.

    Una ventana toma el peor color de todas sus horas y zonas. Orden: color,
    luego menos horas en amarillo, luego la más temprana. Así el orden se repite igual.
    """
    resultado = []
    for inicio in range(0, len(horas) - duracion_h + 1):
        tramo = horas[inicio:inicio + duracion_h]
        peor, motivo, amarillas = "verde", "Todas las horas en verde", 0
        for h in tramo:
            colores_hora = [c for c, _ in h["colores"]]
            if "amarillo" in colores_hora:
                amarillas += 1
            for color, texto in h["colores"]:
                if NIVEL[color] > NIVEL[peor]:
                    peor = color
                    motivo = f"{h['hora_lima'][-5:]} en {color}: {texto[0].lower() + texto[1:]}"
        resultado.append({
            "inicio_utc": tramo[0]["valido_utc"],
            "inicio_lima": tramo[0]["hora_lima"],
            "fin_lima": tramo[-1]["fin_lima"],
            "semaforo": peor,
            "motivo": motivo,
            "horas_amarillo": amarillas,
            "_orden": (NIVEL[peor], amarillas, inicio),
        })
    resultado.sort(key=lambda v: v["_orden"])
    for v in resultado:
        del v["_orden"]
    return resultado

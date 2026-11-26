from django.db import models
from django.db.models import Q

# Límites de la grilla WRF (datos/static.npz). Un punto fuera de aquí no tiene celda.
LAT_MIN, LAT_MAX = -10.264, -8.403
LON_MIN, LON_MAX = -78.033, -77.104
FILAS, COLUMNAS = 70, 35

ZONAS = [
    ("valle", "Zona valle"),
    ("campo_base", "Campo base"),
    ("zona_alta", "Zona alta"),
]
CODIGOS_ZONA = [codigo for codigo, _ in ZONAS]


class Actividad(models.Model):
    codigo = models.CharField(max_length=30, unique=True)
    nombre = models.CharField(max_length=80)
    duracion_tipica_h = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        db_table = "actividad"
        verbose_name_plural = "actividades"
        constraints = [
            models.CheckConstraint(
                condition=Q(duracion_tipica_h__isnull=True) | Q(duracion_tipica_h__range=(1, 72)),
                name="actividad_duracion_1_72",
            ),
        ]

    def __str__(self):
        return self.nombre


class Destino(models.Model):
    codigo = models.CharField(max_length=40, unique=True)
    nombre = models.CharField(max_length=100)
    actividad = models.ForeignKey(Actividad, on_delete=models.PROTECT, related_name="destinos")
    descripcion = models.CharField(max_length=500, blank=True)
    activo = models.BooleanField(default=True)
    fuente_coordenadas = models.CharField(max_length=200)

    class Meta:
        db_table = "destino"

    def __str__(self):
        return self.nombre


class PuntoRuta(models.Model):
    destino = models.ForeignKey(Destino, on_delete=models.CASCADE, related_name="puntos")
    nombre = models.CharField(max_length=100)
    zona = models.CharField(max_length=12, choices=ZONAS)
    orden = models.PositiveSmallIntegerField()
    lat = models.FloatField()
    lon = models.FloatField()
    altitud_real_m = models.IntegerField()
    fila = models.PositiveSmallIntegerField()
    col = models.PositiveSmallIntegerField()

    class Meta:
        db_table = "punto_ruta"
        verbose_name = "punto de ruta"
        verbose_name_plural = "puntos de ruta"
        ordering = ["destino", "orden"]
        constraints = [
            models.UniqueConstraint(fields=["destino", "orden"], name="punto_orden_unico"),
            models.CheckConstraint(condition=Q(zona__in=CODIGOS_ZONA), name="punto_zona_valida"),
            models.CheckConstraint(condition=Q(lat__range=(LAT_MIN, LAT_MAX)), name="punto_lat_en_dominio"),
            models.CheckConstraint(condition=Q(lon__range=(LON_MIN, LON_MAX)), name="punto_lon_en_dominio"),
            models.CheckConstraint(condition=Q(fila__lt=FILAS), name="punto_fila_0_69"),
            models.CheckConstraint(condition=Q(col__lt=COLUMNAS), name="punto_col_0_34"),
        ]

    def __str__(self):
        return f"{self.destino} · {self.nombre}"


class Criterio(models.Model):
    VARIABLES = [
        ("temperatura", "Temperatura"),
        ("sensacion_termica", "Sensación térmica"),
        ("viento", "Viento"),
        ("humedad", "Humedad"),
    ]
    # max: alerta cuando el valor sube (viento). min: cuando baja (temperatura).
    SENTIDOS = [("max", "Máximo"), ("min", "Mínimo")]

    actividad = models.ForeignKey(Actividad, on_delete=models.CASCADE, related_name="criterios")
    zona = models.CharField(max_length=12, choices=ZONAS)
    variable = models.CharField(max_length=20, choices=VARIABLES)
    sentido = models.CharField(max_length=3, choices=SENTIDOS)
    umbral_amarillo = models.FloatField()
    umbral_rojo = models.FloatField()
    unidad = models.CharField(max_length=6)
    fuente = models.CharField(max_length=300)

    class Meta:
        db_table = "criterio"
        constraints = [
            models.UniqueConstraint(fields=["actividad", "zona", "variable"], name="criterio_unico"),
            models.CheckConstraint(condition=Q(zona__in=CODIGOS_ZONA), name="criterio_zona_valida"),
            models.CheckConstraint(
                condition=Q(variable__in=["temperatura", "sensacion_termica", "viento", "humedad"]),
                name="criterio_variable_valida",
            ),
            models.CheckConstraint(condition=Q(sentido__in=["max", "min"]), name="criterio_sentido_valido"),
        ]

    def __str__(self):
        return f"{self.actividad} · {self.zona} · {self.variable}"


class Ejecucion(models.Model):
    ESTADOS = [("en_proceso", "En proceso"), ("exito", "Éxito"), ("error", "Error")]

    estado = models.CharField(max_length=10, choices=ESTADOS, default="en_proceso")
    es_respaldo = models.BooleanField(default=False)
    modelo_version = models.CharField(max_length=20)
    sha256_pesos = models.CharField(max_length=64)
    gfs_inicio_utc = models.DateTimeField()
    inicio_proceso_utc = models.DateTimeField()
    fin_proceso_utc = models.DateTimeField(null=True, blank=True)
    horizonte_h = models.PositiveSmallIntegerField()
    archivo_gfs = models.CharField(max_length=255, blank=True)
    archivo_salida = models.CharField(max_length=255, blank=True)
    mensaje_error = models.CharField(max_length=1000, blank=True)

    class Meta:
        db_table = "ejecucion"
        verbose_name = "ejecución"
        verbose_name_plural = "ejecuciones"
        ordering = ["-gfs_inicio_utc"]
        indexes = [models.Index(fields=["estado", "gfs_inicio_utc"], name="ejecucion_estado_fecha")]
        constraints = [
            models.CheckConstraint(
                condition=Q(estado__in=["en_proceso", "exito", "error"]), name="ejecucion_estado_valido"
            ),
            models.CheckConstraint(condition=Q(horizonte_h__range=(1, 72)), name="ejecucion_horizonte_1_72"),
        ]

    def __str__(self):
        return f"GFS {self.gfs_inicio_utc:%d/%m %H:%M} UTC ({self.estado})"


class PronosticoPunto(models.Model):
    FUENTES = [("wayra", "WAYRA"), ("gfs", "GFS")]

    ejecucion = models.ForeignKey(Ejecucion, on_delete=models.CASCADE, related_name="pronosticos")
    punto_ruta = models.ForeignKey(PuntoRuta, on_delete=models.CASCADE, related_name="pronosticos")
    valido_utc = models.DateTimeField()
    fuente = models.CharField(max_length=5, choices=FUENTES)
    t_k = models.FloatField()
    rh_pct = models.FloatField()
    u_ms = models.FloatField()
    v_ms = models.FloatField()
    precip_mm = models.FloatField(null=True, blank=True)  # solo en las filas gfs

    class Meta:
        db_table = "pronostico_punto"
        verbose_name = "pronóstico por punto"
        verbose_name_plural = "pronósticos por punto"
        constraints = [
            models.UniqueConstraint(
                fields=["ejecucion", "punto_ruta", "valido_utc", "fuente"], name="pronostico_unico"
            ),
            models.CheckConstraint(condition=Q(fuente__in=["wayra", "gfs"]), name="pronostico_fuente_valida"),
            models.CheckConstraint(condition=Q(rh_pct__range=(0, 100)), name="pronostico_rh_0_100"),
        ]

from django.db import models


class TimeStampedModel(models.Model):
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SolicitudContacto(TimeStampedModel):
    class Servicio(models.TextChoices):
        VUELO = "vuelo", "Cotización de vuelo"
        VUELO_PRIVADO = "vuelo privado", "Cotización de vuelo privado"
        TOUR = "tour", "Cotización de tour"
        VUELO_TOUR = "vuelo y tour", "Vuelo y tour"

    class MotivoVueloPrivado(models.TextChoices):
        NEGOCIOS = "negocios", "Negocios"
        TURISMO = "turismo", "Turismo"
        GRUPO = "grupo", "Viaje grupal"
        EMERGENCIA = "emergencia", "Necesidad urgente"
        OTRO = "otro", "Otro"

    class Estado(models.TextChoices):
        NUEVA = "nueva", "Nueva"
        CONTACTADA = "contactada", "Contactada"
        SEGUIMIENTO = "seguimiento", "En seguimiento"
        CONVERTIDA = "convertida", "Convertida"
        DESCARTADA = "descartada", "Descartada"

    nombre = models.CharField(max_length=180)
    contacto = models.CharField(max_length=180)
    correo = models.EmailField(blank=True)
    telefono = models.CharField(max_length=40, blank=True)
    servicio = models.CharField(max_length=20, choices=Servicio.choices)
    origen = models.CharField(max_length=180, blank=True)
    destino = models.CharField(max_length=180, blank=True)
    fecha_ida = models.DateField(null=True, blank=True)
    fecha_regreso = models.DateField(null=True, blank=True)
    hora_salida_preferida = models.TimeField(null=True, blank=True)
    adultos = models.PositiveSmallIntegerField(default=1)
    ninos = models.PositiveSmallIntegerField(default=0)
    edades_ninos = models.CharField(max_length=120, blank=True)
    motivo_vuelo_privado = models.CharField(
        max_length=20, choices=MotivoVueloPrivado.choices, blank=True
    )
    equipaje_estimado = models.CharField(max_length=180, blank=True)
    preferencia_aeronave = models.CharField(max_length=120, blank=True)
    presupuesto = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    lugar_turistico = models.ForeignKey(
        "sami_admin.LugarTuristico",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="solicitudes_publicas",
    )
    tour = models.ForeignKey(
        "sami_admin.Tour",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="solicitudes_publicas",
    )
    detalles = models.TextField(blank=True)
    notas_internas = models.TextField(blank=True)
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.NUEVA,
        db_index=True,
    )
    asignada_a = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="solicitudes_asignadas",
    )
    cotizacion = models.OneToOneField(
        "sami_admin.Cotizacion",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="solicitud_origen",
    )
    atendida = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ("estado", "-creado_en")
        verbose_name = "solicitud de contacto"
        verbose_name_plural = "solicitudes de contacto"

    def __str__(self):
        return f"{self.nombre} — {self.get_servicio_display()}"

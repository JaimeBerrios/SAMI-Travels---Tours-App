from django.core.validators import MinValueValidator
from django.db import models


class TimeStampedModel(models.Model):
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SolicitudContacto(TimeStampedModel):
    class Servicio(models.TextChoices):
        VUELO = "vuelo", "Cotización de vuelo"
        TOUR = "tour", "Cotización de tour"
        VUELO_TOUR = "vuelo y tour", "Vuelo y tour"

    nombre = models.CharField(max_length=180)
    contacto = models.CharField(max_length=180)
    servicio = models.CharField(max_length=20, choices=Servicio.choices)
    destino = models.CharField(max_length=180, blank=True)
    detalles = models.TextField(blank=True)
    atendida = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ("atendida", "-creado_en")
        verbose_name = "solicitud de contacto"
        verbose_name_plural = "solicitudes de contacto"

    def __str__(self):
        return f"{self.nombre} — {self.get_servicio_display()}"


class Servicio(TimeStampedModel):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ("nombre",)
        verbose_name = "servicio"
        verbose_name_plural = "servicios"

    def __str__(self):
        return self.nombre


class Destino(TimeStampedModel):
    nombre = models.CharField(max_length=120)
    ciudad = models.CharField(max_length=120, blank=True)
    pais = models.CharField(max_length=120)
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ("pais", "nombre")
        constraints = [
            models.UniqueConstraint(
                fields=("nombre", "ciudad", "pais"),
                name="destino_ubicacion_unica",
            )
        ]
        verbose_name = "destino"
        verbose_name_plural = "destinos"

    def __str__(self):
        ubicacion = ", ".join(filter(None, (self.nombre, self.ciudad, self.pais)))
        return ubicacion


class PaqueteTuristico(TimeStampedModel):
    nombre = models.CharField(max_length=160)
    destino = models.ForeignKey(
        Destino,
        on_delete=models.PROTECT,
        related_name="paquetes",
    )
    servicios = models.ManyToManyField(Servicio, related_name="paquetes", blank=True)
    descripcion = models.TextField(blank=True)
    duracion_dias = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)]
    )
    precio_base = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Precio base por persona en USD.",
    )
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ("nombre",)
        verbose_name = "paquete turístico"
        verbose_name_plural = "paquetes turísticos"

    def __str__(self):
        return self.nombre


class Cliente(TimeStampedModel):
    nombres = models.CharField(max_length=120)
    apellidos = models.CharField(max_length=120)
    correo = models.EmailField(unique=True)
    telefono = models.CharField(max_length=30, blank=True)
    documento_identidad = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        unique=True,
    )
    notas = models.TextField(blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ("apellidos", "nombres")
        verbose_name = "cliente"
        verbose_name_plural = "clientes"

    def __str__(self):
        return f"{self.nombres} {self.apellidos}".strip()


class Reserva(TimeStampedModel):
    class Estado(models.TextChoices):
        SOLICITADA = "solicitada", "Solicitada"
        COTIZADA = "cotizada", "Cotizada"
        CONFIRMADA = "confirmada", "Confirmada"
        CANCELADA = "cancelada", "Cancelada"
        COMPLETADA = "completada", "Completada"

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name="reservas",
    )
    paquete = models.ForeignKey(
        PaqueteTuristico,
        on_delete=models.PROTECT,
        related_name="reservas",
        blank=True,
        null=True,
    )
    destino = models.ForeignKey(
        Destino,
        on_delete=models.PROTECT,
        related_name="reservas_personalizadas",
        blank=True,
        null=True,
        help_text="Destino para una reserva personalizada sin paquete.",
    )
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.SOLICITADA,
        db_index=True,
    )
    fecha_salida = models.DateField(db_index=True)
    fecha_regreso = models.DateField(blank=True, null=True)
    cantidad_viajeros = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
    )
    precio_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
    )
    notas = models.TextField(blank=True)

    class Meta:
        ordering = ("-creado_en",)
        constraints = [
            models.CheckConstraint(
                check=models.Q(paquete__isnull=False) | models.Q(destino__isnull=False),
                name="reserva_paquete_o_destino",
            ),
            models.CheckConstraint(
                check=models.Q(fecha_regreso__isnull=True)
                | models.Q(fecha_regreso__gte=models.F("fecha_salida")),
                name="reserva_fechas_validas",
            ),
        ]
        verbose_name = "reserva"
        verbose_name_plural = "reservas"

    def __str__(self):
        return f"Reserva #{self.pk or 'nueva'} - {self.cliente}"


class Viajero(TimeStampedModel):
    reserva = models.ForeignKey(
        Reserva,
        on_delete=models.CASCADE,
        related_name="viajeros",
    )
    nombres = models.CharField(max_length=120)
    apellidos = models.CharField(max_length=120)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    numero_pasaporte = models.CharField(max_length=50, blank=True, null=True)
    nacionalidad = models.CharField(max_length=80, blank=True)
    es_titular = models.BooleanField(default=False)

    class Meta:
        ordering = ("apellidos", "nombres")
        constraints = [
            models.UniqueConstraint(
                fields=("reserva", "numero_pasaporte"),
                name="viajero_pasaporte_unico_por_reserva",
            )
        ]
        verbose_name = "viajero"
        verbose_name_plural = "viajeros"

    def __str__(self):
        return f"{self.nombres} {self.apellidos}".strip()

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


AEROLINEAS_CHOICES = [
    ("avianca", "Avianca"),
    ("copa_airlines", "Copa Airlines"),
    ("volaris", "Volaris"),
    ("aeromexico", "Aerom\u00e9xico"),
    ("american_airlines", "American Airlines"),
    ("united_airlines", "United Airlines"),
    ("delta", "Delta"),
    ("spirit_airlines", "Spirit Airlines"),
    ("iberia", "Iberia"),
    ("otra", "Otra"),
]


class Cotizacion(models.Model):
    class TipoCotizacion(models.TextChoices):
        VUELOS = "vuelos", "Vuelos"
        TOURS = "tours", "Tours"
        VUELOS_TOURS = "vuelos_tours", "Vuelos y Tours"

    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        APROBADA = "aprobada", "Aprobada"
        RECHAZADA = "rechazada", "Rechazada"

    asesor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="cotizaciones",
    )
    cliente_nombre = models.CharField(max_length=180)
    cliente_correo = models.EmailField()
    tipo_cotizacion = models.CharField(
        max_length=20,
        choices=TipoCotizacion.choices,
        default=TipoCotizacion.TOURS,
        db_index=True,
    )
    destino = models.CharField(max_length=180)
    ruta_vuelo = models.CharField(max_length=255, null=True, blank=True)
    cantidad_adultos = models.IntegerField(null=True, blank=True)
    cantidad_ninos = models.IntegerField(null=True, blank=True)
    fecha_ida = models.DateField(null=True, blank=True)
    hora_salida_ida = models.TimeField(null=True, blank=True)
    hora_llegada_ida = models.TimeField(null=True, blank=True)
    escala_ida = models.CharField(max_length=180, null=True, blank=True)
    fecha_vuelta = models.DateField(null=True, blank=True)
    hora_salida_vuelta = models.TimeField(null=True, blank=True)
    hora_llegada_vuelta = models.TimeField(null=True, blank=True)
    escala_vuelta = models.CharField(max_length=180, null=True, blank=True)
    aerolinea = models.CharField(
        max_length=30,
        choices=AEROLINEAS_CHOICES,
        null=True,
        blank=True,
    )
    equipaje_incluido = models.TextField(null=True, blank=True)
    notas_importantes = models.TextField(null=True, blank=True)
    precio_estimado = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True, db_index=True)
    estado = models.CharField(
        max_length=12,
        choices=Estado.choices,
        default=Estado.PENDIENTE,
        db_index=True,
    )

    class Meta:
        ordering = ("-fecha_creacion",)
        verbose_name = "cotización"
        verbose_name_plural = "cotizaciones"

    def __str__(self):
        return f"Cotización #{self.pk or 'nueva'} - {self.cliente_nombre}"

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

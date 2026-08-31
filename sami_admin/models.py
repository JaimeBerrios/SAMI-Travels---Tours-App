from django.conf import settings
from django.core.validators import MinValueValidator
from django.core.files.storage import default_storage
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify


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


class Pais(models.Model):
    nombre = models.CharField(max_length=120, unique=True)
    activo = models.BooleanField(default=True, db_index=True)
    creado_en = models.DateTimeField(default=timezone.now, editable=False)
    actualizado_en = models.DateTimeField(auto_now=True, null=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="paises_creados",
    )
    actualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="paises_actualizados",
    )

    class Meta:
        ordering = ("nombre",)
        verbose_name = "país"
        verbose_name_plural = "países"

    def __str__(self):
        return self.nombre


class Departamento(models.Model):
    pais = models.ForeignKey(
        Pais,
        on_delete=models.PROTECT,
        related_name="departamentos",
    )
    nombre = models.CharField(max_length=120)
    activo = models.BooleanField(default=True, db_index=True)
    creado_en = models.DateTimeField(default=timezone.now, editable=False)
    actualizado_en = models.DateTimeField(auto_now=True, null=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="departamentos_creados",
    )
    actualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="departamentos_actualizados",
    )

    class Meta:
        ordering = ("pais__nombre", "nombre")
        constraints = [
            models.UniqueConstraint(
                fields=("pais", "nombre"),
                name="departamento_unico_por_pais",
            )
        ]

    def __str__(self):
        return f"{self.nombre}, {self.pais.nombre}"


class LugarTuristico(models.Model):
    departamento = models.ForeignKey(
        Departamento,
        on_delete=models.PROTECT,
        related_name="lugares_turisticos",
    )
    nombre = models.CharField(max_length=180)
    slug = models.SlugField(max_length=220, unique=True)
    imagen = models.ImageField(upload_to="lugares_turisticos/")
    descripcion_historica = models.TextField()
    resumen_publico = models.CharField(max_length=280, blank=True)
    mejor_epoca = models.CharField(
        max_length=180, blank=True,
        help_text="Meses o temporada recomendada para visitar el destino.",
    )
    duracion_recomendada = models.CharField(
        max_length=120, blank=True,
        help_text="Ejemplo: 4 a 6 días.",
    )
    aeropuerto_principal = models.CharField(max_length=180, blank=True)
    actividades_destacadas = models.TextField(
        blank=True,
        help_text="Una actividad por línea.",
    )
    requisitos_viaje = models.TextField(
        blank=True,
        help_text="Orientación general; evita afirmar requisitos que puedan cambiar.",
    )
    destacado = models.BooleanField(default=False, db_index=True)
    activo = models.BooleanField(default=True, db_index=True)
    creado_en = models.DateTimeField(default=timezone.now, editable=False)
    actualizado_en = models.DateTimeField(auto_now=True, null=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="lugares_creados",
    )
    actualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="lugares_actualizados",
    )

    class Meta:
        ordering = ("departamento__pais__nombre", "departamento__nombre", "nombre")
        constraints = [
            models.UniqueConstraint(
                fields=("departamento", "nombre"),
                name="lugar_turistico_unico_por_departamento",
            )
        ]
        verbose_name = "lugar turístico"
        verbose_name_plural = "lugares turísticos"

    def __str__(self):
        return f"{self.nombre} · {self.departamento}"

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(f"{self.nombre}-{self.departamento.nombre}")[:200]
            candidate = base
            suffix = 2
            while LugarTuristico.objects.exclude(pk=self.pk).filter(
                slug=candidate
            ).exists():
                candidate = f"{base[:214]}-{suffix}"
                suffix += 1
            self.slug = candidate
        super().save(*args, **kwargs)

    @property
    def lista_actividades(self):
        return [item.strip() for item in self.actividades_destacadas.splitlines() if item.strip()]


class Tour(models.Model):
    lugar_turistico = models.ForeignKey(
        LugarTuristico,
        on_delete=models.PROTECT,
        related_name="tours",
    )
    nombre_comercial = models.CharField(max_length=180)
    slug = models.SlugField(max_length=220, unique=True)
    duracion = models.CharField(max_length=120)
    punto_encuentro = models.CharField(max_length=255, blank=True)
    incluye = models.TextField()
    no_incluye = models.TextField(blank=True)
    itinerario = models.TextField()
    recomendaciones = models.TextField(blank=True)
    que_llevar = models.TextField(blank=True)
    restricciones = models.TextField(blank=True)
    politica_cancelacion = models.TextField(blank=True)
    precio_base = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    destacado = models.BooleanField(default=False, db_index=True)
    en_promocion = models.BooleanField(default=False, db_index=True)
    activo = models.BooleanField(default=True, db_index=True)
    creado_en = models.DateTimeField(default=timezone.now, editable=False)
    actualizado_en = models.DateTimeField(auto_now=True, null=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="tours_creados",
    )
    actualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="tours_actualizados",
    )

    class Meta:
        ordering = ("lugar_turistico__nombre", "nombre_comercial")
        constraints = [
            models.UniqueConstraint(
                fields=("lugar_turistico", "nombre_comercial"),
                name="tour_unico_por_lugar",
            )
        ]

    def __str__(self):
        return f"{self.nombre_comercial} · {self.lugar_turistico.nombre}"

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(
                f"{self.nombre_comercial}-{self.lugar_turistico.nombre}"
            )[:200]
            candidate = base
            suffix = 2
            while Tour.objects.exclude(pk=self.pk).filter(slug=candidate).exists():
                candidate = f"{base[:214]}-{suffix}"
                suffix += 1
            self.slug = candidate
        super().save(*args, **kwargs)


class CampanaPromocional(models.Model):
    class TipoEnlace(models.TextChoices):
        COTIZADOR = "cotizador", "Formulario de cotización"
        DESTINO = "destino", "Destino turístico"
        TOUR = "tour", "Tour o paquete"
        PERSONALIZADO = "personalizado", "Enlace personalizado"

    nombre = models.CharField(
        max_length=120,
        help_text="Nombre interno para identificar la campaña.",
    )
    etiqueta = models.CharField(
        max_length=80,
        default="Promoción especial",
        help_text="Texto corto que aparece sobre el título.",
    )
    titulo = models.CharField(max_length=140)
    descripcion = models.TextField(max_length=360)
    imagen_escritorio = models.ImageField(upload_to="campanas/escritorio/")
    imagen_movil = models.ImageField(upload_to="campanas/movil/")
    texto_alternativo = models.CharField(
        max_length=180,
        help_text="Describe brevemente la imagen para accesibilidad.",
    )
    texto_boton = models.CharField(max_length=50, default="Solicitar cotización")
    tipo_enlace = models.CharField(
        max_length=20,
        choices=TipoEnlace.choices,
        default=TipoEnlace.COTIZADOR,
    )
    lugar_turistico = models.ForeignKey(
        LugarTuristico,
        on_delete=models.SET_NULL,
        related_name="campanas",
        null=True,
        blank=True,
    )
    tour = models.ForeignKey(
        Tour,
        on_delete=models.SET_NULL,
        related_name="campanas",
        null=True,
        blank=True,
    )
    url_personalizada = models.URLField(blank=True)
    fecha_inicio = models.DateTimeField(db_index=True)
    fecha_fin = models.DateTimeField(null=True, blank=True, db_index=True)
    prioridad = models.PositiveSmallIntegerField(
        default=10,
        help_text="La campaña activa con el número más alto se mostrará primero.",
    )
    activo = models.BooleanField(default=True, db_index=True)
    mostrar_avion = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="campanas_creadas",
        null=True,
        blank=True,
    )
    actualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="campanas_actualizadas",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ("-prioridad", "-fecha_inicio", "-id")
        verbose_name = "campaña promocional"
        verbose_name_plural = "campañas promocionales"

    def __str__(self):
        return self.nombre

    @property
    def estado_publicacion(self):
        now = timezone.now()
        if not self.activo:
            return "Pausada"
        if self.fecha_inicio > now:
            return "Programada"
        if self.fecha_fin and self.fecha_fin < now:
            return "Finalizada"
        return "Publicada"

    def get_target_url(self):
        portal = reverse("core:portal-publico")
        if self.tipo_enlace == self.TipoEnlace.DESTINO and self.lugar_turistico_id:
            return f"{portal}?lugar={self.lugar_turistico_id}#cotizar"
        if self.tipo_enlace == self.TipoEnlace.TOUR and self.tour_id:
            return f"{portal}?tour={self.tour_id}#cotizar"
        if self.tipo_enlace == self.TipoEnlace.PERSONALIZADO:
            return self.url_personalizada
        return f"{portal}#cotizar"

    @property
    def descripcion_enlace(self):
        if self.tipo_enlace == self.TipoEnlace.DESTINO and self.lugar_turistico_id:
            return f"Cotizador con destino: {self.lugar_turistico.nombre}"
        if self.tipo_enlace == self.TipoEnlace.TOUR and self.tour_id:
            return f"Cotizador con tour: {self.tour.nombre_comercial}"
        if self.tipo_enlace == self.TipoEnlace.PERSONALIZADO:
            return self.url_personalizada or "Enlace pendiente"
        return "Formulario de cotización"


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
    lugar_turistico = models.ForeignKey(
        LugarTuristico,
        on_delete=models.SET_NULL,
        related_name="cotizaciones",
        null=True,
        blank=True,
    )
    tour = models.ForeignKey(
        Tour,
        on_delete=models.SET_NULL,
        related_name="cotizaciones",
        null=True,
        blank=True,
    )
    nombre_destino_cotizado = models.CharField(max_length=180, blank=True)
    nombre_tour_cotizado = models.CharField(max_length=180, blank=True)
    ubicacion_destino_cotizada = models.CharField(max_length=255, blank=True)
    descripcion_historica_cotizada = models.TextField(blank=True)
    imagen_destino_cotizada = models.CharField(max_length=500, blank=True)
    duracion_tour = models.CharField(max_length=120, null=True, blank=True)
    punto_encuentro = models.CharField(max_length=255, null=True, blank=True)
    incluye = models.TextField(null=True, blank=True)
    no_incluye = models.TextField(null=True, blank=True)
    itinerario_resumido = models.TextField(null=True, blank=True)
    recomendaciones_tour = models.TextField(null=True, blank=True)
    que_llevar_tour = models.TextField(null=True, blank=True)
    restricciones_tour = models.TextField(null=True, blank=True)
    politica_cancelacion = models.TextField(null=True, blank=True)
    notas_tour = models.TextField(null=True, blank=True)
    vigencia_cotizacion = models.DateField(null=True, blank=True)
    ruta_vuelo = models.CharField(max_length=255, null=True, blank=True)
    cantidad_adultos = models.IntegerField(null=True, blank=True)
    cantidad_ninos = models.IntegerField(null=True, blank=True)
    edades_ninos = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Edades separadas por comas, por ejemplo: 5, 11",
    )
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
    archivada = models.BooleanField(default=False, db_index=True)
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

    @property
    def nombre_destino_documento(self):
        return self.nombre_destino_cotizado or self.destino

    @property
    def descripcion_destino_documento(self):
        if self.descripcion_historica_cotizada:
            return self.descripcion_historica_cotizada
        if self.lugar_turistico_id:
            return self.lugar_turistico.descripcion_historica
        return ""

    @property
    def imagen_destino_documento(self):
        if self.imagen_destino_cotizada:
            return default_storage.url(self.imagen_destino_cotizada)
        if self.lugar_turistico_id and self.lugar_turistico.imagen:
            return self.lugar_turistico.imagen.url
        return ""


class HistorialCotizacion(models.Model):
    cotizacion = models.ForeignKey(
        Cotizacion,
        on_delete=models.CASCADE,
        related_name="historial",
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    accion = models.CharField(max_length=30)
    estado = models.CharField(max_length=12, blank=True)
    datos = models.JSONField(default=dict, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ("-creado_en",)
        verbose_name = "historial de cotización"
        verbose_name_plural = "historial de cotizaciones"


class CotizacionDestino(models.Model):
    """Ordered destination stop belonging to a quotation itinerary."""

    cotizacion = models.ForeignKey(
        Cotizacion,
        on_delete=models.CASCADE,
        related_name="destinos",
    )
    lugar_turistico = models.ForeignKey(
        LugarTuristico,
        on_delete=models.PROTECT,
        related_name="paradas_cotizadas",
    )
    tour = models.ForeignKey(
        Tour,
        on_delete=models.SET_NULL,
        related_name="paradas_cotizadas",
        null=True,
        blank=True,
    )
    fecha_visita = models.DateField()
    orden = models.PositiveIntegerField(default=1)
    precio_manual = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True,
    )
    notas = models.TextField(blank=True)
    nombre_destino = models.CharField(max_length=180, blank=True)
    ubicacion_destino = models.CharField(max_length=255, blank=True)
    descripcion_historica = models.TextField(blank=True)
    imagen_destino = models.CharField(max_length=500, blank=True)
    nombre_tour = models.CharField(max_length=180, blank=True)
    duracion_tour = models.CharField(max_length=120, blank=True)
    punto_encuentro = models.CharField(max_length=255, blank=True)
    incluye = models.TextField(blank=True)
    no_incluye = models.TextField(blank=True)
    itinerario = models.TextField(blank=True)
    recomendaciones = models.TextField(blank=True)
    que_llevar = models.TextField(blank=True)
    restricciones = models.TextField(blank=True)
    politica_cancelacion = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("fecha_visita", "orden", "id")
        indexes = [models.Index(fields=("cotizacion", "fecha_visita", "orden"))]

    def __str__(self):
        return f"{self.fecha_visita} · {self.nombre_destino or self.lugar_turistico.nombre}"

    @property
    def imagen_url(self):
        return default_storage.url(self.imagen_destino) if self.imagen_destino else ""

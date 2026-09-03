from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.core.files.storage import default_storage
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import get_language
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

    @property
    def tipo_division_administrativa(self):
        """Nombre habitual de la división territorial para mostrar al usuario."""
        nombre = self.nombre.casefold()
        for source, target in (("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u")):
            nombre = nombre.replace(source, target)
        if nombre in {"estados unidos", "mexico", "brasil", "australia", "india", "venezuela"}:
            return "Estado"
        if nombre in {"argentina", "canada", "chile", "ecuador", "panama", "costa rica"}:
            return "Provincia"
        if nombre in {"el salvador", "guatemala", "honduras", "nicaragua", "paraguay", "colombia", "bolivia", "peru"}:
            return "Departamento"
        return "División administrativa"


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
    nombre_en = models.CharField("Nombre en inglés", max_length=180, blank=True)
    slug = models.SlugField(max_length=220, unique=True)
    imagen = models.ImageField(upload_to="lugares_turisticos/")
    imagen_foco_x = models.PositiveSmallIntegerField(
        "Punto focal horizontal",
        default=50,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Posición horizontal del punto importante de la imagen, de 0 a 100%.",
    )
    imagen_foco_y = models.PositiveSmallIntegerField(
        "Punto focal vertical",
        default=50,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Posición vertical del punto importante de la imagen, de 0 a 100%.",
    )
    descripcion_historica = models.TextField()
    descripcion_historica_en = models.TextField("Descripción histórica en inglés", blank=True)
    resumen_publico = models.CharField(max_length=280, blank=True)
    resumen_publico_en = models.CharField("Resumen público en inglés", max_length=280, blank=True)
    mejor_epoca = models.CharField(
        max_length=180, blank=True,
        help_text="Meses o temporada recomendada para visitar el destino.",
    )
    mejor_epoca_en = models.CharField("Mejor época en inglés", max_length=180, blank=True)
    duracion_recomendada = models.CharField(
        max_length=120, blank=True,
        help_text="Ejemplo: 4 a 6 días.",
    )
    duracion_recomendada_en = models.CharField("Duración recomendada en inglés", max_length=120, blank=True)
    aeropuerto_principal = models.CharField(max_length=180, blank=True)
    actividades_destacadas = models.TextField(
        blank=True,
        help_text="Una actividad por línea.",
    )
    actividades_destacadas_en = models.TextField("Actividades destacadas en inglés", blank=True)
    requisitos_viaje = models.TextField(
        blank=True,
        help_text="Orientación general; evita afirmar requisitos que puedan cambiar.",
    )
    requisitos_viaje_en = models.TextField("Requisitos de viaje en inglés", blank=True)
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

    @property
    def posicion_focal_css(self):
        return f"{self.imagen_foco_x}% {self.imagen_foco_y}%"

    def translated(self, field_name, language=None):
        if field_name == "nombre":
            return self.nombre
        language = (language or get_language() or "es").lower()
        if language.startswith("en"):
            translated_value = getattr(self, f"{field_name}_en", "")
            if translated_value:
                return translated_value
        return getattr(self, field_name)

    @property
    def nombre_localizado(self):
        return self.translated("nombre")

    @property
    def resumen_localizado(self):
        return self.translated("resumen_publico") or self.descripcion_localizada

    @property
    def descripcion_localizada(self):
        return self.translated("descripcion_historica")

    @property
    def lista_actividades_localizada(self):
        value = self.translated("actividades_destacadas")
        return [item.strip() for item in value.splitlines() if item.strip()]

    @property
    def mejor_epoca_localizada(self):
        return self.translated("mejor_epoca")

    @property
    def duracion_recomendada_localizada(self):
        return self.translated("duracion_recomendada")

    @property
    def requisitos_viaje_localizados(self):
        return self.translated("requisitos_viaje")


class Tour(models.Model):
    lugar_turistico = models.ForeignKey(
        LugarTuristico,
        on_delete=models.PROTECT,
        related_name="tours",
    )
    nombre_comercial = models.CharField(max_length=180)
    nombre_comercial_en = models.CharField("Nombre comercial en inglés", max_length=180, blank=True)
    slug = models.SlugField(max_length=220, unique=True)
    duracion = models.CharField(max_length=120)
    duracion_en = models.CharField("Duración en inglés", max_length=120, blank=True)
    punto_encuentro = models.CharField(max_length=255, blank=True)
    punto_encuentro_en = models.CharField("Punto de encuentro en inglés", max_length=255, blank=True)
    incluye = models.TextField()
    incluye_en = models.TextField("Incluye en inglés", blank=True)
    no_incluye = models.TextField(blank=True)
    no_incluye_en = models.TextField("No incluye en inglés", blank=True)
    itinerario = models.TextField()
    itinerario_en = models.TextField("Itinerario en inglés", blank=True)
    recomendaciones = models.TextField(blank=True)
    recomendaciones_en = models.TextField("Recomendaciones en inglés", blank=True)
    que_llevar = models.TextField(blank=True)
    que_llevar_en = models.TextField("Qué llevar en inglés", blank=True)
    restricciones = models.TextField(blank=True)
    restricciones_en = models.TextField("Restricciones en inglés", blank=True)
    politica_cancelacion = models.TextField(blank=True)
    politica_cancelacion_en = models.TextField("Política de cancelación en inglés", blank=True)
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

    def translated(self, field_name, language=None):
        language = (language or get_language() or "es").lower()
        if language.startswith("en"):
            translated_value = getattr(self, f"{field_name}_en", "")
            if translated_value:
                return translated_value
        return getattr(self, field_name)

    @property
    def nombre_localizado(self):
        return self.translated("nombre_comercial")

    @property
    def duracion_localizada(self):
        return self.translated("duracion")

    @property
    def punto_encuentro_localizado(self):
        return self.translated("punto_encuentro")

    @property
    def incluye_localizado(self):
        return self.translated("incluye")

    @property
    def no_incluye_localizado(self):
        return self.translated("no_incluye")

    @property
    def itinerario_localizado(self):
        return self.translated("itinerario")

    @property
    def recomendaciones_localizadas(self):
        return self.translated("recomendaciones")

    @property
    def que_llevar_localizado(self):
        return self.translated("que_llevar")

    @property
    def restricciones_localizadas(self):
        return self.translated("restricciones")

    @property
    def politica_cancelacion_localizada(self):
        return self.translated("politica_cancelacion")


class CampanaPromocional(models.Model):
    MEDIA_FIELD_NAMES = (
        "imagen_escritorio",
        "imagen_movil",
        "multimedia_escritorio",
        "multimedia_movil",
    )

    class TipoEnlace(models.TextChoices):
        COTIZADOR = "cotizador", "Formulario de cotización"
        DESTINO = "destino", "Destino turístico"
        TOUR = "tour", "Tour o paquete"
        PERSONALIZADO = "personalizado", "Enlace personalizado"

    class TipoMultimedia(models.TextChoices):
        IMAGEN = "imagen", "Imagen"
        GIF = "gif", "GIF animado"
        VIDEO = "video", "Video"

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
    tipo_multimedia = models.CharField(
        max_length=10,
        choices=TipoMultimedia.choices,
        default=TipoMultimedia.IMAGEN,
        help_text="Las imágenes siempre se conservan como portada y respaldo.",
    )
    multimedia_escritorio = models.FileField(
        upload_to="campanas/multimedia/escritorio/", blank=True
    )
    multimedia_movil = models.FileField(
        upload_to="campanas/multimedia/movil/", blank=True
    )
    color_superposicion = models.CharField(
        "color de superposición",
        max_length=7,
        default="#06152B",
        validators=[
            RegexValidator(
                regex=r"^#[0-9A-Fa-f]{6}$",
                message="Selecciona un color hexadecimal válido.",
            )
        ],
        help_text="Color aplicado sobre la imagen para mejorar el contraste.",
    )
    opacidad_superposicion = models.PositiveSmallIntegerField(
        "transparencia del color",
        default=55,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="0 muestra la imagen original y 100 cubre completamente la imagen.",
    )
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
    orden = models.PositiveSmallIntegerField(
        default=0,
        help_text="Entre campañas con la misma prioridad, el número menor aparece primero.",
    )
    activo = models.BooleanField(default=True, db_index=True)
    mostrar_avion = models.BooleanField(default=True)
    archivada_en = models.DateTimeField(null=True, blank=True, db_index=True)
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
        ordering = ("-prioridad", "orden", "-fecha_inicio", "-id")
        verbose_name = "campaña promocional"
        verbose_name_plural = "campañas promocionales"

    def __str__(self):
        return self.nombre

    @property
    def estado_publicacion(self):
        now = timezone.now()
        if self.archivada_en:
            return "Papelera"
        if not self.activo:
            return "Pausada"
        if self.fecha_inicio > now:
            return "Programada"
        if self.fecha_fin and self.fecha_fin < now:
            return "Finalizada"
        return "Publicada"

    @staticmethod
    def _mime_for_file(file_field, media_type):
        if media_type == CampanaPromocional.TipoMultimedia.GIF:
            return "image/gif"
        if file_field.name.lower().endswith(".webm"):
            return "video/webm"
        return "video/mp4"

    @property
    def tipo_mime_multimedia(self):
        return self._mime_for_file(self.multimedia_escritorio, self.tipo_multimedia)

    @property
    def tipo_mime_multimedia_movil(self):
        return self._mime_for_file(self.multimedia_movil, self.tipo_multimedia)

    @property
    def peso_total_multimedia(self):
        total = 0
        for field_name in self.MEDIA_FIELD_NAMES:
            file_field = getattr(self, field_name)
            if not file_field or not file_field.name:
                continue
            try:
                total += file_field.storage.size(file_field.name)
            except (FileNotFoundError, OSError, NotImplementedError):
                continue
        return total

    @classmethod
    def _delete_files_if_unreferenced(cls, stored_files):
        for storage, name in stored_files:
            if not name:
                continue
            references = Q()
            for field_name in cls.MEDIA_FIELD_NAMES:
                references |= Q(**{field_name: name})
            if cls.objects.filter(references).exists():
                continue
            try:
                if storage.exists(name):
                    storage.delete(name)
            except OSError:
                # Un fallo temporal del proveedor no debe revertir la operación.
                continue

    def save(self, *args, **kwargs):
        previous_files = []
        if self.pk:
            previous = type(self).objects.filter(pk=self.pk).first()
            if previous:
                for field_name in self.MEDIA_FIELD_NAMES:
                    old_file = getattr(previous, field_name)
                    new_file = getattr(self, field_name)
                    if old_file.name and old_file.name != new_file.name:
                        previous_files.append((old_file.storage, old_file.name))
        super().save(*args, **kwargs)
        self._delete_files_if_unreferenced(previous_files)

    def delete(self, *args, **kwargs):
        stored_files = [
            (getattr(self, field_name).storage, getattr(self, field_name).name)
            for field_name in self.MEDIA_FIELD_NAMES
            if getattr(self, field_name).name
        ]
        result = super().delete(*args, **kwargs)
        self._delete_files_if_unreferenced(stored_files)
        return result

    def get_target_url(self):
        portal = reverse("core:portal-publico")
        if self.tipo_enlace == self.TipoEnlace.DESTINO and self.lugar_turistico_id:
            return reverse(
                "core:destination-detail", args=[self.lugar_turistico.slug]
            )
        if self.tipo_enlace == self.TipoEnlace.TOUR and self.tour_id:
            return reverse("core:tour-detail", args=[self.tour.slug])
        if self.tipo_enlace == self.TipoEnlace.PERSONALIZADO:
            return self.url_personalizada or f"{portal}#cotizar"
        return f"{portal}#cotizar"

    @property
    def texto_boton_publico(self):
        return self.texto_boton.strip() or "Solicitar cotización"

    @property
    def descripcion_enlace(self):
        if self.tipo_enlace == self.TipoEnlace.DESTINO and self.lugar_turistico_id:
            return f"Artículo del destino: {self.lugar_turistico.nombre}"
        if self.tipo_enlace == self.TipoEnlace.TOUR and self.tour_id:
            return f"Detalle del tour: {self.tour.nombre_comercial}"
        if self.tipo_enlace == self.TipoEnlace.PERSONALIZADO:
            return self.url_personalizada or "Enlace pendiente"
        return "Formulario de cotización"


class Cotizacion(models.Model):
    class IdiomaDocumento(models.TextChoices):
        ESPANOL = "es", "Español"
        INGLES = "en", "English"

    class TipoCotizacion(models.TextChoices):
        VUELOS = "vuelos", "Vuelos"
        TOURS = "tours", "Tours"
        VUELOS_TOURS = "vuelos_tours", "Vuelos y Tours"

    class Estado(models.TextChoices):
        BORRADOR = "borrador", "Borrador"
        PENDIENTE = "pendiente", "Pendiente"
        ENVIADA = "enviada", "Enviada"
        NEGOCIACION = "negociacion", "En negociación"
        CONFIRMADA = "confirmada", "Confirmada"
        CANCELADA = "cancelada", "Cancelada"
        VENCIDA = "vencida", "Vencida"
        # Valores heredados conservados para registros existentes.
        APROBADA = "aprobada", "Aprobada"
        RECHAZADA = "rechazada", "Rechazada"

    asesor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="cotizaciones",
    )
    cliente_nombre = models.CharField(max_length=180)
    cliente_correo = models.EmailField()
    cliente_telefono = models.CharField(max_length=40, blank=True)
    idioma_documento = models.CharField(
        max_length=2,
        choices=IdiomaDocumento.choices,
        default=IdiomaDocumento.ESPANOL,
    )
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
        max_length=20,
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

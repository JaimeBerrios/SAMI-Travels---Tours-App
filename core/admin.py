from django.contrib import admin

from .models import (
    Cliente,
    Destino,
    PaqueteTuristico,
    Reserva,
    Servicio,
    SolicitudContacto,
    Viajero,
)


@admin.register(SolicitudContacto)
class SolicitudContactoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "contacto", "servicio", "destino", "atendida", "creado_en")
    list_filter = ("atendida", "servicio", "creado_en")
    search_fields = ("nombre", "contacto", "destino", "detalles")
    readonly_fields = ("creado_en", "actualizado_en")


@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ("nombre", "activo")
    list_filter = ("activo",)
    search_fields = ("nombre",)


@admin.register(Destino)
class DestinoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "ciudad", "pais", "activo")
    list_filter = ("pais", "activo")
    search_fields = ("nombre", "ciudad", "pais")


@admin.register(PaqueteTuristico)
class PaqueteTuristicoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "destino", "duracion_dias", "precio_base", "activo")
    list_filter = ("activo", "destino__pais")
    search_fields = ("nombre", "destino__nombre", "destino__pais")
    filter_horizontal = ("servicios",)


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("nombres", "apellidos", "correo", "telefono", "activo")
    list_filter = ("activo",)
    search_fields = ("nombres", "apellidos", "correo", "telefono")


class ViajeroInline(admin.TabularInline):
    model = Viajero
    extra = 0


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "cliente",
        "estado",
        "fecha_salida",
        "cantidad_viajeros",
        "precio_total",
    )
    list_filter = ("estado", "fecha_salida")
    search_fields = ("cliente__nombres", "cliente__apellidos", "cliente__correo")
    autocomplete_fields = ("cliente", "paquete", "destino")
    inlines = (ViajeroInline,)


@admin.register(Viajero)
class ViajeroAdmin(admin.ModelAdmin):
    list_display = ("nombres", "apellidos", "reserva", "es_titular")
    list_filter = ("es_titular",)
    search_fields = ("nombres", "apellidos", "numero_pasaporte")

from django.contrib import admin

from .models import (
    Cotizacion,
    Departamento,
    HistorialCotizacion,
    LugarTuristico,
    Pais,
    Tour,
)


@admin.register(Pais)
class PaisAdmin(admin.ModelAdmin):
    list_display = ("nombre", "activo", "actualizado_en")
    list_filter = ("activo",)
    search_fields = ("nombre",)


@admin.register(Departamento)
class DepartamentoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "pais", "activo")
    list_filter = ("activo", "pais")
    search_fields = ("nombre", "pais__nombre")


@admin.register(LugarTuristico)
class LugarTuristicoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "departamento", "activo")
    list_filter = ("activo", "departamento__pais")
    search_fields = ("nombre", "departamento__nombre", "departamento__pais__nombre")


@admin.register(Tour)
class TourAdmin(admin.ModelAdmin):
    list_display = ("nombre_comercial", "lugar_turistico", "precio_base", "activo")
    list_filter = ("activo", "lugar_turistico__departamento__pais")
    search_fields = ("nombre_comercial", "lugar_turistico__nombre")


@admin.register(Cotizacion)
class CotizacionAdmin(admin.ModelAdmin):
    list_display = ("id", "cliente_nombre", "tipo_cotizacion", "estado", "archivada")
    list_filter = ("tipo_cotizacion", "estado", "archivada")
    search_fields = ("cliente_nombre", "cliente_correo", "destino")


@admin.register(HistorialCotizacion)
class HistorialCotizacionAdmin(admin.ModelAdmin):
    list_display = ("cotizacion", "accion", "usuario", "estado", "creado_en")
    list_filter = ("accion", "estado")
    readonly_fields = ("cotizacion", "usuario", "accion", "estado", "datos", "creado_en")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

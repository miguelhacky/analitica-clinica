from django.contrib import admin
from .models import Paciente, RegistroClinico, Prediccion, ContagiousDisease


class PacienteAdmin(admin.ModelAdmin):
    filter_horizontal = ('enfermedades_contagiosas',)
    list_display = ('id_paciente', 'nombres', 'apellidos', 'edad', 'riesgo_enfermedad', 'estado', 'ubicacion', 'piso', 'listar_enfermedades')
    list_filter = ('estado', 'riesgo_enfermedad', 'ubicacion')
    search_fields = ('id_paciente', 'nombres', 'apellidos')

    def listar_enfermedades(self, obj):
        return ', '.join(d.nombre for d in obj.enfermedades_contagiosas.all()[:5])
    listar_enfermedades.short_description = 'Enf. Contagiosas'


admin.site.register(Paciente, PacienteAdmin)
admin.site.register(RegistroClinico)
admin.site.register(Prediccion)
admin.site.register(ContagiousDisease)

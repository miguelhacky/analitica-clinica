from django.contrib import admin
from .models import Paciente, RegistroClinico, Prediccion

admin.site.register(Paciente)
admin.site.register(RegistroClinico)
admin.site.register(Prediccion)

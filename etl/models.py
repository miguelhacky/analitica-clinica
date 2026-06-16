from django.db import models
from django.conf import settings


class HistorialETL(models.Model):
    fecha = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    archivo = models.CharField('Archivo', max_length=255)
    registros_procesados = models.IntegerField(default=0)
    registros_limpios = models.IntegerField(default=0)
    tiempo_ejecucion = models.FloatField('Tiempo ejecución (s)', default=0)
    estado = models.CharField('Estado', max_length=20, default='Completado')
    logs = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = 'Historial ETL'
        verbose_name_plural = 'Historiales ETL'
        ordering = ['-fecha']

    def __str__(self):
        return f"ETL {self.fecha} - {self.estado} ({self.registros_procesados} registros)"

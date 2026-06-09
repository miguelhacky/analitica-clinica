from django.db import models
from django.conf import settings


class ContagiousDisease(models.Model):
    nombre = models.CharField('Nombre', max_length=100, unique=True)
    descripcion = models.TextField('Descripción', blank=True, null=True)

    class Meta:
        verbose_name = 'Enfermedad Contagiosa'
        verbose_name_plural = 'Enfermedades Contagiosas'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Paciente(models.Model):
    id_paciente = models.CharField('ID Paciente', max_length=20, unique=True)
    nombres = models.CharField('Nombres', max_length=100)
    apellidos = models.CharField('Apellidos', max_length=100)
    edad = models.IntegerField('Edad')
    sexo = models.CharField('Sexo', max_length=10)
    peso = models.FloatField('Peso (kg)')
    altura = models.FloatField('Altura (m)')
    IMC = models.FloatField('IMC', null=True, blank=True)
    presion_sistolica = models.IntegerField('Presión Sistólica')
    presion_diastolica = models.IntegerField('Presión Diastólica')
    frecuencia_cardiaca = models.IntegerField('Frecuencia Cardíaca')
    glucosa = models.FloatField('Glucosa')
    colesterol = models.FloatField('Colesterol')
    saturacion_oxigeno = models.FloatField('Saturación Oxígeno')
    temperatura = models.FloatField('Temperatura')
    antecedentes_familiares = models.CharField('Antecedentes Familiares', max_length=200, blank=True, null=True)
    fumador = models.CharField('Fumador', max_length=2)
    consumo_alcohol = models.CharField('Consumo Alcohol', max_length=2)
    actividad_fisica = models.CharField('Actividad Física', max_length=50)
    diagnostico_preliminar = models.CharField('Diagnóstico Preliminar', max_length=200, blank=True, null=True)
    enfermedades_contagiosas = models.ManyToManyField(ContagiousDisease, verbose_name='Enfermedades Contagiosas', blank=True)
    riesgo_enfermedad = models.CharField('Riesgo Enfermedad', max_length=20)
    estado = models.CharField('Estado', max_length=20, choices=[
        ('Activo', 'Activo'),
        ('Hospitalizado', 'Hospitalizado'),
        ('Dado de Alta', 'Dado de Alta'),
        ('Fallecido', 'Fallecido'),
    ], default='Activo')
    ubicacion = models.CharField('Ubicación', max_length=50, choices=[
        ('Urgencias', 'Urgencias'),
        ('Hospitalización', 'Hospitalización'),
        ('UCI', 'UCI'),
        ('Cirugía', 'Cirugía'),
        ('Consulta Externa', 'Consulta Externa'),
    ], default='Consulta Externa')
    piso = models.IntegerField('Piso', null=True, blank=True)
    necesidades_cuidado = models.TextField('Necesidades de Cuidado', blank=True, null=True,
        help_text='Ej: Oxígeno, Cambio de suero, Medicación, Monitoreo constante, etc.')
    fecha_alta = models.DateField('Fecha de Alta', null=True, blank=True)
    fecha_fallecimiento = models.DateField('Fecha de Fallecimiento', null=True, blank=True)
    fecha_consulta = models.DateField('Fecha Consulta')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Paciente'
        verbose_name_plural = 'Pacientes'
        ordering = ['-fecha_consulta']

    def __str__(self):
        return f"{self.id_paciente} - {self.nombres} {self.apellidos}"


class RegistroClinico(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='registros')
    fecha_registro = models.DateTimeField(auto_now_add=True)
    descripcion = models.TextField()
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name = 'Registro Clínico'
        verbose_name_plural = 'Registros Clínicos'

    def __str__(self):
        return f"Registro de {self.paciente} - {self.fecha_registro}"


class Prediccion(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='predicciones')
    riesgo_predicho = models.CharField('Riesgo Predicho', max_length=20)
    probabilidad = models.FloatField('Probabilidad')
    modelo = models.CharField('Modelo', max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Predicción'
        verbose_name_plural = 'Predicciones'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.paciente} - {self.riesgo_predicho} ({self.probabilidad:.2%})"

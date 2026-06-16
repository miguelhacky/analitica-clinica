from rest_framework import serializers
from .models import Paciente, Prediccion, ContagiousDisease


class ContagiousDiseaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContagiousDisease
        fields = ['id', 'nombre']


class PacienteSerializer(serializers.ModelSerializer):
    enfermedades_contagiosas_nombres = serializers.SerializerMethodField()

    class Meta:
        model = Paciente
        fields = ['id', 'id_paciente', 'nombres', 'apellidos', 'edad', 'sexo', 'peso', 'altura',
                  'IMC', 'presion_sistolica', 'presion_diastolica', 'frecuencia_cardiaca',
                  'glucosa', 'colesterol', 'saturacion_oxigeno', 'temperatura',
                  'antecedentes_familiares', 'fumador', 'consumo_alcohol', 'actividad_fisica',
                  'diagnostico_preliminar', 'enfermedades_contagiosas',
                  'enfermedades_contagiosas_nombres', 'riesgo_enfermedad', 'estado',
                  'ubicacion', 'piso', 'necesidades_cuidado',
                  'fecha_alta', 'fecha_fallecimiento', 'fecha_consulta', 'created_at', 'updated_at']

    def get_enfermedades_contagiosas_nombres(self, obj):
        return [d.nombre for d in obj.enfermedades_contagiosas.all()]


class PrediccionSerializer(serializers.ModelSerializer):
    paciente_id = serializers.CharField(source='paciente.id_paciente', read_only=True)
    paciente_nombre = serializers.SerializerMethodField()
    estado = serializers.SerializerMethodField()
    enfermedades_contagiosas = serializers.SerializerMethodField()

    class Meta:
        model = Prediccion
        fields = '__all__'

    def get_paciente_nombre(self, obj):
        return f"{obj.paciente.nombres} {obj.paciente.apellidos}"

    def get_estado(self, obj):
        return obj.paciente.estado

    def get_enfermedades_contagiosas(self, obj):
        return list(obj.paciente.enfermedades_contagiosas.values_list('nombre', flat=True))

from rest_framework import serializers
from .models import Paciente, Prediccion


class PacienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Paciente
        fields = '__all__'


class PrediccionSerializer(serializers.ModelSerializer):
    paciente_id = serializers.IntegerField(source='paciente.id_paciente', read_only=True)
    paciente_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Prediccion
        fields = '__all__'

    def get_paciente_nombre(self, obj):
        return f"{obj.paciente.nombres} {obj.paciente.apellidos}"

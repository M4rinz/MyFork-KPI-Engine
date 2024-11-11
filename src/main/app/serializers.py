from rest_framework import serializers


# Serializer to format the KPI model into JSON
class KPIResultSerializer(serializers.ModelSerializer):
    """Serializer to format the KPI result of a request into JSON."""

    kpi_name = serializers.CharField(max_length=100)
    kpi_machine = serializers.CharField(max_length=100)
    kpi_value = serializers.FloatField()

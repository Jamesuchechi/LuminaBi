from rest_framework import serializers
from .models import Visualization


class VisualizationSerializer(serializers.ModelSerializer):
    owner = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Visualization
        fields = [
            'id',
            'owner',
            'title',
            'description',
            'chart_type',
            'config',
            'dataset',
            'created_at',
            'updated_at',
            'is_public',
        ]
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']

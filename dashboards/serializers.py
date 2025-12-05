from rest_framework import serializers
from .models import Dashboard
from visualizations.models import Visualization


class DashboardSerializer(serializers.ModelSerializer):
    owner = serializers.StringRelatedField(read_only=True)
    visualizations = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Visualization.objects.all(), required=False
    )

    class Meta:
        model = Dashboard
        fields = [
            'id',
            'owner',
            'name',
            'description',
            'layout',
            'visualizations',
            'created_at',
            'updated_at',
            'is_published',
        ]
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']

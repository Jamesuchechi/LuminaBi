from rest_framework import serializers
from .models import Dashboard
from visualizations.serializers import VisualizationSerializer


class DashboardSerializer(serializers.ModelSerializer):
    owner = serializers.StringRelatedField(read_only=True)
    visualizations = serializers.PrimaryKeyRelatedField(
        many=True, queryset=None, required=False
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Delay setting the queryset to avoid import timing issues
        from visualizations.models import Visualization

        self.fields['visualizations'].queryset = Visualization.objects.all()

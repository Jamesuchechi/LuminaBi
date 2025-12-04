from rest_framework import serializers
from .models import Dataset


class DatasetSerializer(serializers.ModelSerializer):
    owner = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Dataset
        fields = [
            'id',
            'owner',
            'name',
            'description',
            'file',
            'cleaned_file',
            'uploaded_at',
            'row_count',
            'col_count',
            'metadata',
            'is_cleaned',
        ]
        read_only_fields = ['id', 'owner', 'uploaded_at', 'is_cleaned']

from rest_framework import serializers
from .models import Organization, Setting
from django.conf import settings


class OrganizationSerializer(serializers.ModelSerializer):
    owner = serializers.StringRelatedField(read_only=True)
    members = serializers.PrimaryKeyRelatedField(
        many=True, queryset=settings.AUTH_USER_MODEL and None, required=False
    )

    class Meta:
        model = Organization
        fields = [
            'id',
            'name',
            'slug',
            'owner',
            'members',
            'metadata',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'slug', 'owner', 'created_at', 'updated_at']


class SettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Setting
        fields = ['id', 'key', 'value', 'site_wide', 'updated_at']
        read_only_fields = ['id', 'updated_at']

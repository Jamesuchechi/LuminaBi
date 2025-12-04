from django.contrib import admin
from .models import Organization, Setting


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'owner', 'created_at')
    search_fields = ('name', 'owner__username')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Setting)
class SettingAdmin(admin.ModelAdmin):
    list_display = ('id', 'key', 'site_wide', 'updated_at')
    search_fields = ('key',)
from django.contrib import admin

# Register your models here.

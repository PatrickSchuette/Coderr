from django.contrib import admin

from profile_app.models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """Admin configuration for the Profile model."""

    list_display = ('user', 'type', 'first_name', 'last_name', 'created_at')
    list_filter = ('type',)
    search_fields = ('user__username', 'first_name', 'last_name')

from django.contrib import admin

from reviews_app.models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """Admin configuration for the Review model."""

    list_display = ('business_user', 'reviewer', 'rating', 'created_at')
    list_filter = ('rating',)
    search_fields = ('business_user__username', 'reviewer__username', 'description')

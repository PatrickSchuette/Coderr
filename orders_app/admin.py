from django.contrib import admin

from orders_app.models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Admin configuration for the Order model."""

    list_display = ('id', 'title', 'customer_user','business_user', 'status', 'price', 'created_at')
    list_filter = ('status', 'offer_type')
    search_fields = ('title', 'customer_user__username','business_user__username')

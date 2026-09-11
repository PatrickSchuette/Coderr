from django.contrib import admin

# Register your models here.
from django.contrib import admin

from offers_app.models import Offer, OfferDetail


class OfferDetailInline(admin.TabularInline):
    """Inline editor for an Offer's pricing tiers in the admin."""

    model = OfferDetail
    extra = 0


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    """Admin configuration for the Offer model."""

    list_display = ('title', 'user', 'created_at', 'updated_at')
    list_filter = ('created_at',)
    search_fields = ('title', 'description', 'user__username')
    inlines = [OfferDetailInline]


@admin.register(OfferDetail)
class OfferDetailAdmin(admin.ModelAdmin):
    """Admin configuration for the OfferDetail model."""

    list_display = ('offer', 'offer_type', 'price', 'delivery_time_in_days')
    list_filter = ('offer_type',)

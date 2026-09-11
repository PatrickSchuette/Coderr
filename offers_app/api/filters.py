import django_filters

from offers_app.models import Offer


class OfferFilter(django_filters.FilterSet):
    """Supports filtering the offer list by creator, min price, and max delivery time."""

    creator_id = django_filters.NumberFilter(field_name='user_id')
    min_price = django_filters.NumberFilter(field_name='min_price', lookup_expr='gte')
    max_delivery_time = django_filters.NumberFilter(field_name='min_delivery_time', lookup_expr='lte')

    class Meta:
        model = Offer
        fields = ['creator_id', 'min_price', 'max_delivery_time']

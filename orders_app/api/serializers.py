from django.shortcuts import get_object_or_404
from rest_framework import serializers

from offers_app.models import OfferDetail
from orders_app.models import Order


class OrderSerializer(serializers.ModelSerializer):
    """Full read representation of an order, used for GET /api/orders/."""

    price = serializers.DecimalField(
        max_digits=10, decimal_places=2, coerce_to_string=False)

    class Meta:
        model = Order
        fields = ['id', 'customer_user', 'business_user', 'title', 'revisions', 'delivery_time_in_days', 'price', 'features', 'offer_type', 'status', 'created_at', 'updated_at']
        read_only_fields = fields


class OrderCreateSerializer(serializers.ModelSerializer):
    """Serializer for POST /api/orders/ - creates an order from an OfferDetail."""

    offer_detail_id = serializers.IntegerField(write_only=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, coerce_to_string=False, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'customer_user', 'business_user', 'title', 'revisions', 'delivery_time_in_days', 'price', 'features', 'offer_type', 'status', 'created_at', 'updated_at', 'offer_detail_id']
        read_only_fields = ['id', 'customer_user', 'business_user', 'title', 'revisions', 'delivery_time_in_days', 'features', 'offer_type', 'status', 'created_at', 'updated_at']

    def create(self, validated_data: dict) -> Order:
        """Look up the referenced OfferDetail and freeze its data into a new order."""
        offer_detail_id = validated_data.pop('offer_detail_id')
        offer_detail = get_object_or_404(OfferDetail, id=offer_detail_id)
        request = self.context['request']
        return Order.objects.create(
            customer_user=request.user,
            business_user=offer_detail.offer.user,
            title=offer_detail.title,
            revisions=offer_detail.revisions,
            delivery_time_in_days=offer_detail.delivery_time_in_days,
            price=offer_detail.price,
            features=offer_detail.features,
            offer_type=offer_detail.offer_type,
        )


class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    """Serializer for PATCH /api/orders/{id}/ - only the status field is writable."""

    price = serializers.DecimalField(
        max_digits=10, decimal_places=2, coerce_to_string=False, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'customer_user', 'business_user', 'title', 'revisions', 'delivery_time_in_days', 'price', 'features', 'offer_type', 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'customer_user', 'business_user', 'title', 'revisions', 'delivery_time_in_days', 'features', 'offer_type', 'created_at', 'updated_at']

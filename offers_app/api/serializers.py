from rest_framework import serializers

from offers_app.models import Offer, OfferDetail


class OfferDetailWriteSerializer(serializers.ModelSerializer):
    """Full representation of a single pricing tier.

    Used for nested create/update payloads and responses, and for the
    standalone GET /api/offerdetails/{id}/ endpoint.
    """

    price = serializers.DecimalField(
        max_digits=10, decimal_places=2, coerce_to_string=False)

    class Meta:
        model = OfferDetail
        fields = ['id', 'title', 'revisions','delivery_time_in_days', 'price', 'features', 'offer_type']
        read_only_fields = ['id']


class OfferDetailLinkSerializer(serializers.ModelSerializer):
    """Minimal {id, url} representation of a pricing tier, used inside offer list/retrieve."""

    url = serializers.SerializerMethodField()

    class Meta:
        model = OfferDetail
        fields = ['id', 'url']

    def get_url(self, obj: OfferDetail) -> str:
        """Build the absolute URL pointing to this offer detail's own endpoint."""
        request = self.context.get('request')
        path = f'/offerdetails/{obj.id}/'
        return request.build_absolute_uri(path) if request else path


class OfferListSerializer(serializers.ModelSerializer):
    """Serializer for GET /api/offers/ - includes aggregated price/delivery info."""

    details = OfferDetailLinkSerializer(many=True, read_only=True)
    min_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True, coerce_to_string=False)
    min_delivery_time = serializers.IntegerField(read_only=True)
    user_details = serializers.SerializerMethodField()

    class Meta:
        model = Offer
        fields = ['id', 'user', 'title', 'image', 'description', 'created_at', 'updated_at','details', 'min_price', 'min_delivery_time', 'user_details',]

    def get_user_details(self, obj: Offer) -> dict:
        """Return a small summary of the offer creator, pulled from their profile."""
        profile = getattr(obj.user, 'profile', None)
        return {
            'first_name': profile.first_name if profile else '',
            'last_name': profile.last_name if profile else '',
            'username': obj.user.username,
        }


class OfferRetrieveSerializer(serializers.ModelSerializer):
    """Serializer for GET /api/offers/{id}/."""

    details = OfferDetailLinkSerializer(many=True, read_only=True)
    min_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True, coerce_to_string=False)
    min_delivery_time = serializers.IntegerField(read_only=True)

    class Meta:
        model = Offer
        fields = ['id', 'user', 'title', 'image', 'description', 'created_at', 'updated_at','details', 'min_price', 'min_delivery_time',]


class OfferCreateSerializer(serializers.ModelSerializer):
    """Serializer for POST /api/offers/ - requires exactly 3 nested details."""

    details = OfferDetailWriteSerializer(many=True)

    class Meta:
        model = Offer
        fields = ['id', 'title', 'image', 'description', 'details']

    def validate_details(self, value: list) -> list:
        """Ensure exactly one basic, one standard, and one premium tier are provided."""
        if len(value) != 3:
            raise serializers.ValidationError('An offer must include exactly 3 details.')
        offer_types = {detail['offer_type'] for detail in value}
        if offer_types != {'basic', 'standard', 'premium'}:
            raise serializers.ValidationError('Details must include exactly one basic, one standard, and one premium tier.')
        return value

    def create(self, validated_data: dict) -> Offer:
        """Create the offer and its three nested details in one step."""
        details_data = validated_data.pop('details')
        request = self.context['request']
        offer = Offer.objects.create(user=request.user, **validated_data)
        OfferDetail.objects.bulk_create(
            [OfferDetail(offer=offer, **detail_data)
             for detail_data in details_data]
        )
        return offer


class OfferUpdateSerializer(serializers.ModelSerializer):
    """Serializer for PATCH /api/offers/{id}/ - allows partial updates, including per-tier detail edits."""

    details = OfferDetailWriteSerializer(many=True, required=False)

    class Meta:
        model = Offer
        fields = ['id', 'title', 'image', 'description', 'details']

    def update(self, instance: Offer, validated_data: dict) -> Offer:
        """Update the offer's own fields and, if provided, matching detail tiers by offer_type."""
        details_data = validated_data.pop('details', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if details_data:
            for detail_data in details_data:
                detail = instance.details.filter(offer_type=detail_data.get('offer_type')).first()
                if detail is None:
                    continue
                for attr, value in detail_data.items():
                    setattr(detail, attr, value)
                detail.save()

        return instance

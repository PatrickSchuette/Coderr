from rest_framework import serializers

from profile_app.models import Profile
from reviews_app.models import Review


class ReviewSerializer(serializers.ModelSerializer):
    """Read representation of a review, used for GET /api/reviews/."""

    class Meta:
        model = Review
        fields = ['id', 'business_user', 'reviewer', 'rating', 'description', 'created_at', 'updated_at']
        read_only_fields = fields


class ReviewCreateSerializer(serializers.ModelSerializer):
    """Serializer for POST /api/reviews/.

    The reviewer is taken from the authenticated user automatically, and a
    manual check enforces one review per business user per reviewer.
    """

    class Meta:
        model = Review
        fields = ['id', 'business_user', 'reviewer', 'rating', 'description', 'created_at', 'updated_at']
        read_only_fields = ['id', 'reviewer', 'created_at', 'updated_at']

    def validate_business_user(self, value) -> object:
        """Ensure the target user actually has a business profile."""
        profile = getattr(value, 'profile', None)
        if not profile or profile.type != Profile.ProfileType.BUSINESS:
            raise serializers.ValidationError('The selected user is not a business user.')
        return value

    def validate(self, attrs: dict) -> dict:
        """Ensure the requester has not already reviewed this business user."""
        reviewer = self.context['request'].user
        business_user = attrs.get('business_user')
        if Review.objects.filter(business_user=business_user, reviewer=reviewer).exists():
            raise serializers.ValidationError('You have already reviewed this business user.')
        return attrs

    def create(self, validated_data: dict) -> Review:
        """Attach the authenticated user as the reviewer before saving."""
        validated_data['reviewer'] = self.context['request'].user
        return super().create(validated_data)

class ReviewUpdateSerializer(serializers.ModelSerializer):
    """Serializer for PATCH /api/reviews/{id}/ - only rating and description are writable."""

    class Meta:
        model = Review
        fields = ['id', 'business_user', 'reviewer', 'rating', 'description', 'created_at', 'updated_at']
        read_only_fields = ['id', 'business_user', 'reviewer', 'created_at', 'updated_at']

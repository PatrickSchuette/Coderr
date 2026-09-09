from rest_framework import serializers

from profile_app.models import Profile


class ProfileDetailSerializer(serializers.ModelSerializer):
    """Serializer for GET/PATCH /api/profile/{pk}/ - full profile data."""

    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', required=False)

    class Meta:
        model = Profile
        fields = ['user', 'username', 'first_name', 'last_name', 'file','location', 'tel', 'description', 'working_hours','type', 'email', 'created_at',]
        read_only_fields = ['user', 'type', 'created_at']

    def update(self, instance: Profile, validated_data: dict) -> Profile:
        """Update the profile and, if provided, the related user's email."""
        user_data = validated_data.pop('user', None)
        if user_data and 'email' in user_data:
            instance.user.email = user_data['email']
            instance.user.save()
        return super().update(instance, validated_data)


class BusinessProfileListSerializer(serializers.ModelSerializer):
    """Serializer for GET /api/profiles/business/."""

    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Profile
        fields = ['user', 'username', 'first_name', 'last_name', 'file','location', 'tel', 'description', 'working_hours', 'type',]


class CustomerProfileListSerializer(serializers.ModelSerializer):
    """Serializer for GET /api/profiles/customer/."""

    username = serializers.CharField(source='user.username', read_only=True)
    uploaded_at = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = Profile
        fields = ['user', 'username', 'first_name', 'last_name', 'file', 'uploaded_at', 'type']

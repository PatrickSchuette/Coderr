from django.contrib.auth.models import User
from rest_framework import serializers

from profile_app.models import Profile


class RegistrationSerializer(serializers.ModelSerializer):
    """Serializer for creating a new user account plus its matching profile."""

    repeated_password = serializers.CharField(write_only=True)
    type = serializers.ChoiceField(choices=Profile.ProfileType.choices, write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'repeated_password', 'type']
        extra_kwargs = {'password': {'write_only': True}}

    def validate(self, attrs: dict) -> dict:
        """Ensure both password fields match before object creation."""
        if attrs['password'] != attrs['repeated_password']:
            raise serializers.ValidationError({'password': 'Passwords do not match.'})
        return attrs

    def create(self, validated_data: dict) -> User:
        """Create the user and its associated profile in one step."""
        profile_type = validated_data.pop('type')
        validated_data.pop('repeated_password')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
        )
        Profile.objects.create(user=user, type=profile_type)
        return user
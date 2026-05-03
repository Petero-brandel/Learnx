from rest_framework import serializers, exceptions
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['email', 'full_name', 'phone_number', 'password']
        extra_kwargs = {
            'full_name': {'required': False, 'allow_blank': True},
            'phone_number': {'required': False, 'allow_blank': True}
        }

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            full_name=validated_data.get('full_name', ''),
            phone_number=validated_data.get('phone_number', ''),
        )
        return user

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        
        if not self.user.is_email_verified:
            raise exceptions.AuthenticationFailed(
                'Please verify your email address before logging in.',
                'email_unverified'
            )
            
        return data


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'phone_number', 'profile_photo', 'is_staff', 'is_superuser', 'date_joined']
        read_only_fields = ['id', 'email', 'is_staff', 'is_superuser', 'date_joined']


class GoogleAuthSerializer(serializers.Serializer):
    """Accepts a Google OAuth credential (id_token) or access_token from the frontend."""
    credential = serializers.CharField(required=False, allow_blank=True)
    access_token = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        if not data.get('credential') and not data.get('access_token'):
            raise serializers.ValidationError("Either credential or access_token must be provided.")
        return data

from django.contrib.auth.password_validation import validate_password

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

class PasswordResetConfirmSerializer(serializers.Serializer):
    uidb64 = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value

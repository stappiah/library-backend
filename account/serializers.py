import os

from django.conf import settings
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, PasswordResetToken


def _should_enforce_email_domain():
    """Check env var — only enforce university email domain when explicitly enabled."""
    return os.environ.get("RESTRICT_TO_UNIVERSITY_EMAIL", "false").lower() in ("true", "1", "yes")


class CurrentUserProfileSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='user.id', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True, allow_null=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True, allow_null=True)
    name = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    plan = serializers.SerializerMethodField()
    joined = serializers.SerializerMethodField()
    avatarUrl = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = [
            'id', 'email', 'first_name', 'last_name', 'name', 'role', 'plan', 'joined', 'avatarUrl',
            'phone_number', 'address', 'city', 'state', 'bio', 'profile_picture', 'faculty', 'is_verified'
        ]

    def get_name(self, obj):
        full_name = obj.user.get_full_name()
        return full_name if full_name else obj.user.email.split('@')[0]

    def get_role(self, obj):
        return obj.role or 'customer'

    def get_plan(self, obj):
        role = (obj.role or 'customer').lower()
        return 'Vendor Pro' if role == 'vendor' else 'Admin' if role in ('admin', 'superadmin') else 'Student'

    def get_joined(self, obj):
        return obj.user.date_joined.isoformat()

    def get_avatarUrl(self, obj):
        if not obj.profile_picture:
            return None
        try:
            url = obj.profile_picture.url
            request = self.context.get('request')
            return request.build_absolute_uri(url) if request else url
        except Exception:
            return None


class UserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'name', 'role']

    def get_role(self, obj):
        return getattr(getattr(obj, 'profile', None), 'role', 'customer')

    def get_name(self, obj):
        name = obj.get_full_name()
        return name if name else obj.email.split('@')[0]


class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'user_id', 'phone_number', 'address', 'city',
            'state', 'bio', 'profile_picture',
            'role', 'is_verified', 'faculty', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    password2 = serializers.CharField(write_only=True, required=True, min_length=8)
    role = serializers.CharField(required=False, default='customer')

    class Meta:
        model = User
        fields = ['email', 'password', 'password2', 'first_name', 'last_name', 'role']

    def validate_email(self, value):
        if _should_enforce_email_domain():
            domain = settings.UNIVERSITY_EMAIL_DOMAIN.lower().lstrip("@")
            email_value = value.lower()

            if not email_value.endswith(f"@{domain}"):
                raise serializers.ValidationError(
                    f"Registration is restricted to {domain} email addresses."
                )

        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({'password': 'Passwords must match.'})
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        email = validated_data.pop('email')
        role = validated_data.pop('role', 'customer')

        normalized_role = role.strip().lower()
        # Map frontend-friendly role values to match the backend choices
        if normalized_role in ['vendor', 'professor']:
            normalized_role = 'vendor'
        elif normalized_role in ['customer', 'student']:
            normalized_role = 'customer'
        else:
            normalized_role = 'customer'

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            **validated_data
        )

        # Create user profile (ensure no unique constraint collisions)
        # Carry over profile fields if provided in registration payload.
        profile_defaults = {
            'role': normalized_role,
        }
        for field in ["phone_number", "address", "city", "state", "bio", "profile_picture", "faculty", "is_verified"]:
            if field in self.initial_data:
                profile_defaults[field] = self.initial_data[field]

        UserProfile.objects.update_or_create(user=user, defaults=profile_defaults)

        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password2 = serializers.CharField(write_only=True, min_length=8)

    def validate(self, data):
        if data['new_password'] != data['new_password2']:
            raise serializers.ValidationError({'new_password': 'Passwords must match.'})
        return data


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField()
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({'password': 'Passwords must match.'})
        return data

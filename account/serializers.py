from django.conf import settings
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, PasswordResetToken


class UserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'name', 'role']

    def get_role(self, obj):
        return getattr(getattr(obj, 'profile', None), 'role', 'student')

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
    role = serializers.CharField(required=False, default='student')

    class Meta:
        model = User
        fields = ['email', 'password', 'password2', 'first_name', 'last_name', 'role']

    def validate_email(self, value):
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
        role = validated_data.pop('role', 'student')

        normalized_role = role.strip().lower()
        if normalized_role in ['vendor', 'professor']:
            normalized_role = 'professor'
        elif normalized_role in ['customer', 'student']:
            normalized_role = 'student'
        else:
            normalized_role = 'student'

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

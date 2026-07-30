import os
import uuid
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import UserProfile, PasswordResetToken
from .serializers import (
    RegisterSerializer, LoginSerializer, UserSerializer,
    UserProfileSerializer, ChangePasswordSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer,
    CurrentUserProfileSerializer
)


def authenticate_user(request, email, password):
    user = User.objects.filter(email__iexact=email).first()
    if user is None:
        user = User.objects.filter(username__iexact=email).first()

    if user is None:
        return None

    if not user.is_active:
        return None

    # Only enforce university email domain if the env var is explicitly set
    # Set RESTRICT_TO_UNIVERSITY_EMAIL=true to enable this check
    restrict_email = os.environ.get("RESTRICT_TO_UNIVERSITY_EMAIL", "false").lower()
    if restrict_email in ("true", "1", "yes"):
        allowed_domain = getattr(settings, "UNIVERSITY_EMAIL_DOMAIN", "ktu.edu").lower().lstrip("@")
        if not user.email.lower().endswith(f"@{allowed_domain}"):
            return None

    return authenticate(request=request, username=user.username, password=password)


class EmailTokenObtainPairView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response(
                {'error': 'email and password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        auth_user = authenticate_user(request, email, password)
        if auth_user is None:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(auth_user)
        return Response({
            'message': 'Login successful',
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(auth_user).data
        })


class AuthViewSet(viewsets.ViewSet):
    """ViewSet for Authentication"""
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        """Register a new user"""
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response(
                {
                    'message': 'User created successfully',
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'user': UserSerializer(user).data
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):

        serializer = LoginSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        auth_user = authenticate_user(request, email, password)

        if auth_user is None:
            return Response(
                {"error": "Invalid credentials"},
                status=401
            )

        refresh = RefreshToken.for_user(auth_user)

        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": UserSerializer(auth_user).data
        })

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        """Logout user (refresh token blacklist would go here)"""
        return Response({'message': 'Logout successful'})

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Get current user profile in a shape the frontend expects."""
        try:
            profile = request.user.profile
        except (ObjectDoesNotExist, UserProfile.DoesNotExist):
            profile = UserProfile.objects.create(user=request.user, role='customer')

        serializer = CurrentUserProfileSerializer(profile, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def change_password(self, request):
        """Change user password"""
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if not user.check_password(serializer.validated_data['old_password']):
                return Response(
                    {'error': 'Old password is incorrect'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({'message': 'Password changed successfully'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def forgot_password(self, request):
        """Request password reset"""
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email=email)
                token = str(uuid.uuid4())
                expires_at = timezone.now() + timedelta(hours=24)

                PasswordResetToken.objects.create(
                    user=user,
                    token=token,
                    expires_at=expires_at
                )

                # Here you would send an email with the reset link
                return Response({
                    'message': 'Password reset email sent',
                    'token': token  # In production, don't return this; send via email
                })
            except User.DoesNotExist:
                # Don't reveal if email exists for security
                return Response({
                    'message': 'If an account with this email exists, a reset link will be sent'
                })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def reset_password(self, request):
        """Reset password with token"""
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data['token']

            try:
                reset_token = PasswordResetToken.objects.get(
                    token=token,
                    is_used=False
                )

                if timezone.now() > reset_token.expires_at:
                    return Response(
                        {'error': 'Reset token has expired'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                user = reset_token.user
                user.set_password(serializer.validated_data['password'])
                user.save()

                reset_token.is_used = True
                reset_token.save()

                return Response({'message': 'Password reset successfully'})
            except PasswordResetToken.DoesNotExist:
                return Response(
                    {'error': 'Invalid or expired reset token'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileViewSet(viewsets.ModelViewSet):
    """ViewSet for User Profiles"""
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Only allow users to see their own profile
        return UserProfile.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def my_profile(self, request):
        """Get current user's profile"""
        try:
            profile = request.user.profile
            serializer = UserProfileSerializer(profile)
            return Response(serializer.data)
        except (ObjectDoesNotExist, UserProfile.DoesNotExist):
            return Response(
                {'error': 'Profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['patch'])
    def update_profile(self, request):
        """Update current user's profile"""
        try:
            profile = request.user.profile
            serializer = UserProfileSerializer(profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except (ObjectDoesNotExist, UserProfile.DoesNotExist):
            return Response(
                {'error': 'Profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )


from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from .models import UserProfile
from .serializers import RegisterSerializer, UserSerializer


class RegisterSerializerTests(TestCase):
    def test_register_serializer_saves_phone_number_to_profile_without_username(self):
        data = {
            'email': 'john@example.com',
            'password': 'pass1234',
            'password2': 'pass1234',
            'phone_number': '+15551234567'
        }

        serializer = RegisterSerializer(data=data)

        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()

        profile = UserProfile.objects.get(user=user)
        self.assertEqual(profile.phone_number, data['phone_number'])
        self.assertEqual(user.username, data['email'])

    def test_user_serializer_does_not_expose_username(self):
        serializer = UserSerializer()
        self.assertNotIn('username', serializer.fields)


class AuthLoginTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_login_accepts_email_when_username_is_different(self):
        User = get_user_model()
        user = User.objects.create_user(
            username='library-user',
            email='user@example.com',
            password='strongpass123',
        )
        self.assertTrue(UserProfile.objects.filter(user=user).exists())

        response = self.client.post(
            '/api/v1/auth/login/',
            {'email': 'user@example.com', 'password': 'strongpass123'},
            format='json',
        )

        self.assertEqual(response.status_code, 200, response.data)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

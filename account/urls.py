from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import AuthViewSet, UserProfileViewSet
from .register_api import RegisterAPIView

router = DefaultRouter()
router.register(r'profiles', UserProfileViewSet, basename='profile')

urlpatterns = [
    path('', include(router.urls)),
    # Registration must be public (AllowAny).
    path('register/', RegisterAPIView.as_view(), name='register'),

    path('login/', AuthViewSet.as_view({'post': 'login'}), name='login'),

    path('logout/', AuthViewSet.as_view({'post': 'logout'}), name='logout'),
    path('me/', AuthViewSet.as_view({'get': 'me'}), name='me'),
    path('change-password/', AuthViewSet.as_view({'post': 'change_password'}), name='change-password'),
    path('forgot-password/', AuthViewSet.as_view({'post': 'forgot_password'}), name='forgot-password'),
    path('reset-password/', AuthViewSet.as_view({'post': 'reset_password'}), name='reset-password'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

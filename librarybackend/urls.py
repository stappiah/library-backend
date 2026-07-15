"""
URL configuration for librarybackend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include, re_path
from django.views.generic import TemplateView

from rest_framework_simplejwt.views import TokenRefreshView

from account.views import EmailTokenObtainPairView


class FrontendView(TemplateView):
    template_name = "frontend/index.html"


class ApiDocsView(TemplateView):
    template_name = "api/docs.html"


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", lambda request: JsonResponse({"status": "ok", "app": "Library App"})),
    path("api/docs/", ApiDocsView.as_view(), name="api_docs"),
    path("api/v1/auth/", include("account.urls")),
    path("api/v1/", include("base.urls")),
    path("api/token/", EmailTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    re_path(r"^(?!api/|admin/|static/|media/).*$", FrontendView.as_view(), name="frontend"),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


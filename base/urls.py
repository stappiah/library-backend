from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet, FacultyViewSet, VendorViewSet, BookViewSet,
    BookImageViewSet, CartViewSet, WishlistViewSet, OrderViewSet,
    ReviewViewSet, UserShopViewSet, DownloadViewSet
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'faculties', FacultyViewSet, basename='faculty')
router.register(r'vendors', VendorViewSet, basename='vendor')
router.register(r'user-shop', UserShopViewSet, basename='user-shop')
router.register(r'books', BookViewSet, basename='book')
router.register(r'book-images', BookImageViewSet, basename='book-image')
router.register(r'cart', CartViewSet, basename='cart')
router.register(r'wishlist', WishlistViewSet, basename='wishlist')
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'reviews', ReviewViewSet, basename='review')
router.register(
    r'downloads',
    DownloadViewSet,
    basename='download'
)

urlpatterns = [
    path('', include(router.urls)),
]

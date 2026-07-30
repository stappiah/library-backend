from django.contrib import admin
from .models import (
    Category, Faculty, Vendor, Book, BookImage, Order, OrderItem,
    Cart, CartItem, Wishlist, WishlistItem, Review
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'email', 'rating', 'is_active', 'created_at']
    list_filter = ['is_active', 'rating', 'created_at']
    search_fields = ['name', 'email', 'phone', 'address']
    prepopulated_fields = {'slug': ('name',)}


class BookImageInline(admin.TabularInline):
    model = BookImage


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'price', 'category', 'vendor', 'stock', 'rating', 'is_featured', 'created_at']
    list_filter = ['category', 'faculty', 'vendor', 'is_featured', 'created_at']
    search_fields = ['title', 'author', 'isbn']
    prepopulated_fields = {'slug': ('title',)}
    inlines = [BookImageInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'author', 'description')
        }),
        ('Pricing', {
            'fields': ('price', 'discount_price')
        }),
        ('Classification', {
            'fields': ('category', 'faculty', 'vendor')
        }),
        ('Details', {
            'fields': ('isbn', 'publisher', 'publication_year', 'pages', 'language')
        }),
        ('Media', {
            'fields': ('image', 'image_url')
        }),
        ('Status', {
            'fields': ('stock', 'rating', 'is_featured')
        }),
    )


@admin.register(BookImage)
class BookImageAdmin(admin.ModelAdmin):
    list_display = ['book', 'created_at']
    list_filter = ['created_at']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ['price', 'discount_price']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'user', 'total_price', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['order_number', 'user__username', 'email']
    inlines = [OrderItemInline]
    readonly_fields = ['order_number', 'created_at', 'updated_at']
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'user', 'status')
        }),
        ('Pricing', {
            'fields': ('total_price',)
        }),
        ('Shipping', {
            'fields': ('shipping_address', 'phone')
        }),
        ('Billing', {
            'fields': ('billing_address', 'email')
        }),
        ('Additional', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'book', 'quantity', 'price']
    list_filter = ['order__created_at']


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'item_count', 'total_price', 'created_at']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['cart', 'book', 'quantity']


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'item_count', 'created_at']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ['wishlist', 'book', 'added_at']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['book', 'user', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['book__title', 'user__username']
    readonly_fields = ['created_at', 'updated_at']


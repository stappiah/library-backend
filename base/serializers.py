from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Category, Faculty, Vendor, Book, BookImage, Order, OrderItem,
    Cart, CartItem, Wishlist, WishlistItem, Review
)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'image']


class FacultySerializer(serializers.ModelSerializer):
    class Meta:
        model = Faculty
        fields = ['id', 'name', 'slug', 'description']


class VendorSerializer(serializers.ModelSerializer):
    email = serializers.SerializerMethodField()
    rating = serializers.FloatField(read_only=True)
    products_count = serializers.SerializerMethodField()

    class Meta:
        model = Vendor
        fields = [
            'id', 'name', 'slug', 'description', 'email', 'logo',
            'phone', 'address', 'rating', 'products_count',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['rating', 'products_count']

    def get_email(self, obj):
        return obj.email or (obj.user.email if obj.user else '')

    def get_products_count(self, obj):
        return obj.books.count()


class BookImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookImage
        fields = ['id', 'image', 'alt_text']


class BookListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True, required=False, allow_null=True
    )
    category_slug = serializers.SlugRelatedField(
        queryset=Category.objects.all(),
        slug_field='slug',
        source='category',
        write_only=True,
        required=False,
        allow_null=True,
    )
    faculty = FacultySerializer(read_only=True)
    faculty_id = serializers.PrimaryKeyRelatedField(
        queryset=Faculty.objects.all(), source='faculty', write_only=True, required=False, allow_null=True
    )
    vendor = VendorSerializer(read_only=True)
    vendor_id = serializers.PrimaryKeyRelatedField(
        queryset=Vendor.objects.all(), source='vendor', write_only=True, required=False, allow_null=True
    )
    discount_percentage = serializers.ReadOnlyField()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = [
            'id', 'title', 'slug', 'author', 'description', 'price', 'discount_price',
            'category', 'category_id', 'category_slug', 'faculty', 'faculty_id', 'vendor', 'vendor_id',
            'image', 'image_url', 'rating', 'is_featured',
            'discount_percentage', 'stock'
        ]

    def get_image_url(self, obj):
        return obj.get_image_url_safe(self.context.get('request'))


class BookDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True, required=False, allow_null=True
    )
    category_slug = serializers.SlugRelatedField(
        queryset=Category.objects.all(),
        slug_field='slug',
        source='category',
        write_only=True,
        required=False,
        allow_null=True,
    )
    faculty = FacultySerializer(read_only=True)
    faculty_id = serializers.PrimaryKeyRelatedField(
        queryset=Faculty.objects.all(), source='faculty', write_only=True, required=False, allow_null=True
    )
    vendor = VendorSerializer(read_only=True)
    vendor_id = serializers.PrimaryKeyRelatedField(
        queryset=Vendor.objects.all(), source='vendor', write_only=True, required=False, allow_null=True
    )
    gallery_images = BookImageSerializer(many=True, read_only=True)
    reviews = serializers.SerializerMethodField()
    discount_percentage = serializers.ReadOnlyField()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = [
            'id', 'title', 'slug', 'author', 'description', 'price',
            'discount_price', 'category', 'category_id', 'category_slug', 'faculty', 'faculty_id', 'vendor', 'vendor_id', 'isbn', 'publisher',
            'publication_year', 'pages', 'language', 'stock', 'image',
            'image_url', 'rating', 'is_featured', 'discount_percentage',
            'gallery_images', 'reviews', 'created_at', 'updated_at'
        ]

    def get_image_url(self, obj):
        return obj.get_image_url_safe(self.context.get('request'))

    def get_reviews(self, obj):
        reviews = obj.reviews.all()
        return ReviewSerializer(reviews, many=True).data


class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'user', 'user_name', 'title', 'content', 'rating', 'helpful_count', 'created_at']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class CartItemSerializer(serializers.ModelSerializer):
    book = BookListSerializer(read_only=True)
    book_id = serializers.IntegerField(write_only=True)
    total = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['id', 'book', 'book_id', 'quantity', 'total', 'added_at']

    def get_total(self, obj):
        return obj.get_total()


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.ReadOnlyField()
    item_count = serializers.ReadOnlyField()

    class Meta:
        model = Cart
        fields = ['id', 'items', 'total_price', 'item_count', 'created_at', 'updated_at']


class WishlistItemSerializer(serializers.ModelSerializer):
    book = BookListSerializer(read_only=True)
    book_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = WishlistItem
        fields = ['id', 'book', 'book_id', 'added_at']


class WishlistSerializer(serializers.ModelSerializer):
    items = WishlistItemSerializer(many=True, read_only=True)
    item_count = serializers.ReadOnlyField()

    class Meta:
        model = Wishlist
        fields = ['id', 'items', 'item_count', 'created_at', 'updated_at']


class OrderItemSerializer(serializers.ModelSerializer):
    book = BookListSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'book', 'quantity', 'price', 'discount_price']


class OrderListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'total_price', 'status',
            'created_at', 'updated_at'
        ]


class OrderDetailSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'user', 'total_price', 'status',
            'shipping_address', 'billing_address', 'phone', 'email',
            'items', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['order_number', 'user', 'total_price', 'created_at', 'updated_at']

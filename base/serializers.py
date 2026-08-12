from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Category,
    Faculty,
    Vendor,
    Book,
    BookImage,
    Order,
    OrderItem,
    Cart,
    CartItem,
    Wishlist,
    WishlistItem,
    Review,
    Download,
)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description", "image"]


class FacultySerializer(serializers.ModelSerializer):
    class Meta:
        model = Faculty
        fields = ["id", "name", "slug", "description"]


class VendorSerializer(serializers.ModelSerializer):
    email = serializers.SerializerMethodField()
    rating = serializers.FloatField(read_only=True)
    products_count = serializers.SerializerMethodField()

    class Meta:
        model = Vendor
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "email",
            "logo",
            "phone",
            "address",
            "rating",
            "products_count",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["rating", "products_count"]

    def get_email(self, obj):
        return obj.email or (obj.user.email if obj.user else "")

    def get_products_count(self, obj):
        return obj.books.count()


class BookImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookImage
        fields = ["id", "image", "alt_text"]


class BookListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)

    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source="category",
        write_only=True,
        required=False,
        allow_null=True,
    )

    category_slug = serializers.SlugRelatedField(
        queryset=Category.objects.all(),
        slug_field="slug",
        source="category",
        write_only=True,
        required=False,
        allow_null=True,
    )

    faculty = FacultySerializer(read_only=True)

    faculty_id = serializers.PrimaryKeyRelatedField(
        queryset=Faculty.objects.all(),
        source="faculty",
        write_only=True,
        required=False,
        allow_null=True,
    )

    faculty_slug = serializers.SlugRelatedField(
        queryset=Faculty.objects.all(),
        slug_field="slug",
        source="faculty",
        write_only=True,
        required=False,
        allow_null=True,
    )

    vendor = VendorSerializer(read_only=True)

    discount_percentage = serializers.ReadOnlyField()
    image_url = serializers.SerializerMethodField()

    file_name = serializers.ReadOnlyField()
    file_size = serializers.ReadOnlyField()

    has_digital_file = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = [
            "id",
            "title",
            "slug",
            "author",
            "description",
            "price",
            "discount_price",
            "discount_percentage",
            "product_type",
            "category",
            "category_id",
            "category_slug",
            "faculty",
            "faculty_id",
            "faculty_slug",
            "vendor",
            "isbn",
            "publisher",
            "publication_year",
            "pages",
            "language",
            "image",
            "image_url",
            "digital_file",
            "file_name",
            "file_size",
            "has_digital_file",
            "download_limit",
            "download_expiry_days",
            "rating",
            "is_featured",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "slug",
            "vendor",
            "rating",
            "discount_percentage",
            "file_name",
            "file_size",
            "has_digital_file",
            "created_at",
            "updated_at",
        ]

    def get_image_url(self, obj):
        return obj.get_image_url_safe(self.context.get("request"))

    def get_has_digital_file(self, obj):
        return bool(obj.digital_file)


class BookDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)

    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source="category",
        write_only=True,
        required=False,
        allow_null=True,
    )

    category_slug = serializers.SlugRelatedField(
        queryset=Category.objects.all(),
        slug_field="slug",
        source="category",
        write_only=True,
        required=False,
        allow_null=True,
    )

    faculty = FacultySerializer(read_only=True)

    faculty_id = serializers.PrimaryKeyRelatedField(
        queryset=Faculty.objects.all(),
        source="faculty",
        write_only=True,
        required=False,
        allow_null=True,
    )

    faculty_slug = serializers.SlugRelatedField(
        queryset=Faculty.objects.all(),
        slug_field="slug",
        source="faculty",
        write_only=True,
        required=False,
        allow_null=True,
    )

    vendor = VendorSerializer(read_only=True)

    gallery_images = BookImageSerializer(many=True, read_only=True)

    reviews = serializers.SerializerMethodField()

    discount_percentage = serializers.ReadOnlyField()
    image_url = serializers.SerializerMethodField()

    file_name = serializers.ReadOnlyField()
    file_size = serializers.ReadOnlyField()

    has_digital_file = serializers.SerializerMethodField()

    class Meta:
        model = Book

        fields = [
            "id",
            "title",
            "slug",
            "author",
            "description",
            "price",
            "discount_price",
            "discount_percentage",
            "product_type",
            "category",
            "category_id",
            "category_slug",
            "faculty",
            "faculty_id",
            "faculty_slug",
            "vendor",
            "isbn",
            "publisher",
            "publication_year",
            "pages",
            "language",
            "image",
            "image_url",
            "digital_file",
            "file_name",
            "file_size",
            "has_digital_file",
            "download_limit",
            "download_expiry_days",
            "rating",
            "is_featured",
            "gallery_images",
            "reviews",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "slug",
            "vendor",
            "rating",
            "discount_percentage",
            "file_name",
            "file_size",
            "has_digital_file",
            "gallery_images",
            "reviews",
            "created_at",
            "updated_at",
        ]

    def get_image_url(self, obj):
        return obj.get_image_url_safe(self.context.get("request"))

    def get_has_digital_file(self, obj):
        return bool(obj.digital_file)

    def get_reviews(self, obj):
        reviews = obj.reviews.all()

        return ReviewSerializer(
            reviews,
            many=True,
            context=self.context,
        ).data

    def validate(self, attrs):
        product_type = attrs.get(
            "product_type",
            getattr(self.instance, "product_type", "ebook"),
        )

        digital_file = attrs.get("digital_file")

        # For new ebook products, require an actual file.
        if self.instance is None and product_type == "ebook":
            if not digital_file:
                raise serializers.ValidationError(
                    {"digital_file": "An ebook file is required."}
                )

        # Validate discount.
        price = attrs.get(
            "price",
            getattr(self.instance, "price", None),
        )

        discount_price = attrs.get(
            "discount_price",
            getattr(self.instance, "discount_price", None),
        )

        if price is not None and discount_price is not None and discount_price >= price:
            raise serializers.ValidationError(
                {
                    "discount_price": "Discount price must be lower than the original price."
                }
            )

        return attrs


class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.get_full_name", read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Review
        fields = [
            "id",
            "user",
            "user_name",
            "title",
            "content",
            "rating",
            "helpful_count",
            "created_at",
        ]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class CartItemSerializer(serializers.ModelSerializer):
    book = BookListSerializer(read_only=True)
    book_id = serializers.IntegerField(write_only=True)
    total = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ["id", "book", "book_id", "quantity", "total", "added_at"]

    def get_total(self, obj):
        return obj.get_total()


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.ReadOnlyField()
    item_count = serializers.ReadOnlyField()

    class Meta:
        model = Cart
        fields = [
            "id",
            "items",
            "total_price",
            "item_count",
            "created_at",
            "updated_at",
        ]


class WishlistItemSerializer(serializers.ModelSerializer):
    book = BookListSerializer(read_only=True)
    book_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = WishlistItem
        fields = ["id", "book", "book_id", "added_at"]


class WishlistSerializer(serializers.ModelSerializer):
    items = WishlistItemSerializer(many=True, read_only=True)
    item_count = serializers.ReadOnlyField()

    class Meta:
        model = Wishlist
        fields = ["id", "items", "item_count", "created_at", "updated_at"]


class OrderItemSerializer(serializers.ModelSerializer):
    book = BookListSerializer(read_only=True)
    line_total = serializers.ReadOnlyField()

    class Meta:
        model = OrderItem
        fields = ["id", "book", "quantity", "price", "discount_price", "line_total"]


class OrderListSerializer(serializers.ModelSerializer):
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "total_price",
            "status",
            "item_count",
            "created_at",
            "updated_at",
        ]

    def get_item_count(self, obj):
        return obj.items.count()


class OrderDetailSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user_name = serializers.CharField(source="user.get_full_name", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "user",
            "user_name",
            "total_price",
            "status",
            "email",
            "items",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "order_number",
            "user",
            "total_price",
            "created_at",
            "updated_at",
        ]


class DownloadSerializer(serializers.ModelSerializer):
    book = BookListSerializer(read_only=True)
    order_number = serializers.CharField(source="order.order_number", read_only=True)
    remaining_downloads = serializers.SerializerMethodField()

    class Meta:
        model = Download
        fields = [
            "id",
            "book",
            "order_number",
            "downloads",
            "max_downloads",
            "remaining_downloads",
            "expires_at",
            "is_expired",
            "is_exhausted",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_remaining_downloads(self, obj):
        if obj.max_downloads <= 0:
            return None  # unlimited
        return max(0, obj.max_downloads - obj.downloads)

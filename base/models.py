from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.utils.text import slugify
import uuid

PRODUCT_TYPES = (
    ("ebook", "Ebook"),
    ("notes", "Lecture Notes"),
    ("template", "Template"),
    ("software", "Software"),
    ("course", "Course Material"),
)


def build_slug(source: str, pk: int | None = None) -> str:
    base_slug = slugify(source) or "item"
    if pk:
        return f"{base_slug}-{pk}"

    return f"{base_slug}-{uuid.uuid4().hex[:8]}"


class Category(models.Model):
    """Book Category Model"""

    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to="categories/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = build_slug(self.name, self.pk)
            if not self.pk:
                super().save(*args, **kwargs)
                self.slug = build_slug(self.name, self.pk)
                super().save(update_fields=["slug"])
                return

        super().save(*args, **kwargs)


class Faculty(models.Model):
    """Faculty/Department Model"""

    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Faculties"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = build_slug(self.name, self.pk)
            if not self.pk:
                super().save(*args, **kwargs)
                self.slug = build_slug(self.name, self.pk)
                super().save(update_fields=["slug"])
                return

        super().save(*args, **kwargs)


class Vendor(models.Model):
    """Vendor/Store profile for multi-vendor book marketplace."""

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="professor"
    )
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    logo = models.ImageField(upload_to="vendors/", blank=True, null=True)
    email = models.EmailField(
        blank=True,
        null=True,
        help_text="Vendor contact email (falls back to user email)",
    )
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    rating = models.FloatField(
        default=0.0, validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = build_slug(self.name, self.pk)
            if not self.pk:
                super().save(*args, **kwargs)
                self.slug = build_slug(self.name, self.pk)
                super().save(update_fields=["slug"])
                return

        super().save(*args, **kwargs)


class Book(models.Model):
    """Book / Digital Product Model"""

    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    author = models.CharField(max_length=255)
    description = models.TextField()

    price = models.DecimalField(max_digits=10, decimal_places=2)

    product_type = models.CharField(
        max_length=20, choices=PRODUCT_TYPES, default="ebook"
    )

    discount_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )

    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, related_name="books"
    )

    faculty = models.ForeignKey(
        Faculty, on_delete=models.SET_NULL, null=True, blank=True, related_name="books"
    )

    vendor = models.ForeignKey(
        Vendor, on_delete=models.SET_NULL, null=True, blank=True, related_name="books"
    )

    isbn = models.CharField(max_length=20, unique=True, blank=True, null=True)

    publisher = models.CharField(max_length=255, blank=True, null=True)

    publication_year = models.IntegerField(blank=True, null=True)

    pages = models.IntegerField(blank=True, null=True)

    language = models.CharField(max_length=50, default="English")

    # ---------------------------------------------------------
    # BOOK COVER
    # ---------------------------------------------------------

    image = models.ImageField(upload_to="books/", blank=True, null=True)

    image_url = models.URLField(blank=True, null=True, help_text="External image URL.")

    # ---------------------------------------------------------
    # DIGITAL PRODUCT
    # ---------------------------------------------------------

    digital_file = models.FileField(
        upload_to="ebooks/",
        blank=True,
        null=True,
        help_text="Private ebook/document file.",
    )

    file_name = models.CharField(max_length=255, blank=True, null=True, editable=False)

    file_size = models.BigIntegerField(
        blank=True, null=True, editable=False, help_text="File size in bytes."
    )

    has_digital_file = models.BooleanField(default=False, editable=False)

    # Cloudinary asset identifier.
    # This is more useful for generating signed download URLs
    # than exposing digital_file.url directly.
    cloudinary_public_id = models.CharField(
        max_length=500, blank=True, null=True, editable=False
    )

    # ---------------------------------------------------------
    # DOWNLOAD SETTINGS
    # ---------------------------------------------------------

    download_limit = models.PositiveIntegerField(
        default=3, help_text="Maximum downloads allowed per purchased item."
    )

    download_expiry_days = models.PositiveIntegerField(
        default=10,
        help_text="Number of days download access remains valid after purchase.",
    )

    # ---------------------------------------------------------
    # OTHER
    # ---------------------------------------------------------

    rating = models.FloatField(
        default=0, validators=[MinValueValidator(0), MaxValueValidator(5)]
    )

    is_featured = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["category"]),
            models.Index(fields=["product_type"]),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = build_slug(self.title, self.pk)

            if not self.pk:
                super().save(*args, **kwargs)

                self.slug = build_slug(self.title, self.pk)

                super().save(update_fields=["slug"])

                return

        # Keep digital file metadata in sync
        if self.digital_file:
            self.has_digital_file = True

            try:
                self.file_name = self.digital_file.name.split("/")[-1]
            except Exception:
                self.file_name = None

            try:
                self.file_size = self.digital_file.size
            except Exception:
                self.file_size = None

        else:
            self.has_digital_file = False
            self.file_name = None
            self.file_size = None

        super().save(*args, **kwargs)

    @property
    def discount_percentage(self):
        if self.discount_price and self.price:
            return int(((self.price - self.discount_price) / self.price) * 100)

        return 0

    @property
    def effective_price(self):
        """Return the actual selling price."""
        return self.discount_price if self.discount_price is not None else self.price

    def get_image_url_safe(self, request=None):
        """
        Return the best available image URL.

        Priority:
        1. `image_url` (explicit external URL)
        2. Cloudinary canonical URL when enabled
        3. Storage-provided URL
        4. None
        """

        if self.image_url:
            return self.image_url

        if not self.image:
            return None

        try:
            from django.conf import settings

            # If Cloudinary is enabled, prefer canonical Cloudinary URL
            if getattr(settings, "CLOUDINARY_ENABLED", False):
                try:
                    import cloudinary.utils

                    public_id = getattr(self.image, "name", None)
                    if public_id and "." in public_id:
                        public_id = public_id.rsplit(".", 1)[0]

                    if public_id:
                        url, _ = cloudinary.utils.cloudinary_url(
                            public_id, resource_type="image", secure=True
                        )
                        return request.build_absolute_uri(url) if request else url
                except Exception:
                    # ignore and fall back to storage URL
                    pass

            # Fallback to storage-provided URL
            try:
                url = self.image.url
                return request.build_absolute_uri(url) if request else url
            except Exception:
                return None
        except Exception:
            return None

    def get_digital_file_url(self, request=None):
        """Return an absolute URL for the digital file when possible.

        Preference order:
        1. Cloudinary canonical URL (resource_type='raw' for docs)
        2. `digital_file.url`
        3. `default_storage.url(name)`
        4. None
        """
        if not self.digital_file:
            return None

        try:
            from django.core.files.storage import default_storage
            from django.conf import settings

            if getattr(settings, "CLOUDINARY_ENABLED", False):
                try:
                    import cloudinary.utils

                    public_id = getattr(self.digital_file, "name", None)
                    if public_id and "." in public_id:
                        ext = public_id.rsplit(".", 1)[1].lower()
                        public_id_no_ext = public_id.rsplit(".", 1)[0]
                    else:
                        ext = None
                        public_id_no_ext = public_id

                    raw_exts = {"pdf", "epub", "mobi", "zip", "doc", "docx", "txt"}
                    resource_type = "raw" if ext in raw_exts else "auto"

                    if public_id_no_ext:
                        url, _ = cloudinary.utils.cloudinary_url(
                            public_id_no_ext, resource_type=resource_type, secure=True
                        )
                        return request.build_absolute_uri(url) if request else url
                except Exception:
                    pass

            # Fallbacks
            try:
                url = self.digital_file.url
            except Exception:
                try:
                    url = default_storage.url(self.digital_file.name)
                except Exception:
                    url = None

            return request.build_absolute_uri(url) if request and url else url
        except Exception:
            return None


class BookImage(models.Model):
    """Additional Book Images for Gallery"""

    book = models.ForeignKey(
        Book, on_delete=models.CASCADE, related_name="gallery_images"
    )
    image = models.ImageField(upload_to="books/gallery/")
    alt_text = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Image for {self.book.title}"


class Order(models.Model):
    """Order Model"""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
        ("refunded", "Refunded"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    order_number = models.CharField(max_length=20, unique=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="paid")
    email = models.EmailField()
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order {self.order_number}"


class OrderItem(models.Model):
    """Individual Digital Products in an Order"""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # entitlement snapshot
    download_limit = models.PositiveIntegerField(default=3)
    download_expiry_days = models.PositiveIntegerField(default=10)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("order", "book")

    def __str__(self):
        return f"{self.book.title} in Order {self.order.order_number}"

    @property
    def line_total(self):
        unit_price = self.discount_price if self.discount_price is not None else self.price
        return unit_price * self.quantity

    @property
    def is_digital(self):
        return self.book.product_type in ["ebook", "notes", "template", "software", "course"]


class Cart(models.Model):
    """Shopping Cart Model"""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="cart")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart for {self.user.username}"

    @property
    def total_price(self):
        return sum(item.get_total() for item in self.items.all())

    @property
    def item_count(self):
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    """Items in Shopping Cart"""

    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("cart", "book")

    def __str__(self):
        return f"{self.book.title} in {self.cart.user.username}'s cart"

    def get_total(self):
        price = (
            self.book.discount_price if self.book.discount_price else self.book.price
        )
        return price * self.quantity


class Wishlist(models.Model):
    """Wishlist Model"""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="wishlist")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Wishlist for {self.user.username}"

    @property
    def item_count(self):
        return self.items.count()


class WishlistItem(models.Model):
    """Items in Wishlist"""

    wishlist = models.ForeignKey(
        Wishlist, on_delete=models.CASCADE, related_name="items"
    )
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("wishlist", "book")

    def __str__(self):
        return f"{self.book.title} in {self.wishlist.user.username}'s wishlist"


class Review(models.Model):
    """Book Review Model"""

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    content = models.TextField()
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    helpful_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("book", "user")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Review by {self.user.username} for {self.book.title}"


class Download(models.Model):
    """
    Tracks download entitlement for a purchased digital product.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="downloads")

    order_item = models.OneToOneField(
        OrderItem, on_delete=models.CASCADE, related_name="download"
    )

    downloads = models.PositiveIntegerField(default=0)

    max_downloads = models.PositiveIntegerField(default=3)

    expires_at = models.DateTimeField(null=True, blank=True)

    last_downloaded_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self):
        return f"{self.user.username} -> " f"{self.order_item.book.title}"

    @property
    def book(self):
        return self.order_item.book

    @property
    def order(self):
        return self.order_item.order

    @property
    def downloads_remaining(self):
        if self.max_downloads == 0:
            return None

        return max(self.max_downloads - self.downloads, 0)

    @property
    def is_expired(self):
        return self.expires_at is not None and timezone.now() >= self.expires_at

    @property
    def is_exhausted(self):
        return self.max_downloads > 0 and self.downloads >= self.max_downloads

    @property
    def can_download(self):
        return (
            not self.is_expired
            and not self.is_exhausted
            and self.order.status == "paid"
            and self.book.has_digital_file
        )

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
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = build_slug(self.name, self.pk)
            if not self.pk:
                super().save(*args, **kwargs)
                self.slug = build_slug(self.name, self.pk)
                super().save(update_fields=['slug'])
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
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = build_slug(self.name, self.pk)
            if not self.pk:
                super().save(*args, **kwargs)
                self.slug = build_slug(self.name, self.pk)
                super().save(update_fields=['slug'])
                return

        super().save(*args, **kwargs)


class Vendor(models.Model):
    """Vendor/Store profile for multi-vendor book marketplace."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='professor')
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    logo = models.ImageField(upload_to='vendors/', blank=True, null=True)
    email = models.EmailField(blank=True, null=True, help_text="Vendor contact email (falls back to user email)")
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    rating = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(5)])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = build_slug(self.name, self.pk)
            if not self.pk:
                super().save(*args, **kwargs)
                self.slug = build_slug(self.name, self.pk)
                super().save(update_fields=['slug'])
                return

        super().save(*args, **kwargs)


class Book(models.Model):
    """Book/Product Model"""
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    author = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPES, default='ebook')
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='books')
    faculty = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True, related_name='books')
    vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, blank=True, related_name='books')
    isbn = models.CharField(max_length=20, unique=True, blank=True, null=True)
    publisher = models.CharField(max_length=255, blank=True, null=True)
    publication_year = models.IntegerField(blank=True, null=True)
    pages = models.IntegerField(blank=True, null=True)
    language = models.CharField(max_length=50, default='English')
    image = models.ImageField(upload_to='books/', blank=True, null=True)
    image_url = models.URLField(
        blank=True, null=True,
        help_text="External image URL (e.g. Cloudinary/ImgBB). Takes priority over uploaded image."
    )
    digital_file = models.FileField(
        upload_to="products/files/",
        blank=True, null=True,
        help_text="The digital product file (ebook PDF, notes, template, software archive, etc.)"
    )
    download_limit = models.PositiveIntegerField(default=5, help_text="Maximum number of allowed downloads per purchase")
    download_expiry_days = models.PositiveIntegerField(default=30, help_text="Number of days the download link is valid after purchase")
    rating = models.FloatField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['category']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = build_slug(self.title, self.pk)
            if not self.pk:
                super().save(*args, **kwargs)
                self.slug = build_slug(self.title, self.pk)
                super().save(update_fields=['slug'])
                return

        super().save(*args, **kwargs)

    @property
    def discount_percentage(self):
        if self.discount_price and self.price:
            return int(((self.price - self.discount_price) / self.price) * 100)
        return 0

    @property
    def file_name(self):
        """Filename of the digital product (basename of stored file)."""
        if self.digital_file:
            return self.digital_file.name.split("/")[-1]
        return None

    @property
    def file_size(self):
        """Size of the digital product file in bytes (or None)."""
        if self.digital_file:
            try:
                return self.digital_file.size
            except Exception:
                return None
        return None

    def get_image_url_safe(self, request=None):
        """Return the best available image URL.
        
        Priority:
        1. `image_url` (external URL like Cloudinary/ImgBB)
        2. `image.url` (local upload or Cloudinary if DEFAULT_FILE_STORAGE is cloudinary)
        3. None
        """
        if self.image_url:
            return self.image_url
        if self.image:
            try:
                url = self.image.url
                # If the URL looks local (starts with MEDIA_URL) but Cloudinary
                # is enabled, return a Cloudinary fetch URL using the absolute
                # URL so Cloudinary can retrieve and serve it.
                from django.conf import settings
                import logging

                if url and request:
                    abs_url = request.build_absolute_uri(url)
                else:
                    abs_url = url

                # If Cloudinary is enabled and the current URL is a local media
                # path, return a Cloudinary fetch URL pointing to the absolute URL.
                if (
                    getattr(settings, "CLOUDINARY_ENABLED", False)
                    and abs_url
                    and (str(url).startswith(str(settings.MEDIA_URL)) or "/media/" in str(url))
                    and settings.CLOUDINARY_CLOUD_NAME
                ):
                    cloud_name = settings.CLOUDINARY_CLOUD_NAME
                    fetch_url = f"https://res.cloudinary.com/{cloud_name}/image/fetch/{abs_url}"
                    return fetch_url

                if abs_url:
                    return abs_url
                return None
            except Exception:
                return None
        return None


class BookImage(models.Model):
    """Additional Book Images for Gallery"""
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='gallery_images')
    image = models.ImageField(upload_to='books/gallery/')
    alt_text = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

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

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    order_number = models.CharField(max_length=20, unique=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    email = models.EmailField()
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order {self.order_number}"


class OrderItem(models.Model):
    """Individual Digital Products in an Order"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    @property
    def line_total(self):
        unit_price = self.discount_price if self.discount_price else self.price
        return unit_price * self.quantity

    class Meta:
        unique_together = ('order', 'book')

    def __str__(self):
        return f"{self.book.title} in Order {self.order.order_number}"


class Cart(models.Model):
    """Shopping Cart Model"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
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
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cart', 'book')

    def __str__(self):
        return f"{self.book.title} in {self.cart.user.username}'s cart"

    def get_total(self):
        price = self.book.discount_price if self.book.discount_price else self.book.price
        return price * self.quantity


class Wishlist(models.Model):
    """Wishlist Model"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wishlist')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Wishlist for {self.user.username}"

    @property
    def item_count(self):
        return self.items.count()


class WishlistItem(models.Model):
    """Items in Wishlist"""
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name='items')
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('wishlist', 'book')

    def __str__(self):
        return f"{self.book.title} in {self.wishlist.user.username}'s wishlist"


class Review(models.Model):
    """Book Review Model"""
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    content = models.TextField()
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    helpful_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('book', 'user')
        ordering = ['-created_at']

    def __str__(self):
        return f"Review by {self.user.username} for {self.book.title}"


class Download(models.Model):
    """Tracks a user's download rights for a purchased digital product."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='downloads')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='downloads')
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='downloads')
    downloads = models.PositiveIntegerField(default=0)
    max_downloads = models.PositiveIntegerField(default=5)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'book', 'order')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} -> {self.book.title}"

    @property
    def is_expired(self):
        return self.expires_at is not None and timezone.now() > self.expires_at

    @property
    def is_exhausted(self):
        return self.max_downloads > 0 and self.downloads >= self.max_downloads

    def can_download(self):
        return not self.is_expired and not self.is_exhausted

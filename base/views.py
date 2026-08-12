from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser, JSONParser
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.exceptions import PermissionDenied, NotFound
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone

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
from .serializers import (
    CategorySerializer,
    FacultySerializer,
    VendorSerializer,
    BookListSerializer,
    BookDetailSerializer,
    BookImageSerializer,
    CartSerializer,
    CartItemSerializer,
    WishlistSerializer,
    WishlistItemSerializer,
    OrderListSerializer,
    OrderDetailSerializer,
    ReviewSerializer,
    DownloadSerializer,
)


class CategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for Book Categories"""

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = "slug"
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at"]


class FacultyViewSet(viewsets.ModelViewSet):
    """ViewSet for Faculties"""

    queryset = Faculty.objects.all()
    serializer_class = FacultySerializer
    lookup_field = "slug"
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at"]


class VendorViewSet(viewsets.ModelViewSet):
    """ViewSet for vendors in the multi-vendor bookstore."""

    queryset = Vendor.objects.filter(is_active=True)
    serializer_class = VendorSerializer
    lookup_field = "slug"
    search_fields = ["name", "description", "address"]
    ordering_fields = ["name", "created_at"]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["get"])
    def books(self, request, slug=None):
        """Get books sold by a specific vendor."""
        vendor = self.get_object()
        books = Book.objects.filter(vendor=vendor).select_related(
            "category", "faculty", "vendor"
        )
        serializer = BookListSerializer(books, many=True, context={"request": request})
        return Response(serializer.data)


class UserShopViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):

        try:
            vendor = Vendor.objects.get(user=request.user, is_active=True)

            serializer = VendorSerializer(
                vendor,
                context={"request": request}
            )

            return Response(serializer.data)

        except Vendor.DoesNotExist:
            return Response(
                {
                    "error": "You do not have a shop.",
                    "user_id": request.user.id,
                    "email": request.user.email,
                },
                status=status.HTTP_404_NOT_FOUND,
            )


class BookViewSet(viewsets.ModelViewSet):
    """ViewSet for Books/Products"""

    queryset = Book.objects.select_related("category", "faculty", "vendor")
    serializer_class = BookListSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    search_fields = ["title", "author", "description", "isbn"]
    ordering_fields = ["price", "rating", "created_at", "title"]
    lookup_field = "slug"
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]

    def get_serializer_class(self):
        if self.action in ["retrieve", "update", "partial_update"]:
            return BookDetailSerializer
        return BookListSerializer

    def perform_create(self, serializer):
        vendor = None
        if self.request.user.is_authenticated:
            vendor = Vendor.objects.filter(user=self.request.user).first()

        book = serializer.save(vendor=vendor)

        gallery_files = self.request.FILES.getlist("gallery_images")
        for image_file in gallery_files:
            BookImage.objects.create(book=book, image=image_file)

    def get_queryset(self):
        queryset = self.queryset

        # Filter by category
        category_slug = self.request.query_params.get("category", None)
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        # Filter by faculty
        faculty_slug = self.request.query_params.get("faculty", None)
        if faculty_slug:
            queryset = queryset.filter(faculty__slug=faculty_slug)

        # Filter by vendor
        vendor_slug = self.request.query_params.get("vendor", None)
        if vendor_slug:
            queryset = queryset.filter(vendor__slug=vendor_slug)

        # Filter by price range
        min_price = self.request.query_params.get("min_price", None)
        max_price = self.request.query_params.get("max_price", None)
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        # Filter by rating
        min_rating = self.request.query_params.get("min_rating", None)
        if min_rating:
            queryset = queryset.filter(rating__gte=min_rating)

        # Filter featured books
        is_featured = self.request.query_params.get("featured", None)
        if is_featured == "true":
            queryset = queryset.filter(is_featured=True)
        elif is_featured == "false":
            queryset = queryset.filter(is_featured=False)

        # Filter by digital product type (ebook, notes, template, software, course)
        product_type = self.request.query_params.get(
            "type", self.request.query_params.get("product_type", None)
        )
        if product_type:
            queryset = queryset.filter(product_type=product_type)

        # Only show products that have a downloadable file when requested
        has_file = self.request.query_params.get("has_file", None)
        if has_file == "true":
            queryset = queryset.exclude(digital_file="").exclude(
                digital_file__isnull=True
            )
        elif has_file == "false":
            queryset = queryset.filter(digital_file="") | queryset.filter(
                digital_file__isnull=True
            )

        return queryset.distinct()

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def add_to_cart(self, request, slug=None):
        """Add book to cart"""
        book = self.get_object()
        cart, _ = Cart.objects.get_or_create(user=request.user)

        quantity = request.data.get("quantity", 1)
        try:
            quantity = int(quantity)
            if quantity <= 0:
                return Response(
                    {"error": "Quantity must be positive"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid quantity"}, status=status.HTTP_400_BAD_REQUEST
            )

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart, book=book, defaults={"quantity": quantity}
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        return Response({"message": "Added to cart"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def add_to_wishlist(self, request, slug=None):
        """Add book to wishlist"""
        book = self.get_object()
        wishlist, _ = Wishlist.objects.get_or_create(user=request.user)

        wishlist_item, created = WishlistItem.objects.get_or_create(
            wishlist=wishlist, book=book
        )

        if created:
            return Response(
                {"message": "Added to wishlist"}, status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                {"message": "Already in wishlist"}, status=status.HTTP_200_OK
            )

    @action(detail=True, methods=["get"])
    def reviews(self, request, slug=None):
        """Get reviews for a book"""
        book = self.get_object()
        reviews = book.reviews.all()
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated])
    def download(self, request, slug=None):
        """Securely stream a purchased digital product file to the user.

        Requires:
        - An active `Download` entitlement (created when an order is placed)
        - The download must not be expired or have exhausted its limit
        """
        book = self.get_object()

        try:
            entitlement = Download.objects.get(user=request.user, book=book)
        except Download.DoesNotExist:
            raise NotFound("You must purchase this product before downloading it.")

        if not entitlement.can_download():
            if entitlement.is_expired:
                raise PermissionDenied("Your download link has expired.")
            raise PermissionDenied(
                "You have reached the maximum number of downloads for this product."
            )

        if not book.digital_file:
            raise NotFound("No digital file is attached to this product yet.")

        # Increment the download counter before streaming.
        entitlement.downloads += 1
        entitlement.save(update_fields=["downloads", "updated_at"])

        file_name = book.file_name or f"{book.slug or 'download'}.file"
        response = FileResponse(
            book.digital_file.open("rb"),
            as_attachment=True,
            filename=file_name,
        )
        return response


class BookImageViewSet(viewsets.ModelViewSet):
    """ViewSet for Book Images"""

    queryset = BookImage.objects.all()
    serializer_class = BookImageSerializer

    def get_queryset(self):
        book_id = self.request.query_params.get("book_id", None)
        if book_id:
            return BookImage.objects.filter(book_id=book_id)
        return self.queryset


class CartViewSet(viewsets.ViewSet):
    """ViewSet for Shopping Cart"""

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"])
    def get_cart(self, request):
        """Get user's cart"""
        cart, _ = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def add_item(self, request):
        """Add item to cart"""
        cart, _ = Cart.objects.get_or_create(user=request.user)

        book_id = request.data.get("book_id")
        quantity = request.data.get("quantity", 1)

        try:
            quantity = int(quantity)
            if quantity <= 0:
                return Response(
                    {"error": "Quantity must be positive"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid quantity"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            return Response(
                {"error": "Book not found"}, status=status.HTTP_404_NOT_FOUND
            )

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart, book=book, defaults={"quantity": quantity}
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        return Response(CartSerializer(cart).data)

    @action(detail=False, methods=["post"])
    def remove_item(self, request):
        """Remove item from cart"""
        cart = get_object_or_404(Cart, user=request.user)

        book_id = request.data.get("book_id")
        try:
            cart_item = CartItem.objects.get(cart=cart, book_id=book_id)
            cart_item.delete()
            return Response(CartSerializer(cart).data)
        except CartItem.DoesNotExist:
            return Response(
                {"error": "Item not in cart"}, status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=["post"])
    def update_item(self, request):
        """Update quantity of item in cart"""
        cart = get_object_or_404(Cart, user=request.user)

        book_id = request.data.get("book_id")
        quantity = request.data.get("quantity", 1)

        try:
            quantity = int(quantity)
            if quantity <= 0:
                return Response(
                    {"error": "Quantity must be positive"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid quantity"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            cart_item = CartItem.objects.get(cart=cart, book_id=book_id)
            cart_item.quantity = quantity
            cart_item.save()
            return Response(CartSerializer(cart).data)
        except CartItem.DoesNotExist:
            return Response(
                {"error": "Item not in cart"}, status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=["post"])
    def clear_cart(self, request):
        """Clear entire cart"""
        cart = get_object_or_404(Cart, user=request.user)
        cart.items.all().delete()
        return Response({"message": "Cart cleared"})


class WishlistViewSet(viewsets.ViewSet):
    """ViewSet for Wishlist"""

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"])
    def get_wishlist(self, request):
        """Get user's wishlist"""
        wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
        serializer = WishlistSerializer(wishlist)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def add_item(self, request):
        """Add item to wishlist"""
        wishlist, _ = Wishlist.objects.get_or_create(user=request.user)

        book_id = request.data.get("book_id")
        try:
            book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            return Response(
                {"error": "Book not found"}, status=status.HTTP_404_NOT_FOUND
            )

        wishlist_item, created = WishlistItem.objects.get_or_create(
            wishlist=wishlist, book=book
        )

        if created:
            return Response(
                WishlistSerializer(wishlist).data, status=status.HTTP_201_CREATED
            )
        else:
            return Response(WishlistSerializer(wishlist).data)

    @action(detail=False, methods=["post"])
    def remove_item(self, request):
        """Remove item from wishlist"""
        wishlist = get_object_or_404(Wishlist, user=request.user)

        book_id = request.data.get("book_id")
        try:
            wishlist_item = WishlistItem.objects.get(wishlist=wishlist, book_id=book_id)
            wishlist_item.delete()
            return Response(WishlistSerializer(wishlist).data)
        except WishlistItem.DoesNotExist:
            return Response(
                {"error": "Item not in wishlist"}, status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=["post"])
    def clear_wishlist(self, request):
        """Clear entire wishlist"""
        wishlist = get_object_or_404(Wishlist, user=request.user)
        wishlist.items.all().delete()
        return Response({"message": "Wishlist cleared"})


class OrderViewSet(viewsets.ModelViewSet):
    """ViewSet for Orders"""

    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["created_at", "total_price"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "retrieve":
            return OrderDetailSerializer
        return OrderListSerializer

    def create(self, request, *args, **kwargs):
        """Create a new digital order from the cart or from a direct order payload."""
        email = request.data.get("email", request.user.email)
        notes = request.data.get("notes", "")
        items_data = request.data.get("items", None)

        order_items = []
        total_price = 0

        if items_data is not None:
            if not isinstance(items_data, list) or len(items_data) == 0:
                return Response(
                    {"error": "Order items must be provided as a non-empty list"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            for item in items_data:
                try:
                    book_id = int(item.get("book_id"))
                    quantity = int(item.get("quantity", 1))
                except (TypeError, ValueError):
                    return Response(
                        {"error": "Invalid order item format"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                if quantity <= 0:
                    return Response(
                        {"error": "Quantity must be positive"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                try:
                    book = Book.objects.get(id=book_id)
                except Book.DoesNotExist:
                    return Response(
                        {"error": f"Book with id {book_id} not found"},
                        status=status.HTTP_404_NOT_FOUND,
                    )

                order_items.append(
                    {
                        "book": book,
                        "quantity": quantity,
                        "price": book.price,
                        "discount_price": book.discount_price,
                    }
                )
                price = book.discount_price if book.discount_price else book.price
                total_price += price * quantity
        else:
            cart = get_object_or_404(Cart, user=request.user)
            if not cart.items.exists():
                return Response(
                    {"error": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST
                )

            for cart_item in cart.items.all():
                order_items.append(
                    {
                        "book": cart_item.book,
                        "quantity": cart_item.quantity,
                        "price": cart_item.book.price,
                        "discount_price": cart_item.book.discount_price,
                    }
                )
                total_price += cart_item.get_total()

        from datetime import datetime

        order_number = f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        order = Order.objects.create(
            user=request.user,
            order_number=order_number,
            total_price=total_price,
            email=email,
            notes=notes,
        )

        for item_data in order_items:
            OrderItem.objects.create(
                order=order,
                book=item_data["book"],
                quantity=item_data["quantity"],
                price=item_data["price"],
                discount_price=item_data["discount_price"],
            )

            # Create a Download entitlement for each purchased digital product
            book = item_data["book"]
            Download.objects.get_or_create(
                user=request.user,
                book=book,
                order=order,
                defaults={
                    "max_downloads": book.download_limit,
                    "expires_at": timezone.now()
                    + timezone.timedelta(days=book.download_expiry_days),
                },
            )

        if items_data is None:
            cart.items.all().delete()

        return Response(
            OrderDetailSerializer(order).data, status=status.HTTP_201_CREATED
        )

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def my_orders(self, request):
        """Get the current user's orders (explicit alias for list)."""
        orders = self.get_queryset().prefetch_related("items__book")
        serializer = OrderListSerializer(
            orders, many=True, context={"request": request}
        )
        return Response(serializer.data)


class DownloadViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for a user's purchased digital downloads."""

    serializer_class = DownloadSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Download.objects.filter(user=self.request.user).select_related(
            "book", "order"
        )


class ReviewViewSet(viewsets.ModelViewSet):
    """ViewSet for Book Reviews"""

    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        book_id = self.request.query_params.get("book_id", None)
        if book_id:
            return Review.objects.filter(book_id=book_id)
        return self.queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        # Only allow updating own reviews
        if serializer.instance.user != self.request.user:
            raise PermissionDenied("You can only edit your own reviews")
        serializer.save()

    def perform_destroy(self, instance):
        # Only allow deleting own reviews
        if instance.user != self.request.user:
            raise PermissionDenied("You can only delete your own reviews")
        instance.delete()

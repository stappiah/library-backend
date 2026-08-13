"""
Management command to migrate existing books with local images to Cloudinary.

This command:
1. Finds all books with a local `image` set but no `image_url`.
2. Attempts to re-upload the local image through Django's storage (Cloudinary).
3. Sets the `image_url` field to the Cloudinary URL so it works in production.

Usage:
    python manage.py migrate_images_to_cloudinary
    python manage.py migrate_images_to_cloudinary --dry-run  # preview only

Requires:
    - Cloudinary credentials configured in settings/environment
    - DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from base.models import Book
import logging
import os
from django.core.files import File as DjangoFile
from django.core.files.storage import default_storage

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Migrate existing books with local images to Cloudinary and save URL."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Only list books that would be updated without making changes.",
        )

    def handle(self, *args, **options):
        dry_run = options.get("dry_run", False)
        books = Book.objects.exclude(image="").exclude(image__isnull=True).filter(image_url__isnull=True)

        if not books.exists():
            self.stdout.write(self.style.SUCCESS("No books found needing migration."))
            return

        self.stdout.write(f"Found {books.count()} book(s) with local images but no image_url.")

        if dry_run:
            for book in books:
                self.stdout.write(f"  Would migrate: {book.title} (ID: {book.id}) - {book.image.url}")
            self.stdout.write(self.style.WARNING("Dry run complete. No changes made."))
            return

        for book in books:
            try:
                # If the current default storage is cloudinary, re-save the
                # existing local file through the storage backend so it gets
                # uploaded to Cloudinary. Otherwise, attempt to upload via
                # the storage backend directly.
                migrated_url = None

                # If the file still exists on disk under MEDIA_ROOT, open and
                # re-save it through the default storage. This works even when
                # DEFAULT_FILE_STORAGE is cloudinary_storage.
                if book.image and hasattr(book.image, 'name'):
                    local_path = os.path.join(settings.MEDIA_ROOT, book.image.name)
                    if os.path.exists(local_path):
                        with open(local_path, 'rb') as f:
                            django_file = DjangoFile(f)
                            # Save using the same name so storage backend
                            # (Cloudinary) will upload and return a URL.
                            book.image.save(book.image.name, django_file, save=False)
                            # Ensure storage has produced a URL
                            migrated_url = book.image.url

                # Fallback: try to get the URL from the storage backend
                if not migrated_url:
                    try:
                        migrated_url = book.image.url
                    except Exception:
                        migrated_url = None

                if migrated_url:
                    book.image_url = migrated_url
                    book.save(update_fields=["image_url", "image"])
                    self.stdout.write(
                        self.style.SUCCESS(f"  Migrated: {book.title} -> {migrated_url}")
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f"  Failed to migrate (no URL): {book.title} (ID: {book.id})")
                    )
                    logger.error(f"Migration produced no URL for book {book.id}")
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"  Failed for {book.title} (ID: {book.id}): {e}")
                )
                logger.exception(f"Migration failed for book {book.id}")

        self.stdout.write(self.style.SUCCESS("Migration complete."))


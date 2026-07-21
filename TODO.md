# TODO

- [x] Reproduce/confirm why `/api/v1/auth/auth/register/` returns 401.
- [x] Update routing/permissions so `register` is truly `AllowAny`.
- [x] Fix serializer so profile fields like `phone_number` are persisted during registration.
- [x] Run Django tests / verify register works without JWT (201 created, no auth header required).

## Image Display Fix

- [x] Add `get_image_url_safe()` helper method to `Book` model in `base/models.py`
- [x] Fix `get_image_url` in `base/serializers.py` (both `BookListSerializer` & `BookDetailSerializer`)
- [x] Create management command `migrate_images_to_cloudinary` to backfill existing book records


# Frontend API Integration Guide (Library Backend)

## Base URLs
- API: `http://localhost:8000/api`
- JWT token endpoints:
  - `POST /api/token/` (obtain access/refresh)
  - `POST /api/token/refresh/` (refresh access token)

## Authentication (JWT)
Send the access token in the `Authorization` header:

`Authorization: Bearer <access_token>`

> Access tokens are configured via `rest_framework_simplejwt`.

## Core endpoints
### Health
- `GET /api/health/`

### Categories / Faculties / Vendors
- `GET /api/v1/categories/`
- `GET /api/v1/faculties/`
- `GET /api/v1/vendors/`

### Books
- `GET /api/v1/books/`
  - Supports query params (when available in the backend):
    - `category`, `faculty`, `vendor`
    - `min_price`, `max_price`
    - `min_rating`
    - `featured=true`
    - `in_stock=true`
- `GET /api/v1/books/{slug}/reviews/` (custom action)

### Cart / Wishlist / Orders
- Cart:
  - `GET /api/v1/cart/` (get cart)
  - `POST /api/v1/cart/add_item/` (add item)
  - `POST /api/v1/cart/remove_item/` (remove)
  - `POST /api/v1/cart/update_item/` (update quantity)
  - `POST /api/v1/cart/clear_cart/` (clear)
- Wishlist:
  - `GET /api/v1/wishlist/` (get wishlist)
  - `POST /api/v1/wishlist/add_item/` (add)
  - `POST /api/v1/wishlist/remove_item/` (remove)
  - `POST /api/v1/wishlist/clear_wishlist/` (clear)
- Orders:
  - `GET /api/v1/orders/`
  - `POST /api/v1/orders/` (creates order from current cart)

## API Docs
Frontend developers can view a Swagger UI powered page:
- `GET /api/docs/`

OpenAPI JSON source of truth:
- `GET /static/api/openapi.json`


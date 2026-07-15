# TODO

- [x] Reproduce/confirm why `/api/v1/auth/auth/register/` returns 401.
- [x] Update routing/permissions so `register` is truly `AllowAny`.
- [x] Fix serializer so profile fields like `phone_number` are persisted during registration.
- [x] Run Django tests / verify register works without JWT (201 created, no auth header required).



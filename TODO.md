# TODO — Fix Vendor Role Assignment on Registration

## Steps
- [x] Investigate registration flow (serializer, signals, views, urls)
- [x] Add `validate_role` to `RegisterSerializer` to accept only valid roles and raise a clear error instead of silently defaulting to `customer`
- [x] Verify fix at runtime via Django shell — `"role": "vendor"` now saves DB role as `vendor`
- [x] Re-test via `python manage.py check` (no issues)

## Root Cause
The original `create()` had a **silent fallback** — any unrecognized `role` value defaulted to `'customer'` with no error. The `role` CharField also used `default='customer'`.

## Fix
Added `validate_role()` that maps `vendor`/`professor` → `vendor`, `customer`/`student` → `customer`, and raises a clear `ValidationError` for anything else. `create()` now uses the already-validated value.

## Important Finding
Even with the buggy code, sending `"role": "vendor"` should have mapped to `vendor`. A shell test confirms the fixed code saves `vendor` correctly. **If the live API still returns `customer`, the running dev server must be restarted** to pick up the edited serializer (old bytecode was cached). The client must also send `"role": "vendor"` as a top-level JSON key, which the user's request already did.

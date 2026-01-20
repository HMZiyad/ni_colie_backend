# User Profile Module Implementation

## Goal
Implement a comprehensive User Profile module allowing users to manage their personal data, settings, and preferences.

## Schema Updates
### `users/models.py`
- Add to `User` model:
    - `profile_image`: `ImageField` (requires `Pillow`, stub if not available or use FileField/URLField). *Decision: Use ImageField, assume Pillow is installable.*
    - `settings`: `JSONField(default=dict)` for arbitrary user settings.
    - `favorite_roles`: `JSONField(default=list)` to store a list of role strings.

## API Endpoints

### 1. User Profile (`/api/v1/users/me`)
- **GET**: Retrieve full profile (User fields + InmateProfile if exists).
- **PUT**: Update generic fields (full_name, phone_number, bio, etc.).
- **DELETE**: Deactivate/Delete account.

### 2. Specific Attributes
- **PATCH `/api/v1/users/me/profile-image`**: Upload/Update profile picture.
- **PUT `/api/v1/users/me/user-type`**: Update `role`.
- **PUT `/api/v1/users/me/birth-date`**: Update `birth_date`.
- **PUT `/api/v1/users/me/favorite-roles`**: Update list of favorite roles.

### 3. Settings (`/api/v1/users/me/settings`)
- **GET**: Retrieve settings JSON.
- **PUT**: Update settings JSON.

## Registration Updates
- Update `UserRegistrationSerializer` to accept `favorite_roles`, `settings`, `profile_image` (if multipart) during sign-up.

## Verification
- Add automated tests for all above endpoints.
- Verify through Postman.

## Dependencies
- `Pillow` for ImageField.

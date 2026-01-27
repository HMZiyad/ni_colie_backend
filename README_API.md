# Authentication API V1 Documentation

**Base URL**: `/api/v1/auth/`

## Endpoints

### 1. Register
*   **URL**: `/register/`
*   **Method**: `POST`
*   **Body**:
    ```json
    {
        "username": "user123",
        "email": "user@example.com",
        "password": "securepassword",
        "full_name": "John Doe",
        "role": "ADULT"  // Options: KID, TEEN, ADULT, INMATE
    }
    ```

### 2. Verify OTP (Email Verification)
*   **URL**: `/verify-otp/`
*   **Method**: `POST`
*   **Body**:
    ```json
    {
        "email": "user@example.com",
        "code": "123456"
    }
    ```

### 3. Login
*   **URL**: `/login/`
*   **Method**: `POST`
*   **Body**:
    ```json
    {
        "username": "user123",  // or email if configured
        "password": "securepassword"
    }
    ```
*   **Response**:
    ```json
    {
        "message": "Login Successful",
        "tokens": {
            "refresh": "eyJ...",
            "access": "eyJ..."
        },
        "user": { ... }
    }
    ```

### 4. Refresh Token
*   **URL**: `/refresh-token/`
*   **Method**: `POST`
*   **Body**:
    ```json
    {
        "refresh": "eyJ..." // The refresh token obtained during login
    }
    ```

### 5. Logout
*   **URL**: `/logout/`
*   **Method**: `POST`
*   **Body**:
    ```json
    {
        "refresh": "eyJ..." // The refresh token to blacklist
    }
    ```

### 6. Resend OTP
*   **URL**: `/resend-otp/`
*   **Method**: `POST`
*   **Body**:
    ```json
    {
        "email": "user@example.com"
    }
    ```

### 7. Forgot Password
*   **URL**: `/forgot-password/`
*   **Method**: `POST`
*   **Body**:
    ```json
    {
        "email": "user@example.com"
    }
    ```

### 8. Reset Password
*   **URL**: `/reset-password/`
*   **Method**: `POST`
*   **Body**:
    ```json
    {
        "email": "user@example.com",
        "code": "123456",
        "new_password": "newsecurepassword"
    }
    ```

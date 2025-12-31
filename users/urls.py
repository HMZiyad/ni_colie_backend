from django.urls import path
from .views import RegisterView, LoginView, auth_test_view, VerifyEmailView, ForgotPasswordView, ResetPasswordView

urlpatterns = [
    path('api/auth/register/', RegisterView.as_view(), name='register'),
    path('api/auth/verify-email/', VerifyEmailView.as_view(), name='verify_email'),
    path('api/auth/forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('api/auth/reset-password/', ResetPasswordView.as_view(), name='reset_password'),
    path('api/auth/login/', LoginView.as_view(), name='login'),
    path('mock-auth/', auth_test_view, name='mock_auth'),
]

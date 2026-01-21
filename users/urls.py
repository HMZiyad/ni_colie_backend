from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView, LoginView, LogoutView, 
    VerifyOTPView, ResendOTPView, VerifyEmailTokenView,
    ForgotPasswordView, ResetPasswordView, 
    auth_test_view,
    UserProfileView, ProfileImageView, UserTypeUpdateView,
    UserBirthDateView, FavoriteRolesView, UserSettingsView,
    UserSearchView, FriendRequestCreateView, FriendRequestReceivedView,
    FriendRequestSentView, FriendRequestAcceptView, FriendRequestDeclineView,
    FriendListView, UnfriendView
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('refresh-token/', TokenRefreshView.as_view(), name='token_refresh'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset_password'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify_otp'),
    path('resend-otp/', ResendOTPView.as_view(), name='resend_otp'),
    path('verify-email/<str:token>/', VerifyEmailTokenView.as_view(), name='verify_email_token'),
    
    path('mock-auth/', auth_test_view, name='mock_auth'),

    # User Profile Endpoints
    path('me/', UserProfileView.as_view(), name='user_profile'),
    path('me/profile-image/', ProfileImageView.as_view(), name='profile_image'),
    path('me/user-type/', UserTypeUpdateView.as_view(), name='user_type'),
    path('me/birth-date/', UserBirthDateView.as_view(), name='user_birth_date'),
    path('me/favorite-roles/', FavoriteRolesView.as_view(), name='user_favorite_roles'),
    path('me/settings/', UserSettingsView.as_view(), name='user_settings'),

    # Friends / Social Endpoints
    path('users/search/', UserSearchView.as_view(), name='user_search'),
    path('friends/', FriendListView.as_view(), name='friend_list'),
    path('friends/<int:friend_id>/', UnfriendView.as_view(), name='unfriend'),
    path('friends/requests/', FriendRequestCreateView.as_view(), name='friend_request_create'),
    path('friends/requests/received/', FriendRequestReceivedView.as_view(), name='friend_request_received'),
    path('friends/requests/sent/', FriendRequestSentView.as_view(), name='friend_request_sent'),
    path('friends/requests/<int:pk>/accept/', FriendRequestAcceptView.as_view(), name='friend_request_accept'),
    path('friends/requests/<int:pk>/decline/', FriendRequestDeclineView.as_view(), name='friend_request_decline'),
]

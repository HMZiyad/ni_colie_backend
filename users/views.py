from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.models import Token # We'll just return user info for now if Token not set up or use simple JWT later
from .serializers import UserRegistrationSerializer, LoginSerializer
from django.contrib.auth import login

from .serializers import (
    UserRegistrationSerializer, LoginSerializer, OTPSerializer, 
    PasswordResetSerializer, PasswordResetConfirmSerializer,
    LogoutSerializer, ResendOTPSerializer, UserProfileSerializer,
    UserSettingsSerializer, FriendUserSerializer, FriendRequestSerializer
)
from .utils import send_otp_email
from .models import OTP, User, FriendRequest
from django.db.models import Q
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import transaction
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser

class RegisterView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            with transaction.atomic():
                self.perform_create(serializer)
                headers = self.get_success_headers(serializer.data)
                return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except Exception as e:
            return Response({"error": f"Registration failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def perform_create(self, serializer):
        user = serializer.save()
        send_otp_email(user, OTP.Purpose.EMAIL_VERIFICATION)

class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = OTPSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            code = serializer.validated_data['code']
            
            # Find the user (handle duplicates by taking the latest, as logic error fix)
            user = User.objects.filter(email=email).order_by('-id').first()
            if not user:
                return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

            otp = user.otps.filter(
                code=code, 
                purpose=OTP.Purpose.EMAIL_VERIFICATION, 
                is_used=False
            ).last()
            
            if otp:
                if otp.is_expired:
                    return Response({"error": "OTP has expired."}, status=status.HTTP_400_BAD_REQUEST)
                    
                user.is_email_verified = True
                user.is_active = True
                user.save()
                otp.is_used = True
                otp.save()
                return Response({"message": "Email verified successfully. You can now login."}, status=status.HTTP_200_OK)
            return Response({"error": "Invalid or expired code."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ResendOTPView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = User.objects.filter(email=email).order_by('-id').first()
            if not user:
                 return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
            
            if user.is_email_verified:
                 return Response({"message": "Email already verified."}, status=status.HTTP_400_BAD_REQUEST)
                 
            send_otp_email(user, OTP.Purpose.EMAIL_VERIFICATION)
            return Response({"message": "OTP resent successfully."}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyEmailTokenView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request, token):
        # Placeholder for link-based verification
        return Response({"message": "GET verification not fully implemented. Please use POST /verify-otp with code."}, status=status.HTTP_501_NOT_IMPLEMENTED)


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = User.objects.filter(email=email).order_by('-id').first()
            
            if user:
                send_otp_email(user, OTP.Purpose.PASSWORD_RESET)
                return Response({"message": "OTP sent to email."}, status=status.HTTP_200_OK)
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            code = serializer.validated_data['code']
            new_password = serializer.validated_data['new_password']
            
            user = User.objects.filter(email=email).order_by('-id').first()
            if not user:
                return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

            otp = user.otps.filter(
                code=code, 
                purpose=OTP.Purpose.PASSWORD_RESET, 
                is_used=False
            ).last()
            
            if otp:
                if otp.is_expired:
                    return Response({"error": "OTP has expired."}, status=status.HTTP_400_BAD_REQUEST)

                user.set_password(new_password)
                user.save()
                otp.is_used = True
                otp.save()
                return Response({"message": "Password reset successfully."}, status=status.HTTP_200_OK)
            return Response({"error": "Invalid or expired code."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data
            refresh = RefreshToken.for_user(user)
            
            return Response({
                "message": "Login Successful",
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
                "user": { 
                    "username": user.username,
                    "email": user.email,
                    "role": user.role,
                    "id": user.id
                }
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        if serializer.is_valid():
            try:
                token = RefreshToken(serializer.validated_data['refresh'])
                token.blacklist()
                return Response({"message": "Logout Successful"}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def auth_test_view(request):
    return render(request, 'auth_test.html')

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        user = request.user
        user.is_active = False # Soft delete
        user.save()
        return Response({"message": "Account deactivated successfully."}, status=status.HTTP_200_OK)

class ProfileImageView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def patch(self, request):
        user = request.user
        if 'profile_image' not in request.data:
             return Response({"error": "No image provided"}, status=status.HTTP_400_BAD_REQUEST)
             
        user.profile_image = request.data['profile_image']
        user.save()
        return Response({"message": "Profile image updated", "profile_image": user.profile_image.url}, status=status.HTTP_200_OK)

class UserTypeUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        role = request.data.get('role')
        if role not in User.Role.values:
             return Response({"error": "Invalid role"}, status=status.HTTP_400_BAD_REQUEST)
        
        request.user.role = role
        request.user.save()
        return Response({"message": "User role updated", "role": role}, status=status.HTTP_200_OK)

class UserBirthDateView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        birth_date = request.data.get('birth_date')
        if not birth_date:
            return Response({"error": "Birth date is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        request.user.birth_date = birth_date
        request.user.save()
        return Response({"message": "Birth date updated", "birth_date": birth_date}, status=status.HTTP_200_OK)

class FavoriteRolesView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        roles = request.data.get('favorite_roles')
        if not isinstance(roles, list):
             return Response({"error": "favorite_roles must be a list"}, status=status.HTTP_400_BAD_REQUEST)
        
        request.user.favorite_roles = roles
        request.user.save()
        return Response({"message": "Favorite roles updated", "favorite_roles": roles}, status=status.HTTP_200_OK)

class UserSettingsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(request.user.settings)

    def put(self, request):
        settings = request.data.get('settings')
        if not isinstance(settings, dict):
            return Response({"error": "Settings must be a JSON object"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Merge or Replace? Requirement usually implies replace or update. Let's merge for flexibility.
        request.user.settings.update(settings)
        request.user.save()
        return Response(request.user.settings, status=status.HTTP_200_OK)


class UserSearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get('query', '')
        if not query:
            return Response([], status=status.HTTP_200_OK)
        
        users = User.objects.filter(
            Q(username__icontains=query) | Q(full_name__icontains=query)
        ).exclude(id=request.user.id)[:20] # Limit results
        
        serializer = FriendUserSerializer(users, many=True)
        return Response(serializer.data)

class FriendRequestCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        to_user_id = request.data.get('to_user_id')
        if not to_user_id:
            return Response({"error": "to_user_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            to_user = User.objects.get(id=to_user_id)
        except User.DoesNotExist:
             return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        
        if to_user == request.user:
             return Response({"error": "Cannot send friend request to yourself"}, status=status.HTTP_400_BAD_REQUEST)
             
        if request.user.friends.filter(id=to_user.id).exists():
             return Response({"error": "User is already your friend"}, status=status.HTTP_400_BAD_REQUEST)

        if FriendRequest.objects.filter(from_user=request.user, to_user=to_user).exists():
            return Response({"error": "Friend request already sent"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if they sent one to us already (reverse direction)
        reverse_req = FriendRequest.objects.filter(from_user=to_user, to_user=request.user).first()
        if reverse_req:
             if reverse_req.status == FriendRequest.Status.PENDING:
                 # Auto-accept? Or just tell them to accept the pending one?
                 # Standard flow: tell them.
                 return Response({"error": "This user has already sent you a friend request. Please accept it."}, status=status.HTTP_400_BAD_REQUEST)

        friend_request = FriendRequest.objects.create(from_user=request.user, to_user=to_user)
        serializer = FriendRequestSerializer(friend_request)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class FriendRequestReceivedView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = FriendRequestSerializer

    def get_queryset(self):
        return FriendRequest.objects.filter(to_user=self.request.user, status=FriendRequest.Status.PENDING)

class FriendRequestSentView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = FriendRequestSerializer

    def get_queryset(self):
        return FriendRequest.objects.filter(from_user=self.request.user, status=FriendRequest.Status.PENDING)

class FriendRequestAcceptView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        try:
            friend_request = FriendRequest.objects.get(pk=pk, to_user=request.user, status=FriendRequest.Status.PENDING)
        except FriendRequest.DoesNotExist:
            return Response({"error": "Friend request not found or not pending"}, status=status.HTTP_404_NOT_FOUND)
        
        with transaction.atomic():
            friend_request.status = FriendRequest.Status.ACCEPTED
            friend_request.save()
            
            # Add to friends list for BOTH users
            request.user.friends.add(friend_request.from_user)
            friend_request.from_user.friends.add(request.user)
            
        return Response({"message": "Friend request accepted"}, status=status.HTTP_200_OK)

class FriendRequestDeclineView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        try:
            friend_request = FriendRequest.objects.get(pk=pk, to_user=request.user, status=FriendRequest.Status.PENDING)
        except FriendRequest.DoesNotExist:
             return Response({"error": "Friend request not found or not pending"}, status=status.HTTP_404_NOT_FOUND)
        
        friend_request.status = FriendRequest.Status.DECLINED
        friend_request.save()
        return Response({"message": "Friend request declined"}, status=status.HTTP_200_OK)

class FriendListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        friends = request.user.friends.all()
        serializer = FriendUserSerializer(friends, many=True)
        return Response(serializer.data)

class UnfriendView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, friend_id):
        try:
            friend = User.objects.get(id=friend_id)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
            
        if not request.user.friends.filter(id=friend_id).exists():
             return Response({"error": "User is not in your friend list"}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            request.user.friends.remove(friend)
            friend.friends.remove(request.user)
            
            # Also clean up any accepted friend request records if we want to allow re-requesting easily?
            # Or keep them for history. Only DELETE them if we want to allow new requests cleanly without checking old status.
            # Best practice: leave them as history (ACCEPTED/DECLINED).
            # But if I try to send request again, code checks if request exists.
            # If I unfriend, I should probably be able to add again.
            # The create logic checks: `FriendRequest.objects.filter(from_user=request.user, to_user=to_user).exists()`
            # This WILL fail if there is an old ACCEPTED request.
            # So I should probably delete the FriendRequest record associated with this friendship, OR update logic to only check for PENDING requests.
            
            # Let's delete the related FriendRequest(s) to reset state completely.
            FriendRequest.objects.filter(
                Q(from_user=request.user, to_user=friend) | Q(from_user=friend, to_user=request.user)
            ).delete()

        return Response({"message": "User unfriended successfully"}, status=status.HTTP_200_OK)


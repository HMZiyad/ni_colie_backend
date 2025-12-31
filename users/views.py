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
    PasswordResetSerializer, PasswordResetConfirmSerializer
)
from django.contrib.auth import login
from .utils import send_otp_email
from .models import OTP, User

class RegisterView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        user = serializer.save()
        send_otp_email(user, OTP.Purpose.EMAIL_VERIFICATION)

class VerifyEmailView(APIView):
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
                user.is_email_verified = True
                user.is_active = True
                user.save()
                otp.is_used = True
                otp.save()
                return Response({"message": "Email verified successfully. You can now login."}, status=status.HTTP_200_OK)
            return Response({"error": "Invalid or expired code."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
            login(request, user)
            return Response({
                "message": "Login Successful",
                "user": {
                    "username": user.username,
                    "role": user.role,
                    "id": user.id
                }
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def auth_test_view(request):
    return render(request, 'auth_test.html')

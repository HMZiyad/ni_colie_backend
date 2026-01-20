from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, InmateProfile

class InmateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = InmateProfile
        fields = ['age', 'highest_education', 'incarceration_status', 'training_completed', 'priorities']

class UserSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['settings']

class UserProfileSerializer(serializers.ModelSerializer):
    inmate_profile = InmateProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'full_name', 'phone_number', 'role', 
            'birth_date', 'profile_image', 'settings', 'favorite_roles', 
            'is_email_verified', 'inmate_profile'
        ]
        read_only_fields = ['id', 'username', 'email', 'role', 'is_email_verified', 'inmate_profile']

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    inmate_profile = InmateProfileSerializer(required=False)

    class Meta:
        model = User
        fields = ['username', 'password', 'email', 'full_name', 'phone_number', 'role', 'birth_date', 'inmate_profile', 'settings', 'favorite_roles']

    def create(self, validated_data):
        inmate_data = validated_data.pop('inmate_profile', None)
        password = validated_data.pop('password')
        
        user = User(**validated_data)
        user.set_password(password)
        # Account inactive until verified
        user.is_active = False 
        user.save()

        if user.role == User.Role.INMATE and inmate_data:
            InmateProfile.objects.create(user=user, **inmate_data)
        
        return user

class OTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)

class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True)

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(**data)
        if user and user.is_active:
            return user
        raise serializers.ValidationError("Incorrect Credentials")


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()


from django.contrib.auth.models import AbstractUser
from django.db import models

from django.utils import timezone
from datetime import timedelta

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        INMATE = "INMATE", "Inmate"
        KID = "KID", "Kid"
        TEEN = "TEEN", "Teen"
        ADULT = "ADULT", "Adult"

    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.ADULT)
    token_balance = models.IntegerField(default=0)
    is_blocked = models.BooleanField(default=False)
    birth_date = models.DateField(null=True, blank=True)
    is_email_verified = models.BooleanField(default=False)
    
    # Profile Fields
    profile_image = models.ImageField(upload_to='profile_images/', null=True, blank=True)
    settings = models.JSONField(default=dict, blank=True)
    favorite_roles = models.JSONField(default=list, blank=True)

    def __str__(self):
        return self.username

class OTP(models.Model):
    class Purpose(models.TextChoices):
        EMAIL_VERIFICATION = "EMAIL_VERIFICATION", "Email Verification"
        PASSWORD_RESET = "PASSWORD_RESET", "Password Reset"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="otps")
    code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=20, choices=Purpose.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    @property
    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=2)

    def __str__(self):
        return f"{self.code} - {self.user.username} ({self.purpose})"


class InmateProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="inmate_profile")
    age = models.IntegerField()
    highest_education = models.CharField(max_length=255)
    incarceration_status = models.CharField(max_length=255)
    training_completed = models.TextField(blank=True, help_text="Comma-separated list of trainings")
    priorities = models.TextField(blank=True)

    def __str__(self):
        return f"Profile of {self.user.username}"

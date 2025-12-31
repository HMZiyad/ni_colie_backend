from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, InmateProfile, OTP

class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "role", "is_blocked")
    fieldsets = UserAdmin.fieldsets + (
        ("Custom Fields", {"fields": ("full_name", "phone_number", "role", "token_balance", "is_blocked")}),
    )

admin.site.register(User, CustomUserAdmin)
admin.site.register(InmateProfile)
admin.site.register(OTP)


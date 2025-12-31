import random
from django.core.mail import send_mail
from django.conf import settings
from .models import OTP

def generate_otp(user, purpose):
    code = f"{random.randint(100000, 999999)}"
    OTP.objects.create(user=user, code=code, purpose=purpose)
    return code

def send_otp_email(user, purpose):
    code = generate_otp(user, purpose)
    subject = "Verification Code"
    message = f"Your verification code is: {code}"
    
    if purpose == OTP.Purpose.PASSWORD_RESET:
        subject = "Password Reset Request"
        message = f"Use this code to reset your password: {code}"
    
    # In development, we print to console if EMAIL_BACKEND is console
    print(f"--- OTP for {user.email}: {code} ---")
    
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL or 'noreply@nicoli.com', [user.email])
    except Exception as e:
        print(f"Failed to send email: {e}")

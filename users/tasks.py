from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import User, OTP
from .models import User, OTP

@shared_task
def send_otp_email_task(email, code, purpose='email_verification'):
    """
    Celery task to send OTP email asynchronously.
    """
    subject = "Your Verification Code"
    message = f"Your verification code is: {code}"
    
    # We can improve this to reuse the logic in utils if possible, 
    # but send_raw_otp_email was simple.
    # If we want to use the template logic, we might need to duplicate or refactor utils.
    # For now, let's keep it simple as per the request "send OTP to real email".
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
        return f"OTP sent to {email}"
    except Exception as e:
        return f"Failed to send OTP to {email}: {str(e)}"

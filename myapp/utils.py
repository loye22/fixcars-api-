import random
import string
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def generate_otp(length=6):
    """Generate a random OTP of specified length"""
    return ''.join(random.choices(string.digits, k=length))


def send_otp_email(email, otp, subject="Your OTP Code"):
    """Send OTP via email"""
    try:
        # HTML template for the email
        html_message = f"""
        <html>
        <body>
            <h2>Your OTP Code</h2>
            <p>Your verification code is: <strong>{otp}</strong></p>
            <p>This code will expire in 10 minutes.</p>
            <p>If you didn't request this code, please ignore this email.</p>
        </body>
        </html>
        """
        
        # Plain text version
        plain_message = strip_tags(html_message)
        
        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def send_welcome_email(email, user_name):
    """Send welcome email to new users"""
    try:
        subject = "Welcome to FixCars!"
        html_message = f"""
        <html>
        <body>
            <h2>Welcome to FixCars!</h2>
            <p>Hello {user_name},</p>
            <p>Thank you for joining FixCars. We're excited to have you on board!</p>
            <p>Best regards,<br>The FixCars Team</p>
        </body>
        </html>
        """
        
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending welcome email: {e}")
        return False 
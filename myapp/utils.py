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
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #007bff; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                .content {{ background-color: #f8f9fa; padding: 30px; border-radius: 0 0 5px 5px; }}
                .otp-code {{ background-color: #007bff; color: white; padding: 15px; text-align: center; font-size: 24px; font-weight: bold; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 12px; }}
                .warning {{ background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>FixCars Verification</h1>
                </div>
                <div class="content">
                    <h2>Welcome to FixCars!</h2>
                    <p>Thank you for creating your account with FixCars. To complete your registration, please use the verification code below:</p>
                    
                    <div class="otp-code">
                        {otp}
                    </div>
                    
                    <p><strong>Important:</strong></p>
                    <ul>
                        <li>This code will expire in 10 minutes</li>
                        <li>Do not share this code with anyone</li>
                        <li>If you didn't request this code, please ignore this email</li>
                    </ul>
                    
                    <div class="warning">
                        <strong>Security Notice:</strong> FixCars will never ask for your verification code via phone call or text message.
                    </div>
                    
                    <p>Once verified, you'll be able to access all FixCars features and connect with automotive service providers in your area.</p>
                    
                    <p>Best regards,<br>The FixCars Team</p>
                </div>
                <div class="footer">
                    <p>This is an automated message. Please do not reply to this email.</p>
                    <p>&copy; 2024 FixCars. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text version
        plain_message = f"""
Welcome to FixCars!

Thank you for creating your account with FixCars. To complete your registration, please use the verification code below:

{otp}

Important:
- This code will expire in 10 minutes
- Do not share this code with anyone
- If you didn't request this code, please ignore this email

Security Notice: FixCars will never ask for your verification code via phone call or text message.

Once verified, you'll be able to access all FixCars features and connect with automotive service providers in your area.

Best regards,
The FixCars Team

---
This is an automated message. Please do not reply to this email.
© 2024 FixCars. All rights reserved.
        """
        
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
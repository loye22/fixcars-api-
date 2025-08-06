import random
import string
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def generate_otp(length=6):
    """Generate a random OTP of specified length"""
    return ''.join(random.choices(string.digits, k=length))


def send_otp_email(email, otp, subject="Codul tău de verificare FixCars"):
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
                    <h1>FixCars.ro - Verificare</h1>
                </div>
                <div class="content">
                    <h2>Bun venit la FixCars!</h2>
                    <p>Mulțumim că ți-ai creat contul pe FixCars.ro. Pentru a-ți finaliza înregistrarea, te rugăm să folosești codul de verificare de mai jos:</p>
                    
                    <div class="otp-code">
                        {otp}
                    </div>
                    
                    <p><strong>Important:</strong></p>
                    <ul>
                        <li>Acest cod va expira în 10 minute</li>
                        <li>Nu împărtăși acest cod cu nimeni</li>
                        <li>Dacă nu ai solicitat acest cod, te rugăm să ignori acest email</li>
                    </ul>
                    
                    <div class="warning">
                        <strong>Notă de securitate:</strong> FixCars.ro nu va cere niciodată codul tău de verificare prin apel telefonic sau mesaj text.
                    </div>
                    
                    <p>După verificare, vei putea accesa toate funcționalitățile FixCars și să te conectezi cu furnizorii de servicii auto din zona ta.</p>
                    
                    <p>Cu stimă,<br>Echipa FixCars.ro</p>
                </div>
                <div class="footer">
                    <p>Acesta este un mesaj automat. Te rugăm să nu răspunzi la acest email.</p>
                    <p>&copy; 2024 FixCars.ro. Toate drepturile rezervate.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text version
        plain_message = f"""
Bun venit la FixCars!

Mulțumim că ți-ai creat contul pe FixCars.ro. Pentru a-ți finaliza înregistrarea, te rugăm să folosești codul de verificare de mai jos:

{otp}

Important:
- Acest cod va expira în 10 minute
- Nu împărtăși acest cod cu nimeni
- Dacă nu ai solicitat acest cod, te rugăm să ignori acest email

Notă de securitate: FixCars.ro nu va cere niciodată codul tău de verificare prin apel telefonic sau mesaj text.

După verificare, vei putea accesa toate funcționalitățile FixCars și să te conectezi cu furnizorii de servicii auto din zona ta.

Cu stimă,
Echipa FixCars.ro

---
Acesta este un mesaj automat. Te rugăm să nu răspunzi la acest email.
© 2024 FixCars.ro. Toate drepturile rezervate.
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
        subject = "Bun venit la FixCars.ro!"
        html_message = f"""
        <html>
        <body>
            <h2>Bun venit la FixCars.ro!</h2>
            <p>Salut {user_name},</p>
            <p>Mulțumim că te-ai alăturat FixCars.ro. Suntem încântați să te avem cu noi!</p>
            <p>Cu stimă,<br>Echipa FixCars.ro</p>
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
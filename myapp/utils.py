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


def generate_reset_token():
    """Generate a secure random token for password reset"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=32))


def send_password_reset_email(email, reset_token, user_name):
    """Send elegant Romanian password reset email"""
    try:
        # Create reset URL - pointing to our Django server
        reset_url = f"http://localhost:8000/reset-password?token={reset_token}"
        
        # Elegant Romanian HTML email
        html_message = f"""
        <html>
        <head>
            <style>
                body {{ 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                    line-height: 1.6; 
                    color: #333; 
                    margin: 0; 
                    padding: 0; 
                    background-color: #f8f9fa; 
                }}
                .container {{ 
                    max-width: 600px; 
                    margin: 0 auto; 
                    background-color: #ffffff; 
                    border-radius: 12px; 
                    overflow: hidden; 
                    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1); 
                }}
                .header {{ 
                    background: linear-gradient(135deg, #007bff 0%, #0056b3 100%); 
                    color: white; 
                    padding: 40px 30px; 
                    text-align: center; 
                }}
                .header h1 {{ 
                    margin: 0; 
                    font-size: 32px; 
                    font-weight: 600; 
                }}
                .logo {{ 
                    font-size: 28px; 
                    font-weight: bold; 
                    margin-bottom: 15px; 
                }}
                .content {{ 
                    padding: 40px 30px; 
                }}
                .greeting {{ 
                    font-size: 20px; 
                    margin-bottom: 25px; 
                    color: #2c3e50; 
                    font-weight: 500; 
                }}
                .message {{ 
                    font-size: 16px; 
                    margin-bottom: 30px; 
                    color: #555; 
                    line-height: 1.7; 
                }}
                .reset-button {{ 
                    display: inline-block; 
                    background: linear-gradient(135deg, #28a745 0%, #20c997 100%); 
                    color: white; 
                    padding: 18px 35px; 
                    text-decoration: none; 
                    border-radius: 30px; 
                    font-weight: 600; 
                    font-size: 16px; 
                    margin: 25px 0; 
                    box-shadow: 0 6px 20px rgba(40, 167, 69, 0.3); 
                    transition: all 0.3s ease; 
                }}
                .reset-button:hover {{ 
                    transform: translateY(-2px); 
                    box-shadow: 0 8px 25px rgba(40, 167, 69, 0.4); 
                }}
                .info-box {{ 
                    background-color: #e3f2fd; 
                    border-left: 4px solid #2196f3; 
                    padding: 20px; 
                    margin: 30px 0; 
                    border-radius: 8px; 
                }}
                .info-box p {{ 
                    margin: 0; 
                    color: #1976d2; 
                    font-size: 14px; 
                    font-weight: 500; 
                }}
                .security-box {{ 
                    background-color: #fff3cd; 
                    border-left: 4px solid #ffc107; 
                    padding: 20px; 
                    margin: 30px 0; 
                    border-radius: 8px; 
                }}
                .security-box h3 {{ 
                    margin: 0 0 10px 0; 
                    color: #856404; 
                    font-size: 16px; 
                    font-weight: 600; 
                }}
                .security-box p {{ 
                    margin: 0; 
                    color: #856404; 
                    font-size: 14px; 
                }}
                .footer {{ 
                    background-color: #f8f9fa; 
                    padding: 30px; 
                    text-align: center; 
                    border-top: 1px solid #e9ecef; 
                }}
                .footer p {{ 
                    margin: 5px 0; 
                    color: #6c757d; 
                    font-size: 14px; 
                }}
                .link-fallback {{ 
                    background-color: #f8f9fa; 
                    padding: 15px; 
                    border-radius: 8px; 
                    margin: 20px 0; 
                    word-break: break-all; 
                }}
                .link-fallback a {{ 
                    color: #007bff; 
                    text-decoration: none; 
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">🔧 FixCars.ro</div>
                    <h1>Resetare Parolă</h1>
                </div>
                <div class="content">
                    <div class="greeting">
                        Salut {user_name}!
                    </div>
                    <div class="message">
                        Am primit o solicitare de resetare a parolei pentru contul tău FixCars.ro. 
                        Dacă ai fost tu cel care a făcut această solicitare, apasă butonul de mai jos pentru a-ți reseta parola.
                    </div>
                    
                    <div style="text-align: center;">
                        <a href="{reset_url}" class="reset-button">
                            🔐 Resetează Parola
                        </a>
                    </div>
                    
                    <div class="info-box">
                        <p><strong>⏰ Important:</strong> Acest link va expira în 1 oră din motive de securitate.</p>
                    </div>
                    
                    <div class="security-box">
                        <h3>🛡️ Securitate</h3>
                        <p>Dacă nu ai solicitat resetarea parolei, te rugăm să ignori acest email. 
                        Parola ta va rămâne neschimbată și contul tău va fi în siguranță.</p>
                    </div>
                    
                    <div class="message">
                        Dacă butonul nu funcționează, poți copia și lipi următorul link în browser-ul tău:
                    </div>
                    
                    <div class="link-fallback">
                        <a href="{reset_url}">{reset_url}</a>
                    </div>
                </div>
                <div class="footer">
                    <p><strong>FixCars.ro</strong> - Servicii Auto de Încredere</p>
                    <p>Acesta este un mesaj automat. Te rugăm să nu răspunzi la acest email.</p>
                    <p>&copy; 2024 FixCars.ro. Toate drepturile rezervate.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text version
        plain_message = f"""
Salut {user_name}!

Am primit o solicitare de resetare a parolei pentru contul tău FixCars.ro. 
Dacă ai fost tu cel care a făcut această solicitare, folosește link-ul de mai jos pentru a-ți reseta parola:

{reset_url}

IMPORTANT:
- Acest link va expira în 1 oră din motive de securitate
- Dacă nu ai solicitat resetarea parolei, te rugăm să ignori acest email
- Parola ta va rămâne neschimbată dacă nu folosești acest link

Securitate: Dacă nu ai solicitat resetarea parolei, te rugăm să ignori acest email. 
Contul tău va fi în siguranță.

Cu stimă,
Echipa FixCars.ro

---
FixCars.ro - Servicii Auto de Încredere
Acesta este un mesaj automat. Te rugăm să nu răspunzi la acest email.
© 2024 FixCars.ro. Toate drepturile rezervate.
        """
        
        # Send email
        send_mail(
            subject="🔐 Resetare Parolă - FixCars.ro",
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending password reset email: {e}")
        return False 
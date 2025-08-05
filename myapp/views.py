from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import send_mail
from django.conf import settings
from django.http import HttpResponse
import os
from django.conf import settings
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import parser_classes
import uuid
from .models import UserProfile, OTPVerification
from .utils import generate_otp, send_otp_email
from django.utils import timezone
from datetime import timedelta
import re
from django.contrib.auth.models import User


# Create your views here.

def home(request):
    """Simple home page view"""
    return HttpResponse("<h1>home</h1>")


class ClientSignupView(APIView):
    """API endpoint for client registration"""
    
    def post(self, request):
        django_user = None
        user_profile = None
        
        try:
            # Extract data from request
            full_name = request.data.get('full_name')
            email = request.data.get('email')
            password = request.data.get('password')
            phone = request.data.get('phone')
            photo_url = request.data.get('photo_url')
            
            # Validate required fields
            if not all([full_name, email, password, phone, photo_url]):
                missing_fields = []
                if not full_name:
                    missing_fields.append('full_name')
                if not email:
                    missing_fields.append('email')
                if not password:
                    missing_fields.append('password')
                if not phone:
                    missing_fields.append('phone')
                if not photo_url:
                    missing_fields.append('photo_url')
                
                return Response({
                    'success': False,
                    'error': f'Missing required fields: {", ".join(missing_fields)}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate email format
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email):
                return Response({
                    'success': False,
                    'error': 'Please provide a valid email address'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate phone number format (must start with '07')
            if not phone.startswith('07'):
                return Response({
                    'success': False,
                    'error': 'Phone number must start with "07"'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate phone number length (should be 10 digits for Romanian numbers)
            if len(phone) != 10 or not phone.isdigit():
                return Response({
                    'success': False,
                    'error': 'Phone number must be exactly 10 digits'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate password length
            if len(password) < 8:
                return Response({
                    'success': False,
                    'error': 'Password must be at least 8 characters long'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if email already exists in Django User model
            if User.objects.filter(email=email).exists():
                return Response({
                    'success': False,
                    'error': 'An account with this email address already exists'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if email already exists in UserProfile
            if UserProfile.objects.filter(email=email).exists():
                return Response({
                    'success': False,
                    'error': 'An account with this email address already exists'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if phone number already exists
            if UserProfile.objects.filter(phone=phone).exists():
                return Response({
                    'success': False,
                    'error': 'An account with this phone number already exists'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create Django User first
            django_user = User.objects.create_user(
                username=email,  # Use email as username
                email=email,
                password=password,
                first_name=full_name.split()[0] if full_name else '',
                last_name=' '.join(full_name.split()[1:]) if len(full_name.split()) > 1 else ''
            )
            
            # Create UserProfile linked to Django User
            user_profile = UserProfile.objects.create(
                django_user=django_user,
                full_name=full_name,
                email=email,
                phone=phone,
                profile_photo=photo_url,
                user_type='client',
                approval_status='pending',
                account_status='active'
            )
            
            # Generate 6-digit OTP
            otp = generate_otp(6)
            
            # Set OTP expiration (10 minutes from now)
            expires_at = timezone.now() + timedelta(minutes=10)
            
            # Create OTP record
            OTPVerification.objects.create(
                user=user_profile,
                otp=otp,
                expires_at=expires_at
            )
            
            # Send OTP email
            email_sent = send_otp_email(
                email=email,
                otp=otp,
                subject="Your FixCars Verification Code"
            )
            
            if not email_sent:
                # If email fails, delete both user and profile
                if user_profile:
                    user_profile.delete()
                if django_user:
                    django_user.delete()
                return Response({
                    'success': False,
                    'error': 'Failed to send verification email. Please try again.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            return Response({
                'success': True,
                'message': 'Client account created successfully. Please check your email for verification code.',
                'user_id': str(user_profile.user_id),
                'django_user_id': django_user.id,
                'email': user_profile.email
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            # Cleanup on error
            if user_profile:
                user_profile.delete()
            if django_user:
                django_user.delete()
            
            return Response({
                'success': False,
                'error': f'An error occurred during registration: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)







class SendEmailView(APIView):
    """Simple API view to send email"""
    
    def post(self, request):
        try:
            email = request.data.get('email')
            subject = request.data.get('subject', 'Test Email')
            message = request.data.get('message', 'This is a test email')
            
            if not email:
                return Response({
                    'error': 'Email is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Send email
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            
            return Response({
                'success': True,
                'message': f'Email sent to {email}'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class FileUploadView(APIView):
    """API view to upload files and return URL"""
    parser_classes = (MultiPartParser, FormParser)
    
    def post(self, request):
        try:
            # Check if file is present
            if 'file' not in request.FILES:
                return Response({
                    'success': False,
                    'error': 'No file provided'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            uploaded_file = request.FILES['file']
            
            # Validate file size (optional - 10MB limit)
            if uploaded_file.size > 10 * 1024 * 1024:  # 10MB
                return Response({
                    'success': False,
                    'error': 'File size too large. Maximum 10MB allowed.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate file type (optional)
            allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'application/pdf', 'text/plain']
            if uploaded_file.content_type not in allowed_types:
                return Response({
                    'success': False,
                    'error': 'File type not allowed. Allowed types: JPEG, PNG, GIF, PDF, TXT'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create media directory if it doesn't exist
            media_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
            os.makedirs(media_dir, exist_ok=True)
            
            # Generate unique filename
            file_extension = os.path.splitext(uploaded_file.name)[1]
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            
            # Save file
            file_path = os.path.join(media_dir, unique_filename)
            with open(file_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)
            
            # Generate URL
            file_url = f"{settings.MEDIA_URL}uploads/{unique_filename}"
            
            return Response({
                'success': True,
                'message': 'File uploaded successfully',
                'file_url': file_url,
                'filename': unique_filename,
                'original_name': uploaded_file.name,
                'file_size': uploaded_file.size
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class OTPValidationView(APIView):
    """API endpoint to validate OTP for user verification"""
    def post(self, request):
        from django.utils import timezone
        user_id = request.data.get('user_id')
        otp = request.data.get('otp')

        if not user_id or not otp:
            return Response({
                "status": "error",
                "message": "Both user_id and otp are required."
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            from .models import UserProfile, OTPVerification
            try:
                user = UserProfile.objects.get(user_id=user_id)
            except UserProfile.DoesNotExist:
                return Response({
                    "status": "error",
                    "message": "User not found."
                }, status=status.HTTP_400_BAD_REQUEST)

            otp_record = OTPVerification.objects.filter(user=user, otp=otp).order_by('-created_at').first()
            if not otp_record:
                return Response({
                    "status": "error",
                    "message": "OTP code is incorrect."
                }, status=status.HTTP_400_BAD_REQUEST)

            if otp_record.is_used:
                return Response({
                    "status": "error",
                    "message": "OTP code has already been used."
                }, status=status.HTTP_400_BAD_REQUEST)

            if otp_record.expires_at < timezone.now():
                return Response({
                    "status": "error",
                    "message": "OTP code has expired."
                }, status=status.HTTP_400_BAD_REQUEST)

            # Mark OTP as used
            otp_record.is_used = True
            otp_record.save()

            # Approve the user
            user.approval_status = 'approved'
            user.save()

            return Response({
                "status": "success",
                "message": "OTP verified successfully. Account approved."
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": "error",
                "message": f"An error occurred: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ResendOTPView(APIView):
    """API endpoint to resend OTP for user verification"""
    def post(self, request):
        from django.utils import timezone
        from datetime import timedelta
        
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response({
                "status": "error",
                "message": "user_id is required."
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            from .models import UserProfile, OTPVerification
            
            # Check if user exists
            try:
                user = UserProfile.objects.get(user_id=user_id)
            except UserProfile.DoesNotExist:
                return Response({
                    "status": "error",
                    "message": "User not found."
                }, status=status.HTTP_400_BAD_REQUEST)

            # Check for existing OTP
            existing_otp = OTPVerification.objects.filter(
                user=user,
                is_used=False
            ).order_by('-created_at').first()

            if existing_otp:
                # Check if the existing OTP is less than 5 minutes old
                time_diff = timezone.now() - existing_otp.created_at
                if time_diff < timedelta(minutes=5):
                    remaining_minutes = 5 - (time_diff.seconds // 60)
                    return Response({
                        "status": "error",
                        "message": f"Please wait {remaining_minutes} minutes before requesting a new OTP."
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Mark existing OTP as used (since we're creating a new one)
                existing_otp.is_used = True
                existing_otp.save()

            # Generate new 6-digit OTP
            otp = generate_otp(6)
            
            # Set OTP expiration (10 minutes from now)
            expires_at = timezone.now() + timedelta(minutes=10)
            
            # Create new OTP record
            new_otp = OTPVerification.objects.create(
                user=user,
                otp=otp,
                expires_at=expires_at
            )
            
            # Send OTP email
            email_sent = send_otp_email(
                email=user.email,
                otp=otp,
                subject="Your FixCars Verification Code (Resent)"
            )
            
            if not email_sent:
                # If email fails, delete the OTP
                new_otp.delete()
                return Response({
                    "status": "error",
                    "message": "Failed to send verification email. Please try again."
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            return Response({
                "status": "success",
                "message": "OTP has been resent successfully. Please check your email."
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": "error",
                "message": f"An error occurred: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
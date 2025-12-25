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
from rest_framework.permissions import AllowAny, IsAuthenticated
import uuid
from .models import UserProfile, OTPVerification, CarBrand, SupplierBrandService, BusinessHours, Service, Review, SERVICE_CATEGORIES, Request, Notification, CoverPhoto, UserDevice, SalesRepresentative, SupplierReferral, ROMANIAN_CITIES, SECTORS, AppLink, JUDETE, Car, CarObligation, ObligationDefinition, OBLIGATION_TO_SERVICE_MAP
from django.db import models
from .utils import generate_otp, send_otp_email
from django.utils import timezone
from datetime import timedelta
import re
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import AddCarObligationSerializer,  CarBrandSerializer, SupplierBrandServiceSerializer, SupplierBrandServiceWithoutServicesSerializer, ServiceWithTagsSerializer, SupplierProfileSerializer, ReviewSummarySerializer, ReviewListSerializer, RequestCreateSerializer, RequestListSerializer, NotificationSerializer, SupplierBrandServiceCreateSerializer, ServiceSerializer, BusinessHoursSerializer, BusinessHoursUpdateSerializer, CarSerializer, CarObligationSerializer, CarObligationCreateSerializer, CarObligationUpdateByIdSerializer, CarCreateSerializer, CarUpdateSerializer
from .onesignal_service import OneSignalService
import math
from decimal import Decimal
from rest_framework import viewsets
from firebase_admin import auth as firebase_auth
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from .models import SalesRepresentative, UserProfile


# Create your views here.

def home(request):
    """Simple home page view"""
    return HttpResponse("<h1>home</h1>")


class HealthCheckView(APIView):
    """API endpoint for health check"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Return a simple health check response"""
        return Response({
            'status': 'healthy',
            'message': 'API is running successfully',
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)


class AccountStatusView(APIView):
    """API endpoint to check current user's account status"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Check the authenticated user's account status"""
        try:
            # Get the user profile for the authenticated user
            user_profile = UserProfile.objects.get(django_user=request.user)
            
            return Response({
                'success': True,
                'account_status': {
                    'user_id': str(user_profile.user_id),
                    'email': user_profile.email,
                    'full_name': user_profile.full_name,
                    'is_active': user_profile.is_active,
                    'is_verified': user_profile.is_verified,
                    'account_status': user_profile.account_status,
                    'approval_status': user_profile.approval_status,
                    'user_type': user_profile.user_type,
                    'created_at': user_profile.created_at.isoformat()
                }
            }, status=status.HTTP_200_OK)
            
        except UserProfile.DoesNotExist:
            return Response({
                'success': False,
                'error': 'User profile not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'error': 'An error occurred while checking account status'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ClientSignupView(APIView):
    """API endpoint for client registration"""
    permission_classes = [AllowAny]
    
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
            
            # Check if email already exists but account is not verified yet
            existing_user = UserProfile.objects.filter(email=email).first()
            if existing_user and not existing_user.is_verified:
                return Response({
                    'success': False,
                    'error': 'Contul există, dar adresa de email nu este verificată. Te rugăm să te conectezi în schimb',
                    'user_status': 'unverified',
                    'user_id': str(existing_user.user_id),
                    'message': 'Please verify your email or request a new OTP'
                }, status=status.HTTP_400_BAD_REQUEST)
            
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
            
            # Block re-registration if a deleted account exists with same email or phone
            deleted_profile = UserProfile.objects.filter(models.Q(email=email) | models.Q(phone=phone), is_deleted=True).first()
            if deleted_profile:
                return Response({
                    'success': False,
                    'error': 'Acest cont a fost șters. Reînregistrarea cu aceleași credențiale nu este permisă.'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Check if email already exists in Django User model
            if User.objects.filter(email=email).exists():
                return Response({
                    'success': False,
                    'error': 'An account with this email address already exists'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if email already exists in UserProfile (verified users)
            existing_verified_user = UserProfile.objects.filter(email=email, is_verified=True).first()
            if existing_verified_user:
                return Response({
                    'success': False,
                    'error': 'An account with this email address already exists',
                    'user_status': 'verified',
                    'user_id': str(existing_verified_user.user_id),
                    'message': 'Please login instead of creating a new account'
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
                is_active=True,
                is_verified=False
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
                subject="Codul tău de verificare FixCars.ro"
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


class SupplierSignupView(APIView):
    """API endpoint for supplier registration"""
    permission_classes = [AllowAny]
    
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
            cover_photos_urls = request.data.get('cover_photos_urls', [])  # List of cover photo URLs
            latitude = request.data.get('latitude')
            longitude = request.data.get('longitude')
            bio = request.data.get('bio')
            business_address = request.data.get('business_address')
            
            # Check if email already exists but account is not verified yet
            existing_user = UserProfile.objects.filter(email=email).first()
            if existing_user and not existing_user.is_verified:
                return Response({
                    'success': False,
                    'error': 'Contul există, dar adresa de email nu este verificată. Te rugăm să te conectezi în schimb',
                    'user_status': 'unverified',
                    'user_id': str(existing_user.user_id),
                    'message': 'Please verify your email or request a new OTP'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate required fields
            if not all([full_name, email, password, phone, photo_url, latitude, longitude, business_address, bio]):
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
                if not latitude:
                    missing_fields.append('latitude')
                if not longitude:
                    missing_fields.append('longitude')
                if not business_address:
                    missing_fields.append('business_address')
                if not bio:
                    missing_fields.append('bio')
                
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
            
            # Validate cover photos (must have at least 1, maximum 5)
            if not cover_photos_urls:
                return Response({
                    'success': False,
                    'error': 'At least one cover photo is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if len(cover_photos_urls) > 5:
                return Response({
                    'success': False,
                    'error': 'Maximum 5 cover photos allowed'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate latitude and longitude
            try:
                lat = float(latitude)
                lng = float(longitude)
                if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                    return Response({
                        'success': False,
                        'error': 'Invalid latitude or longitude values'
                    }, status=status.HTTP_400_BAD_REQUEST)
            except (ValueError, TypeError):
                return Response({
                    'success': False,
                    'error': 'Latitude and longitude must be valid numbers'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Block re-registration if a deleted account exists with same email or phone
            deleted_profile = UserProfile.objects.filter(models.Q(email=email) | models.Q(phone=phone), is_deleted=True).first()
            if deleted_profile:
                return Response({
                    'success': False,
                    'error': 'Acest cont a fost șters. Reînregistrarea cu aceleași credențiale nu este permisă.'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Check if email already exists in Django User model
            if User.objects.filter(email=email).exists():
                return Response({
                    'success': False,
                    'error': 'An account with this email address already exists'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if email already exists in UserProfile (verified users)
            existing_verified_user = UserProfile.objects.filter(email=email, is_verified=True).first()
            if existing_verified_user:
                return Response({
                    'success': False,
                    'error': 'An account with this email address already exists',
                    'user_status': 'verified',
                    'user_id': str(existing_verified_user.user_id),
                    'message': 'Please login instead of creating a new account'
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
                user_type='supplier',
                latitude=lat,
                longitude=lng,
                business_address=business_address,
                bio=bio,
                is_active=True,  # Default to True for suppliers
                is_verified=False  # Default to False for suppliers
            )
            
            # Create default business hours for the supplier
            BusinessHours.objects.create(supplier=user_profile)
            
            # Create cover photos and link them to the user profile
            for cover_photo_url in cover_photos_urls:
                cover_photo = CoverPhoto.objects.create(photo_url=cover_photo_url)
                user_profile.cover_photos.add(cover_photo)
            
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
            
            # Send OTP email (best-effort; do not fail on email issues)
            try:
                send_otp_email(
                    email=email,
                    otp=otp,
                    subject="Codul tău de verificare FixCars.ro - Supplier Account"
                )
            except Exception:
                pass
            
            return Response({
                'success': True,
                'message': 'Supplier account created successfully. Please check your email for verification code.',
                'user_id': str(user_profile.user_id),
                'django_user_id': django_user.id,
                'email': user_profile.email,
                'note': 'Your account is pending approval and will be activated after verification and admin review.'
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


class FileUploadView(APIView):

    """API view to upload files and return URL"""
    permission_classes = [AllowAny]

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
            allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'application/pdf', 'text/plain' , 'image/jpg']
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
            
            # Generate URLs (relative and absolute)
            file_url = f"{settings.MEDIA_URL}uploads/{unique_filename}"
            absolute_file_url = request.build_absolute_uri(file_url)
            
            return Response({
                'success': True,
                'message': 'File uploaded successfully',
                'file_url': absolute_file_url,
                'file_path': file_url,
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
    permission_classes = [AllowAny]
    
    def post(self, request):
        from django.utils import timezone
        user_id = request.data.get('user_id')
        otp = request.data.get('otp')

        if not user_id or not otp:
            return Response({
                "status": "error",
                "message": "user_id and otp are required"
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Find the user profile
            from django.utils import timezone
            try:
                user = UserProfile.objects.get(user_id=user_id)
            except UserProfile.DoesNotExist:
                return Response({
                    "status": "error",
                    "message": "Invalid or expired OTP"
                }, status=status.HTTP_400_BAD_REQUEST)

            # Find the OTPVerification record
            otp_record = OTPVerification.objects.filter(user=user, otp=otp).order_by('-created_at').first()
            if not otp_record:
                return Response({
                    "status": "error",
                    "message": "Invalid or expired OTP"
                }, status=status.HTTP_400_BAD_REQUEST)

            # Check if OTP is valid
            if otp_record.is_used or otp_record.expires_at < timezone.now():
                return Response({
                    "status": "error",
                    "message": "Invalid or expired OTP"
                }, status=status.HTTP_400_BAD_REQUEST)

            # Mark OTP as used
            otp_record.is_used = True
            otp_record.save()

            # Verify the user
            user.approval_status = 'approved'
            user.is_verified = True
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
    permission_classes = [AllowAny]
    
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
                subject="Codul tău de verificare FixCars.ro (Retrimis)"
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


class LoginView(APIView):
    """API endpoint for user login"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        # Validate required fields
        if not email or not password:
            return Response({
                'success': False,
                'message':  'Adresa de email și parola sunt obligatorii.' , 
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Authenticate user with Django's auth system
            django_user = authenticate(username=email, password=password)
            
            if not django_user:
                return Response({
                    'success': False,
                    'message': 'Adresă de email sau parolă incorectă.' ,  
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Get the associated UserProfile
            try:
                user_profile = UserProfile.objects.get(django_user=django_user)
            except UserProfile.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Contul este suspendat. Vă rugăm să contactați suportul.'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Block login if account is deleted
            if getattr(user_profile, 'is_deleted', False):
                return Response({
                    'success': False,
                    'message': 'Acest cont a fost șters și nu mai poate fi folosit.'
                }, status=status.HTTP_403_FORBIDDEN)

            # Check if account is active
            if not user_profile.is_active:
                return Response({
                    'success': False,
                    'message':  'Vă mulțumim pentru înregistrare! Contul dvs. FixCar a fost creat și așteaptă verificarea echipei noastre, care vă va contacta în următoarele 24 de ore pentru activare; dacă după acest timp nu ați primit niciun semn sau aveți întrebări, ne puteți scrie direct la support@fixcars.ro',
                    'code': 409
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Check if email is verified
            if not user_profile.is_verified:
                return Response({
                    'success': False,
                    'message': 'Vă rugăm să vă verificați adresa de email înainte de autentificare.',
                    'user_status': 'unverified',
                    'user_id': str(user_profile.user_id),
                    'message':'Vă rugăm să verificați emailul sau să solicitați un nou cod OTP'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(django_user)
            
            # Prepare user data
            user_data = {
                'user_id': str(user_profile.user_id),
                'full_name': user_profile.full_name,
                'email': user_profile.email,
                'phone': user_profile.phone,
                'profile_photo': user_profile.profile_photo,
                'user_type': user_profile.user_type,
                'is_active': user_profile.is_active,
                'is_verified': user_profile.is_verified,
                'created_at': user_profile.created_at.isoformat()
            }
            
            return Response({
                'success': True,
                'message': 'Login successful',
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh),
                'user': user_data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'An error occurred during login: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DeleteAccountView(APIView):
    """Authenticated endpoint to soft-delete current user's account"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            user_profile = getattr(request.user, 'user_profile', None)
            if not user_profile:
                return Response({'success': False, 'error': 'User profile not found'}, status=status.HTTP_404_NOT_FOUND)

            if user_profile.is_deleted:
                return Response({'success': True, 'message': 'Account already deleted'}, status=status.HTTP_200_OK)

            user_profile.is_deleted = True
            user_profile.is_active = False
            user_profile.account_status = 'suspended'
            user_profile.save(update_fields=['is_deleted', 'is_active', 'account_status'])

            # Also deactivate Django auth user to prevent login via other flows
            try:
                if user_profile.django_user:
                    user_profile.django_user.is_active = False
                    user_profile.django_user.save(update_fields=['is_active'])
            except Exception:
                pass

            return Response({'success': True, 'message': 'Contul a fost șters.'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class CarBrandListView(APIView):
    """Public endpoint to list all car brands"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        brands_qs = CarBrand.objects.all().order_by('brand_name')
        serializer = CarBrandSerializer(brands_qs, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class ServicesView(APIView):
    """API endpoint to get SupplierBrandService records with specified service category, sorted by distance"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get required parameters
        category = request.query_params.get('category')
        
        # Validate required category parameter
        if not category:
            return Response({
                'success': False,
                'error': 'Category parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate category is in allowed list
        valid_categories = [choice[0] for choice in SERVICE_CATEGORIES]
        if category not in valid_categories:
            return Response({
                'success': False,
                'error': f'Invalid category. Valid categories are: {", ".join(valid_categories)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get optional parameters with defaults
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        car_brand = request.query_params.get('car_brand', 'all cars')
        tags = request.query_params.getlist('tags')  # Get list of tags
        
        # Set default coordinates to center of Bucharest if not provided
        if not lat or not lng:
            # Bucharest center coordinates
            user_lat = Decimal('44.4268')
            user_lng = Decimal('26.1025')
        else:
            try:
                user_lat = Decimal(lat)
                user_lng = Decimal(lng)
            except (ValueError, TypeError):
                return Response({
                    'success': False,
                    'error': 'Invalid latitude or longitude values'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Build base queryset
        qs = SupplierBrandService.objects.filter(
            services__category=category,
            active=True
        )
        
        # Filter by car brand if specified (and not "all cars")
        if car_brand and car_brand.lower() != 'all cars':
            qs = qs.filter(brand__brand_name__icontains=car_brand)
        
        # Filter by tags if provided
        if tags:
            # Filter services that have any of the specified tags
            qs = qs.filter(services__tags__tag_name__in=tags).distinct()
        
        # Prefetch related data for performance
        qs = qs.prefetch_related(
            'services__tags',  # Prefetch services and their tags
            'supplier__business_hours',  # Prefetch business hours for is_open calculation
            'supplier__supplier_reviews'  # Prefetch reviews for rating calculation
        ).distinct()
        
        # Calculate distance for each record and add it as a property
        def calculate_distance(service_lat, service_lng):
            """Calculate distance between two points using Haversine formula (in kilometers)"""
            # Convert decimal degrees to radians
            lat1, lon1 = math.radians(float(user_lat)), math.radians(float(user_lng))
            lat2, lon2 = math.radians(float(service_lat)), math.radians(float(service_lng))
            
            # Haversine formula
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
            c = 2 * math.asin(math.sqrt(a))
            
            # Radius of Earth in kilometers
            r = 6371
            return round(r * c, 2)
        
        # Add distance to each queryset object using supplier profile coordinates
        for service in qs:
            supplier_lat = getattr(service.supplier, 'latitude', None)
            supplier_lng = getattr(service.supplier, 'longitude', None)
            lat_value = float(supplier_lat) if supplier_lat is not None else 0.0
            lng_value = float(supplier_lng) if supplier_lng is not None else 0.0
            service.distance_km = calculate_distance(lat_value, lng_value)
        
        # Sort by distance (closest first)
        sorted_services = sorted(qs, key=lambda x: x.distance_km)
        
        # Deduplicate by supplier_id (keep first occurrence - closest supplier)
        seen_supplier_ids = set()
        unique_services = []
        for service in sorted_services:
            supplier_id = str(service.supplier.user_id)
            if supplier_id not in seen_supplier_ids:
                seen_supplier_ids.add(supplier_id)
                unique_services.append(service)
        
        # Limit to first 30 results
        limited_services = unique_services[:30]
        
        serializer = SupplierBrandServiceSerializer(limited_services, many=True)
        return Response({
            'success': True,
            'message': f'Services retrieved successfully for category: {category}',
            'data': serializer.data,
            'count': len(limited_services),
            'category': category,
            'car_brand': car_brand,
            'tags': tags,
            'location': {
                'lat': float(user_lat),
                'lng': float(user_lng)
            }
        })


class ServicesByCategoryView(APIView):
    """API endpoint to get all services with a specific category and their tags"""
    permission_classes = [IsAuthenticated]  # Public endpoint, no authentication required

    def get(self, request):
        # Get category from query parameters, default to 'mecanic_auto'
        category = request.query_params.get('category', 'mecanic_auto')
        
        # Validate category
        valid_categories = [choice[0] for choice in SERVICE_CATEGORIES]
        if category not in valid_categories:
            return Response({
                'success': False,
                'error': f'Invalid category. Valid categories are: {", ".join(valid_categories)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get all services with the specified category
            services = Service.objects.filter(category=category).prefetch_related('tags')
            
            if not services.exists():
                return Response({
                    'success': True,
                    'message': f'No services found for category: {category}',
                    'data': [],
                    'count': 0
                }, status=status.HTTP_200_OK)
            
            # Serialize the services with their tags
            serializer = ServiceWithTagsSerializer(services, many=True)
            
            return Response({
                'success': True,
                'message': f'Services retrieved successfully for category: {category}',
                'data': serializer.data,
                'count': services.count(),
                'category': category
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'An error occurred while fetching services: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SupplierBrandServiceOptionsView(APIView):
    """API endpoint to get brands and services grouped by category for mobile app"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Returns:
        - List of brands (with brand name and photo)
        - List of services grouped by category
        """
        try:
            # Get all brands
            brands = CarBrand.objects.all().order_by('brand_name')
            brand_serializer = CarBrandSerializer(brands, many=True, context={"request": request})
            
            # Get all services grouped by category
            services_by_category = {}
            all_services = Service.objects.all().prefetch_related('tags').order_by('service_name')
            service_serializer = ServiceWithTagsSerializer(all_services, many=True, context={"request": request})
            
            # Group services by category
            for service_data in service_serializer.data:
                category = service_data['category']
                category_display = dict(SERVICE_CATEGORIES).get(category, category)
                
                if category not in services_by_category:
                    services_by_category[category] = {
                        'category': category,
                        'category_name': category_display,
                        'services': []
                    }
                
                services_by_category[category]['services'].append(service_data)
            
            # Convert dict to list
            services_list = list(services_by_category.values())
            
            # Format cities as list of {value, label} objects
            cities_list = [{'value': city[0], 'label': city[1]} for city in ROMANIAN_CITIES]
            
            # Format sectors as list of {value, label} objects
            sectors_list = [{'value': sector[0], 'label': sector[1]} for sector in SECTORS]
            
            return Response({
                'success': True,
                'data': {
                    'brands': brand_serializer.data,
                    'services_by_category': services_list,
                    'cities': cities_list,
                    'sectors': sectors_list
                },
                'counts': {
                    'brands': brands.count(),
                    'categories': len(services_list),
                    'total_services': all_services.count(),
                    'cities': len(cities_list),
                    'sectors': len(sectors_list)
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'An error occurred while fetching data: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SupplierBrandServiceCreateView(APIView):
    """API endpoint to create new SupplierBrandService entries"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Create multiple SupplierBrandService entries.
        
        Expected JSON structure:
        {
            "total_payloads": 2,
            "shared_location": {
                "city": "Constanța",
                "sector": "sector_4",
                "latitude": 44.462894,
                "longitude": 26.136899,
                "is_real_location": true
            },
            "payloads": [
                {
                    "brand_id": "6c6ef239-03bf-408e-a4d6-865f3fc2844b",
                    "service_ids": ["e2fbeeec-bd66-48a6-862a-7e5c928b7abf"]
                }
            ],
            "metadata": {
                "price": 0.0,
                "created_at": "2025-12-06T16:31:21.599664"
            }
        }
        
        The supplier is automatically determined from the authenticated user.
        """
        # Get the supplier from the authenticated user
        try:
            supplier = getattr(request.user, 'user_profile', None)
            if not supplier:
                return Response({
                    'success': False,
                    'error': 'User profile not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Verify the user is a supplier
            if supplier.user_type != 'supplier':
                return Response({
                    'success': False,
                    'error': 'Authenticated user is not a supplier'
                }, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Error retrieving user profile: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Extract data from request
        data = request.data
        
        # Validate required top-level fields
        if 'shared_location' not in data:
            return Response({
                'success': False,
                'error': 'shared_location is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if 'payloads' not in data:
            return Response({
                'success': False,
                'error': 'payloads is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        shared_location = data.get('shared_location', {})
        payloads = data.get('payloads', [])
        metadata = data.get('metadata', {})
        
        # Validate shared_location fields (handle null values)
        city = shared_location.get('city')
        sector = shared_location.get('sector')  # Can be null
        latitude = shared_location.get('latitude')
        longitude = shared_location.get('longitude')
        
        if not city:
            return Response({
                'success': False,
                'error': 'shared_location.city is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if city not in [choice[0] for choice in ROMANIAN_CITIES]:
            return Response({
                'success': False,
                'error': f'Invalid city. Valid cities are: {", ".join([choice[0] for choice in ROMANIAN_CITIES])}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if sector and sector not in [choice[0] for choice in SECTORS]:
            return Response({
                'success': False,
                'error': f'Invalid sector. Valid sectors are: {", ".join([choice[0] for choice in SECTORS])}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if latitude is None or longitude is None:
            return Response({
                'success': False,
                'error': 'shared_location.latitude and shared_location.longitude are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            latitude = Decimal(str(latitude))
            longitude = Decimal(str(longitude))
        except (ValueError, TypeError):
            return Response({
                'success': False,
                'error': 'shared_location.latitude and shared_location.longitude must be valid numbers'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get price from metadata, default to 0 if not provided or null
        price = metadata.get('price')
        if price is None:
            price = Decimal('0.0')
        else:
            try:
                price = Decimal(str(price))
            except (ValueError, TypeError):
                return Response({
                    'success': False,
                    'error': 'metadata.price must be a valid number'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate payloads array
        if not isinstance(payloads, list) or len(payloads) == 0:
            return Response({
                'success': False,
                'error': 'payloads must be a non-empty array'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Collect all brand_ids and service_ids for validation
        all_brand_ids = []
        all_service_ids = []
        
        for idx, payload in enumerate(payloads):
            if not isinstance(payload, dict):
                return Response({
                    'success': False,
                    'error': f'payloads[{idx}] must be an object'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            brand_id = payload.get('brand_id')
            service_ids = payload.get('service_ids', [])
            
            if not brand_id:
                return Response({
                    'success': False,
                    'error': f'payloads[{idx}].brand_id is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not service_ids or not isinstance(service_ids, list) or len(service_ids) == 0:
                return Response({
                    'success': False,
                    'error': f'payloads[{idx}].service_ids must contain at least one service_id'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            all_brand_ids.append(brand_id)
            all_service_ids.extend(service_ids)
        
        # Validate all IDs are valid UUIDs
        invalid_uuids = []
        for brand_id in all_brand_ids:
            if brand_id is None:
                invalid_uuids.append(f'brand_id: null')
            else:
                try:
                    uuid.UUID(str(brand_id))
                except (ValueError, TypeError):
                    invalid_uuids.append(f'brand_id: {brand_id}')
        
        for service_id in all_service_ids:
            if service_id is None:
                invalid_uuids.append(f'service_id: null')
            else:
                try:
                    uuid.UUID(str(service_id))
                except (ValueError, TypeError):
                    invalid_uuids.append(f'service_id: {service_id}')
        
        if invalid_uuids:
            return Response({
                'success': False,
                'error': 'Invalid UUID format',
                'invalid_ids': invalid_uuids
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate all brand_ids exist in database
        unique_brand_ids = list(set(all_brand_ids))
        existing_brands = CarBrand.objects.filter(brand_id__in=unique_brand_ids)
        existing_brand_ids = set(str(brand.brand_id) for brand in existing_brands)
        
        missing_brand_ids = [bid for bid in unique_brand_ids if str(bid) not in existing_brand_ids]
        if missing_brand_ids:
            return Response({
                'success': False,
                'error': 'One or more brand_ids do not exist in the database',
                'missing_brand_ids': missing_brand_ids
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate all service_ids exist in database
        unique_service_ids = list(set(all_service_ids))
        existing_services = Service.objects.filter(service_id__in=unique_service_ids)
        existing_service_ids = set(str(service.service_id) for service in existing_services)
        
        missing_service_ids = [sid for sid in unique_service_ids if str(sid) not in existing_service_ids]
        if missing_service_ids:
            return Response({
                'success': False,
                'error': 'One or more service_ids do not exist in the database',
                'missing_service_ids': missing_service_ids
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check for duplicate entries (same supplier, brand, and overlapping services)
        duplicate_errors = []
        for idx, payload in enumerate(payloads):
            brand_id = payload.get('brand_id')
            service_ids = payload.get('service_ids', [])
            
            # Convert service_ids to a set for comparison
            service_ids_set = set(str(sid) for sid in service_ids)
            
            # Check for existing SupplierBrandService with same supplier and brand
            existing_entries = SupplierBrandService.objects.filter(
                supplier=supplier,
                brand_id=brand_id
            ).prefetch_related('services')
            
            # Collect all existing service IDs for this brand
            existing_service_ids_for_brand = set()
            for entry in existing_entries:
                entry_service_ids = set(str(sid) for sid in entry.services.values_list('service_id', flat=True))
                existing_service_ids_for_brand.update(entry_service_ids)
            
            # Check if any of the selected services already exist for this brand
            overlapping_services = service_ids_set.intersection(existing_service_ids_for_brand)
            if overlapping_services:
                # Get service names for better error message
                overlapping_service_uuids = [uuid.UUID(sid) for sid in overlapping_services]
                overlapping_service_names = Service.objects.filter(
                    service_id__in=overlapping_service_uuids
                ).values_list('service_name', flat=True)
                
                service_names_str = ', '.join(overlapping_service_names)
                duplicate_errors.append({
                    'payload_index': idx,
                    'brand_id': str(brand_id),
                    'error': f"The following service(s) are already associated with this brand: {service_names_str}. Please remove them from your selection or update the existing entry.",
                    'overlapping_service_ids': list(overlapping_services)
                })
        
        if duplicate_errors:
            return Response({
                'success': False,
                'error': 'One or more payloads contain services that already exist for the specified brand',
                'duplicate_errors': duplicate_errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # All validations passed, create the SupplierBrandService entries
        created_services = []
        errors = []
        
        for idx, payload in enumerate(payloads):
            try:
                brand_id = payload.get('brand_id')
                service_ids = payload.get('service_ids', [])
                
                # Get the brand object
                brand = CarBrand.objects.get(brand_id=brand_id)
                
                # Get the service objects
                services = Service.objects.filter(service_id__in=service_ids)
                
                # Create the SupplierBrandService
                supplier_brand_service = SupplierBrandService.objects.create(
                    supplier=supplier,
                    brand=brand,
                    city=city,
                    sector=sector if sector else None,
                    latitude=latitude,
                    longitude=longitude,
                    price=price,
                    active=True
                )
                
                # Add the services (ManyToMany relationship)
                supplier_brand_service.services.set(services)
                
                # Serialize the created object for response
                response_serializer = SupplierBrandServiceSerializer(
                    supplier_brand_service,
                    context={"request": request}
                )
                
                created_services.append(response_serializer.data)
                
            except Exception as e:
                errors.append({
                    'payload_index': idx,
                    'error': str(e)
                })
        
        if errors:
            return Response({
                'success': False,
                'error': 'Some services failed to create',
                'created_count': len(created_services),
                'errors': errors,
                'created_services': created_services
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': True,
            'message': f'Successfully created {len(created_services)} supplier brand service(s)',
            'created_count': len(created_services),
            'data': created_services
        }, status=status.HTTP_201_CREATED)


class SupplierProfileSummaryView(APIView):
    """New API endpoint to return supplier profile summary with requested fields"""
    permission_classes = [IsAuthenticated]
    

    def get(self, request, supplier_id=None):
        try:
            if supplier_id:
                supplier = UserProfile.objects.get(user_id=supplier_id, user_type='supplier')
            else:
                supplier = getattr(request.user, 'user_profile', None)
                if not supplier or supplier.user_type != 'supplier':
                    return Response({'success': False, 'error': 'Authenticated user is not a supplier', 'code': 403}, status=status.HTTP_403_FORBIDDEN)
        except UserProfile.DoesNotExist:
            return Response({'success': False, 'error': 'Supplier not found', 'code': 404}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Business hours and is_open
        business_hours_obj = supplier.business_hours.first()
        business_hours = None
        is_open = False
        if business_hours_obj:
            business_hours = {
                'monday': {
                    'open': str(business_hours_obj.monday_open),
                    'close': str(business_hours_obj.monday_close),
                    'closed': business_hours_obj.monday_closed,
                },
                'tuesday': {
                    'open': str(business_hours_obj.tuesday_open),
                    'close': str(business_hours_obj.tuesday_close),
                    'closed': business_hours_obj.tuesday_closed,
                },
                'wednesday': {
                    'open': str(business_hours_obj.wednesday_open),
                    'close': str(business_hours_obj.wednesday_close),
                    'closed': business_hours_obj.wednesday_closed,
                },
                'thursday': {
                    'open': str(business_hours_obj.thursday_open),
                    'close': str(business_hours_obj.thursday_close),
                    'closed': business_hours_obj.thursday_closed,
                },
                'friday': {
                    'open': str(business_hours_obj.friday_open),
                    'close': str(business_hours_obj.friday_close),
                    'closed': business_hours_obj.friday_closed,
                },
                'saturday': {
                    'open': str(business_hours_obj.saturday_open),
                    'close': str(business_hours_obj.saturday_close),
                    'closed': business_hours_obj.saturday_closed,
                },
                'sunday': {
                    'open': str(business_hours_obj.sunday_open),
                    'close': str(business_hours_obj.sunday_close),
                    'closed': business_hours_obj.sunday_closed,
                },
            }

            try:
                now = timezone.now()
                current_day = now.weekday()
                current_time = now.time()
                if current_day == 0:
                    is_open = (not business_hours_obj.monday_closed and business_hours_obj.monday_open <= current_time <= business_hours_obj.monday_close)
                elif current_day == 1:
                    is_open = (not business_hours_obj.tuesday_closed and business_hours_obj.tuesday_open <= current_time <= business_hours_obj.tuesday_close)
                elif current_day == 2:
                    is_open = (not business_hours_obj.wednesday_closed and business_hours_obj.wednesday_open <= current_time <= business_hours_obj.wednesday_close)
                elif current_day == 3:
                    is_open = (not business_hours_obj.thursday_closed and business_hours_obj.thursday_open <= current_time <= business_hours_obj.thursday_close)
                elif current_day == 4:
                    is_open = (not business_hours_obj.friday_closed and business_hours_obj.friday_open <= current_time <= business_hours_obj.friday_close)
                elif current_day == 5:
                    is_open = (not business_hours_obj.saturday_closed and business_hours_obj.saturday_open <= current_time <= business_hours_obj.saturday_close)
                elif current_day == 6:
                    is_open = (not business_hours_obj.sunday_closed and business_hours_obj.sunday_open <= current_time <= business_hours_obj.sunday_close)
            except Exception:
                is_open = False

        # Completed requests
        completed_requests = Request.objects.filter(supplier=supplier, status='completed').count()

        # Reviews stats
        total_reviews = supplier.supplier_reviews.count()
        average_rating = 0
        if total_reviews > 0:
            average_rating = sum(r.rating for r in supplier.supplier_reviews.all()) / total_reviews

        # Offered services count (distinct services across active SupplierBrandService)
        offered_services_count = Service.objects.filter(
            supplier_brand_services__supplier=supplier,
            supplier_brand_services__active=True
        ).distinct().count()

        # Newest 5 notifications for this supplier
        latest_notifications = Notification.objects.filter(receiver=supplier).order_by('-created_at')[:5]
        notifications_data = NotificationSerializer(latest_notifications, many=True).data

        data = {
            'supplierId': str(supplier.user_id),
            'supplierFullName': supplier.full_name,
            'supplierPhotoUrl': supplier.profile_photo,
            'subscriptionPlan': supplier.subscription_plan,
            'isOpen': is_open,
            'businessHours': business_hours,
            'completedRequests': completed_requests,
            'reviews': {
                'total': total_reviews,
                'averageRating': round(average_rating, 1) if total_reviews > 0 else 0
            },
            'offeredServicesCount': offered_services_count,
            'notifications': notifications_data,
        }

        return Response({'success': True, 'data': data}, status=status.HTTP_200_OK)

class SupplierProfileView(APIView):
    """API endpoint to fetch complete supplier profile by UUID"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, supplier_id):
        try:
            # Get the supplier profile
            supplier = UserProfile.objects.get(user_id=supplier_id, user_type='supplier')
        except UserProfile.DoesNotExist:
            return Response({
                'code': 404,
                'success': False,
                'error': 'Supplier not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Error fetching supplier profile: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        try:
            # Get supplier profile data
            profile_data = SupplierProfileSerializer(supplier).data
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Error serializing supplier profile data: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        try:
            # Get cover photos (just URLs)
            cover_photos = [photo.photo_url for photo in supplier.cover_photos.all()]
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Error fetching cover photos: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        try:
            # Get reviews data
            reviews = supplier.supplier_reviews.all().order_by('-created_at')[:3]
            total_reviews = supplier.supplier_reviews.count()
            average_rating = 0
            if total_reviews > 0:
                average_rating = sum(review.rating for review in supplier.supplier_reviews.all()) / total_reviews
            
            reviews_data = {
                'totalReviews': total_reviews,
                'averageRating': round(average_rating, 1),
                'reviews': ReviewSummarySerializer(reviews, many=True).data
            }
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Error fetching reviews data: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        try:
            # Get supplier services data
            supplier_services = SupplierBrandService.objects.filter(
                supplier=supplier, 
                active=True
            ).select_related('brand').prefetch_related('services')
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Error fetching supplier services: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        try:
            # Get unique car brands
            car_brands = []
            seen_brands = set()
            for service in supplier_services:
                brand = service.brand
                if brand.brand_id not in seen_brands:
                    car_brands.append({
                        'url': str(brand.brand_photo) if brand.brand_photo else '',
                        'name': brand.brand_name
                    })
                    seen_brands.add(brand.brand_id)
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Error processing car brands data: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        try:
            # Get unique services
            services = []
            seen_services = set()
            for service in supplier_services:
                for service_item in service.services.all():
                    if service_item.service_id not in seen_services:
                        services.append({
                            'serviceName': service_item.service_name,
                            'description': service_item.description
                        })
                        seen_services.add(service_item.service_id)
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Error processing services data: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        try:
            # Get location and price from first active service (or default values)
            lat = lng = price = None
            if supplier_services.exists():
                first_service = supplier_services.first()
                lat = float(first_service.latitude)
                lng = float(first_service.longitude)
                price = float(first_service.price)
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Error processing location and price data: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        try:
            services_data = {
                'carBrands': car_brands,
                'services': services,
                'lat': lat,
                'lng': lng
            }
            
            # Construct final response
            response_data = {
                'userProfile': profile_data,
                'coverPhotos': cover_photos,
                'reviews': reviews_data,
                'services': services_data
            }
            
            return Response({
                'success': True,
                'data': response_data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Error constructing final response: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ReviewsListView(APIView):
    """API endpoint to get all reviews for a specific supplier"""
    permission_classes = [IsAuthenticated]

    def get(self, request, supplier_id):
        try:
            supplier = UserProfile.objects.get(user_id=supplier_id, user_type='supplier')
        except UserProfile.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Supplier not found'
            }, status=status.HTTP_404_NOT_FOUND)

        try:
            reviews = Review.objects.filter(supplier=supplier).order_by('-created_at')
            serializer = ReviewListSerializer(reviews, many=True)
            return Response({
                'success': True,
                'message': f'Reviews retrieved successfully for supplier {supplier_id}',
                'data': serializer.data,
                'count': reviews.count()
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'success': False,
                'error': f'An error occurred while fetching reviews: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CreateUpdateReviewView(APIView):
    """API endpoint to create or update a review for a supplier"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, supplier_id):
        """Create or update a review for a supplier"""
        try:
            # Get the authenticated user's profile
            client = request.user.user_profile
            
            # Validate that the client is not trying to review themselves
            if str(client.user_id) == supplier_id:
                return Response({
                    'success': False,
                    'error': 'You cannot review yourself'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get the supplier
            try:
                supplier = UserProfile.objects.get(user_id=supplier_id, user_type='supplier')
            except UserProfile.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Supplier not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Get review data from request
            rating = request.data.get('rating')
            comment = request.data.get('comment', '')
            
            # Validate required fields
            if not rating:
                return Response({
                    'success': False,
                    'error': 'Rating is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate rating range (1-5)
            try:
                rating = int(rating)
                if rating < 1 or rating > 5:
                    return Response({
                        'success': False,
                        'error': 'Rating must be between 1 and 5'
                    }, status=status.HTTP_400_BAD_REQUEST)
            except (ValueError, TypeError):
                return Response({
                    'success': False,
                    'error': 'Rating must be a valid number'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if review already exists for this client-supplier pair
            existing_review = Review.objects.filter(
                client=client,
                supplier=supplier
            ).first()
            
            if existing_review:
                # Update existing review
                existing_review.rating = rating
                existing_review.comment = comment
                existing_review.save()
                
                serializer = ReviewListSerializer(existing_review)
                return Response({
                    'success': True,
                    'message': 'Review updated successfully',
                    'data': serializer.data,
                    'action': 'updated'
                }, status=status.HTTP_200_OK)
            else:
                # Create new review
                new_review = Review.objects.create(
                    client=client,
                    supplier=supplier,
                    rating=rating,
                    comment=comment
                )
                
                serializer = ReviewListSerializer(new_review)
                return Response({
                    'success': True,
                    'message': 'Review created successfully',
                    'data': serializer.data,
                    'action': 'created'
                }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            return Response({
                'success': False,
                'error': f'An error occurred while creating/updating review: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CreateRequestView(APIView):
    """API endpoint to create a new request for a supplier"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data.copy()
        supplier_id = data.get('supplier')
        client_profile = getattr(request.user, 'user_profile', None)
        if not client_profile:
            return Response({'success': False, 'error': 'Client profile not found.'}, status=400)
        if not supplier_id:
            return Response({'success': False, 'error': 'Supplier ID is required.'}, status=400)
        # Check if there are any non-completed requests to the same supplier
        existing_requests = Request.objects.filter(
            client=client_profile, 
            supplier_id=supplier_id
        ).exclude(status='completed')
        
        if existing_requests.exists():
            return Response({
                'success': False, 
                'error': 'Ai deja o cerere activă către acest furnizor. Te rugăm să aștepți până când cererea anterioară va fi finalizată.', 
                'code': 'active_request_exists'
            }, status=400)
        data['status'] = 'pending'
        data['client'] = client_profile.pk
        data['phone_number'] = client_profile.phone  # Set phone number from client profile
        serializer = RequestCreateSerializer(data=data)
        if serializer.is_valid():
            request_obj = serializer.save(client=client_profile, status='pending', phone_number=client_profile.phone)
            # Create notification for the client (receiver is the sender)
            from .models import Notification
            Notification.objects.create(
                receiver=client_profile,
                type='request_update',
                message='Cererea ta a fost trimisă cu succes. Te rugăm să aștepți până când platforma va ajunge.'
            )
            # Create notification for the supplier (new request received)
            try:
                Notification.objects.create(
                    receiver=request_obj.supplier,
                    type='request_update',
                    message='Ai primit o cerere nouă de la un client.'
                )
            except Exception:
                pass
            return Response({'success': True, 'message': 'Cererea a fost creată cu succes.'}, status=201)
        else:
            return Response({'success': False, 'errors': serializer.errors}, status=400)


class RequestListView(APIView):
    """API endpoint to get all requests for the current user sorted by date (newest first)"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Get the current user's profile
            user_profile = getattr(request.user, 'user_profile', None)
            if not user_profile:
                return Response({
                    'success': False,
                    'error': 'User profile not found.'
                }, status=404)
            
            # Get requests for the current user (both as client and supplier)
            user_requests = Request.objects.filter(
                models.Q(client=user_profile) | models.Q(supplier=user_profile)
            ).order_by('-created_at')
            
            if not user_requests.exists():
                return Response({
                    'success': True,
                    'message': 'No requests found for this user',
                    'data': [],
                    'count': 0
                }, status=200)
            
            serializer = RequestListSerializer(user_requests, many=True)
            return Response({
                'success': True,
                'message': 'User requests retrieved successfully',
                'data': serializer.data,
                'count': user_requests.count()
            }, status=200)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'An error occurred while fetching user requests: {str(e)}'
            }, status=500)


class PendingRequestsCountView(APIView):
    """Return number of pending requests for current user (as client or supplier)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user_profile = getattr(request.user, 'user_profile', None)
            if not user_profile:
                return Response({'success': False, 'error': 'User profile not found.'}, status=404)

            count = Request.objects.filter(
                (models.Q(client=user_profile) | models.Q(supplier=user_profile)) & models.Q(status='pending')
            ).count()

            return Response({'success': True, 'pending_count': count}, status=200)
        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=500)


class UpdateRequestStatusView(APIView):
    """Update a request status enforcing allowed status flow.

    Flow:
    - pending -> accepted | rejected
    - accepted -> completed | expired
    - rejected -> (terminal, no further changes)
    - completed/expired -> (terminal)
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request_id = request.data.get('request_id')
        new_status = request.data.get('status')

        if not request_id or not new_status:
            return Response({'success': False, 'error': 'request_id and status are required.'}, status=400)

        # Validate UUID
        try:
            parsed_uuid = uuid.UUID(str(request_id))
        except (ValueError, AttributeError, TypeError):
            return Response({'success': False, 'error': 'request_id must be a valid UUID.'}, status=400)

        # Validate status choice
        valid_statuses = {choice[0] for choice in Request._meta.get_field('status').choices}
        if new_status not in valid_statuses:
            return Response({'success': False, 'error': f'Invalid status. Allowed: {", ".join(sorted(valid_statuses))}'}, status=400)

        req = Request.objects.filter(id=parsed_uuid).first()
        if not req:
            return Response({'success': False, 'error': 'Request not found.'}, status=404)

        # Ensure the current user is either the client or supplier of this request
        user_profile = getattr(request.user, 'user_profile', None)
        if not user_profile or (req.client_id != user_profile.pk and req.supplier_id != user_profile.pk):
            return Response({'success': False, 'error': 'Not authorized to update this request.'}, status=403)

        current_status = req.status

        # Terminal states cannot transition
        terminal_statuses = {'rejected', 'completed', 'expired'}
        if current_status in terminal_statuses:
            if new_status != current_status:
                return Response({'success': False, 'error': f'Request in status "{current_status}" cannot be changed.'}, status=400)
            # If same status, just acknowledge
            return Response({'success': True, 'message': 'No change. Status already set.', 'status': current_status}, status=200)

        # Allowed transitions mapping
        allowed_transitions = {
            'pending': {'accepted', 'rejected'},
            'accepted': {'completed', 'expired'},
        }

        allowed_next = allowed_transitions.get(current_status, set())
        if new_status == current_status:
            return Response({'success': True, 'message': 'No change. Status already set.', 'status': current_status}, status=200)

        if new_status not in allowed_next:
            return Response({'success': False, 'error': f'Invalid transition: {current_status} -> {new_status}.'}, status=400)

        # Apply change
        req.status = new_status
        req.save(update_fields=['status'])

        # Create notifications to both parties
        try:
            message = f'Solicitarea ta a fost actualizată la statusul: {new_status}.'
            Notification.objects.create(receiver=req.client, type='request_update', message=message)
            if req.client_id != req.supplier_id:
                Notification.objects.create(receiver=req.supplier, type='request_update', message=message)
            # Send OneSignal push to client (best-effort)
            try:
                OneSignalService.send_to_user(req.client, message)
            except Exception:
                pass
        except Exception:
            # Notifications are best-effort; do not fail the request
            pass

        return Response({'success': True, 'message': 'Request status updated successfully.', 'data': {
            'id': str(req.id),
            'status': req.status,
        }}, status=200)

class NotificationsListView(APIView):
    """API endpoint to get all notifications for the requesting user"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_profile = getattr(request.user, 'user_profile', None)
        if not user_profile:
            return Response({'success': False, 'error': 'User profile not found.'}, status=404)
        notifications = Notification.objects.filter(receiver=user_profile).order_by('-created_at')
        serializer = NotificationSerializer(notifications, many=True)
        return Response({
            'success': True,
            'data': serializer.data,
            'count': notifications.count()
        }, status=200)


class MarkNotificationReadView(APIView):
    """API endpoint to mark a notification as read by ID"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_profile = getattr(request.user, 'user_profile', None)
        if not user_profile:
            return Response({'success': False, 'error': 'User profile not found.'}, status=404)

        notification_id = request.data.get('notification_id')
        if not notification_id:
            return Response({'success': False, 'error': 'notification_id is required.'}, status=400)

        # Validate UUID format
        try:
            parsed_uuid = uuid.UUID(str(notification_id))
        except (ValueError, AttributeError, TypeError):
            return Response({'success': False, 'error': 'notification_id must be a valid UUID.'}, status=400)

        notification = Notification.objects.filter(notification_id=parsed_uuid, receiver=user_profile).first()
        if not notification:
            return Response({'success': False, 'error': 'Notification not found.'}, status=404)

        if not notification.is_read:
            notification.is_read = True
            notification.save()

        serializer = NotificationSerializer(notification)
        return Response({'success': True, 'message': 'Notification marked as read.', 'data': serializer.data}, status=200)


class RegisterDeviceView(APIView):
    """API endpoint to register or update a user device for OneSignal notifications"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        player_id = request.data.get('player_id')
        
        if not player_id:
            return Response({'error': 'player_id required'}, status=400)

        user_profile = request.user.user_profile
        
        # First, try to find an existing device for this user
        existing_device = UserDevice.objects.filter(user=user_profile).first()
        
        if existing_device:
            # Update existing device with new player_id
            existing_device.player_id = player_id
            existing_device.is_active = True
            existing_device.save()
            created = False
            device = existing_device
        else:
            # Create new device if none exists
            device = UserDevice.objects.create(
                user=user_profile,
                player_id=player_id,
                is_active=True
            )
            created = True

        return Response({
            'success': True,
            'message': f'Device {created and "registered" or "updated"} successfully',
            'action': 'created' if created else 'updated',
            'device_id': str(device.id)
        })


class HasUnreadNotificationsView(APIView):
    """API endpoint to check if user has unread notifications"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_profile = getattr(request.user, 'user_profile', None)
        if not user_profile:
            return Response({'success': False, 'error': 'User profile not found.'}, status=404)
        
        # Check if there are any unread notifications for this user
        has_unread = Notification.objects.filter(receiver=user_profile, is_read=False).exists()
        
        return Response({
            'success': True,
            'has_unread_notifications': has_unread
        }, status=200)


class ReferedByView(APIView):
    """Allow an authenticated supplier to set a referral by a sales representative's email."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # Validate current user profile
            supplier = getattr(request.user, 'user_profile', None)
            if not supplier:
                return Response({'success': False, 'error': 'User profile not found.'}, status=status.HTTP_404_NOT_FOUND)
            if supplier.user_type != 'supplier':
                return Response({'success': False, 'error': 'Only suppliers can set referral.'}, status=status.HTTP_403_FORBIDDEN)

            # Get and validate email
            email = request.data.get('email')
            if not email:
                return Response({'success': False, 'error': 'email is required.'}, status=status.HTTP_400_BAD_REQUEST)

            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email):
                return Response({'success': False, 'error': 'Please provide a valid email address.'}, status=status.HTTP_400_BAD_REQUEST)

            # Check sales representative existence
            sales_rep = SalesRepresentative.objects.filter(email=email).first()
            if not sales_rep:
                return Response({'success': False, 'error': 'Sales representative not found for the provided email.'}, status=status.HTTP_404_NOT_FOUND)
            if not sales_rep.approved:
                return Response({'success': False, 'error': 'Sales representative is not approved.'}, status=status.HTTP_403_FORBIDDEN)

            # Prevent duplicate referral
            existing = SupplierReferral.objects.filter(sales_representative=sales_rep, supplier=supplier).first()
            if existing:
                return Response({'success': True, 'message': 'Referral already exists.', 'data': {
                    'referral_id': str(existing.referral_id),
                    'sales_representative': sales_rep.email,
                    'has_received_commission': existing.has_received_commission,
                    'created_at': existing.created_at.isoformat(),
                }}, status=status.HTTP_200_OK)

            # Create referral
            referral = SupplierReferral.objects.create(
                sales_representative=sales_rep,
                supplier=supplier
            )

            return Response({'success': True, 'message': 'Referral saved successfully.', 'data': {
                'referral_id': str(referral.referral_id),
                'sales_representative': sales_rep.email,
                'has_received_commission': referral.has_received_commission,
                'created_at': referral.created_at.isoformat(),
            }}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SendNotificationView(APIView):
    """API endpoint to send a notification to a specific user"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_id = request.data.get('user_id')
        message = request.data.get('message')
        
        if not user_id or not message:
            return Response({'error': 'user_id and message required'}, status=400)

        try:
            user_profile = UserProfile.objects.get(user_id=user_id)
            
            # Check if user has any active devices
            active_devices = user_profile.devices.filter(is_active=True)
            device_count = active_devices.count()
            
            if device_count == 0:
                return Response({
                    'error': 'User has no active devices registered',
                    'details': 'User must register a device first via /api/register-device/',
                    'user_id': str(user_id),
                    'device_count': 0
                }, status=400)
            
            # Get device details for debugging
            device_info = list(active_devices.values('id', 'player_id', 'is_active', 'created_at'))
            
            # Try to send notification
            success = OneSignalService.send_to_user(user_profile, message)
            
            if success:
                return Response({
                    'success': True, 
                    'message': 'Notification sent',
                    'device_count': device_count,
                    'devices': device_info
                })
            else:
                return Response({
                    'error': 'Failed to send notification via OneSignal',
                    'details': 'OneSignal service returned False. Check OneSignal configuration and logs.',
                    'user_id': str(user_id),
                    'device_count': device_count,
                    'devices': device_info,
                    'onesignal_app_id': getattr(settings, 'ONESIGNAL_APP_ID', 'Not configured')
                }, status=500)
                
        except UserProfile.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)
        except Exception as e:
            return Response({
                'error': 'Unexpected error occurred',
                'details': str(e),
                'user_id': str(user_id)
            }, status=500)


class FirebaseTokenViewSet(viewsets.ViewSet):
    """
    ViewSet for Firebase token management using CRUD patterns
    """
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """
        GET /api/firebase-token/ - Get user's Firebase token
        This is the main endpoint the Flutter app will use
        """
        try:
            # Get the actual UUID from UserProfile instead of Django User ID
            user_profile = request.user.user_profile
            user_uuid = str(user_profile.user_id) if user_profile else str(request.user.id)
            
            custom_token = firebase_auth.create_custom_token(user_uuid)
            
            # Get user's profile photo URL
            try:
                profile_photo_url = user_profile.profile_photo if user_profile else None
            except:
                profile_photo_url = None
            
            return Response({
                'token': custom_token.decode('utf-8') if isinstance(custom_token, (bytes, bytearray)) else str(custom_token),
                'user_uuid': user_uuid,
                'email': request.user.email,
                'display_name': request.user.get_full_name() or request.user.username,
                'profile_photo_url': profile_photo_url
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': f'Failed to generate Firebase token: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def create(self, request):
        """
        POST /api/firebase-token/ - Create a new Firebase token (same as list)
        """
        return self.list(request)

    def retrieve(self, request, pk=None):
        """
        GET /api/firebase-token/{pk}/ - Not typically used, but follows CRUD pattern
        """
        return Response(
            {'error': 'Use the list endpoint to get your Firebase token'},
            status=status.HTTP_400_BAD_REQUEST
        )

    def update(self, request, pk=None):
        """
        PUT /api/firebase-token/{pk}/ - Not typically used
        """
        return Response(
            {'error': 'Firebase tokens cannot be updated, request a new one'},
            status=status.HTTP_400_BAD_REQUEST
        )

    def destroy(self, request, pk=None):
        """
        DELETE /api/firebase-token/{pk}/ - Not typically used
        """
        return Response(
            {'error': 'Firebase tokens cannot be deleted through this API'},
            status=status.HTTP_400_BAD_REQUEST
        )


class UserDetailView(APIView):
    """Public endpoint to fetch basic user info by UUID"""
    permission_classes = [IsAuthenticated]

    def get(self, request, user_uuid):
        try:
            user = UserProfile.objects.get(user_id=user_uuid)
        except UserProfile.DoesNotExist:
            return Response({
                'success': False,
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'success': True,
            'display_name': user.full_name,
            'profile_photo_url': user.profile_photo
        }, status=status.HTTP_200_OK)


class RequestPasswordResetView(APIView):
    """Request password reset - sends email with reset link"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            email = request.data.get('email')
            
            if not email:
                return Response({
                    'success': False,
                    'error': 'Email-ul este obligatoriu'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate email format
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email):
                return Response({
                    'success': False,
                    'error': 'Formatul email-ului nu este valid'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if user exists
            try:
                user_profile = UserProfile.objects.get(email=email)
            except UserProfile.DoesNotExist:
                # For security reasons, don't reveal if email exists
                return Response({
                    'success': True,
                    'message': 'Dacă email-ul există în sistem, vei primi un link de resetare a parolei'
                }, status=status.HTTP_200_OK)
            
            # Check if user is active
            if not user_profile.is_active:
                return Response({
                    'success': False,
                    'error': 'Contul este dezactivat. Contactează suportul pentru asistență.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Generate reset token
            from .utils import generate_reset_token, send_password_reset_email
            reset_token = generate_reset_token()
            
            # Create password reset token record
            from .models import PasswordResetToken
            from django.utils import timezone
            from datetime import timedelta
            
            # Delete any existing tokens for this user
            PasswordResetToken.objects.filter(user=user_profile, is_used=False).delete()
            
            # Create new token
            reset_token_obj = PasswordResetToken.objects.create(
                user=user_profile,
                token=reset_token,
                expires_at=timezone.now() + timedelta(hours=1)
            )
            
            # Send password reset email
            email_sent = send_password_reset_email(
                email=email,
                reset_token=reset_token,
                user_name=user_profile.full_name
            )
            
            if email_sent:
                return Response({
                    'success': True,
                    'message': 'Link-ul de resetare a parolei a fost trimis pe email-ul tău'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'error': 'Nu s-a putut trimite email-ul. Încearcă din nou.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            return Response({
                'success': False,
                'error': 'A apărut o eroare. Încearcă din nou.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ResetPasswordView(APIView):
    """Reset password using token"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            token = request.data.get('token')
            new_password = request.data.get('new_password')
            
            if not token or not new_password:
                return Response({
                    'success': False,
                    'error': 'Token-ul și noua parolă sunt obligatorii'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate password strength
            if len(new_password) < 8:
                return Response({
                    'success': False,
                    'error': 'Parola trebuie să aibă cel puțin 8 caractere'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Find the reset token
            from .models import PasswordResetToken
            try:
                reset_token_obj = PasswordResetToken.objects.get(
                    token=token,
                    is_used=False
                )
            except PasswordResetToken.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Token-ul de resetare este invalid sau a fost deja folosit'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if token is expired
            if reset_token_obj.is_expired():
                return Response({
                    'success': False,
                    'error': 'Token-ul de resetare a expirat. Solicită unul nou.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get user profile
            user_profile = reset_token_obj.user
            
            # Update Django user password
            if user_profile.django_user:
                user_profile.django_user.set_password(new_password)
                user_profile.django_user.save()
            
            # Mark token as used
            reset_token_obj.is_used = True
            reset_token_obj.save()
            
            return Response({
                'success': True,
                'message': 'Parola a fost resetată cu succes. Poți să te conectezi cu noua parolă.'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': 'A apărut o eroare. Încearcă din nou.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BusinessHoursView(APIView):
    """API endpoint to get business hours for the current authenticated user"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Fetch business hours for the current user"""
        try:
            # Get the current user's profile
            user_profile = getattr(request.user, 'user_profile', None)
            if not user_profile:
                return Response({
                    'success': False,
                    'error': 'User profile not found.'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Check if user is a supplier
            if user_profile.user_type != 'supplier':
                return Response({
                    'success': False,
                    'error': 'Business hours are only available for suppliers.'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Get or create business hours
            business_hours, created = BusinessHours.objects.get_or_create(
                supplier=user_profile,
                defaults={
                    'monday_open': '08:00',
                    'monday_close': '19:00',
                    'monday_closed': False,
                    'tuesday_open': '08:00',
                    'tuesday_close': '19:00',
                    'tuesday_closed': False,
                    'wednesday_open': '08:00',
                    'wednesday_close': '19:00',
                    'wednesday_closed': False,
                    'thursday_open': '08:00',
                    'thursday_close': '19:00',
                    'thursday_closed': False,
                    'friday_open': '08:00',
                    'friday_close': '19:00',
                    'friday_closed': False,
                    'saturday_open': '09:00',
                    'saturday_close': '17:00',
                    'saturday_closed': True,
                    'sunday_open': '09:00',
                    'sunday_close': '17:00',
                    'sunday_closed': True,
                }
            )
            
            serializer = BusinessHoursSerializer(business_hours)
            return Response({
                'success': True,
                'data': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'An error occurred while fetching business hours: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BusinessHoursUpdateView(APIView):
    """API endpoint to update business hours for the current authenticated user"""
    permission_classes = [IsAuthenticated]
    
    def put(self, request):
        """Update business hours for the current user"""
        try:
            # Get the current user's profile
            user_profile = getattr(request.user, 'user_profile', None)
            if not user_profile:
                return Response({
                    'success': False,
                    'error': 'User profile not found.'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Check if user is a supplier
            if user_profile.user_type != 'supplier':
                return Response({
                    'success': False,
                    'error': 'Business hours can only be updated by suppliers.'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Get or create business hours
            business_hours, created = BusinessHours.objects.get_or_create(
                supplier=user_profile,
                defaults={
                    'monday_open': '08:00',
                    'monday_close': '19:00',
                    'monday_closed': False,
                    'tuesday_open': '08:00',
                    'tuesday_close': '19:00',
                    'tuesday_closed': False,
                    'wednesday_open': '08:00',
                    'wednesday_close': '19:00',
                    'wednesday_closed': False,
                    'thursday_open': '08:00',
                    'thursday_close': '19:00',
                    'thursday_closed': False,
                    'friday_open': '08:00',
                    'friday_close': '19:00',
                    'friday_closed': False,
                    'saturday_open': '09:00',
                    'saturday_close': '17:00',
                    'saturday_closed': True,
                    'sunday_open': '09:00',
                    'sunday_close': '17:00',
                    'sunday_closed': True,
                }
            )
            
            # Validate and update
            serializer = BusinessHoursUpdateSerializer(business_hours, data=request.data)
            if serializer.is_valid():
                serializer.save()
                
                # Return updated data
                response_serializer = BusinessHoursSerializer(business_hours)
                return Response({
                    'success': True,
                    'message': 'Business hours updated successfully.',
                    'data': response_serializer.data
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'An error occurred while updating business hours: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def reset_password_page(request):
    """Simple web page for password reset"""
    token = request.GET.get('token')
    
    if not token:
        return HttpResponse("""
        <html>
        <head>
            <title>Resetare Parolă - FixCars.ro</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                * { box-sizing: border-box; }
                body { 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    margin: 0; 
                    padding: 20px; 
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                .container { 
                    background: white; 
                    padding: 40px 30px; 
                    border-radius: 15px; 
                    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                    max-width: 400px;
                    width: 100%;
                    text-align: center;
                }
                .logo { 
                    font-size: 24px; 
                    font-weight: bold; 
                    margin-bottom: 20px;
                    color: #007bff;
                }
                h1 { 
                    color: #333; 
                    margin-bottom: 20px;
                    font-size: 24px;
                }
                .error { 
                    color: #dc3545; 
                    background: #f8d7da;
                    border: 1px solid #f5c6cb;
                    padding: 15px;
                    border-radius: 8px;
                    margin: 20px 0;
                }
                @media (max-width: 480px) {
                    body { padding: 15px; }
                    .container { padding: 30px 20px; }
                    .logo { font-size: 20px; }
                    h1 { font-size: 20px; }
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="logo">🔧 FixCars.ro</div>
                <h1>Resetare Parolă</h1>
                <div class="error">Token-ul de resetare lipsește.</div>
                <p>Te rugăm să folosești link-ul din email-ul de resetare.</p>
            </div>
        </body>
        </html>
        """)
    
    # Check if token is valid
    from .models import PasswordResetToken
    try:
        reset_token_obj = PasswordResetToken.objects.get(token=token, is_used=False)
        if reset_token_obj.is_expired():
            return HttpResponse("""
            <html>
            <head>
                <title>Resetare Parolă - FixCars.ro</title>
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    * { box-sizing: border-box; }
                    body { 
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        margin: 0; 
                        padding: 20px; 
                        min-height: 100vh;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                    }
                    .container { 
                        background: white; 
                        padding: 40px 30px; 
                        border-radius: 15px; 
                        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                        max-width: 400px;
                        width: 100%;
                        text-align: center;
                    }
                    .logo { 
                        font-size: 24px; 
                        font-weight: bold; 
                        margin-bottom: 20px;
                        color: #007bff;
                    }
                    h1 { 
                        color: #333; 
                        margin-bottom: 20px;
                        font-size: 24px;
                    }
                    .error { 
                        color: #dc3545; 
                        background: #f8d7da;
                        border: 1px solid #f5c6cb;
                        padding: 15px;
                        border-radius: 8px;
                        margin: 20px 0;
                    }
                    @media (max-width: 480px) {
                        body { padding: 15px; }
                        .container { padding: 30px 20px; }
                        .logo { font-size: 20px; }
                        h1 { font-size: 20px; }
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="logo">🔧 FixCars.ro</div>
                    <h1>Resetare Parolă</h1>
                    <div class="error">Token-ul de resetare a expirat.</div>
                    <p>Te rugăm să soliciți un nou link de resetare.</p>
                </div>
            </body>
            </html>
            """)
    except PasswordResetToken.DoesNotExist:
        return HttpResponse("""
        <html>
        <head>
            <title>Resetare Parolă - FixCars.ro</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                * { box-sizing: border-box; }
                body { 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    margin: 0; 
                    padding: 20px; 
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                .container { 
                    background: white; 
                    padding: 40px 30px; 
                    border-radius: 15px; 
                    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                    max-width: 400px;
                    width: 100%;
                    text-align: center;
                }
                .logo { 
                    font-size: 24px; 
                    font-weight: bold; 
                    margin-bottom: 20px;
                    color: #007bff;
                }
                h1 { 
                    color: #333; 
                    margin-bottom: 20px;
                    font-size: 24px;
                }
                .error { 
                    color: #dc3545; 
                    background: #f8d7da;
                    border: 1px solid #f5c6cb;
                    padding: 15px;
                    border-radius: 8px;
                    margin: 20px 0;
                }
                @media (max-width: 480px) {
                    body { padding: 15px; }
                    .container { padding: 30px 20px; }
                    .logo { font-size: 20px; }
                    h1 { font-size: 20px; }
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="logo">🔧 FixCars.ro</div>
                <h1>Resetare Parolă</h1>
                <div class="error">Token-ul de resetare este invalid.</div>
                <p>Te rugăm să folosești link-ul din email-ul de resetare.</p>
            </div>
        </body>
        </html>
        """)
    
    # Valid token - show reset form
    return HttpResponse(f"""
    <html>
    <head>
        <title>Resetare Parolă - FixCars.ro</title>
        <style>
            body {{ 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                margin: 0; 
                padding: 20px; 
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }}
            .container {{ 
                background: white; 
                padding: 40px; 
                border-radius: 15px; 
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                max-width: 400px;
                width: 100%;
            }}
            .logo {{ 
                text-align: center; 
                font-size: 24px; 
                font-weight: bold; 
                margin-bottom: 20px;
                color: #007bff;
            }}
            h1 {{ 
                text-align: center; 
                color: #333; 
                margin-bottom: 30px;
            }}
            .form-group {{ 
                margin-bottom: 20px; 
            }}
            label {{ 
                display: block; 
                margin-bottom: 8px; 
                color: #555; 
                font-weight: 500;
            }}
            input[type="password"] {{ 
                width: 100%; 
                padding: 12px; 
                border: 2px solid #e1e5e9; 
                border-radius: 8px; 
                font-size: 16px; 
                box-sizing: border-box;
                transition: border-color 0.3s;
            }}
            input[type="password"]:focus {{ 
                outline: none; 
                border-color: #007bff; 
            }}
            .btn {{ 
                width: 100%; 
                padding: 15px; 
                background: linear-gradient(135deg, #28a745 0%, #20c997 100%); 
                color: white; 
                border: none; 
                border-radius: 8px; 
                font-size: 16px; 
                font-weight: 600; 
                cursor: pointer; 
                transition: transform 0.2s;
            }}
            .btn:hover {{ 
                transform: translateY(-2px); 
            }}
            .btn:disabled {{ 
                opacity: 0.6; 
                cursor: not-allowed; 
                transform: none; 
            }}
            .message {{ 
                margin-top: 20px; 
                padding: 15px; 
                border-radius: 8px; 
                text-align: center; 
                display: none;
            }}
            .success {{ 
                background-color: #d4edda; 
                color: #155724; 
                border: 1px solid #c3e6cb; 
            }}
            .error {{ 
                background-color: #f8d7da; 
                color: #721c24; 
                border: 1px solid #f5c6cb; 
            }}
            .info {{ 
                background-color: #e3f2fd; 
                color: #1976d2; 
                border: 1px solid #bbdefb; 
                margin-bottom: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logo">🔧 FixCars.ro</div>
            <h1>Resetare Parolă</h1>
            
            <div class="info">
                <strong>⏰ Important:</strong> Această pagină va expira în 1 oră din motive de securitate.
            </div>
            
            <form id="resetForm">
                <div class="form-group">
                    <label for="newPassword">Noua Parolă:</label>
                    <input type="password" id="newPassword" name="newPassword" 
                           placeholder="Introduceți noua parolă (min. 8 caractere)" 
                           minlength="8" required>
                </div>
                
                <div class="form-group">
                    <label for="confirmPassword">Confirmă Parola:</label>
                    <input type="password" id="confirmPassword" name="confirmPassword" 
                           placeholder="Confirmați noua parolă" 
                           minlength="8" required>
                </div>
                
                <button type="submit" class="btn" id="submitBtn">
                    🔐 Resetează Parola
                </button>
            </form>
            
            <div id="message" class="message"></div>
        </div>

        <script>
            const form = document.getElementById('resetForm');
            const message = document.getElementById('message');
            const submitBtn = document.getElementById('submitBtn');
            const token = '{token}';

            form.addEventListener('submit', async (e) => {{
                e.preventDefault();
                
                const newPassword = document.getElementById('newPassword').value;
                const confirmPassword = document.getElementById('confirmPassword').value;
                
                // Validate passwords match
                if (newPassword !== confirmPassword) {{
                    showMessage('Parolele nu se potrivesc. Încercați din nou.', 'error');
                    return;
                }}
                
                // Validate password length
                if (newPassword.length < 8) {{
                    showMessage('Parola trebuie să aibă cel puțin 8 caractere.', 'error');
                    return;
                }}
                
                // Disable button and show loading
                submitBtn.disabled = true;
                submitBtn.textContent = 'Se procesează...';
                
                try {{
                    const response = await fetch('/api/password-reset/reset/', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json',
                        }},
                        body: JSON.stringify({{
                            token: token,
                            new_password: newPassword
                        }})
                    }});
                    
                    const data = await response.json();
                    
                    if (data.success) {{
                        showMessage('✅ Parola a fost resetată cu succes! Poți să te conectezi cu noua parolă.', 'success');
                        form.reset();
                    }} else {{
                        showMessage('❌ ' + data.error, 'error');
                    }}
                }} catch (error) {{
                    showMessage('❌ A apărut o eroare. Încercați din nou.', 'error');
                }} finally {{
                    submitBtn.disabled = false;
                    submitBtn.textContent = '🔐 Resetează Parola';
                }}
            }});
            
            function showMessage(text, type) {{
                message.textContent = text;
                message.className = 'message ' + type;
                message.style.display = 'block';
                
                if (type === 'success') {{
                    setTimeout(() => {{
                        message.style.display = 'none';
                    }}, 5000);
                }}
            }}
        </script>
    </body>
    </html>
    """)



from django.shortcuts import render, redirect
from django.contrib import messages

def download_page(request):
    # Get the newest AppLink entry
    app_link = AppLink.objects.first()  # Using first() because of ordering = ['-timestamp'] in Meta
    android_url = app_link.url if app_link else "#"  # Fallback to "#" if no link exists
    
    context = {
        'android_url': android_url
    }
    return render(request, 'download.html', context)


def sales_representatives_page(request):
    """View to display and handle sales representative submissions"""
    
    # Get all representatives for display
    representatives = SalesRepresentative.objects.all().order_by('-created_at')
    
    if request.method == 'POST':
        # Get form data
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        judet = request.POST.get('judet', '').strip()
        address = request.POST.get('address', '').strip()
        phone = request.POST.get('phone', '').strip()
        
        # Validation
        errors = []
        
        if not name:
            errors.append('Numele este obligatoriu.')
        if not email:
            errors.append('Email-ul este obligatoriu.')
        elif not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            errors.append('Email-ul nu este valid.')
        
        if not judet:
            errors.append('Județul este obligatoriu.')
        elif judet not in [choice[0] for choice in JUDETE]:
            errors.append('Județul selectat nu este valid.')
        
        if not phone:
            errors.append('Telefonul este obligatoriu.')
        elif not re.match(r'^\d{10}$', phone):
            errors.append('Telefonul trebuie să conțină exact 10 cifre.')
        
        # Check for duplicate email
        if email and SalesRepresentative.objects.filter(email=email).exists():
            errors.append('Un reprezentant cu acest email există deja.')
        
        # Check for duplicate phone
        if phone and SalesRepresentative.objects.filter(phone=phone).exists():
            errors.append('Un reprezentant cu acest telefon există deja.')
        
        if errors:
            # Return form with errors
            context = {
                'representatives': representatives,
                'errors': errors,
                'form_data': {
                    'name': name,
                    'email': email,
                    'judet': judet,
                    'address': address,
                    'phone': phone,
                },
                'judete': JUDETE,
            }
            return render(request, 'sales_representatives.html', context)
        
        # Create new sales representative
        try:
            SalesRepresentative.objects.create(
                name=name,
                email=email,
                judet=judet,
                address=address,
                phone=phone,
                approved=False  # Default to not approved
            )
            messages.success(request, 'Cererea ta a fost trimisă cu succes! Vei fi contactat în curând.')
            return redirect('myapp:sales_representatives')
        except Exception as e:
            errors.append(f'Eroare la salvarea datelor: {str(e)}')
            context = {
                'representatives': representatives,
                'errors': errors,
                'form_data': {
                    'name': name,
                    'email': email,
                    'judet': judet,
                    'address': address,
                    'phone': phone,
                },
                'judete': JUDETE,
            }
            return render(request, 'sales_representatives.html', context)
    
    # GET request - show form and list
    context = {
        'representatives': representatives,
        'judete': JUDETE,
        'form_data': {},
    }
    return render(request, 'sales_representatives.html', context)


def privacy_policy_page(request):
    """View to display the privacy policy page"""
    return render(request, 'privacypolicy.html')





# ---------- Helper ----------
def staff_required(view_func):
    return user_passes_test(lambda u: u.is_staff, login_url='myapp:panel_login')(view_func)

# ---------- Login Page ----------
@csrf_exempt
def admin_login(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user and user.is_staff:
            from django.contrib.auth import login
            login(request, user)
            return redirect('myapp:panel_dashboard')
        else:
            messages.error(request, "Credențiale invalide sau acces restricționat.")
    return render(request, 'admin_login.html')  # create a simple login form

# ---------- Dashboard ----------
@login_required
@staff_required
def admin_dashboard(request):
    pending_sales = SalesRepresentative.objects.filter(approved=False).count()
    pending_mechanics = UserProfile.objects.filter(user_type='supplier', is_active=False).count()

    sales_reps = SalesRepresentative.objects.all().order_by('-created_at')
    mechanics = UserProfile.objects.filter(user_type='supplier').order_by('-created_at')

    context = {
        'pending_sales': pending_sales,
        'pending_mechanics': pending_mechanics,
        'sales_reps': sales_reps,
        'mechanics': mechanics,
    }
    return render(request, 'admin_dashboard.html', context)

# ---------- Accept Sales Rep ----------
@csrf_exempt
@login_required
@staff_required
def admin_accept_sales(request, rep_id):
    rep = get_object_or_404(SalesRepresentative, representative_id=rep_id)
    if request.method == "POST":
        rep.approved = True
        rep.save()
        messages.success(request, f"Reprezentantul {rep.name} a fost acceptat.")
    return redirect('myapp:panel_dashboard')

class UserCarsListView(APIView):
    """API endpoint to fetch all cars for the current user with obligations and missing obligations"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get all cars for the authenticated user with their obligations"""
        try:
            # Get the user profile for the authenticated user
            user_profile = UserProfile.objects.get(django_user=request.user)
        except UserProfile.DoesNotExist:
            return Response({
                'success': False,
                'error': 'User profile not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Error fetching user profile: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        try:
            # Get all cars for this user with related data
            cars = Car.objects.filter(user=user_profile).select_related('brand').prefetch_related('obligations')
            
            # Serialize the cars with request context for absolute URLs
            serializer = CarSerializer(cars, many=True, context={'request': request})
            
            return Response({
                'success': True,
                'data': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Error fetching cars: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CarObligationCreateView(APIView):
    """
    API endpoint to add a new obligation for a specific car
    that belongs to the currently authenticated user.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, car_id):
        # Ensure the authenticated user has a UserProfile
        try:
            user_profile = UserProfile.objects.get(django_user=request.user)
        except UserProfile.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "error": "User profile not found",
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return Response(
                {
                    "success": False,
                    "error": f"Error fetching user profile: {str(e)}",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Ensure the car exists and is owned by the current user
        from django.shortcuts import get_object_or_404

        car = get_object_or_404(Car, car_id=car_id, user=user_profile)

        # Validate and create the obligation
        serializer = CarObligationCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        obligation = serializer.save(car=car)
        response_serializer = CarObligationSerializer(obligation)

        return Response(
            {
                "success": True,
                "data": response_serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )


class CarObligationDeleteView(APIView):
    """
    Delete a specific obligation for a car owned by the authenticated user.
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request, car_id, obligation_id):
        # Ensure the authenticated user has a UserProfile
        try:
            user_profile = UserProfile.objects.get(django_user=request.user)
        except UserProfile.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "error": "User profile not found",
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return Response(
                {
                    "success": False,
                    "error": f"Error fetching user profile: {str(e)}",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Ensure the car exists and belongs to the current user
        try:
            car = Car.objects.get(car_id=car_id, user=user_profile)
        except Car.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "error": "Car not found or you do not have permission to modify it.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # Ensure the obligation exists for this car
        try:
            obligation = CarObligation.objects.get(id=obligation_id, car=car)
        except CarObligation.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "error": "Obligation not found for this car.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        obligation.delete()

        return Response(
            {
                "success": True,
                "message": "Obligation deleted successfully.",
            },
            status=status.HTTP_200_OK,
        )


class UpdateCarObligationByIdView(APIView):
    """
    Update a car obligation by its ID for the authenticated user's car.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Validate obligation_id presence
        obligation_id = request.data.get("obligation_id")
        if not obligation_id:
            return Response(
                {
                    "success": False,
                    "error": "obligation_id is required.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate obligation_id format (must be a valid UUID)
        try:
            uuid.UUID(str(obligation_id))
        except (ValueError, TypeError, AttributeError):
            return Response(
                {
                    "success": False,
                    "error": "obligation_id must be a valid UUID.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Ensure the authenticated user has a UserProfile
        try:
            user_profile = UserProfile.objects.get(django_user=request.user)
        except UserProfile.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "error": "User profile not found",
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return Response(
                {
                    "success": False,
                    "error": f"Error fetching user profile: {str(e)}",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Fetch obligation and ensure it belongs to a car owned by this user
        try:
            obligation = CarObligation.objects.select_related("car", "car__user").get(id=obligation_id)
        except CarObligation.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "error": "Obligation not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if obligation.car.user != user_profile:
            return Response(
                {
                    "success": False,
                    "error": "You do not have permission to update this obligation.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = CarObligationUpdateByIdSerializer(
            obligation,
            data=request.data,
            partial=False,  # require the required fields defined in serializer
        )

        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        obligation = serializer.save()
        response_serializer = CarObligationSerializer(obligation)

        return Response(
            {
                "success": True,
                "data": response_serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class UserCarCreateView(APIView):
    """
    API endpoint to create a new car for the currently authenticated user.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Ensure the authenticated user has a UserProfile
        try:
            user_profile = UserProfile.objects.get(django_user=request.user)
        except UserProfile.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "error": "User profile not found",
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return Response(
                {
                    "success": False,
                    "error": f"Error fetching user profile: {str(e)}",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        serializer = CarCreateSerializer(
            data=request.data,
            context={"user_profile": user_profile},
        )

        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        car = serializer.save()
        # Re-use CarSerializer for response (includes obligations / missing obligations)
        response_serializer = CarSerializer(car, context={"request": request})

        return Response(
            {
                "success": True,
                "data": response_serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )


class UserCarUpdateView(APIView):
    """
    API endpoint to update a car for the currently authenticated user.
    """
    permission_classes = [IsAuthenticated]

    def put(self, request, car_id):
        """
        Update a car (full update) for the authenticated user.
        """
        return self._update_car(request, car_id, partial=False)

    def patch(self, request, car_id):
        """
        Partially update a car for the authenticated user.
        """
        return self._update_car(request, car_id, partial=True)

    def _update_car(self, request, car_id, partial=False):
        """
        Helper method to handle both PUT and PATCH requests.
        """
        # Ensure the authenticated user has a UserProfile
        try:
            user_profile = UserProfile.objects.get(django_user=request.user)
        except UserProfile.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "error": "User profile not found",
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return Response(
                {
                    "success": False,
                    "error": f"Error fetching user profile: {str(e)}",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Ensure the car exists and is owned by the current user
        from django.shortcuts import get_object_or_404

        try:
            car = Car.objects.get(car_id=car_id, user=user_profile)
        except Car.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "error": "Car not found or you do not have permission to update it.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # Validate and update the car
        serializer = CarUpdateSerializer(
            car,
            data=request.data,
            partial=partial,
            context={"user_profile": user_profile},
        )

        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        updated_car = serializer.save()
        # Re-use CarSerializer for response (includes obligations / missing obligations)
        response_serializer = CarSerializer(updated_car, context={"request": request})

        return Response(
            {
                "success": True,
                "data": response_serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class InitCarDetailsUpdateView(APIView):
    """
    API endpoint to initialize the car details update form.
    Returns the user's current car (if exists) and all available car brands.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get the user's current car and all car brands"""
        try:
            # Get the user profile for the authenticated user
            user_profile = UserProfile.objects.get(django_user=request.user)
        except UserProfile.DoesNotExist:
            return Response({
                'success': False,
                'error': 'User profile not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Error fetching user profile: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        try:
            # Get the user's first/most recent car (ordered by created_at descending)
            user_car = Car.objects.filter(user=user_profile).select_related('brand').prefetch_related('obligations').order_by('-created_at').first()
            
            # Serialize the car if it exists
            car_data = None
            if user_car:
                car_serializer = CarSerializer(user_car, context={'request': request})
                car_data = car_serializer.data
            
            # Get all car brands
            brands_qs = CarBrand.objects.all().order_by('brand_name')
            brand_serializer = CarBrandSerializer(brands_qs, many=True, context={"request": request})
            
            return Response({
                'success': True,
                'data': {
                    'current_car': car_data,
                    'available_brands': brand_serializer.data
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Error fetching car details: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ---------- Activate Mechanic ----------
@csrf_exempt
@login_required
@staff_required
def admin_activate_mechanic(request, user_id):
    mech = get_object_or_404(UserProfile, user_id=user_id, user_type='supplier')
    if request.method == "POST":
        mech.is_active = True
        mech.save()
        messages.success(request, f"Mecanicul {mech.full_name} a fost activat.")
    return redirect('myapp:panel_dashboard')


# views.py

class AddCarObligationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            user_profile = UserProfile.objects.get(django_user=request.user)
            current_car = Car.objects.filter(user=user_profile).order_by('-created_at').first()
            
            if not current_car:
                return Response({
                    "success": False,
                    "message": "No current car found"
                }, status=status.HTTP_404_NOT_FOUND)

            # --- DUPLICATE CHECK START ---
            obligation_type = request.data.get('obligation_type')
            
            if CarObligation.objects.filter(car=current_car, obligation_type=obligation_type).exists():
                return Response({
                    "success": False,
                    "message": f"An obligation of type '{obligation_type}' already exists for this car."
                }, status=status.HTTP_400_BAD_REQUEST)
            # --- DUPLICATE CHECK END ---

            serializer = AddCarObligationSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(car=current_car)
                return Response({
                    "success": True,
                    "message": "Obligation added successfully"
                }, status=status.HTTP_201_CREATED)
            
            return Response({
                "success": False,
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                "success": False,
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SuggestBusinessesForObligationView(APIView):
    """API endpoint to suggest golden tier businesses that can handle a given car obligation"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get obligation_type from query parameters
        obligation_type = request.query_params.get('obligation_type')
        
        # Validate required parameter
        if not obligation_type:
            return Response({
                'success': False,
                'error': 'obligation_type parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate obligation_type is in ObligationDefinition choices
        valid_obligation_types = [choice[0] for choice in ObligationDefinition.choices]
        if obligation_type not in valid_obligation_types:
            return Response({
                'success': False,
                'error': f'Invalid obligation_type. Valid types are: {", ".join(valid_obligation_types)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Map obligation type to service category
        service_category = OBLIGATION_TO_SERVICE_MAP.get(obligation_type)
        
        # If no mapping exists, return empty results with a message
        if not service_category:
            return Response({
                'success': True,
                'message': f'No service providers available for obligation type: {obligation_type}',
                'data': [],
                'count': 0,
                'obligation_type': obligation_type
            }, status=status.HTTP_200_OK)
        
        # Query businesses: filter by service category, golden tier subscription, and active status
        businesses = SupplierBrandService.objects.filter(
            services__category=service_category,
            supplier__subscription_plan='gold',
            active=True
        ).prefetch_related(
            'services__tags',
            'supplier__business_hours',
            'supplier__supplier_reviews'
        ).distinct()
        
        # Deduplicate by supplier_id (keep first occurrence)
        seen_supplier_ids = set()
        unique_businesses = []
        for business in businesses:
            supplier_id = str(business.supplier.user_id)
            if supplier_id not in seen_supplier_ids:
                seen_supplier_ids.add(supplier_id)
                unique_businesses.append(business)
        
        # Serialize the results (without services field)
        serializer = SupplierBrandServiceWithoutServicesSerializer(unique_businesses, many=True)
        
        return Response({
            'success': True,
            'message': f'Businesses found for obligation type: {obligation_type}',
            'data': serializer.data,
            'count': len(serializer.data),
            'obligation_type': obligation_type,
            'service_category': service_category
        }, status=status.HTTP_200_OK)
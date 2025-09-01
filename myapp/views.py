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
from .models import UserProfile, OTPVerification, CarBrand, SupplierBrandService, BusinessHours, Service, Review, SERVICE_CATEGORIES, Request, Notification, CoverPhoto, UserDevice
from django.db import models
from .utils import generate_otp, send_otp_email
from django.utils import timezone
from datetime import timedelta
import re
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import CarBrandSerializer, SupplierBrandServiceSerializer, ServiceWithTagsSerializer, SupplierProfileSerializer, ReviewSummarySerializer, ReviewListSerializer, RequestCreateSerializer, RequestListSerializer, NotificationSerializer
from .onesignal_service import OneSignalService
import math
from decimal import Decimal
from rest_framework import viewsets
from firebase_admin import auth as firebase_auth


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
                is_active=False,  # Default to False for suppliers
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
            
            # Send OTP email
            email_sent = send_otp_email(
                email=email,
                otp=otp,
                subject="Codul tău de verificare FixCars.ro - Supplier Account"
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
        
        # Add distance to each queryset object
        for service in qs:
            service.distance_km = calculate_distance(service.latitude, service.longitude)
        
        # Sort by distance (closest first)
        sorted_services = sorted(qs, key=lambda x: x.distance_km)
        
        # Limit to first 30 results
        limited_services = sorted_services[:30]
        
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
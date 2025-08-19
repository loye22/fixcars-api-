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
from .models import UserProfile, OTPVerification, CarBrand, SupplierBrandService, BusinessHours, Service, Review, SERVICE_CATEGORIES, Request, Notification
from .utils import generate_otp, send_otp_email
from django.utils import timezone
from datetime import timedelta
import re
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import CarBrandSerializer, SupplierBrandServiceSerializer, ServiceWithTagsSerializer, SupplierProfileSerializer, ReviewSummarySerializer, ReviewListSerializer, RequestCreateSerializer
import math
from decimal import Decimal


# Create your views here.

def home(request):
    """Simple home page view"""
    return HttpResponse("<h1>home</h1>")


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
                    'message':  'Contul este suspendat. Vă rugăm să contactați suportul.'
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
        # Uniqueness validation in the view
        if Request.objects.filter(client=client_profile, supplier_id=supplier_id).exists():
            return Response({'success': False, 'error': 'Ai făcut deja o cerere către acest furnizor. Te rugăm să mai aștepți puțin până te va contacta sau sună-l direct.', 'code': 'duplicate_request'}, status=400)
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
            return Response({'success': True, 'message': 'Cererea a fost creată cu succes.'}, status=201)
        else:
            return Response({'success': False, 'errors': serializer.errors}, status=400)
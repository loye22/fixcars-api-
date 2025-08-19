from rest_framework import serializers
from .models import CarBrand, SupplierBrandService, Service, UserProfile, BusinessHours, Tag, Review, CoverPhoto, Request, Notification
from django.utils import timezone

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['tag_id', 'tag_name']

class CarBrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarBrand
        fields = [
            "brand_id",
            "brand_name",
            "brand_photo",
        ]

class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['service_id', 'service_name', 'description', 'service_photo', 'category']

class ServiceWithTagsSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Service
        fields = ['service_id', 'service_name', 'description', 'service_photo', 'category', 'tags']

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['full_name']

class SupplierBrandServiceSerializer(serializers.ModelSerializer):
    supplier_id = serializers.CharField(source='supplier.user_id', read_only=True)
    supplier_name = serializers.CharField(source='supplier.full_name', read_only=True)
    supplier_photo = serializers.CharField(source='supplier.profile_photo', read_only=True)
    supplier_address = serializers.CharField(source='supplier.business_address', read_only=True)
    supplier_phone = serializers.CharField(source='supplier.phone', read_only=True)
    brand_name = serializers.CharField(source='brand.brand_name', read_only=True)
    brand_photo = serializers.CharField(source='brand.brand_photo', read_only=True)
    is_open = serializers.SerializerMethodField()
    review_score = serializers.SerializerMethodField()
    total_reviews = serializers.SerializerMethodField()
    distance_km = serializers.SerializerMethodField()
    services = ServiceWithTagsSerializer(many=True, read_only=True)

    class Meta:
        model = SupplierBrandService
        fields = [
            'id',
            'supplier_id',
            'supplier_name',
            'supplier_photo',
            'supplier_address',
            'supplier_phone',
            'brand_name',
            'brand_photo',
            'is_open',
            'review_score',
            'total_reviews',
            'distance_km',
            'city',
            'sector',
            'latitude',
            'longitude',
            'price',
            'active',
            'services',
            'photo_url'
        ]

    def get_is_open(self, obj):
        try:
            business_hours = obj.supplier.business_hours.first()
            if not business_hours:
                return False

            now = timezone.now()
            current_day = now.weekday()  # 0=Monday, 6=Sunday
            current_time = now.time()

            if current_day == 0:  # Monday
                return not business_hours.monday_closed and business_hours.monday_open <= current_time <= business_hours.monday_close
            elif current_day == 1:  # Tuesday
                return not business_hours.tuesday_closed and business_hours.tuesday_open <= current_time <= business_hours.tuesday_close
            elif current_day == 2:  # Wednesday
                return not business_hours.wednesday_closed and business_hours.wednesday_open <= current_time <= business_hours.wednesday_close
            elif current_day == 3:  # Thursday
                return not business_hours.thursday_closed and business_hours.thursday_open <= current_time <= business_hours.thursday_close
            elif current_day == 4:  # Friday
                return not business_hours.friday_closed and business_hours.friday_open <= current_time <= business_hours.friday_close
            elif current_day == 5:  # Saturday
                return not business_hours.saturday_closed and business_hours.saturday_open <= current_time <= business_hours.saturday_close
            elif current_day == 6:  # Sunday
                return not business_hours.sunday_closed and business_hours.sunday_open <= current_time <= business_hours.sunday_close

            return False
        except:
            return False

    def get_review_score(self, obj):
        reviews = obj.supplier.supplier_reviews.all()
        if reviews.exists():
            return sum(review.rating for review in reviews) / reviews.count()
        return 0

    def get_total_reviews(self, obj):
        return obj.supplier.supplier_reviews.count()

    def get_distance_km(self, obj):
        """Get the distance in kilometers that was calculated in the view"""
        return getattr(obj, 'distance_km', None)

class SupplierProfileSerializer(serializers.ModelSerializer):
    """Serializer for supplier profile data (excluding sensitive fields)"""
    class Meta:
        model = UserProfile
        fields = [
            'user_id', 'full_name', 'email', 'phone', 'profile_photo', 
            'business_address', 'city', 'sector', 'latitude', 'longitude', 
            'bio', 'is_active', 'is_verified', 'created_at'
        ]

class CoverPhotoSerializer(serializers.ModelSerializer):
    """Serializer for cover photos - returns just the URL"""
    class Meta:
        model = CoverPhoto
        fields = ['photo_url']

class ReviewSummarySerializer(serializers.ModelSerializer):
    """Serializer for review summary data"""
    clientName = serializers.CharField(source='client.full_name', read_only=True)
    
    class Meta:
        model = Review
        fields = ['comment', 'rating', 'clientName', 'created_at']

class CarBrandSummarySerializer(serializers.ModelSerializer):
    """Serializer for car brand summary in supplier services"""
    url = serializers.CharField(source='brand_photo', read_only=True)
    name = serializers.CharField(source='brand_name', read_only=True)
    
    class Meta:
        model = CarBrand
        fields = ['url', 'name']

class ServiceSummarySerializer(serializers.ModelSerializer):
    """Serializer for service summary in supplier services"""
    serviceName = serializers.CharField(source='service_name', read_only=True)
    
    class Meta:
        model = Service
        fields = ['serviceName', 'description']

class ReviewListSerializer(serializers.ModelSerializer):
    """Serializer for detailed review data in reviews list"""
    client_name = serializers.CharField(source='client.full_name', read_only=True)
    client_photo = serializers.CharField(source='client.profile_photo', read_only=True)
    supplier_name = serializers.CharField(source='supplier.full_name', read_only=True)
    supplier_photo = serializers.CharField(source='supplier.profile_photo', read_only=True)
    supplier_id = serializers.CharField(source='supplier.user_id', read_only=True)
    
    class Meta:
        model = Review
        fields = [
            'review_id', 
            'client_name', 
            'client_photo', 
            'supplier_name', 
            'supplier_photo', 
            'supplier_id',
            'rating', 
            'comment', 
            'created_at'
        ]

class RequestCreateSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(required=False)
    class Meta:
        model = Request
        fields = ['supplier', 'longitude', 'latitude', 'phone_number', 'reason']

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'notification_id',
            'type',
            'message',
            'is_read',
            'created_at',
        ]



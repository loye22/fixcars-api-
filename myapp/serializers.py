from rest_framework import serializers
from .models import CarBrand, SupplierBrandService, Service, UserProfile, BusinessHours, Tag
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



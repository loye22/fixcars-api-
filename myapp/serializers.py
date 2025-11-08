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
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()

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

    def get_latitude(self, obj):
        supplier_lat = getattr(obj.supplier, 'latitude', None)
        return float(supplier_lat) if supplier_lat is not None else 0.0

    def get_longitude(self, obj):
        supplier_lng = getattr(obj.supplier, 'longitude', None)
        return float(supplier_lng) if supplier_lng is not None else 0.0

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


class RequestListSerializer(serializers.ModelSerializer):
    """Serializer for listing requests with client and supplier information"""
    client_name = serializers.CharField(source='client.full_name', read_only=True)
    client_photo = serializers.CharField(source='client.profile_photo', read_only=True)
    client_id = serializers.CharField(source='client.user_id', read_only=True)
    supplier_name = serializers.CharField(source='supplier.full_name', read_only=True)
    supplier_photo = serializers.CharField(source='supplier.profile_photo', read_only=True)
    supplier_id = serializers.CharField(source='supplier.user_id', read_only=True)
    
    class Meta:
        model = Request
        fields = [
            'id',
            'client_name',
            'client_photo', 
            'client_id',
            'supplier_name',
            'supplier_photo',
            'supplier_id',
            'longitude',
            'latitude',
            'status',
            'phone_number',
            'reason',
            'created_at'
        ]


class SupplierBrandServiceCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new SupplierBrandService"""
    brand_id = serializers.UUIDField(write_only=True)
    service_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        help_text="List of service IDs to associate with this supplier brand service"
    )
    sector = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    
    class Meta:
        model = SupplierBrandService
        fields = [
            'brand_id',
            'service_ids',
            'city',
            'sector',
            'latitude',
            'longitude',
            'price',
        ]
    
    def validate_brand_id(self, value):
        """Validate that the brand exists"""
        try:
            CarBrand.objects.get(brand_id=value)
            return value
        except CarBrand.DoesNotExist:
            raise serializers.ValidationError("Brand not found.")
    
    def validate_service_ids(self, value):
        """Validate that all service IDs exist"""
        if not value:
            raise serializers.ValidationError("At least one service must be provided.")
        
        existing_services = Service.objects.filter(service_id__in=value)
        if existing_services.count() != len(value):
            raise serializers.ValidationError("One or more services not found.")
        
        return value
    
    def validate(self, data):
        """Validate that none of the selected services already exist for the given brand"""
        # Get supplier from context
        supplier = self.context.get('supplier')
        if not supplier:
            return data
        
        brand_id = data.get('brand_id')
        service_ids = data.get('service_ids', [])
        
        if brand_id and service_ids:
            # Convert service_ids to a set for comparison
            service_ids_set = set(service_ids)
            
            # Check for existing SupplierBrandService with same supplier and brand
            existing_entries = SupplierBrandService.objects.filter(
                supplier=supplier,
                brand_id=brand_id
            ).prefetch_related('services')
            
            # Collect all existing service IDs for this brand
            existing_service_ids = set()
            for entry in existing_entries:
                entry_service_ids = set(entry.services.values_list('service_id', flat=True))
                existing_service_ids.update(entry_service_ids)
            
            # Check if any of the selected services already exist for this brand
            overlapping_services = service_ids_set.intersection(existing_service_ids)
            if overlapping_services:
                # Get service names for better error message
                overlapping_service_names = Service.objects.filter(
                    service_id__in=overlapping_services
                ).values_list('service_name', flat=True)
                
                service_names_str = ', '.join(overlapping_service_names)
                raise serializers.ValidationError(
                    f"The following service(s) are already associated with this brand: {service_names_str}. "
                    "Please remove them from your selection or update the existing entry."
                )
        
        return data
    
    def create(self, validated_data):
        """Create a new SupplierBrandService with active=True by default"""
        service_ids = validated_data.pop('service_ids')
        brand_id = validated_data.pop('brand_id')
        
        # Get supplier from context (set by the view from authenticated user)
        supplier = self.context.get('supplier')
        if not supplier:
            raise serializers.ValidationError("Supplier not found. Please ensure you are authenticated as a supplier.")
        
        # Handle optional price field - if None, use default 0
        price = validated_data.pop('price', None)
        if price is None:
            price = 0
        
        # Get the brand object
        brand = CarBrand.objects.get(brand_id=brand_id)
        
        # Create the SupplierBrandService with active=True
        supplier_brand_service = SupplierBrandService.objects.create(
            supplier=supplier,
            brand=brand,
            active=True,  # Set active=True by default
            price=price,
            **validated_data
        )
        
        # Add the services (ManyToMany relationship)
        services = Service.objects.filter(service_id__in=service_ids)
        supplier_brand_service.services.set(services)
        
        return supplier_brand_service



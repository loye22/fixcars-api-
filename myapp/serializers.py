from rest_framework import serializers
from .models import CarBrand, SupplierBrandService, Service, UserProfile, BusinessHours, Tag, Review, CoverPhoto, Request, Notification, Car, CarObligation, ObligationDefinition, ReminderType
from django.utils import timezone

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['tag_id', 'tag_name']

class CarBrandSerializer(serializers.ModelSerializer):
    brand_photo = serializers.SerializerMethodField()
    
    class Meta:
        model = CarBrand
        fields = [
            "brand_id",
            "brand_name",
            "brand_photo",
        ]
    
    def get_brand_photo(self, obj):
        """Get the full URL for the brand photo"""
        if obj.brand_photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.brand_photo.url)
            return obj.brand_photo.url
        return None

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

class SupplierBrandServiceWithoutServicesSerializer(SupplierBrandServiceSerializer):
    """Serializer for SupplierBrandService that excludes the services field"""
    class Meta(SupplierBrandServiceSerializer.Meta):
        fields = [field for field in SupplierBrandServiceSerializer.Meta.fields if field != 'services']


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


class BusinessHoursSerializer(serializers.ModelSerializer):
    """Serializer for BusinessHours model - used for reading business hours"""
    monday = serializers.SerializerMethodField()
    tuesday = serializers.SerializerMethodField()
    wednesday = serializers.SerializerMethodField()
    thursday = serializers.SerializerMethodField()
    friday = serializers.SerializerMethodField()
    saturday = serializers.SerializerMethodField()
    sunday = serializers.SerializerMethodField()
    
    class Meta:
        model = BusinessHours
        fields = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        read_only_fields = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    
    def get_monday(self, obj):
        return {
            'open': str(obj.monday_open),
            'close': str(obj.monday_close),
            'closed': obj.monday_closed
        }
    
    def get_tuesday(self, obj):
        return {
            'open': str(obj.tuesday_open),
            'close': str(obj.tuesday_close),
            'closed': obj.tuesday_closed
        }
    
    def get_wednesday(self, obj):
        return {
            'open': str(obj.wednesday_open),
            'close': str(obj.wednesday_close),
            'closed': obj.wednesday_closed
        }
    
    def get_thursday(self, obj):
        return {
            'open': str(obj.thursday_open),
            'close': str(obj.thursday_close),
            'closed': obj.thursday_closed
        }
    
    def get_friday(self, obj):
        return {
            'open': str(obj.friday_open),
            'close': str(obj.friday_close),
            'closed': obj.friday_closed
        }
    
    def get_saturday(self, obj):
        return {
            'open': str(obj.saturday_open),
            'close': str(obj.saturday_close),
            'closed': obj.saturday_closed
        }
    
    def get_sunday(self, obj):
        return {
            'open': str(obj.sunday_open),
            'close': str(obj.sunday_close),
            'closed': obj.sunday_closed
        }


class BusinessHoursUpdateSerializer(serializers.Serializer):
    """Serializer for updating BusinessHours - accepts nested day objects"""
    monday = serializers.DictField(required=False)
    tuesday = serializers.DictField(required=False)
    wednesday = serializers.DictField(required=False)
    thursday = serializers.DictField(required=False)
    friday = serializers.DictField(required=False)
    saturday = serializers.DictField(required=False)
    sunday = serializers.DictField(required=False)
    
    def validate_day_data(self, day_data, day_name):
        """Validate a single day's data"""
        if not isinstance(day_data, dict):
            raise serializers.ValidationError(f"{day_name} must be an object")
        
        required_fields = ['open', 'close', 'closed']
        for field in required_fields:
            if field not in day_data:
                raise serializers.ValidationError(f"{day_name}.{field} is required")
        
        # Validate time format (HH:MM in 24-hour format)
        for time_field in ['open', 'close']:
            time_value = day_data[time_field]
            if not isinstance(time_value, str):
                raise serializers.ValidationError(f"{day_name}.{time_field} must be a string in HH:MM format")
            
            try:
                # Try to parse the time
                from datetime import datetime
                datetime.strptime(time_value, '%H:%M')
            except ValueError:
                raise serializers.ValidationError(f"{day_name}.{time_field} must be in HH:MM format (24-hour system)")
        
        # Validate closed is boolean
        if not isinstance(day_data['closed'], bool):
            raise serializers.ValidationError(f"{day_name}.closed must be a boolean")
        
        return day_data
    
    def validate(self, data):
        """Validate all day data"""
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        for day in days:
            if day in data:
                data[day] = self.validate_day_data(data[day], day)
        return data
    
    def update(self, instance, validated_data):
        """Update the BusinessHours instance with validated data"""
        from django.utils.dateparse import parse_time
        
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        
        for day in days:
            if day in validated_data:
                day_data = validated_data[day]
                # Parse time strings to Time objects
                open_time = parse_time(day_data['open'])
                close_time = parse_time(day_data['close'])
                
                if open_time is None or close_time is None:
                    raise serializers.ValidationError(f"{day}: Invalid time format. Use HH:MM (24-hour system)")
                
                setattr(instance, f"{day}_open", open_time)
                setattr(instance, f"{day}_close", close_time)
                setattr(instance, f"{day}_closed", day_data['closed'])
        
        instance.save()
        return instance


class CarObligationSerializer(serializers.ModelSerializer):
    """Serializer for CarObligation model"""
    obligation_type_display = serializers.CharField(source='get_obligation_type_display', read_only=True)
    reminder_type_display = serializers.CharField(source='get_reminder_type_display', read_only=True)
    due_date = serializers.SerializerMethodField()
    
    class Meta:
        model = CarObligation
        fields = [
            'id',
            'obligation_type',
            'obligation_type_display',
            'reminder_type',
            'reminder_type_display',
            'doc_url',
            'due_date',
            'note',
            'created_at',
            'updated_at',
        ]
    
    def get_due_date(self, obj):
        """Convert due_date to date, handling both date and datetime objects"""
        if obj.due_date:
            # Import here to avoid circular imports
            from datetime import datetime, date
            # If it's a datetime, convert to date
            if isinstance(obj.due_date, datetime):
                return obj.due_date.date()
            # If it's already a date, return as-is
            elif isinstance(obj.due_date, date):
                return obj.due_date
            # If it's a string or other type, try to convert
            else:
                return obj.due_date
        return None


class CarObligationCreateSerializer(serializers.ModelSerializer):
    """
    Serializer used when creating/updating a car obligation.
    Uses the native DateField for `due_date` so it can be written,
    while the read-only CarObligationSerializer is used for responses.
    """
    class Meta:
        model = CarObligation
        fields = [
            'obligation_type',
            'reminder_type',
            'doc_url',
            'due_date',
            'note',
        ]


class CarObligationUpdateByIdSerializer(serializers.ModelSerializer):
    """
    Serializer for updating an existing car obligation by its ID.
    Only allows updating the specified writable fields.
    """
    obligation_type = serializers.ChoiceField(choices=ObligationDefinition.choices, required=True)
    reminder_type = serializers.ChoiceField(choices=ReminderType.choices, required=True)
    due_date = serializers.DateField(required=True)
    doc_url = serializers.URLField(required=False, allow_null=True, allow_blank=True)
    note = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = CarObligation
        fields = [
            'obligation_type',
            'reminder_type',
            'due_date',
            'doc_url',
            'note',
        ]


class CarSerializer(serializers.ModelSerializer):
    """Serializer for Car model with brand information"""
    id = serializers.UUIDField(source='car_id', read_only=True)
    brand_name = serializers.CharField(source='brand.brand_name', read_only=True)
    brand_id = serializers.UUIDField(source='brand.brand_id', read_only=True)
    brand_photo = serializers.SerializerMethodField()
    existing_obligations = CarObligationSerializer(many=True, read_only=True, source='obligations')
    missing_obligations = serializers.SerializerMethodField()
    
    class Meta:
        model = Car
        fields = [
            'id',
            'car_id',
            'brand_id',
            'brand_name',
            'brand_photo',
            'model',
            'year',
            'license_plate',
            'vin',
            'current_km',
            'last_km_updated_at',
            'created_at',
            'updated_at',
            'existing_obligations',
            'missing_obligations',
        ]
    
    def get_brand_photo(self, obj):
        """Get the full URL for the brand photo"""
        if obj.brand and obj.brand.brand_photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.brand.brand_photo.url)
            return obj.brand.brand_photo.url
        return None
    
    def get_missing_obligations(self, obj):
        """Get all obligation types that don't have a CarObligation record for this car"""
        existing_obligation_types = set(
            obj.obligations.values_list('obligation_type', flat=True)
        )
        
        # Get all obligation types from ObligationDefinition
        all_obligation_types = set([choice[0] for choice in ObligationDefinition.choices])
        
        missing_types = all_obligation_types - existing_obligation_types
        
        # Return list of missing obligation types with their display names
        missing_obligations = []
        for obligation_type in missing_types:
            # Get the display label for this obligation type
            obligation_label = dict(ObligationDefinition.choices).get(obligation_type, obligation_type)
            missing_obligations.append({
                'obligation_type': obligation_type,
                'obligation_type_display': obligation_label,
            })
        
        return missing_obligations


class CarCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/updating a Car for the current user.
    The owner (user) is taken from the authenticated request user in the view.
    """
    brand_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = Car
        fields = [
            'brand_id',
            'model',
            'year',
            'license_plate',
            'vin',
            'current_km',
            'last_km_updated_at',
        ]

    def validate_brand_id(self, value):
        from .models import CarBrand

        try:
            CarBrand.objects.get(brand_id=value)
        except CarBrand.DoesNotExist:
            raise serializers.ValidationError("Selected brand does not exist.")
        return value

    def validate(self, attrs):
        """
        Prevent creating duplicate cars for the same user based on:
        - license_plate (case-insensitive), if provided
        - vin (case-insensitive), if provided
        """
        user_profile = self.context.get('user_profile')
        if not user_profile:
            return attrs

        license_plate = attrs.get('license_plate')
        vin = attrs.get('vin')

        queryset = Car.objects.filter(user=user_profile)
        errors = {}

        if license_plate:
            if queryset.filter(license_plate__iexact=license_plate).exists():
                errors['license_plate'] = [
                    'A car with this license plate already exists for the current user.'
                ]

        if vin:
            if queryset.filter(vin__iexact=vin).exists():
                errors['vin'] = [
                    'A car with this VIN already exists for the current user.'
                ]

        if errors:
            raise serializers.ValidationError(errors)

        return attrs

    def create(self, validated_data):
        """
        Create a Car instance for the given user (passed in context as `user_profile`).
        """
        from .models import CarBrand

        user_profile = self.context.get('user_profile')
        if not user_profile:
            raise serializers.ValidationError("User profile not provided in serializer context.")

        brand_id = validated_data.pop('brand_id')
        brand = CarBrand.objects.get(brand_id=brand_id)

        car = Car.objects.create(
            user=user_profile,
            brand=brand,
            **validated_data,
        )
        return car


class CarUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating a Car for the current user.
    Excludes the current car instance from duplicate checks.
    """
    brand_id = serializers.UUIDField(write_only=True, required=False)

    class Meta:
        model = Car
        fields = [
            'brand_id',
            'model',
            'year',
            'license_plate',
            'vin',
            'current_km',
            'last_km_updated_at',
        ]

    def validate_brand_id(self, value):
        from .models import CarBrand

        # Allow None for optional updates
        if value is None:
            return value

        try:
            CarBrand.objects.get(brand_id=value)
        except CarBrand.DoesNotExist:
            raise serializers.ValidationError("Selected brand does not exist.")
        return value

    def validate(self, attrs):
        """
        Prevent updating to duplicate license_plate or vin for the same user,
        excluding the current car instance from the check.
        """
        user_profile = self.context.get('user_profile')
        car_instance = self.instance  # The car being updated
        
        if not user_profile:
            return attrs

        license_plate = attrs.get('license_plate')
        vin = attrs.get('vin')

        # Exclude the current car from duplicate checks
        queryset = Car.objects.filter(user=user_profile)
        if car_instance:
            queryset = queryset.exclude(car_id=car_instance.car_id)
        
        errors = {}

        # Only check if license_plate is being updated and has a non-empty value
        if license_plate is not None:
            license_plate_value = license_plate.strip() if isinstance(license_plate, str) else license_plate
            if license_plate_value:
                if queryset.filter(license_plate__iexact=license_plate).exists():
                    errors['license_plate'] = [
                        'A car with this license plate already exists for the current user.'
                    ]

        # Only check if vin is being updated and has a non-empty value
        if vin is not None:
            vin_value = vin.strip() if isinstance(vin, str) else vin
            if vin_value:
                if queryset.filter(vin__iexact=vin).exists():
                    errors['vin'] = [
                        'A car with this VIN already exists for the current user.'
                    ]

        if errors:
            raise serializers.ValidationError(errors)

        return attrs

    def update(self, instance, validated_data):
        """
        Update a Car instance.
        """
        from .models import CarBrand

        # Handle brand_id if provided (it's popped to prevent it from being set as a model attribute)
        brand_id = validated_data.pop('brand_id', None)
        if brand_id is not None:
            # If brand_id is provided, update the brand
            try:
                brand = CarBrand.objects.get(brand_id=brand_id)
                instance.brand = brand
            except CarBrand.DoesNotExist:
                raise serializers.ValidationError({"brand_id": "Selected brand does not exist."})

        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance




# serializers.py

class AddCarObligationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarObligation
        fields = [
            'obligation_type', 
            'reminder_type', 
            'due_date', 
            'doc_url', 
            'note'
        ]
        extra_kwargs = {
            'obligation_type': {'required': True},
            'reminder_type': {'required': True},
            'due_date': {'required': True},
        }
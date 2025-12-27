from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from .models import (
    SalesRepresentative, SupplierReferral, UserProfile, CarBrand, Tag, 
    Service, SupplierBrandService, Review, Notification, Request, 
    OTPVerification, BusinessHours, CoverPhoto, UserDevice, AppLink, 
    Car, CarObligation
)

# --- CLEAN & EFFECTIVE RESOURCES ---

class TagResource(resources.ModelResource):
    class Meta:
        model = Tag
        import_id_fields = ('tag_id',)
        skip_unchanged = True

class CarBrandResource(resources.ModelResource):
    class Meta:
        model = CarBrand
        import_id_fields = ('brand_id',)
        fields = ('brand_id', 'brand_name', 'brand_photo')
        skip_unchanged = True

class CoverPhotoResource(resources.ModelResource):
    class Meta:
        model = CoverPhoto
        import_id_fields = ('photo_id',)
        skip_unchanged = True

class ServiceResource(resources.ModelResource):
    class Meta:
        model = Service
        import_id_fields = ('service_id',)
        fields = ('service_id', 'service_name', 'description', 'service_photo', 'category', 'tags')
        skip_unchanged = True

class UserProfileResource(resources.ModelResource):
    class Meta:
        model = UserProfile
        import_id_fields = ('user_id',)
        exclude = ('created_at',)
        skip_unchanged = True

class SupplierBrandServiceResource(resources.ModelResource):
    class Meta:
        model = SupplierBrandService
        # This model uses default auto-incrementing ID
        import_id_fields = ('id',)
        skip_unchanged = True

class ReviewResource(resources.ModelResource):
    class Meta:
        model = Review
        import_id_fields = ('review_id',)
        skip_unchanged = True

class NotificationResource(resources.ModelResource):
    class Meta:
        model = Notification
        import_id_fields = ('notification_id',)
        skip_unchanged = True

class RequestResource(resources.ModelResource):
    class Meta:
        model = Request
        import_id_fields = ('id',)
        skip_unchanged = True

class OTPVerificationResource(resources.ModelResource):
    class Meta:
        model = OTPVerification
        import_id_fields = ('id',)
        skip_unchanged = True

class BusinessHoursResource(resources.ModelResource):
    class Meta:
        model = BusinessHours
        # Since this links to supplier, we use ID or supplier as the identifier
        import_id_fields = ('id',)
        skip_unchanged = True

class UserDeviceResource(resources.ModelResource):
    class Meta:
        model = UserDevice
        import_id_fields = ('id',)
        skip_unchanged = True

class SalesRepresentativeResource(resources.ModelResource):
    class Meta:
        model = SalesRepresentative
        import_id_fields = ('representative_id',)
        fields = ('representative_id', 'name', 'email', 'judet', 'address', 'phone', 'approved', 'created_at')
        skip_unchanged = True

class SupplierReferralResource(resources.ModelResource):
    class Meta:
        model = SupplierReferral
        import_id_fields = ('referral_id',)
        skip_unchanged = True

class AppLinkResource(resources.ModelResource):
    class Meta:
        model = AppLink
        import_id_fields = ('id',)
        skip_unchanged = True

class CarResource(resources.ModelResource):
    class Meta:
        model = Car
        import_id_fields = ('car_id',)
        skip_unchanged = True

class CarObligationResource(resources.ModelResource):
    class Meta:
        model = CarObligation
        import_id_fields = ('id',)
        skip_unchanged = True
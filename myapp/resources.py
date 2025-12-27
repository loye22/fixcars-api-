from import_export import resources
from .models import (
    SalesRepresentative, SupplierReferral, UserProfile, CarBrand, Tag, 
    Service, SupplierBrandService, Review, Notification, Request, 
    OTPVerification, BusinessHours, CoverPhoto, UserDevice, AppLink, 
    Car, CarObligation
)

# --- CONFIGURATION NOTES ---
# import_id_fields: Tells Django which field is the Primary Key.
# skip_unchanged: Prevents duplicate processing if data hasn't changed.
# report_skipped: Shows you which rows were skipped in the admin UI.

class TagResource(resources.ModelResource):
    class Meta:
        model = Tag
        import_id_fields = ('tag_id',)
        skip_unchanged = True

class CarBrandResource(resources.ModelResource):
    class Meta:
        model = CarBrand
        import_id_fields = ('brand_id',)
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
        skip_unchanged = True

class UserProfileResource(resources.ModelResource):
    class Meta:
        model = UserProfile
        import_id_fields = ('user_id',)
        exclude = ('created_at', 'django_user')
        skip_unchanged = True

class SupplierBrandServiceResource(resources.ModelResource):
    class Meta:
        model = SupplierBrandService
        import_id_fields = ('id',)
        skip_unchanged = True

class ReviewResource(resources.ModelResource):
    class Meta:
        model = Review
        import_id_fields = ('review_id',)
        exclude = ('created_at',)
        skip_unchanged = True

class NotificationResource(resources.ModelResource):
    class Meta:
        model = Notification
        import_id_fields = ('notification_id',)
        exclude = ('created_at',)
        skip_unchanged = True

class RequestResource(resources.ModelResource):
    class Meta:
        model = Request
        import_id_fields = ('id',)
        exclude = ('created_at',)
        skip_unchanged = True

class OTPVerificationResource(resources.ModelResource):
    class Meta:
        model = OTPVerification
        # Uses default Django ID if not specified in model
        exclude = ('created_at',)
        skip_unchanged = True

class BusinessHoursResource(resources.ModelResource):
    class Meta:
        model = BusinessHours
        import_id_fields = ('supplier',) # unique_together field
        skip_unchanged = True

class UserDeviceResource(resources.ModelResource):
    class Meta:
        model = UserDevice
        exclude = ('created_at',)
        skip_unchanged = True

class SalesRepresentativeResource(resources.ModelResource):
    class Meta:
        model = SalesRepresentative
        import_id_fields = ('representative_id',)
        exclude = ('created_at',)
        skip_unchanged = True

class SupplierReferralResource(resources.ModelResource):
    class Meta:
        model = SupplierReferral
        import_id_fields = ('referral_id',)
        exclude = ('created_at',)
        skip_unchanged = True

class AppLinkResource(resources.ModelResource):
    class Meta:
        model = AppLink
        exclude = ('timestamp',)
        skip_unchanged = True

class CarResource(resources.ModelResource):
    class Meta:
        model = Car
        import_id_fields = ('car_id',)
        exclude = ('created_at', 'updated_at')
        skip_unchanged = True

class CarObligationResource(resources.ModelResource):
    class Meta:
        model = CarObligation
        import_id_fields = ('id',)
        exclude = ('created_at', 'updated_at')
        skip_unchanged = True
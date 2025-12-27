from import_export import resources
from .models import (
    SalesRepresentative, SupplierReferral, UserProfile, CarBrand, Tag, 
    Service, SupplierBrandService, Review, Notification, Request, 
    OTPVerification, BusinessHours, CoverPhoto, UserDevice, AppLink, 
    Car, CarObligation
)

# 1. TAG
class TagResource(resources.ModelResource):
    class Meta:
        model = Tag
        import_id_fields = ('tag_id',)
        skip_unchanged = True

# 2. CAR BRAND
class CarBrandResource(resources.ModelResource):
    class Meta:
        model = CarBrand
        import_id_fields = ('brand_id',)
        fields = ('brand_id', 'brand_name', 'brand_photo')
        skip_unchanged = True

# 3. COVER PHOTO
class CoverPhotoResource(resources.ModelResource):
    class Meta:
        model = CoverPhoto
        import_id_fields = ('photo_id',)
        skip_unchanged = True

# 4. SERVICE
class ServiceResource(resources.ModelResource):
    class Meta:
        model = Service
        import_id_fields = ('service_id',)
        fields = ('service_id', 'service_name', 'description', 'service_photo', 'category', 'tags')
        skip_unchanged = True

# 5. USER PROFILE
class UserProfileResource(resources.ModelResource):
    class Meta:
        model = UserProfile
        import_id_fields = ('user_id',)
        exclude = ('created_at',)
        skip_unchanged = True

# 6. SUPPLIER BRAND SERVICE (Uses default Django ID)
class SupplierBrandServiceResource(resources.ModelResource):
    class Meta:
        model = SupplierBrandService
        import_id_fields = ('id',)
        skip_unchanged = True

# 7. REVIEW
class ReviewResource(resources.ModelResource):
    class Meta:
        model = Review
        import_id_fields = ('review_id',)
        skip_unchanged = True

# 8. NOTIFICATION
class NotificationResource(resources.ModelResource):
    class Meta:
        model = Notification
        import_id_fields = ('notification_id',)
        skip_unchanged = True

# 9. REQUEST
class RequestResource(resources.ModelResource):
    class Meta:
        model = Request
        import_id_fields = ('id',)
        skip_unchanged = True

# 10. OTP VERIFICATION
class OTPVerificationResource(resources.ModelResource):
    class Meta:
        model = OTPVerification
        import_id_fields = ('id',)
        skip_unchanged = True

# 11. BUSINESS HOURS
class BusinessHoursResource(resources.ModelResource):
    class Meta:
        model = BusinessHours
        import_id_fields = ('id',)
        skip_unchanged = True

# 12. USER DEVICE
class UserDeviceResource(resources.ModelResource):
    class Meta:
        model = UserDevice
        import_id_fields = ('id',)
        skip_unchanged = True

# 13. SALES REPRESENTATIVE
class SalesRepresentativeResource(resources.ModelResource):
    class Meta:
        model = SalesRepresentative
        import_id_fields = ('representative_id',)
        fields = ('representative_id', 'name', 'email', 'judet', 'address', 'phone', 'approved', 'created_at')
        skip_unchanged = True

# 14. SUPPLIER REFERRAL
class SupplierReferralResource(resources.ModelResource):
    class Meta:
        model = SupplierReferral
        import_id_fields = ('referral_id',)
        skip_unchanged = True

# 15. APP LINK
class AppLinkResource(resources.ModelResource):
    class Meta:
        model = AppLink
        import_id_fields = ('id',)
        skip_unchanged = True

# 16. CAR
class CarResource(resources.ModelResource):
    class Meta:
        model = Car
        import_id_fields = ('car_id',)
        skip_unchanged = True

# 17. CAR OBLIGATION
class CarObligationResource(resources.ModelResource):
    class Meta:
        model = CarObligation
        import_id_fields = ('id',)
        skip_unchanged = True
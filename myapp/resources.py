from import_export import resources
from .models import (
    SalesRepresentative, SupplierReferral, UserProfile, CarBrand, Tag, 
    Service, SupplierBrandService, Review, Notification, Request, 
    OTPVerification, BusinessHours, CoverPhoto, UserDevice, AppLink, 
    Car, CarObligation
)


class TagResource(resources.ModelResource):
    class Meta:
        model = Tag
        import_id_fields = []  # Exclude tag_id from import (auto-generated)
        exclude = ('tag_id',)
        skip_unchanged = True
        report_skipped = True


class CarBrandResource(resources.ModelResource):
    class Meta:
        model = CarBrand
        import_id_fields = []  # Exclude brand_id from import (auto-generated)
        exclude = ('brand_id',)
        skip_unchanged = True
        report_skipped = True


class CoverPhotoResource(resources.ModelResource):
    class Meta:
        model = CoverPhoto
        import_id_fields = []  # Exclude photo_id from import (auto-generated)
        exclude = ('photo_id',)
        skip_unchanged = True
        report_skipped = True


class ServiceResource(resources.ModelResource):
    class Meta:
        model = Service
        import_id_fields = []  # Exclude service_id from import (auto-generated)
        exclude = ('service_id',)
        skip_unchanged = True
        report_skipped = True


class UserProfileResource(resources.ModelResource):
    class Meta:
        model = UserProfile
        import_id_fields = []  # Exclude user_id from import (auto-generated)
        exclude = ('user_id', 'created_at', 'django_user')
        skip_unchanged = True
        report_skipped = True


class SupplierBrandServiceResource(resources.ModelResource):
    class Meta:
        model = SupplierBrandService
        import_id_fields = []  # Exclude id from import (auto-generated)
        exclude = ('id',)
        skip_unchanged = True
        report_skipped = True


class ReviewResource(resources.ModelResource):
    class Meta:
        model = Review
        import_id_fields = []  # Exclude review_id from import (auto-generated)
        exclude = ('review_id', 'created_at')
        skip_unchanged = True
        report_skipped = True


class NotificationResource(resources.ModelResource):
    class Meta:
        model = Notification
        import_id_fields = []  # Exclude notification_id from import (auto-generated)
        exclude = ('notification_id', 'created_at')
        skip_unchanged = True
        report_skipped = True


class RequestResource(resources.ModelResource):
    class Meta:
        model = Request
        import_id_fields = []  # Exclude id from import (auto-generated)
        exclude = ('id', 'created_at')
        skip_unchanged = True
        report_skipped = True


class OTPVerificationResource(resources.ModelResource):
    class Meta:
        model = OTPVerification
        exclude = ('created_at',)
        skip_unchanged = True
        report_skipped = True


class BusinessHoursResource(resources.ModelResource):
    class Meta:
        model = BusinessHours
        skip_unchanged = True
        report_skipped = True


class UserDeviceResource(resources.ModelResource):
    class Meta:
        model = UserDevice
        exclude = ('created_at',)
        skip_unchanged = True
        report_skipped = True


class SalesRepresentativeResource(resources.ModelResource):
    class Meta:
        model = SalesRepresentative
        import_id_fields = []  # Exclude representative_id from import (auto-generated)
        exclude = ('representative_id', 'created_at')
        skip_unchanged = True
        report_skipped = True


class SupplierReferralResource(resources.ModelResource):
    class Meta:
        model = SupplierReferral
        import_id_fields = []  # Exclude referral_id from import (auto-generated)
        exclude = ('referral_id', 'created_at')
        skip_unchanged = True
        report_skipped = True


class AppLinkResource(resources.ModelResource):
    class Meta:
        model = AppLink
        exclude = ('id', 'timestamp')
        skip_unchanged = True
        report_skipped = True


class CarResource(resources.ModelResource):
    class Meta:
        model = Car
        import_id_fields = []  # Exclude car_id from import (auto-generated)
        exclude = ('car_id', 'created_at', 'updated_at')
        skip_unchanged = True
        report_skipped = True


class CarObligationResource(resources.ModelResource):
    class Meta:
        model = CarObligation
        import_id_fields = []  # Exclude id from import (auto-generated)
        exclude = ('id', 'created_at', 'updated_at')
        skip_unchanged = True
        report_skipped = True


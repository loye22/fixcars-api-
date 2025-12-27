from import_export import resources
from .models import (
    SalesRepresentative, SupplierReferral, UserProfile, CarBrand, Tag, 
    Service, SupplierBrandService, Review, Notification, Request, 
    OTPVerification, BusinessHours, CoverPhoto, UserDevice, AppLink, 
    Car, CarObligation
)


class BaseResource(resources.ModelResource):
    """Base resource class that ignores 'id' and other unknown fields during import"""
    
    def get_fields(self, **kwargs):
        """Override to exclude 'id' field if model doesn't have it"""
        fields = super().get_fields(**kwargs)
        
        # Get all field names from the model (including related fields)
        model_field_names = set()
        for field in self._meta.model._meta.get_fields():
            model_field_names.add(field.name)
            # Also add the primary key name
            if hasattr(field, 'primary_key') and field.primary_key:
                model_field_names.add(field.name)
        
        # Check if model has an 'id' field
        has_id_field = 'id' in model_field_names
        
        # Filter out 'id' field from fields if model doesn't have it
        if not has_id_field:
            fields = [f for f in fields if f.attribute != 'id']
        
        return fields
    
    def before_import_row(self, row, **kwargs):
        """Remove 'id' column from row data if model doesn't have 'id' field"""
        # Get model field names
        model_field_names = {f.name for f in self._meta.model._meta.get_fields()}
        
        # If model doesn't have 'id' field, remove it from row
        if 'id' not in model_field_names:
            # Handle different row types (dict, OrderedDict, Row object, etc.)
            try:
                if hasattr(row, 'pop'):
                    row.pop('id', None)
                elif hasattr(row, '__delitem__'):
                    if 'id' in row:
                        del row['id']
                elif isinstance(row, dict):
                    row.pop('id', None)
                elif hasattr(row, 'keys') and 'id' in row:
                    # For Row objects, we might need to convert
                    if hasattr(row, '_values'):
                        # Remove from internal values
                        if 'id' in row._values:
                            del row._values['id']
            except (KeyError, AttributeError, TypeError):
                # If we can't remove it, that's okay - get_fields() will filter it out
                pass
        
        return row


class TagResource(BaseResource):
    class Meta:
        model = Tag
        import_id_fields = []  # Exclude tag_id from import (auto-generated)
        exclude = ('tag_id',)
        skip_unchanged = True
        report_skipped = True


class CarBrandResource(BaseResource):
    class Meta:
        model = CarBrand
        import_id_fields = []  # Exclude brand_id from import (auto-generated)
        exclude = ('brand_id',)
        skip_unchanged = True
        report_skipped = True


class CoverPhotoResource(BaseResource):
    class Meta:
        model = CoverPhoto
        import_id_fields = []  # Exclude photo_id from import (auto-generated)
        exclude = ('photo_id',)
        skip_unchanged = True
        report_skipped = True


class ServiceResource(BaseResource):
    class Meta:
        model = Service
        import_id_fields = []  # Exclude service_id from import (auto-generated)
        exclude = ('service_id',)
        skip_unchanged = True
        report_skipped = True


class UserProfileResource(BaseResource):
    class Meta:
        model = UserProfile
        import_id_fields = []  # Exclude user_id from import (auto-generated)
        exclude = ('user_id', 'created_at', 'django_user')
        skip_unchanged = True
        report_skipped = True


class SupplierBrandServiceResource(BaseResource):
    class Meta:
        model = SupplierBrandService
        import_id_fields = []  # Exclude id from import (auto-generated)
        exclude = ('id',)
        skip_unchanged = True
        report_skipped = True


class ReviewResource(BaseResource):
    class Meta:
        model = Review
        import_id_fields = []  # Exclude review_id from import (auto-generated)
        exclude = ('review_id', 'created_at')
        skip_unchanged = True
        report_skipped = True


class NotificationResource(BaseResource):
    class Meta:
        model = Notification
        import_id_fields = []  # Exclude notification_id from import (auto-generated)
        exclude = ('notification_id', 'created_at')
        skip_unchanged = True
        report_skipped = True


class RequestResource(BaseResource):
    class Meta:
        model = Request
        import_id_fields = []  # Exclude id from import (auto-generated)
        exclude = ('id', 'created_at')
        skip_unchanged = True
        report_skipped = True


class OTPVerificationResource(BaseResource):
    class Meta:
        model = OTPVerification
        exclude = ('created_at',)
        skip_unchanged = True
        report_skipped = True


class BusinessHoursResource(BaseResource):
    class Meta:
        model = BusinessHours
        skip_unchanged = True
        report_skipped = True


class UserDeviceResource(BaseResource):
    class Meta:
        model = UserDevice
        exclude = ('created_at',)
        skip_unchanged = True
        report_skipped = True


class SalesRepresentativeResource(BaseResource):
    class Meta:
        model = SalesRepresentative
        import_id_fields = []  # Exclude representative_id from import (auto-generated)
        exclude = ('representative_id', 'created_at')
        skip_unchanged = True
        report_skipped = True


class SupplierReferralResource(BaseResource):
    class Meta:
        model = SupplierReferral
        import_id_fields = []  # Exclude referral_id from import (auto-generated)
        exclude = ('referral_id', 'created_at')
        skip_unchanged = True
        report_skipped = True


class AppLinkResource(BaseResource):
    class Meta:
        model = AppLink
        exclude = ('id', 'timestamp')
        skip_unchanged = True
        report_skipped = True


class CarResource(BaseResource):
    class Meta:
        model = Car
        import_id_fields = []  # Exclude car_id from import (auto-generated)
        exclude = ('car_id', 'created_at', 'updated_at')
        skip_unchanged = True
        report_skipped = True


class CarObligationResource(BaseResource):
    class Meta:
        model = CarObligation
        import_id_fields = []  # Exclude id from import (auto-generated)
        exclude = ('id', 'created_at', 'updated_at')
        skip_unchanged = True
        report_skipped = True


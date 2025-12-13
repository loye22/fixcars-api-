from django.contrib import admin
from .models import SalesRepresentative, SupplierReferral, UserProfile, CarBrand, Tag, Service, SupplierBrandService, Review, Notification, Request, OTPVerification, BusinessHours, CoverPhoto, UserDevice, AppLink, Car, CarObligation
from django.contrib import admin
from .models import UserProfile
# Register your models here.
 

admin.site.register(Tag)

@admin.register(CarBrand)
class CarBrandAdmin(admin.ModelAdmin):
    list_display = ('brand_id', 'brand_name', 'brand_photo')
    search_fields = ('brand_name',)
    readonly_fields = ('brand_id',)
    ordering = ('brand_name',)

admin.site.register(CoverPhoto)

   
 
@admin.register(SupplierBrandService)
class SupplierBrandServiceAdmin(admin.ModelAdmin):
    list_display = ('supplier', 'brand', 'city', 'sector', 'active')
    search_fields = ('supplier__full_name', 'brand__brand_name')
    list_filter = ('city', 'sector', 'active')
    filter_horizontal = ('services',)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "supplier":
            kwargs["queryset"] = UserProfile.objects.filter(user_type='supplier')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('service_id' , 'service_name', 'category', 'service_photo')
    search_fields = ('service_name',)
    list_filter = ('category',)
    filter_horizontal = ('tags',) 

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    # list_display = (
    #     'user_id', 'full_name', 'email', 'phone', 'user_type', 'city', 'sector',
    #     'approval_status', 'account_status', 'is_active', 'is_verified', 'created_at'
    # )
    list_display = ('full_name', 'is_active' ,  'email')

    search_fields = ('full_name', 'email', 'phone')
    list_filter = ('user_type', 'city', 'sector', 'approval_status', 'account_status', 'is_active', 'is_verified')
    readonly_fields = ('user_id', 'created_at')
    filter_horizontal = ('cover_photos',)


@admin.register(OTPVerification)
class OTPVerificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'otp', 'is_used', 'expires_at', 'created_at')
    list_filter = ('is_used', 'created_at', 'expires_at')
    search_fields = ('user__email', 'user__full_name', 'otp')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('OTP Details', {
            'fields': ('otp', 'expires_at', 'is_used')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'
    
    def user_name(self, obj):
        return obj.user.full_name
    user_name.short_description = 'User Name'

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('client', 'supplier', 'rating', 'comment', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('client__full_name', 'supplier__full_name', 'comment')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "client":
            kwargs["queryset"] = UserProfile.objects.filter(user_type='client')
        elif db_field.name == "supplier":
            kwargs["queryset"] = UserProfile.objects.filter(user_type='supplier')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(BusinessHours)
class BusinessHoursAdmin(admin.ModelAdmin):
    list_display = ('supplier',)
    search_fields = ('supplier__full_name',)
    
    fields = (
        'supplier',
        ('monday_open', 'monday_close', 'monday_closed'),
        ('tuesday_open', 'tuesday_close', 'tuesday_closed'),
        ('wednesday_open', 'wednesday_close', 'wednesday_closed'),
        ('thursday_open', 'thursday_close', 'thursday_closed'),
        ('friday_open', 'friday_close', 'friday_closed'),
        ('saturday_open', 'saturday_close', 'saturday_closed'),
        ('sunday_open', 'sunday_close', 'sunday_closed'),
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "supplier":
            kwargs["queryset"] = UserProfile.objects.filter(user_type='supplier')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'supplier', 'client', 'longitude', 'latitude', 'phone_number', 'reason', 'status')
    search_fields = ('supplier__full_name', 'client__full_name', 'phone_number', 'reason')
    list_filter = ('status', 'created_at')
    readonly_fields = ('id', 'created_at')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('notification_id', 'receiver', 'type', 'message', 'is_read', 'created_at')
    search_fields = ('receiver__full_name', 'message', 'type')
    list_filter = ('type', 'is_read', 'created_at')
    readonly_fields = ('notification_id', 'created_at')

@admin.register(UserDevice)
class UserDeviceAdmin(admin.ModelAdmin):
    list_display = ('user', 'player_id', 'is_active', 'created_at')
    search_fields = ('user__full_name', 'user__email', 'player_id')
    list_filter = ('is_active', 'created_at')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Device Information', {
            'fields': ('user', 'player_id', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')



@admin.register(SalesRepresentative)
class SalesRepresentativeAdmin(admin.ModelAdmin):
    list_display = ('representative_id', 'name', 'email', 'judet', 'address', 'phone', 'created_at')
    search_fields = ('name', 'email', 'phone', 'judet', 'address')
    list_filter = ('judet', 'created_at')
    readonly_fields = ('representative_id', 'created_at')
    ordering = ('-created_at',)


@admin.register(SupplierReferral)
class SupplierReferralAdmin(admin.ModelAdmin):
    list_display = (
        'referral_id',
        'sales_representative',
        'supplier',
        'has_received_commission',
        'created_at',
    )
    search_fields = (
        'sales_representative__name',
        'sales_representative__email',
        'supplier__full_name',
    )
    list_filter = ('has_received_commission', 'created_at',)
    readonly_fields = ('referral_id', 'created_at')
    ordering = ('-created_at',)
    #search_fields = ['supplier__full_name']
    autocomplete_fields = ['supplier', 'sales_representative']

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Limit foreign key choices for cleaner admin UI."""
        from .models import UserProfile, SalesRepresentative
        if db_field.name == "supplier":
            kwargs["queryset"] = UserProfile.objects.filter(user_type='supplier')
        elif db_field.name == "sales_representative":
            kwargs["queryset"] = SalesRepresentative.objects.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(AppLink)
class AppLinkAdmin(admin.ModelAdmin):
    list_display = ('url', 'timestamp')
    search_fields = ('url',)
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ('car_id', 'user', 'brand', 'model', 'year', 'license_plate', 'current_km', 'last_km_updated_at', 'created_at')
    search_fields = ('license_plate', 'brand__brand_name', 'model', 'user__full_name', 'user__email')
    list_filter = ('brand', 'year', 'created_at')
    readonly_fields = ('car_id', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Car Information', {
            'fields': ('user', 'brand', 'model', 'year', 'license_plate')
        }),
        ('Mileage Information', {
            'fields': ('current_km', 'last_km_updated_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'brand')


@admin.register(CarObligation)
class CarObligationAdmin(admin.ModelAdmin):
    list_display = ('id', 'car', 'obligation_type', 'reminder_type', 'due_date', 'created_at')
    search_fields = ('car__license_plate', 'car__brand__brand_name', 'car__model', 'car__user__full_name', 'note')
    list_filter = ('obligation_type', 'reminder_type', 'due_date', 'created_at')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Obligation Information', {
            'fields': ('car', 'obligation_type', 'reminder_type')
        }),
        ('Details', {
            'fields': ('due_date', 'doc_url', 'note')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('car', 'car__user', 'car__brand')

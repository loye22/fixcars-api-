from django.contrib import admin
from .models import UserProfile, CarBrand, Tag, Service, SupplierBrandService, Review, Notification, Request, OTPVerification, BusinessHours
from django.contrib import admin
from .models import UserProfile
# Register your models here.
 

admin.site.register(Tag)
admin.site.register(Notification)
admin.site.register(Request)
admin.site.register(CarBrand)

   

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
    list_display = ('service_name', 'category', 'service_photo')
    search_fields = ('service_name',)
    list_filter = ('category',)
    filter_horizontal = ('tags',)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user_id', 'full_name', 'email', 'phone', 'user_type', 'city', 'sector',
        'approval_status', 'account_status', 'is_active', 'is_verified', 'created_at'
    )
    search_fields = ('full_name', 'email', 'phone')
    list_filter = ('user_type', 'city', 'sector', 'approval_status', 'account_status', 'is_active', 'is_verified')
    readonly_fields = ('user_id', 'created_at')


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

from django.contrib import admin
from .models import UserProfile, CarBrand, Tag, Service, SupplierBrandService, Review, Notification, Request, OTPVerification

# Register your models here.
 
admin.site.register(CarBrand)
admin.site.register(Tag)
admin.site.register(Service)
admin.site.register(SupplierBrandService)
admin.site.register(Review)
admin.site.register(Notification)
admin.site.register(Request)
   

from django.contrib import admin
from .models import UserProfile

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

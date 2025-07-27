from django.contrib import admin
from .models import User, CarBrand, ServiceCategory, Tag, Service, SupplierBrandService, Review, Notification, Request


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'phone', 'user_type', 'city', 'sector', 'approval_status', 'account_status', 'created_at')
    list_filter = ('user_type', 'city', 'sector', 'approval_status', 'account_status', 'availability_days', 'availability_times')

@admin.register(CarBrand)
class CarBrandAdmin(admin.ModelAdmin):
    list_display = ('brand_name', 'brand_photo')
    search_fields = ('brand_name',)

@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ('category_name',)
    search_fields = ('category_name',)

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('tag_name',)
    search_fields = ('tag_name',)

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('service_name', 'category', 'service_photo')
    list_filter = ('category',)
    search_fields = ('service_name',)

@admin.register(SupplierBrandService)
class SupplierBrandServiceAdmin(admin.ModelAdmin):
    list_display = ('supplier', 'brand', 'city', 'sector', 'active')
    list_filter = ('brand', 'city', 'sector', 'active')
    filter_horizontal = ('services',)

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('client', 'supplier', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('type', 'sender', 'receiver', 'is_read', 'created_at')
    list_filter = ('type', 'is_read', 'created_at')

@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = ('client', 'supplier', 'status', 'phone_number', 'address')
    list_filter = ('status',)

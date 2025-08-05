from django.contrib import admin
from .models import UserProfile, CarBrand, Tag, Service, SupplierBrandService, Review, Notification, Request

# Register your models here.
admin.site.register(UserProfile)
admin.site.register(CarBrand)
admin.site.register(Tag)
admin.site.register(Service)
admin.site.register(SupplierBrandService)
admin.site.register(Review)
admin.site.register(Notification)
admin.site.register(Request)

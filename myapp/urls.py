from django.urls import path
from .views import  home , FileUploadView, ClientSignupView, OTPValidationView, ResendOTPView, LoginView, CarBrandListView, ServicesView, ServicesByCategoryView, SupplierProfileView, ReviewsListView, CreateUpdateReviewView, CreateRequestView
from rest_framework_simplejwt.views import TokenRefreshView 

app_name = 'myapp'

urlpatterns = [
    path('', home, name='home'),
    path('api/upload-file/', FileUploadView.as_view(), name='upload_file'),
    path('api/client-signup/', ClientSignupView.as_view(), name='client_signup'),
    path('api/validate-otp/', OTPValidationView.as_view(), name='validate_otp'),
    path('api/resend-otp/', ResendOTPView.as_view(), name='resend_otp'),
    path('api/login/', LoginView.as_view(), name='login'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/brands/', CarBrandListView.as_view(), name='brand_list'),
    path('api/services/', ServicesView.as_view(), name='services'),
    path('api/services-by-category/', ServicesByCategoryView.as_view(), name='services_by_category'), # this end point will give me all the servises by category
    path('api/supplierProfile/<uuid:supplier_id>/', SupplierProfileView.as_view(), name='supplier_profile'),
    path('api/reviews/<uuid:supplier_id>/', ReviewsListView.as_view(), name='reviews_list'),
    path('api/reviews/<uuid:supplier_id>/create-update/', CreateUpdateReviewView.as_view(), name='create_update_review'),
    path('api/requests/create/', CreateRequestView.as_view(), name='create_request'),
] 
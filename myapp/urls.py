from django.urls import path
from .views import  home , FileUploadView, ClientSignupView, OTPValidationView, ResendOTPView, LoginView, CarBrandListView, MecanicAutoServicesView
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
    path('api/mecanic-auto-services/', MecanicAutoServicesView.as_view(), name='mecanic_auto_services'),
] 
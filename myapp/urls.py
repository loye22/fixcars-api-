from django.urls import path
from .views import SendEmailView, home , FileUploadView, ClientSignupView, OTPValidationView, ResendOTPView

app_name = 'myapp'

urlpatterns = [
    path('', home, name='home'),
    path('api/send-email/', SendEmailView.as_view(), name='send_email'),
    path('api/upload-file/', FileUploadView.as_view(), name='upload_file'),
    path('api/client-signup/', ClientSignupView.as_view(), name='client_signup'),
    path('api/validate-otp/', OTPValidationView.as_view(), name='validate_otp'),
    path('api/resend-otp/', ResendOTPView.as_view(), name='resend_otp'),
] 
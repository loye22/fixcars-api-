from django.urls import path
from .views import SendEmailView, home , FileUploadView 

app_name = 'myapp'

urlpatterns = [
    path('', home, name='home'),
    path('api/send-email/', SendEmailView.as_view(), name='send_email'),
    path('api/upload-file/', FileUploadView.as_view(), name='upload_file'),

] 
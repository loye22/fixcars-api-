from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import send_mail
from django.conf import settings
from django.http import HttpResponse
import os
from django.conf import settings
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import parser_classes
import uuid


# Create your views here.

def home(request):
    """Simple home page view"""
    return HttpResponse("<h1>home</h1>")


class SendEmailView(APIView):
    """Simple API view to send email"""
    
    def post(self, request):
        try:
            email = request.data.get('email')
            subject = request.data.get('subject', 'Test Email')
            message = request.data.get('message', 'This is a test email')
            
            if not email:
                return Response({
                    'error': 'Email is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Send email
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            
            return Response({
                'success': True,
                'message': f'Email sent to {email}'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)







class FileUploadView(APIView):
    """API view to upload files and return URL"""
    parser_classes = (MultiPartParser, FormParser)
    
    def post(self, request):
        try:
            # Check if file is present
            if 'file' not in request.FILES:
                return Response({
                    'success': False,
                    'error': 'No file provided'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            uploaded_file = request.FILES['file']
            
            # Validate file size (optional - 10MB limit)
            if uploaded_file.size > 10 * 1024 * 1024:  # 10MB
                return Response({
                    'success': False,
                    'error': 'File size too large. Maximum 10MB allowed.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate file type (optional)
            allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'application/pdf', 'text/plain']
            if uploaded_file.content_type not in allowed_types:
                return Response({
                    'success': False,
                    'error': 'File type not allowed. Allowed types: JPEG, PNG, GIF, PDF, TXT'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create media directory if it doesn't exist
            media_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
            os.makedirs(media_dir, exist_ok=True)
            
            # Generate unique filename
            file_extension = os.path.splitext(uploaded_file.name)[1]
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            
            # Save file
            file_path = os.path.join(media_dir, unique_filename)
            with open(file_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)
            
            # Generate URL
            file_url = f"{settings.MEDIA_URL}uploads/{unique_filename}"
            
            return Response({
                'success': True,
                'message': 'File uploaded successfully',
                'file_url': file_url,
                'filename': unique_filename,
                'original_name': uploaded_file.name,
                'file_size': uploaded_file.size
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
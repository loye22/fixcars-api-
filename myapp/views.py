from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import send_mail
from django.conf import settings
from django.http import HttpResponse


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

from django.urls import path
from .views import    AddCarObligationView,admin_login, download_page, sales_representatives_page, privacy_policy_page, home , HealthCheckView, AccountStatusView, FileUploadView, ClientSignupView, SupplierSignupView, OTPValidationView, ResendOTPView, LoginView, CarBrandListView, ServicesView, ServicesByCategoryView, SupplierProfileView, ReviewsListView, CreateUpdateReviewView, CreateRequestView, RequestListView, PendingRequestsCountView, NotificationsListView, MarkNotificationReadView, HasUnreadNotificationsView, SupplierProfileSummaryView, RegisterDeviceView, SendNotificationView, UserDetailView, UpdateRequestStatusView, RequestPasswordResetView, ResetPasswordView, reset_password_page, DeleteAccountView, ReferedByView, SupplierBrandServiceOptionsView, SupplierBrandServiceCreateView, BusinessHoursView, BusinessHoursUpdateView, UserCarsListView, CarObligationCreateView, CarObligationDeleteView, UpdateCarObligationByIdView, UserCarCreateView, UserCarUpdateView, InitCarDetailsUpdateView
from rest_framework_simplejwt.views import TokenRefreshView 
from .views import FirebaseTokenViewSet
from . import views

app_name = 'myapp'

firebase_token_view = FirebaseTokenViewSet.as_view({'get': 'list', 'post': 'create'})

urlpatterns = [
    path('', home, name='home'),
    path('api/health/', HealthCheckView.as_view(), name='health_check'),
    path('api/account-status/', AccountStatusView.as_view(), name='account_status'),
    path('api/upload-file/', FileUploadView.as_view(), name='upload_file'),
    path('api/client-signup/', ClientSignupView.as_view(), name='client_signup'),
    path('api/supplier-signup/', SupplierSignupView.as_view(), name='supplier_signup'),
    path('api/validate-otp/', OTPValidationView.as_view(), name='validate_otp'),
    path('api/resend-otp/', ResendOTPView.as_view(), name='resend_otp'),
    path('api/login/', LoginView.as_view(), name='login'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/brands/', CarBrandListView.as_view(), name='brand_list'),
    path('api/services/', ServicesView.as_view(), name='services'),
    path('api/services-by-category/', ServicesByCategoryView.as_view(), name='services_by_category'), # this end point will give me all the servises by category
    path('api/supplier-brand-service-options/', SupplierBrandServiceOptionsView.as_view(), name='supplier_brand_service_options'),
    path('api/supplier-brand-services/', SupplierBrandServiceCreateView.as_view(), name='supplier_brand_service_create'),
    path('api/supplierProfile/<uuid:supplier_id>/', SupplierProfileView.as_view(), name='supplier_profile'),
    path('api/supplierProfileSummary/', SupplierProfileSummaryView.as_view(), name='supplier_profile_summary_me'),
    path('api/supplierProfileSummary/<uuid:supplier_id>/', SupplierProfileSummaryView.as_view(), name='supplier_profile_summary'),
    path('api/reviews/<uuid:supplier_id>/', ReviewsListView.as_view(), name='reviews_list'),
    path('api/reviews/<uuid:supplier_id>/create-update/', CreateUpdateReviewView.as_view(), name='create_update_review'),
    path('api/requests/create/', CreateRequestView.as_view(), name='create_request'),
    path('api/requests/', RequestListView.as_view(), name='requests_list'),
    path('api/requests/pending-count/', PendingRequestsCountView.as_view(), name='pending_requests_count'),
    path('api/requests/update-status/', UpdateRequestStatusView.as_view(), name='update_request_status'),
    path('api/notifications/', NotificationsListView.as_view(), name='notifications_list'),
    path('api/notifications/mark-read/', MarkNotificationReadView.as_view(), name='notification_mark_read'),
    path('api/notifications/has-unread/', HasUnreadNotificationsView.as_view(), name='has_unread_notifications'),
    path('api/referedBy/', ReferedByView.as_view(), name='refered_by'),
    path('api/register-device/', RegisterDeviceView.as_view(), name='register_device'),
    path('api/send-notification/', SendNotificationView.as_view(), name='send_notification'),
    path('api/firebase-token/', firebase_token_view, name='firebase_token'),
    path('api/user/<uuid:user_uuid>/', UserDetailView.as_view(), name='user_detail'),
    path('api/password-reset/request/', RequestPasswordResetView.as_view(), name='request_password_reset'),
    path('api/password-reset/reset/', ResetPasswordView.as_view(), name='reset_password'),
    path('reset-password/', reset_password_page, name='reset_password_page'),
    path('api/delete-account/', DeleteAccountView.as_view(), name='delete_account'),
    path('api/business-hours/', BusinessHoursView.as_view(), name='business_hours'),
    path('api/business-hours/update/', BusinessHoursUpdateView.as_view(), name='business_hours_update'),
    path('api/cars/', UserCarsListView.as_view(), name='user_cars_list'),
    path('api/cars/create/', UserCarCreateView.as_view(), name='user_car_create'),
    path('api/cars/<uuid:car_id>/', UserCarUpdateView.as_view(), name='user_car_update'),
    path('api/cars/<uuid:car_id>/obligations/', CarObligationCreateView.as_view(), name='car_obligation_create'),
    path('api/cars/<uuid:car_id>/obligations/<uuid:obligation_id>/', CarObligationDeleteView.as_view(), name='car_obligation_delete'),
    path('api/init-car-details-update/', InitCarDetailsUpdateView.as_view(), name='init_car_details_update'),
    path('api/updatecarobligationbyid', UpdateCarObligationByIdView.as_view(), name='update_car_obligation_by_id'),
    path('delete-account/', DeleteAccountView.as_view(), name='delete_account_noapi'),
    path('download/', download_page, name='download'),
    path('sales-representatives/', sales_representatives_page, name='sales_representatives'),
    path('privacy-policy/', privacy_policy_page, name='privacy_policy'),
    path('panel/login/', views.admin_login, name='panel_login'),
    path('panel/', views.admin_dashboard, name='panel_dashboard'),                   # main dashboard
    path('panel/accept-sales/<uuid:rep_id>/', views.admin_accept_sales,
         name='panel_accept_sales'),                                                # accept a rep
    path('panel/activate-mechanic/<uuid:user_id>/', views.admin_activate_mechanic,
         name='panel_activate_mechanic'),

         path('api/add-car-obligation/', AddCarObligationView.as_view(), name='add_car_obligation'),
    
] 
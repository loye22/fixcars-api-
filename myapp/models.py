from django.db import models
import uuid
from multiselectfield import MultiSelectField


# Choices for enumerated fields
USER_TYPES = (
    ('client', 'Client'),
    ('supplier', 'Supplier'),
)

APPROVAL_STATUSES = (
    ('pending', 'Pending'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
)

ACCOUNT_STATUSES = (
    ('active', 'Active'),
    ('suspended', 'Suspended'),
)

ROMANIAN_CITIES = (
    ('Bucharest', 'Bucharest'),
    ('Cluj-Napoca', 'Cluj-Napoca'),
    ('Timișoara', 'Timișoara'),
    ('Iași', 'Iași'),
    ('Constanța', 'Constanța'),
    ('Craiova', 'Craiova'),
    ('Brașov', 'Brașov'),
    ('Galați', 'Galați'),
    ('Ploiești', 'Ploiești'),
    ('Oradea', 'Oradea'),
)

NOTIFICATION_TYPES = (
    ('appointment_reminder', 'Appointment Reminder'),
    ('new_message', 'New Message'),
    ('supplier_approval', 'Supplier Approval'),
    ('subscription_reminder', 'Subscription Reminder'),
    ('subscription_expiry', 'Subscription Expiry'),
)

SCHEDULE_STATUSES = (
    ('pending', 'Pending'),
    ('accepted', 'Accepted'),
    ('cancelled', 'Cancelled'),
    ('finished', 'Finished'),
)

REQUEST_STATUSES = (
    ('accepted', 'Accepted'),
    ('rejected', 'Rejected'),
    ('expired', 'Expired'),
)


DAYS_OF_WEEK = (
    ('mon', 'Monday'),
    ('tue', 'Tuesday'),
    ('wed', 'Wednesday'),
    ('thu', 'Thursday'),
    ('fri', 'Friday'),
    ('sat', 'Saturday'),
    ('sun', 'Sunday'),
)

TIME_SLOTS = (
    ('morning', 'Morning (09:00-12:00)'),
    ('afternoon', 'Afternoon (12:00-17:00)'),
    ('evening', 'Evening (17:00-21:00)'),
)

class User(models.Model):
    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, unique=True)
    password_hash = models.CharField(max_length=255)
    profile_photo = models.URLField()  # Required: Stores URL for profile photo
    user_type = models.CharField(max_length=20, choices=USER_TYPES)
    business_address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=50, choices=ROMANIAN_CITIES, blank=True, null=True)
    sector = models.CharField(max_length=50, blank=True, null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    availability_days = MultiSelectField(choices=DAYS_OF_WEEK, blank=True, null=True)
    availability_times = MultiSelectField(choices=TIME_SLOTS, blank=True, null=True)
    approval_status = models.CharField(max_length=20, choices=APPROVAL_STATUSES, default='pending')
    account_status = models.CharField(max_length=20, choices=ACCOUNT_STATUSES, default='active')
    approved_at = models.DateTimeField(blank=True, null=True)
    admin = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_users')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'users'

    def __str__(self):
        return self.full_name

class CarBrand(models.Model):
    brand_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    brand_name = models.CharField(max_length=255, unique=True)
    brand_photo = models.URLField()  # Required: Stores URL for brand photo

    class Meta:
        db_table = 'car_brands'

    def __str__(self):
        return self.brand_name

class ServiceCategory(models.Model):
    category_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category_name = models.CharField(max_length=255, unique=True)

    class Meta:
        db_table = 'service_categories'

    def __str__(self):
        return self.category_name

class Tag(models.Model):
    tag_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tag_name = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = 'tags'

    def __str__(self):
        return self.tag_name

class Service(models.Model):
    service_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service_name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    service_photo = models.URLField()  # Required: Stores URL for service photo
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, related_name='services')
    tags = models.ManyToManyField(Tag, related_name='services', blank=True)

    class Meta:
        db_table = 'services'

    def __str__(self):
        return self.service_name

class SupplierBrandService(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    supplier = models.ForeignKey(User, on_delete=models.CASCADE, related_name='supplier_services')
    brand = models.ForeignKey(CarBrand, on_delete=models.CASCADE, related_name='brand_services')
    services = models.ManyToManyField(Service, related_name='supplier_brand_services')
    city = models.CharField(max_length=50, choices=ROMANIAN_CITIES, blank=True, null=True)
    sector = models.CharField(max_length=50, blank=True, null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    photo_url = models.URLField()  # Required: Stores URL for service photo
    active = models.BooleanField(default=True)

    class Meta:
        db_table = 'supplier_brand_services'

    def __str__(self):
        service_names = ', '.join([s.service_name for s in self.services.all()])
        return f"{self.supplier.full_name} - {self.brand.brand_name} - {service_names}"

class Review(models.Model):
    review_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='client_reviews')
    supplier = models.ForeignKey(User, on_delete=models.CASCADE, related_name='supplier_reviews')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reviews'

    def __str__(self):
        return f"Review by {self.client.full_name} for {self.supplier.full_name}"

class Notification(models.Model):
    notification_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_notifications')
    type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'

    def __str__(self):
        return f"Notification {self.type} from {self.sender.full_name} to {self.receiver.full_name}"



class Request(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='client_requests')
    supplier = models.ForeignKey(User, on_delete=models.CASCADE, related_name='supplier_requests')
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    status = models.CharField(max_length=20, choices=REQUEST_STATUSES)
    phone_number = models.CharField(max_length=20)
    address = models.CharField(max_length=255)
    reason = models.TextField()

    class Meta:
        db_table = 'requests'

    def __str__(self):
        return f"Request from {self.client.full_name} to {self.supplier.full_name}"
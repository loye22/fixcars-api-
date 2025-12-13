from django.db import models
import uuid
from multiselectfield import MultiSelectField
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.validators import RegexValidator

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

JUDETE = (
    ('Alba', 'Alba'),
    ('Arad', 'Arad'),
    ('Argeș', 'Argeș'),
    ('Bacău', 'Bacău'),
    ('Bihor', 'Bihor'),
    ('Bistrița-Năsăud', 'Bistrița-Năsăud'),
    ('Botoșani', 'Botoșani'),
    ('Brașov', 'Brașov'),
    ('Brăila', 'Brăila'),
    ('Buzău', 'Buzău'),
    ('Caraș-Severin', 'Caraș-Severin'),
    ('Călărași', 'Călărași'),
    ('Cluj', 'Cluj'),
    ('Constanța', 'Constanța'),
    ('Covasna', 'Covasna'),
    ('Dâmbovița', 'Dâmbovița'),
    ('Dolj', 'Dolj'),
    ('Galați', 'Galați'),
    ('Giurgiu', 'Giurgiu'),
    ('Gorj', 'Gorj'),
    ('Harghita', 'Harghita'),
    ('Hunedoara', 'Hunedoara'),
    ('Ialomița', 'Ialomița'),
    ('Iași', 'Iași'),
    ('Ilfov', 'Ilfov'),
    ('Maramureș', 'Maramureș'),
    ('Mehedinți', 'Mehedinți'),
    ('Mureș', 'Mureș'),
    ('Neamț', 'Neamț'),
    ('Olt', 'Olt'),
    ('Prahova', 'Prahova'),
    ('Satu Mare', 'Satu Mare'),
    ('Sălaj', 'Sălaj'),
    ('Sibiu', 'Sibiu'),
    ('Suceava', 'Suceava'),
    ('Teleorman', 'Teleorman'),
    ('Timiș', 'Timiș'),
    ('Tulcea', 'Tulcea'),
    ('Vaslui', 'Vaslui'),
    ('Vâlcea', 'Vâlcea'),
    ('Vrancea', 'Vrancea'),
    ('Municipiul București', 'Municipiul București'),
)

SECTORS = (
    ('sector_1', 'Sector 1'),
    ('sector_2', 'Sector 2'),
    ('sector_3', 'Sector 3'),
    ('sector_4', 'Sector 4'),
    ('sector_5', 'Sector 5'),
    ('sector_6', 'Sector 6'),
    ('no_sector', 'No Sector'),
)

NOTIFICATION_TYPES = (
    ('new_message', 'New Message'),
    ('supplier_approval', 'Supplier Approval'),
    ('request_update', 'Request Update'),
    ('general_notification', 'General Notification'),
)

SCHEDULE_STATUSES = (
    ('pending', 'Pending'),
    ('accepted', 'Accepted'),
    ('cancelled', 'Cancelled'),
    ('finished', 'Finished'),
)

REQUEST_STATUSES = (
    ('pending', 'Pending'),
    ('accepted', 'Accepted'),
    ('rejected', 'Rejected'),
    ('expired', 'Expired'),
    ('completed', 'Completed'),
)

SUBSCRIPTION_PLANS = (
    ('bronze', 'Bronze'),
    ('silver', 'Silver'),
    ('gold', 'Gold'),
)



SERVICE_CATEGORIES = (
    ('mecanic_auto', 'Mecanic Auto'),
    ('autocolant_folie_auto', 'Autocolant & Folie Auto'),
    ('detailing_auto_profesionist', 'Detailing Auto Profesionist'),
    ('itp', 'ITP'),
    ('tapiterie_auto', 'Tapițerie Auto'),
    ('vulcanizare_auto_mobila', 'Vulcanizare Auto Mobilă'),
    ('tractari_auto', 'Tractări Auto'),
    ('tuning_auto', 'Tuning Auto'),
    ('spalatorie_auto', 'Spălătorie Auto'),
    ('climatizare_auto', 'Climatizare Auto'),
    ('caroserie_si_vopsitorie', 'Caroserie și Vopsitorie'),
    ('electrica_auto', 'Electrica Auto'),
)



class ObligationDefinition(models.TextChoices):
    # Legal Obligations
    ITP = 'ITP', 'ITP (Inspecția Tehnică Periodică)'
    RCA = 'RCA', 'RCA (Asigurare Obligatorie Răspundere Civilă Auto)'
    CASCO = 'CASCO', 'CASCO (Asigurare Facultativă Auto)'
    ROVINIETA = 'ROVINIETA', 'Rovinietă (Taxă de Drum/Vignetă)'
    AUTO_TAX = 'AUTO_TAX', 'Impozit Auto Anual'

    # Mechanical/Maintenance Obligations
    OIL_CHANGE = 'OIL_CHANGE', 'Schimb Ulei'
    AIR_FILTER = 'AIR_FILTER', 'Filtru de Aer'
    CABIN_FILTER = 'CABIN_FILTER', 'Filtru de Polen/Habitaclu'
    BRAKE_CHECK = 'BRAKE_CHECK', 'Verificare Frâne'
    COOLANT = 'COOLANT', 'Verificare/Schimb Lichid de Răcire'
    BATTERY = 'BATTERY', 'Verificare/Înlocuire Baterie'
    TIRES = 'TIRES', 'Anvelope (Schimb Sezonier)'
    WIPERS = 'WIPERS', 'Ștergătoare de Parbriz'

    # Safety/Equipment Obligations
    FIRE_EXTINGUISHER = 'FIRE_EXTINGUISHER', 'Extinctor'
    FIRST_AID_KIT = 'FIRST_AID_KIT', 'Trusă de Prim Ajutor'


class ReminderType(models.TextChoices):
    LEGAL = 'LEGAL', 'Legal/Administrativ'
    MECHANICAL = 'MECHANICAL', 'Mecanică/Întreținere'
    SAFETY = 'SAFETY', 'Siguranță/Echipament'
    FINANCIAL = 'FINANCIAL', 'Financiar/Asigurări'
    SEASONAL = 'SEASONAL', 'Sezonier/Operațional'
    OTHER = 'OTHER', 'Altele'




class UserProfile(models.Model):
    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    django_user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_profile', null=True, blank=True)
    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, unique=True)
    profile_photo = models.URLField()  # Required: Stores URL for profile photo
    cover_photos = models.ManyToManyField('CoverPhoto', blank=True, related_name='users')
    user_type = models.CharField(max_length=20, choices=USER_TYPES)
    business_address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=50, choices=ROMANIAN_CITIES, blank=True, null=True)
    sector = models.CharField(max_length=20, choices=SECTORS, blank=True, null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    approval_status = models.CharField(max_length=20, choices=APPROVAL_STATUSES, default='pending')
    account_status = models.CharField(max_length=20, choices=ACCOUNT_STATUSES, default='active')
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    subscription_plan = models.CharField(max_length=20, choices=SUBSCRIPTION_PLANS, default='bronze')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_profiles'

    def __str__(self):
        return self.full_name


class CoverPhoto(models.Model):
    photo_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    photo_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'cover_photos'

    def __str__(self):
        return f"Cover photo: {self.photo_url}"


class CarBrand(models.Model):
    brand_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    brand_name = models.CharField(max_length=255, unique=True)
    brand_photo = models.ImageField(upload_to='brands/', blank=True, null=True)

    class Meta:
        db_table = 'car_brands'

    def __str__(self):
        return self.brand_name

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
    description = models.TextField()
    service_photo = models.ImageField(upload_to='services/')
    category = models.CharField(max_length=50, choices=SERVICE_CATEGORIES)
    tags = models.ManyToManyField(Tag, related_name='services', blank=True)

    class Meta:
        db_table = 'services'

    def __str__(self):
        return self.service_name

class SupplierBrandService(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    supplier = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='supplier_services')
    brand = models.ForeignKey(CarBrand, on_delete=models.CASCADE, related_name='brand_services')
    services = models.ManyToManyField(Service, related_name='supplier_brand_services')
    city = models.CharField(max_length=50, choices=ROMANIAN_CITIES)
    sector = models.CharField(max_length=20, choices=SECTORS, blank=True, null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    #photo_url = models.URLField()  # Required: Stores URL for service photo
    active = models.BooleanField(default=True)

    class Meta:
        db_table = 'supplier_brand_services'

    def __str__(self):
        service_names = ', '.join([s.service_name for s in self.services.all()])
        return f"{self.supplier.full_name} - {self.brand.brand_name} - {service_names}"

class Review(models.Model):
    review_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='client_reviews')
    supplier = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='supplier_reviews')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reviews'

    def __str__(self):
        return f"Review by {self.client.full_name} for {self.supplier.full_name}"

class Notification(models.Model):
    notification_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    receiver = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='received_notifications')
    type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'

    def __str__(self):
        return f"Notification {self.type} to {self.receiver.full_name}"



class Request(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='client_requests')
    supplier = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='supplier_requests')
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    status = models.CharField(max_length=20, choices=REQUEST_STATUSES)
    phone_number = models.CharField(max_length=20)
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)  
    created_at = models.DateTimeField(default=timezone.now)


    class Meta:
        db_table = 'requests'

    def __str__(self):
        return f"Request from {self.client.full_name} to {self.supplier.full_name}"




class OTPVerification(models.Model):
    user = models.ForeignKey('UserProfile', on_delete=models.CASCADE, related_name='otp_verifications')
    otp = models.CharField(max_length=6)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'otp_verifications'

    def __str__(self):
        return f"OTP for {self.user.email}"

class BusinessHours(models.Model):
    supplier = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='business_hours')
    
    # Monday to Friday (default open)
    monday_open = models.TimeField(default='08:00')
    monday_close = models.TimeField(default='19:00')
    monday_closed = models.BooleanField(default=False)
    
    tuesday_open = models.TimeField(default='08:00')
    tuesday_close = models.TimeField(default='19:00')
    tuesday_closed = models.BooleanField(default=False)
    
    wednesday_open = models.TimeField(default='08:00')
    wednesday_close = models.TimeField(default='19:00')
    wednesday_closed = models.BooleanField(default=False)
    
    thursday_open = models.TimeField(default='08:00')
    thursday_close = models.TimeField(default='19:00')
    thursday_closed = models.BooleanField(default=False)
    
    friday_open = models.TimeField(default='08:00')
    friday_close = models.TimeField(default='19:00')
    friday_closed = models.BooleanField(default=False)
    
    # Weekend (default closed)
    saturday_open = models.TimeField(default='09:00')
    saturday_close = models.TimeField(default='17:00')
    saturday_closed = models.BooleanField(default=True)
    
    sunday_open = models.TimeField(default='09:00')
    sunday_close = models.TimeField(default='17:00')
    sunday_closed = models.BooleanField(default=True)

    class Meta:
        db_table = 'business_hours'
        unique_together = ('supplier',)

    def __str__(self):
        return f"Business Hours for {self.supplier.full_name}"




# models.py - Add this to your existing models
class UserDevice(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='devices')
    player_id = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'user_devices'

    def __str__(self):
        return f"{self.user.full_name} - {self.player_id}"


class PasswordResetToken(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='password_reset_tokens')
    token = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'password_reset_tokens'

    def __str__(self):
        return f"Password reset for {self.user.email}"

    def is_expired(self):
        return timezone.now() > self.expires_at



# In models.py

class SalesRepresentative(models.Model):
    representative_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    judet = models.CharField(max_length=50, choices=JUDETE)
    address = models.CharField(max_length=200, blank=True, null=True)
    phone = models.CharField(
        max_length=10,
        unique=True,
        validators=[RegexValidator(r'^\d{10}$', 'Phone must be exactly 10 digits.')]
    )
    approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'sales_representatives'

    def __str__(self):
        return self.name

class SupplierReferral(models.Model):
    referral_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sales_representative = models.ForeignKey(SalesRepresentative, on_delete=models.CASCADE, related_name='referrals')
    supplier = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='referrals')
    has_received_commission = models.BooleanField(default=False)  # Moved here
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'supplier_referrals'
        unique_together = ('sales_representative', 'supplier')

    def __str__(self):
        return f"{self.sales_representative.name} referred {self.supplier.full_name}"


class AppLink(models.Model):
    url = models.URLField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'app_links'
        ordering = ['-timestamp']

    def __str__(self):
        return f"App Link - {self.url} ({self.timestamp})"



# --- CAR AND OBLIGATION MODELS ---

class Car(models.Model):
    """
    Core model for the vehicle itself.
    """
    car_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Links to the UserProfile for ownership
    user = models.ForeignKey(
        'UserProfile', 
        on_delete=models.CASCADE,
        related_name='cars',
        verbose_name='Owner'
    )
    
    # Links to the existing CarBrand model
    brand = models.ForeignKey(
        'CarBrand', 
        on_delete=models.PROTECT, 
        related_name='cars_of_this_brand'
    )
    
    model = models.CharField(max_length=100)
    year = models.PositiveIntegerField()
    license_plate = models.CharField(max_length=20, unique=True)

    # Kilometers/Odometer Tracking
    current_km = models.PositiveIntegerField(
        verbose_name='Current Mileage (KM)'
    )
    last_km_updated_at = models.DateTimeField(
        verbose_name='Last Mileage Update'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'cars'
    
    def __str__(self):
        return f"{self.brand.brand_name} {self.model} ({self.license_plate})"



class CarObligation(models.Model):
    """
    Tracks a specific obligation (e.g., ITP, Oil Change) for a specific car.
    This replaces the old repetitive *_status fields.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    car = models.ForeignKey(
        Car,
        on_delete=models.CASCADE,
        related_name='obligations',
        verbose_name='Car'
    )
    
    obligation_type = models.CharField(
        max_length=50,
        choices=ObligationDefinition.choices,
        verbose_name='Obligation Type'
    )
    
    reminder_type = models.CharField(
        max_length=20,
        choices=ReminderType.choices,
        verbose_name='Reminder Type'
    )
    
    doc_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name='Document URL'
    )
    
    due_date = models.DateField(
        verbose_name='Obligation Due Date'
    )
    
    note = models.TextField(
        blank=True,
        null=True,
        verbose_name='Note'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'car_obligations'
        
    def __str__(self):
        return f"{self.car.license_plate} - {self.get_obligation_type_display()}"


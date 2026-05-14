from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone
import jdatetime
from datetime import datetime

VEHICLE_TYPES = [
    ('Nissan', 'نیسان'),
    ('Pickup_nissan', 'نیسان کمپرسی'),
    ('Roomy_nissan', 'نیسان اتاقی'),
    ('Khorman', 'خاور'),
    ('Truck', 'کامیون'),
    ('Trailer', 'تریلی'),
    ('Pickup_truck', 'وانت'),
]
CITIES = [
    ('Dezful', 'دزفول'),
    ('Tehran', 'تهران'),
    ('Shiraz', 'شیراز'),
    ('Isfahan', 'اصفهان'),
    ('Mashhad', 'مشهد'),
    ('Tabriz', 'تبریز'),
    ('Ahvaz', 'اهواز'),
    ('Karaj', 'کرج'),
    ('Qom', 'قم'),
    ('Kermanshah', 'کرمانشاه'),
    ('Rasht', 'رشت'),
    ('Zahedan', 'زاهدان'),
    ('Hamadan', 'همدان'),
    ('Yazd', 'یزد'),
    ('Ardabil', 'اردبیل'),
    ('Bandar_Abbas', 'بندرعباس'),
    ('Arak', 'اراک'),
    ('Urmia', 'ارومیه'),
    ('Sanandaj', 'سنندج'),
    ('Gorgan', 'گرگان'),
    ('Babol', 'بابل'),
    ('Qazvin', 'قزوین'),
    ('Zanjan', 'زنجان'),
    ('Khorramabad', 'خرم‌آباد'),
    ('Bushehr', 'بوشهر'),
    ('Sari', 'ساری'),
    ('Birjand', 'بیرجند'),
    ('Ilam', 'ایلام'),
    ('Yasuj', 'یاسوج'),
    ('Shahrekord', 'شهرکرد'),
    ('Bojnord', 'بجنورد'),
]

class UserManager(BaseUserManager):
    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError('شماره موبایل الزامی است')
        phone_number = phone_number.strip()
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('سوپر یوزر باید is_staff=True داشته باشد')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('سوپر یوزر باید is_superuser=True داشته باشد')
        
        return self.create_user(phone_number, password, **extra_fields)


class User(AbstractUser):
    username = None  
    phone_number = models.CharField(max_length=11, unique=True, verbose_name='شماره موبایل')
    email = models.EmailField(blank=True, null=True)
    first_name = models.CharField(max_length=150, verbose_name='نام')
    last_name = models.CharField(max_length=150, verbose_name='نام خانوادگی')
    
    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []
    
    objects = UserManager()
    
    def __str__(self):
        return self.phone_number
    
    class Meta:
        verbose_name = 'کاربر'
        verbose_name_plural = 'کاربران'


class Driver(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='driver')
    vehicle_type = models.CharField(max_length=50, choices=VEHICLE_TYPES, verbose_name='نوع وسیله')
    driver_city = models.CharField(max_length=50, choices=CITIES, verbose_name='شهر فعالیت')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.vehicle_type}"
    
    class Meta:
        verbose_name = 'راننده'
        verbose_name_plural = 'رانندگان'


class Load(models.Model):
    STATUS_CHOICES = [
        ('pending', 'در انتظار راننده'),
        ('assigned', 'اختصاص داده شده'),
        ('in_progress', 'در حال حمل'),
        ('delivered', 'تحویل شده'),
        ('cancelled', 'لغو شده'),
    ]
    ROUTE_TYPES = [
        ('within_city', 'درون شهری'),
        ('intercity', 'برون شهری'),
    ]
    route_type = models.CharField(
        max_length=20, 
        choices=ROUTE_TYPES, 
        default='within_city', 
        verbose_name='نوع مسیر'
    )
    cargo_type = models.CharField(max_length=100, verbose_name='نوع بار')
    weight = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='وزن (تن)')
    price = models.DecimalField(max_digits=15, decimal_places=0, verbose_name='مبلغ (تومان)')
    
    pickup_location = models.CharField(max_length=200, verbose_name='مبدا')
    pickup_address = models.TextField(verbose_name='آدرس دقیق بارگیری')
    dropoff_location = models.CharField(max_length=200, verbose_name='مقصد')
    dropoff_address = models.TextField(verbose_name='آدرس دقیق تخلیه')
    
    pickup_date_shamsi = models.CharField(max_length=20, verbose_name='تاریخ بارگیری (شمسی)', blank=True, null=True)
    pickup_time = models.TimeField(verbose_name='ساعت بارگیری', blank=True, null=True)
    pickup_datetime_gregorian = models.DateTimeField(verbose_name='تاریخ و زمان (میلادی)', blank=True, null=True)
    
    expected_delivery_date_shamsi = models.CharField(max_length=20, verbose_name='تاریخ تحویل (شمسی)', blank=True, null=True)
    expected_delivery_time = models.TimeField(verbose_name='ساعت تحویل', blank=True, null=True)
    
    required_vehicle = models.CharField(max_length=50, choices=VEHICLE_TYPES, verbose_name='وسیله مورد نیاز')
    city = models.CharField(max_length=50, choices=CITIES, verbose_name='شهر بارگیری')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    accepted_driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, blank=True, related_name='accepted_loads')
    accepted_datetime = models.DateTimeField(null=True, blank=True)
    
    description = models.TextField(blank=True, verbose_name='توضیحات اضافی')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if self.pickup_date_shamsi and self.pickup_time:
            try:
                year, month, day = map(int, self.pickup_date_shamsi.split('-'))
                shamsi_date = jdatetime.date(year, month, day)
                gregorian_date = shamsi_date.togregorian()
                self.pickup_datetime_gregorian = timezone.make_aware(
                    datetime.combine(gregorian_date, self.pickup_time)
                )
            except:
                pass
        super().save(*args, **kwargs)
    
    def get_pickup_date_display(self):
        if self.pickup_date_shamsi:
            return self.pickup_date_shamsi
        return ''
    
    def __str__(self):
        return f"{self.cargo_type} - {self.pickup_location} به {self.dropoff_location}"
    
    def can_be_accepted(self):
        return self.status == 'pending'
    
    def accept_by_driver(self, driver):
        from django.db import transaction
        with transaction.atomic():
            if self.status == 'pending':
                self.status = 'assigned'
                self.accepted_driver = driver
                self.accepted_datetime = timezone.now()
                self.save()
                return True
        return False
    
    class Meta:
        verbose_name = 'بار'
        verbose_name_plural = 'بارها'
        ordering = ['-created_at']


class LoadLog(models.Model):
    load = models.ForeignKey(Load, on_delete=models.CASCADE, related_name='logs')
    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.load} - {self.action} - {self.timestamp}"
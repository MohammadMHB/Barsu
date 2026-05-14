from django import forms
from django.contrib.auth import authenticate
from django.core.cache import cache
from .models import Load, Driver, VEHICLE_TYPES, CITIES, User
import jdatetime
import random

class LoadForm(forms.ModelForm):
    pickup_date_shamsi = forms.CharField(
        max_length=20, 
        label='تاریخ بارگیری (مثال: 1403-02-15)',
        widget=forms.TextInput(attrs={'placeholder': '1403-02-15', 'dir': 'ltr'})
    )
    pickup_time = forms.TimeField(
        label='ساعت بارگیری',
        widget=forms.TimeInput(attrs={'type': 'time', 'dir': 'ltr'})
    )
    expected_delivery_date_shamsi = forms.CharField(
        max_length=20,
        label='تاریخ تحویل (مثال: 1403-02-15)',
        required=False,
        widget=forms.TextInput(attrs={'placeholder': '1403-02-15', 'dir': 'ltr'})
    )
    expected_delivery_time = forms.TimeField(
        label='ساعت تحویل',
        required=False,
        widget=forms.TimeInput(attrs={'type': 'time', 'dir': 'ltr'})
    )

    class Meta:
        model = Load
        fields = [
            'cargo_type', 'weight', 'price',
            'pickup_location', 'pickup_address',
            'dropoff_location', 'dropoff_address',
            'pickup_date_shamsi', 'pickup_time',
            'expected_delivery_date_shamsi', 'expected_delivery_time',
            'required_vehicle', 'city', 'route_type', 'description'
        ]
        widgets = {
            'pickup_address': forms.Textarea(attrs={'rows': 3}),
            'dropoff_address': forms.Textarea(attrs={'rows': 3}),
            'description': forms.Textarea(attrs={'rows': 2}),
            'cargo_type': forms.TextInput(attrs={'placeholder': 'مثال: سیمان، سولفات، آهن، ...'}),
            'required_vehicle': forms.Select(choices=VEHICLE_TYPES, attrs={'class': 'form-control'}),
            'city': forms.Select(choices=CITIES, attrs={'class': 'form-control'}),
            'route_type': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'cargo_type': 'نوع بار (دلخواه بنویسید)',
            'weight': 'وزن (تن)',
            'price': 'مبلغ (تومان)',
            'pickup_location': 'محله بارگیری',
            'pickup_address': 'آدرس کامل بارگیری',
            'dropoff_location': 'محله تخلیه',
            'dropoff_address': 'آدرس کامل تخلیه',
            'required_vehicle': 'نوع وسیله مورد نیاز',
            'city': 'شهر بارگیری',
            'description': 'توضیحات اضافی',
            'route_type': 'نوع مسیر',  
        }
    
    def clean_pickup_date_shamsi(self):
        data = self.cleaned_data['pickup_date_shamsi']
        try:
            parts = data.split('-')
            if len(parts) == 3:
                year, month, day = map(int, parts)
                jdatetime.date(year, month, day)
            return data
        except:
            raise forms.ValidationError('تاریخ نامعتبر است. فرمت صحیح: 1403-02-15')
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.pickup_date_shamsi = self.cleaned_data['pickup_date_shamsi']
        instance.pickup_time = self.cleaned_data['pickup_time']
        if self.cleaned_data.get('expected_delivery_date_shamsi'):
            instance.expected_delivery_date_shamsi = self.cleaned_data['expected_delivery_date_shamsi']
            instance.expected_delivery_time = self.cleaned_data['expected_delivery_time']
        
        if commit:
            instance.save()
        return instance


class DriverForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, label='نام')
    last_name = forms.CharField(max_length=30, label='نام خانوادگی')
    phone_number = forms.CharField(max_length=11, label='شماره موبایل')
    
    class Meta:
        model = Driver
        fields = ['vehicle_type', 'driver_city', 'is_active']
        labels = {
            'vehicle_type': 'نوع وسیله',
            'driver_city': 'شهر فعالیت',
            'is_active': 'فعال',
        }
        widgets = {
            'vehicle_type': forms.Select(choices=VEHICLE_TYPES, attrs={'class': 'form-control'}),
            'driver_city': forms.Select(choices=CITIES, attrs={'class': 'form-control'}),
        }
    
    def clean_phone_number(self):
        phone = self.cleaned_data['phone_number']
        if User.objects.filter(phone_number=phone).exists():
            raise forms.ValidationError('این شماره موبایل قبلاً ثبت شده است')
        return phone
    
    def save(self, commit=True):
        default_password = '12345678'
        user = User(
            phone_number=self.cleaned_data['phone_number'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
        )
        user.set_password(default_password)
        user.save()
        
        driver = super().save(commit=False)
        driver.user = user
        if commit:
            driver.save()
        return driver


class DriverEditForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, label='نام')
    last_name = forms.CharField(max_length=30, label='نام خانوادگی')
    phone_number = forms.CharField(max_length=11, label='شماره موبایل')
    
    class Meta:
        model = Driver
        fields = ['phone_number', 'vehicle_type', 'driver_city', 'is_active']
        labels = {
            'phone_number': 'شماره موبایل',
            'vehicle_type': 'نوع وسیله',
            'driver_city': 'شهر فعالیت',
            'is_active': 'فعال',
        }
        widgets = {
            'vehicle_type': forms.Select(choices=VEHICLE_TYPES, attrs={'class': 'form-control'}),
            'driver_city': forms.Select(choices=CITIES, attrs={'class': 'form-control'}),
        }
    
    def save(self, commit=True):
        driver = super().save(commit=False)
        if commit:
            driver.save()
            user = driver.user
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.phone_number = self.cleaned_data['phone_number']
            user.save()
        return driver


class OTPRequestForm(forms.Form):
    phone_number = forms.CharField(
        max_length=11,
        label='شماره موبایل',
        widget=forms.TextInput(attrs={
            'id': 'phone_number',
            'placeholder': '09123456789',
            'dir': 'ltr',
            'class': 'form-control'
        })
    )
    
    def clean_phone_number(self):
        phone = self.cleaned_data['phone_number']
        # if not User.objects.filter(phone_number=phone).exists():
        #     raise forms.ValidationError('این شماره موبایل در سیستم ثبت نشده است')
        return phone
    
    def send_otp(self):
        phone = self.cleaned_data['phone_number']
        otp = str(random.randint(100000, 999999))
        cache.set(f'otp_{phone}', otp, timeout=120)
        return otp


class OTPVerifyForm(forms.Form):
    phone_number = forms.CharField(max_length=11, widget=forms.HiddenInput())
    otp_code = forms.CharField(
        max_length=6,
        label='رمز یکبارمصرف',
        widget=forms.TextInput(attrs={
            'id': 'otp_code',
            'placeholder': '123456',
            'dir': 'ltr',
            'class': 'form-control'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        phone = cleaned_data.get('phone_number')
        otp_code = cleaned_data.get('otp_code')
        
        if phone and otp_code:
            cached_otp = cache.get(f'otp_{phone}')
            if not cached_otp:
                raise forms.ValidationError('کد منقضی شده است. دوباره درخواست کنید')
            if cached_otp != otp_code:
                raise forms.ValidationError('کد وارد شده صحیح نیست')
        
        return cleaned_data
    
    def get_user(self):
        phone = self.cleaned_data['phone_number']
        return User.objects.get(phone_number=phone)
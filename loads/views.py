from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.http import JsonResponse
from django.core.cache import cache
from django.conf import settings
from .models import Load, Driver, LoadLog, User
from .forms import LoadForm, DriverForm, DriverEditForm, OTPRequestForm, OTPVerifyForm
from .kavenegar_sms import send_sms_to_driver, notify_drivers_new_load, notify_driver_accepted, notify_admin_load_accepted
import random

def is_admin_user(user):
    return user.is_superuser or user.groups.filter(name='Admin').exists()

def is_driver_user(user):
    if not user.is_authenticated:
        return False
    try:
        driver = Driver.objects.get(user=user)
        return driver.is_active
    except Driver.DoesNotExist:
        return False

def get_driver_from_user(user):
    try:
        return Driver.objects.get(user=user)
    except Driver.DoesNotExist:
        return None

def otp_request_view(request):
    if request.method == 'POST':
        form = OTPRequestForm(request.POST)
        if form.is_valid():
            phone = form.cleaned_data['phone_number']
            otp = str(random.randint(100000, 999999))
            cache.set(f'otp_{phone}', otp, timeout=120)
            
            send_sms_to_driver(phone, f'🔐 کد ورود شما: {otp}\n\nاین کد تا 2 دقیقه معتبر است.')
            
            request.session['otp_phone'] = phone
            request.session.modified = True
            
            return redirect('loads:otp_verify')
        else:
            messages.error(request, 'شماره موبایل معتبر نیست')
    else:
        form = OTPRequestForm()
    
    return render(request, 'otp_request.html', {'form': form})

def otp_verify_view(request):
    phone = request.session.get('otp_phone')
    
    if not phone:
        messages.error(request, 'لطفاً ابتدا شماره موبایل خود را وارد کنید')
        return redirect('loads:otp_request')
    
    if request.method == 'POST':
        form = OTPVerifyForm(request.POST, initial={'phone_number': phone})
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            cache.delete(f'otp_{phone}')
            request.session.pop('otp_phone', None)
            request.session.modified = True
            
            if hasattr(user, 'driver') and user.driver.is_active:
                return redirect('loads:driver_dashboard')
            return redirect('loads:admin_dashboard')
        else:
            messages.error(request, 'کد وارد شده صحیح نیست')
    else:
        form = OTPVerifyForm(initial={'phone_number': phone})
    
    return render(request, 'otp_verify.html', {'form': form, 'phone': phone})

def driver_logout_view(request):
    logout(request)
    return redirect('loads:otp_request')

@login_required
@user_passes_test(is_admin_user)
def admin_dashboard(request):
    pending_loads = Load.objects.filter(status='pending').count()
    assigned_loads = Load.objects.filter(status='assigned').count()
    total_drivers = Driver.objects.filter(is_active=True).count()
    
    intercity_count = Load.objects.filter(route_type='intercity').count()
    within_city_count = Load.objects.filter(route_type='within_city').count()
    
    recent_loads = Load.objects.all().order_by('-created_at')[:10]
    
    context = {
        'pending_loads': pending_loads,
        'assigned_loads': assigned_loads,
        'total_drivers': total_drivers,
        'intercity_count': intercity_count,
        'within_city_count': within_city_count,
        'recent_loads': recent_loads,
    }
    return render(request, 'admin_panel/dashboard.html', context)

@login_required
@user_passes_test(is_admin_user)
def add_load(request):
    if request.method == 'POST':
        form = LoadForm(request.POST)
        if form.is_valid():
            load = form.save()
            
            print("="*50)
            print(f"🔍 بار جدید ثبت شد: {load.cargo_type}")
            print(f"🔍 وسیله مورد نیاز: {load.required_vehicle}")
            
            eligible_drivers = Driver.objects.filter(
                is_active=True,
                vehicle_type=load.required_vehicle,
                driver_city=load.city
            )
            
            print(f"🔍 تعداد رانندگان مناسب: {eligible_drivers.count()}")
            for d in eligible_drivers:
                print(f"   - {d.user.username}: {d.user.phone_number} | وسیله: {d.vehicle_type}")
            print("="*50)
            
            LoadLog.objects.create(
                load=load,
                action='created',
                details=f'بار توسط {request.user.phone_number} ایجاد شد'
            )
            
            if eligible_drivers.exists():
                sent_count = notify_drivers_new_load(load, eligible_drivers)
                messages.success(request, f'✅ بار با موفقیت ثبت شد. پیامک به {sent_count} راننده ارسال شد.')
            else:
                messages.warning(request, f'⚠️ بار ثبت شد اما هیچ راننده فعالی با وسیله {load.get_required_vehicle_display()} یافت نشد!')
            
            return redirect('/admin/loads/')
    else:
        form = LoadForm()
    
    return render(request, 'admin_panel/add_load.html', {'form': form})

@login_required
@user_passes_test(is_admin_user)
def load_list(request):
    loads = Load.objects.all().order_by('-created_at')
    return render(request, 'admin_panel/load_list.html', {'loads': loads})

@login_required
def driver_dashboard(request):
    try:
        driver = Driver.objects.get(user=request.user)
    except Driver.DoesNotExist:
        if request.user.is_superuser or is_admin_user(request.user):
            return redirect('loads:admin_dashboard')
        return render(request, 'error.html', {'message': 'پروفایل راننده یافت نشد. لطفاً با ادمین تماس بگیرید.'})
    
    filter_by_vehicle = request.GET.get('filter_vehicle', 'false') == 'true'
    
    all_loads = Load.objects.filter(status='pending').order_by('-created_at')
    
    my_loads = Load.objects.filter(accepted_driver=driver, status='assigned').order_by('-created_at')
    
    taken_loads = Load.objects.filter(status='assigned').exclude(accepted_driver=driver).order_by('-created_at')
    
    if filter_by_vehicle:
        available_loads = all_loads.filter(required_vehicle=driver.vehicle_type)
    else:
        available_loads = all_loads
    
    context = {
        'driver': driver,
        'available_loads': available_loads,
        'my_loads': my_loads,
        'taken_loads': taken_loads,
        'filter_active': filter_by_vehicle,
    }
    return render(request, 'driver/dashboard.html', context)

@login_required
def accept_load(request, load_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'روش غیرمجاز'}, status=405)
    
    driver = get_driver_from_user(request.user)
    if not driver:
        return JsonResponse({'success': False, 'message': 'پروفایل راننده یافت نشد'})
    
    load = get_object_or_404(Load, id=load_id)
    
    if load.status != 'pending':
        return JsonResponse({'success': False, 'message': 'این بار قبلاً توسط راننده دیگری قبول شده است'})
    
    with transaction.atomic():
        load = Load.objects.select_for_update().get(id=load_id)
        if load.status == 'pending':
            load.status = 'assigned'
            load.accepted_driver = driver
            load.accepted_datetime = timezone.now()
            load.save()
            
            LoadLog.objects.create(
                load=load,
                driver=driver,
                action='accepted',
                details=f'راننده {driver.user.get_full_name()} بار را قبول کرد'
            )
            
            notify_driver_accepted(driver, load)
            notify_admin_load_accepted(settings.ADMIN_PHONE_NUMBER, load, driver)
            
            return JsonResponse({
                'success': True,
                'message': '✅ بار با موفقیت قبول شد.'
            })
    
    return JsonResponse({'success': False, 'message': 'خطا در پذیرش بار'})

@login_required
def my_loads(request):
    driver = get_driver_from_user(request.user)
    loads = Load.objects.filter(accepted_driver=driver, status='assigned').order_by('-created_at')
    return render(request, 'driver/my_loads.html', {'loads': loads})

@login_required
@user_passes_test(is_admin_user)
def driver_list(request):
    drivers = Driver.objects.select_related('user').all().order_by('-created_at')
    return render(request, 'admin_panel/drivers.html', {'drivers': drivers})

@login_required
@user_passes_test(is_admin_user)
def add_driver(request):
    if request.method == 'POST':
        form = DriverForm(request.POST)
        if form.is_valid():
            driver = form.save()
            messages.success(request, f'✅ راننده {driver.user.get_full_name()} با موفقیت اضافه شد. رمز عبور پیش‌فرض: 12345678')
            return redirect('/admin/drivers/')
        else:
            messages.error(request, '❌ خطا در فرم. لطفاً اطلاعات را بررسی کنید.')
    else:
        form = DriverForm()
    
    return render(request, 'admin_panel/add_driver.html', {'form': form})

@login_required
@user_passes_test(is_admin_user)
def toggle_driver_status(request, driver_id):
    driver = get_object_or_404(Driver, id=driver_id)
    driver.is_active = not driver.is_active
    driver.save()
    status = "فعال" if driver.is_active else "غیرفعال"
    messages.success(request, f'وضعیت راننده {driver.user.get_full_name()} به {status} تغییر کرد')
    return redirect('/admin/drivers/')

@login_required
@user_passes_test(is_admin_user)
def edit_load(request, load_id):
    load = get_object_or_404(Load, id=load_id)
    
    if request.method == 'POST':
        form = LoadForm(request.POST, instance=load)
        if form.is_valid():
            form.save()
            messages.success(request, f'✅ بار {load.cargo_type} با موفقیت ویرایش شد.')
            return redirect('/admin/loads/')
    else:
        form = LoadForm(instance=load)
    
    return render(request, 'admin_panel/edit_load.html', {'form': form, 'load': load})

@login_required
@user_passes_test(is_admin_user)
def edit_driver(request, driver_id):
    driver = get_object_or_404(Driver, id=driver_id)
    
    if request.method == 'POST':
        form = DriverEditForm(request.POST, instance=driver)
        if form.is_valid():
            form.save()
            messages.success(request, f'✅ راننده {driver.user.get_full_name()} با موفقیت ویرایش شد.')
            return redirect('/admin/drivers/')
    else:
        form = DriverEditForm(instance=driver, initial={
            'first_name': driver.user.first_name,
            'last_name': driver.user.last_name,
            'phone_number': driver.user.phone_number,
        })
    
    return render(request, 'admin_panel/edit_driver.html', {'form': form, 'driver': driver})
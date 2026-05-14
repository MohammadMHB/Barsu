import requests
from django.conf import settings
from sms_ir import SmsIr

def send_sms_to_driver(phone_number, message):

    print(f"[SMS] به شماره {phone_number}: {message[:50]}...")
    
    api_key = getattr(settings, 'SMS_IR_API_KEY', None)
    line_number = getattr(settings, 'SMS_IR_LINE_NUMBER', None)
    
    if not api_key:
        print("❌ SMS_IR_API_KEY در settings.py تنظیم نشده")
        return {'success': False, 'error': 'API Key missing'}
    
    try:
        sms_ir = SmsIr(api_key, line_number if line_number else "0")
        result = sms_ir.send_sms(phone_number, message, line_number if line_number else "0")
        print(f"✅ پیامک به {phone_number} ارسال شد")
        print(f"📦 پاسخ: {result}")
        return {'success': True, 'result': result}
    except Exception as e:
        print(f"❌ خطا در ارسال به {phone_number}: {e}")
        return {'success': False, 'error': str(e)}


def notify_drivers_new_load(load, drivers):

    try:
        if hasattr(load, 'get_cargo_type_display'):
            cargo_type = load.get_cargo_type_display()
        else:
            cargo_type = load.cargo_type
    except:
        cargo_type = load.cargo_type if hasattr(load, 'cargo_type') else 'بار'
    
    try:
        if load.pickup_time:
            pickup_time = load.pickup_time.strftime('%H:%M')
        else:
            pickup_time = 'نامشخص'
    except:
        pickup_time = 'نامشخص'
    
    try:
        formatted_price = f"{load.price:,}".replace(',', '.')
    except:
        formatted_price = str(load.price) if load.price else 'نامشخص'
    
    route_type = "برون شهری" if getattr(load, 'route_type', 'within_city') == 'intercity' else "درون شهری"
    
    message = f"""🚚 بار جدید در بارسو !

📦 نوع بار: {cargo_type}
📍 مسیر: {route_type}
📅 زمان بارگیری: {load.pickup_date_shamsi} - {pickup_time}
💰 مبلغ: {formatted_price} تومان

برای قبول بار، وارد پنل شوید:
https://barsu.ir/driver/dashboard"""
    
    sent_count = 0
    for driver in drivers:
        phone_number = driver.user.phone_number
        result = send_sms_to_driver(phone_number, message)
        if result.get('success'):
            sent_count += 1
    
    return sent_count


def notify_driver_accepted(driver, load):

    try:
        if hasattr(load, 'get_cargo_type_display'):
            cargo_type = load.get_cargo_type_display()
        else:
            cargo_type = load.cargo_type
    except:
        cargo_type = load.cargo_type if hasattr(load, 'cargo_type') else 'بار'
    
    try:
        if load.pickup_time:
            pickup_time = load.pickup_time.strftime('%H:%M')
        else:
            pickup_time = 'نامشخص'
    except:
        pickup_time = 'نامشخص'
    
    try:
        formatted_price = f"{load.price:,}".replace(',', '.')
    except:
        formatted_price = str(load.price) if load.price else 'نامشخص'
    
    message = f"""✅ تایید قبول بار

📦 نوع بار: {cargo_type}
📅 زمان بارگیری: {load.pickup_date_shamsi} - {pickup_time}
📌 آدرس مبدا:
{load.pickup_address}
📌 آدرس مقصد:
{load.dropoff_address}
💰 مبلغ: {formatted_price} تومان

لطفاً در زمان مشخص شده در محل بارگیری حضور داشته باشید.
موفق باشید! 🚚"""
    
    return send_sms_to_driver(driver.user.phone_number, message)


def notify_admin_load_accepted(admin_phone, load, driver):
 
    try:
        if hasattr(load, 'get_cargo_type_display'):
            cargo_type = load.get_cargo_type_display()
        else:
            cargo_type = load.cargo_type
    except:
        cargo_type = load.cargo_type if hasattr(load, 'cargo_type') else 'بار'
    
    route_type = "برون شهری" if getattr(load, 'route_type', 'within_city') == 'intercity' else "درون شهری"
    
    try:
        formatted_price = f"{load.price:,}".replace(',', '.')
    except:
        formatted_price = str(load.price) if load.price else 'نامشخص'
    
    message = f"""✅ قبول بار جدید

📦 نوع بار: {cargo_type}
👤 راننده: {driver.user.get_full_name()}
📱 موبایل: {driver.user.phone_number}

📍 آدرس مبدا:
{load.pickup_address}

📍 آدرس مقصد:
{load.dropoff_address}

🚗 نوع مسیر: {route_type}
💰 مبلغ: {formatted_price} تومان

لطفاً در پنل مدیریت بررسی کنید."""
    
    return send_sms_to_driver(admin_phone, message)
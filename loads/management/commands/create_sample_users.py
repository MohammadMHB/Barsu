from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from loads.models import Driver

class Command(BaseCommand):
    help = 'ایجاد کاربران نمونه برای تست'
    
    def handle(self, *args, **kwargs):
        # ایجاد گروه ادمین
        admin_group, _ = Group.objects.get_or_create(name='Admin')
        
        # ایجاد ادمین
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_user(
                username='admin',
                password='admin123',
                email='admin@example.com'
            )
            admin.is_superuser = True
            admin.is_staff = True
            admin.first_name = 'مدیر'
            admin.last_name = 'سیستم'
            admin.save()
            admin.groups.add(admin_group)
            self.stdout.write(self.style.SUCCESS('ادمین با موفقیت ایجاد شد (admin/admin123)'))
        
        # ایجاد رانندگان نمونه
        drivers_data = [
            {'username': 'ahmad', 'password': 'driver123', 'first_name': 'احمد', 'last_name': 'رضایی',
             'phone': '09120000001', 'vehicle': 'Nissan', 'city': 'Tehran'},
            {'username': 'mehdi', 'password': 'driver123', 'first_name': 'مهدی', 'last_name': 'کریمی',
             'phone': '09120000002', 'vehicle': 'Nissan', 'city': 'Tehran'},
            {'username': 'saeed', 'password': 'driver123', 'first_name': 'سعید', 'last_name': 'احمدی',
             'phone': '09120000003', 'vehicle': 'Nissan', 'city': 'Tehran'},
            {'username': 'ali', 'password': 'driver123', 'first_name': 'علی', 'last_name': 'محمدی',
             'phone': '09120000004', 'vehicle': 'Khorman', 'city': 'Shiraz'},
        ]
        
        for data in drivers_data:
            if not User.objects.filter(username=data['username']).exists():
                user = User.objects.create_user(
                    username=data['username'],
                    password=data['password'],
                    first_name=data['first_name'],
                    last_name=data['last_name']
                )
                
                Driver.objects.create(
                    user=user,
                    phone_number=data['phone'],
                    vehicle_type=data['vehicle'],
                    driver_city=data['city'],
                    is_active=True
                )
                self.stdout.write(self.style.SUCCESS(f'راننده {data["first_name"]} {data["last_name"]} ایجاد شد'))
        
        self.stdout.write(self.style.SUCCESS('عملیات با موفقیت انجام شد!'))
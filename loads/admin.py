from django.contrib import admin
from .models import Load, Driver, LoadLog, User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'username', 'first_name', 'last_name', 'is_active')
    search_fields = ('phone_number', 'username', 'first_name', 'last_name')
    list_filter = ('is_active',)
    ordering = ('-date_joined',)

@admin.register(Load)
class LoadAdmin(admin.ModelAdmin):
    list_display = ['id', 'cargo_type', 'pickup_location', 'dropoff_location', 'status', 'accepted_driver']
    list_filter = ['status', 'cargo_type', 'city']
    search_fields = ['cargo_type', 'pickup_location', 'dropoff_location']
    readonly_fields = ['created_at', 'updated_at', 'accepted_datetime']
    raw_id_fields = ['accepted_driver']
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('cargo_type', 'weight', 'price', 'description')
        }),
        ('مسیر', {
            'fields': ('pickup_location', 'pickup_address', 'dropoff_location', 'dropoff_address')
        }),
        ('زمان‌بندی', {
            'fields': ('pickup_time', 'expected_delivery_time')
        }),
        ('شرایط', {
            'fields': ('required_vehicle', 'city', 'status')
        }),
        ('تخصیص', {
            'fields': ('accepted_driver', 'accepted_datetime')
        }),
        ('سیستم', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ['get_full_name', 'get_phone_number', 'vehicle_type', 'driver_city', 'is_active']
    list_filter = ['vehicle_type', 'driver_city', 'is_active']
    search_fields = ['user__phone_number', 'user__username', 'user__first_name', 'user__last_name']
    raw_id_fields = ['user']
    
    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'نام و نام خانوادگی'
    get_full_name.admin_order_field = 'user__first_name'
    
    def get_phone_number(self, obj):
        return obj.user.phone_number
    get_phone_number.short_description = 'شماره موبایل'
    get_phone_number.admin_order_field = 'user__phone_number'

@admin.register(LoadLog)
class LoadLogAdmin(admin.ModelAdmin):
    list_display = ['load', 'driver', 'action', 'timestamp']
    list_filter = ['action', 'timestamp']
    search_fields = ['load__cargo_type', 'driver__user__username']
    readonly_fields = ['timestamp']
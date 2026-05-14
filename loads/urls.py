from django.urls import path
from . import views

app_name = 'loads'

urlpatterns = [
    path('', views.otp_request_view, name='home'),
    path('login/', views.otp_request_view, name='otp_request'),
    path('verify/', views.otp_verify_view, name='otp_verify'),
    path('logout/', views.driver_logout_view, name='driver_logout'),
    
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/add-load/', views.add_load, name='add_load'),
    path('admin/loads/', views.load_list, name='load_list'),
    path('admin/edit-load/<int:load_id>/', views.edit_load, name='edit_load'),
    
    path('driver/dashboard/', views.driver_dashboard, name='driver_dashboard'),
    path('driver/accept-load/<int:load_id>/', views.accept_load, name='accept_load'),
    path('driver/my-loads/', views.my_loads, name='my_loads'),
    
    path('admin/drivers/', views.driver_list, name='driver_list'),
    path('admin/add-driver/', views.add_driver, name='add_driver'),
    path('admin/toggle-driver/<int:driver_id>/', views.toggle_driver_status, name='toggle_driver'),
    path('admin/edit-driver/<int:driver_id>/', views.edit_driver, name='edit_driver'),
]
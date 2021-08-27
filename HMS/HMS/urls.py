"""
Definition of paths for HotelFlexProject.
"""

from datetime import datetime
from django.contrib.auth import views
from django.urls import path , include
from django.contrib import admin


from app import views

#Uncomment the next lines to enable the admin:
admin.autodiscover()

urlpatterns = [
    # Examples:
    path('admin/',admin.site.urls),
    path('', views.home, name='home'),
    path('contact', views.contact, name='contact'),
    path('about', views.about, name='about'),
    path('register/',views.register,name='register'),
    path('login/',views.login,name='login'),
    path('booking/',views.booking,name='booking'),
    path('logout',views.logout,name='logout'),
    path('roombooking/',views.roombooking,name='roombooking'),
    path('single/',views.single,name='single'),
    path('forgotpassword/',views.forgotpassword,name='forgot'),
    path('double/',views.double,name='double'),
    path('luxury/',views.luxury,name='luxury'),
    path('deluxe/',views.deluxe,name='deluxe'),
    path('executive/',views.executive,name='executive'),
    path('presidential/',views.presidential,name='presidential'),
    path('bookinghistory/',views.bookinghistory,name='history'),
    path('rooms/',views.rooms,name='rooms'),
    path('adminruby/',views.adminruby,name='adminruby'),
    path('adminlogin/',views.adminlogin,name='adminlogin'),
    path('getusers/',views.getusers,name='adminlogin'),
    path('adminbooking/',views.adminbooking,name='adminbooking'),
    path('salesanalysis/',views.salesanalysis,name='salesanalysis'),
    
    # Uncomment the admin/doc line below to enable admin documentation:
    # path('admin/doc/', include('django.contrib.admindocs.paths')),

    # Uncomment the next line to enable the admin:
    ]

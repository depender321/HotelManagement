from django.contrib import admin
from django.contrib.auth.models import Group
from .models import *
from django.contrib.auth.models import User

# admin.site.site_header ='Admin Page'

# class Admin(admin.ModelAdmin):
#     list_display=('first_name','last_name','email')
#     list_filter=('email')

admin.site.register(RoomBooking)
admin.site.register(BookingHistory)
admin.site.register(Rooms)
admin.site.register(UserDetails)





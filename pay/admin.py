from django.contrib import admin
from pay.models import *

class PayPalSettingsAdmin(admin.ModelAdmin):
    list_display = ('business', 'email', 'use_sandbox')
  
admin.site.register(PayPalSettings, PayPalSettingsAdmin)


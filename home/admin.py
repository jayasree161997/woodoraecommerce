
from django.contrib import admin

from .models import Wallet, Transaction, CustomUser

admin.site.register(Wallet)
admin.site.register(Transaction)
admin.site.register(CustomUser)
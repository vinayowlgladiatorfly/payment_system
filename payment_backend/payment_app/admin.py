from django.contrib import admin
from .models import *
# Register your models here.

admin.site.register(User)
admin.site.register(Wallet)
admin.site.register(Transaction)
admin.site.register(BillPayment)
admin.site.register(BankAccount)
admin.site.register(Notification)
admin.site.register(TwoFactorAuth)
admin.site.register(LoginAttempt)
admin.site.register(JWTBlacklist)
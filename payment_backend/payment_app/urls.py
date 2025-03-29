from django.contrib import admin
from django.urls import path,include
from .authenticate_views import *
from .wallet_views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    path('signup/',signup,name='signup'),
    path('login/',login,name='login'),
    path('wallet_balance/',wallet_balance,name='wallet_balance')
]

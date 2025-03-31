from django.contrib import admin
from django.urls import path,include
from .authenticate_views import *
from .wallet_views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    path('signup/',signup,name='signup'),
    path('login/',login,name='login'),
    path('wallet_balance/',wallet_balance,name='wallet_balance'),
    path('add_money/',add_money,name='add_money'),
    path('send_money/',send_money,name='send_money'),
    path('request_money/',request_money,name='request_money'),
    path('hist/',transaction_history,name='transaction_history'),
]

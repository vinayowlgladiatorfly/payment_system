from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Wallet
import jwt
from django.conf import settings
import datetime
import json

# ---------------------- Wallet Management ----------------------------

@csrf_exempt
def wallet_balance(request):
    if request.method != 'GET':
        return JsonResponse({'error': 'Only GET method allowed.'}, status=405)

    # Extract the Authorization header
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return JsonResponse({'error': 'Bearer token required'}, status=401)

    token = auth_header.split(' ')[1].strip()

    try:
        # Decode the JWT token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        user_id = payload.get('user_id')

        # Retrieve wallet information for the authenticated user
        wallet = Wallet.objects.select_related('user').get(user_id=user_id)

        return JsonResponse({
            'user_id': user_id,
            'balance': float(wallet.balance),
            'currency': wallet.currency
        }, status=200)

    except jwt.ExpiredSignatureError:
        return JsonResponse({
            'error': 'Token expired',
            'refresh_required': True,
            'refresh_endpoint': '/authenticate/refresh/'
        }, status=401)
    except Wallet.DoesNotExist:
        return JsonResponse({'error': 'Wallet not found.'}, status=404)
    except jwt.InvalidTokenError:
        return JsonResponse({'error': 'Invalid token'}, status=401)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

# -------------------Add Money to Wallet -----------------


@csrf_exempt
def add_money(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            amount = data.get('amount')
            payment_method = data.get('payment_method')

            if not amount or not payment_method:
                return JsonResponse({'error':"Amount and payment method are required."},status=400)
            
            

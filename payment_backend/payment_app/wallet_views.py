from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import *
import jwt
from django.conf import settings
import json
from decimal import Decimal
from django.utils import timezone
from datetime import datetime
from django.db import transaction



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
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        # Extract Bearer Token
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Bearer token required'}, status=401)

        token = auth_header.split(' ')[1].strip()

        # Decode the JWT token
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            user_id = payload.get('user_id')  # Extract user_id
        except jwt.ExpiredSignatureError:
            return JsonResponse({'error': 'Token expired, refresh required'}, status=401)
        except jwt.InvalidTokenError:
            return JsonResponse({'error': 'Invalid token'}, status=401)

        # Parse request data
        data = json.loads(request.body)
        amount = data.get('amount')
        payment_method = data.get('payment_method')

        # Validate input fields
        if not amount or amount <= 0:
            return JsonResponse({'error': 'Invalid amount'}, status=400)
        if not payment_method:
            return JsonResponse({'error': 'Payment method required'}, status=400)

        # Ensure Wallet Exists
        wallet, created = Wallet.objects.get_or_create(user_id=user_id)

        # Update Wallet Balance
        wallet.balance += amount
        wallet.save()

        # Log Transaction
        transaction = Transaction.objects.create(
            sender_id=user_id,
            receiver_id=user_id,  # Since user is adding money to their own wallet
            amount=amount,
            type='ADD_MONEY',
            status='SUCCESS',
            note=f'Added {amount} via {payment_method}',
            timestamp=datetime.now(),  # ✅ Corrected this
            reference_id=f'TXN_{user_id}_{int(datetime.datetime.now(datetime.timezone.utc))}'  # ✅ Corrected this
        )

        return JsonResponse({
            'message': 'Money added successfully',
            'new_balance': float(wallet.balance),
            'transaction_id': transaction.reference_id
        }, status=200)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON request'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)



#-----------------------Send Money -------------------------
import json
import jwt
import datetime
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction  # ✅ Corrected import

from .models import Wallet, Transaction, User

@csrf_exempt
def send_money(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method allowed'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
        print(data)

        receiver_upi = data.get('receiver_upi')  # ✅ Fixed key name
        amount = data.get('amount')
        note = data.get('note', "")

        if not receiver_upi or not amount:
            return JsonResponse({'error': 'Receiver UPI and amount are required'}, status=400)
        if amount <= 0:
            return JsonResponse({'error': 'Invalid amount'}, status=400)

        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Bearer token required'}, status=401)

        token = auth_header.split(' ')[1].strip()
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])  # ✅ Fixed 'algorithm' -> 'algorithms'
        sender_id = payload.get('user_id')

        sender_wallet = Wallet.objects.filter(user_id=sender_id).first()
        if not sender_wallet:
            return JsonResponse({'error': 'Sender wallet not found'}, status=404)
        if sender_wallet.balance < amount:
            return JsonResponse({'error': 'Insufficient balance'}, status=400)

        receiver_user = User.objects.filter(upi_id=receiver_upi).first()
        if not receiver_user:
            return JsonResponse({'error': 'Receiver user not found'}, status=404)

        receiver_wallet, created = Wallet.objects.get_or_create(user=receiver_user)

        with transaction.atomic():  # ✅ Fixed incorrect Transaction.atomic()
            sender_wallet.balance -= amount
            sender_wallet.save()
            receiver_wallet.balance += amount
            receiver_wallet.save()

            Transaction.objects.create(
                sender=sender_wallet.user,
                receiver=receiver_wallet.user,
                amount=amount,
                type='SEND',
                status='SUCCESS',
                note=note,
                timestamp=datetime.datetime.now(datetime.timezone.utc)  # ✅ Fixed incorrect datetime usage
            )

        return JsonResponse({'message': 'Money sent successfully'}, status=200)

    except jwt.ExpiredSignatureError:
        return JsonResponse({'error': 'Token expired, please refresh'}, status=401)

    except jwt.InvalidTokenError:
        return JsonResponse({'error': 'Invalid token'}, status=401)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON request'}, status=400)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


#--------------Request Money -------------------------

import json
import jwt
import datetime
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from .models import User, Transaction, Notification

@csrf_exempt
def request_money(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method allowed'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
        print(data)

        sender_upi = data.get('sender_upi')  # ✅ Extract sender UPI ID
        amount = data.get('amount')
        note = data.get('note', "")

        if not sender_upi or not amount:
            return JsonResponse({'error': 'Sender UPI and amount are required'}, status=400)
        if amount <= 0:
            return JsonResponse({'error': 'Invalid amount'}, status=400)

        # Get Authorization Token
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Bearer token required'}, status=401)

        token = auth_header.split(' ')[1].strip()
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        receiver_id = payload.get('user_id')

        receiver_user = User.objects.filter(id=receiver_id).first()
        if not receiver_user:
            return JsonResponse({'error': 'Receiver user not found'}, status=404)

        sender_user = User.objects.filter(upi_id=sender_upi).first()
        if not sender_user:
            return JsonResponse({'error': 'Sender user not found'}, status=404)

        # Log Request in Transaction Model
        with transaction.atomic():
            Transaction.objects.create(
                sender=sender_user,
                receiver=receiver_user,
                amount=amount,
                type='REQUEST',
                status='PENDING',  # ✅ Mark as pending
                note=note,
                timestamp=datetime.datetime.now(datetime.timezone.utc)
            )

            # Send Notification to Sender
            Notification.objects.create(
                user=sender_user,
                message=f"Payment request of ₹{amount} from {receiver_user.name} ({receiver_user.upi_id})",
                created_at=datetime.datetime.now(datetime.timezone.utc)
            )

        return JsonResponse({'message': 'Money request sent successfully'}, status=200)

    except jwt.ExpiredSignatureError:
        return JsonResponse({'error': 'Token expired, please refresh'}, status=401)

    except jwt.InvalidTokenError:
        return JsonResponse({'error': 'Invalid token'}, status=401)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON request'}, status=400)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


#-----------------------------Get transaction history ---------------
import json
import jwt
import datetime
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Transaction, User

@csrf_exempt
def transaction_history(request):
    if request.method!= 'GET':
        return JsonResponse({'error': 'Only GET method allowed'}, status=405)
    try:
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Bearer token required'}, status=401)
        token = auth_header.split(' ')[1].strip()
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        user_id = payload.get('user_id')


        user = User.objects.filter(id=user_id).first()
        if not user:
            return JsonResponse({'error': 'User not found'}, status=404)
        

        transaction_type = request.GET.get('type')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        transactions = Transaction.objects.filter(sender=user) | Transaction.objects.filter(receiver=user)

        if transaction_type:
            if transaction_type.upper() == 'SEND':
                transactions = transactions.filter(sender=user)
            elif transaction_type.lower() == 'REQUEST':
                transactions = transactions.filter(receiver=user)
        
        if start_date:
            transactions = transactions.filter(timestamp__gte=start_date)
        if end_date:
            transactions = transactions.filter(timestamp__lte=end_date)
        transactions_list = [
            {
                "id": txn.id,
                "sender": txn.sender.name if txn.sender else None,
                "receiver": txn.receiver.name if txn.receiver else None,
                "amount": txn.amount,
                "type": txn.type,
                "status": txn.status,
                "note": txn.note,
                "timestamp": txn.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            }
            for txn in transactions
        ]

        return JsonResponse({"transactions":transactions_list},status=401)
    except jwt.ExpiredSignatureError:
        return JsonResponse({'error': 'Token expired, please refresh'}, status=401)

    except jwt.InvalidTokenError:
        return JsonResponse({'error': 'Invalid token'}, status=401)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)        
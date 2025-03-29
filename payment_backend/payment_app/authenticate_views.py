from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import User, Wallet
import bcrypt
import json
from django.http import JsonResponse
from django.conf import settings
import datetime
import jwt

# ------------------------ User Management ----------------------------

@csrf_exempt
def signup(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name')
            email = data.get('email')
            phone = data.get('phone')
            password_hash = data.get('password_hash')

            # Validate input fields
            if not all([name, email, phone, password_hash]):
                return JsonResponse({'error': 'All fields are required.'}, status=400)
            if User.objects.filter(email=email).exists():
                return JsonResponse({'error': 'Email already exists.'}, status=400)

            # Hash password
            password_hash = bcrypt.hashpw(password_hash.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            # Create new user
            user = User.objects.create(
                name=name,
                email=email,
                phone=phone,
                password_hash=password_hash,
                created_at=timezone.now(),
                is_verified=False
            )
            return JsonResponse({'message': 'User created successfully.'}, status=201)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON request.'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method.'}, status=405)


@csrf_exempt
def login(request):
    if request.method == 'POST':
        try:
            # Parse request data
            data = json.loads(request.body)
            email = data.get('email')
            password_hash = data.get('password_hash')

            # Validate input
            if not email or not password_hash:
                return JsonResponse({'error': 'Email and password are required'}, status=400)

            # Find user by email
            user = User.objects.filter(email=email).first()
            if not user:
                return JsonResponse({'error': 'Invalid credentials'}, status=401)

            # Verify password
            if not bcrypt.checkpw(password_hash.encode('utf-8'), user.password_hash.encode('utf-8')):
                return JsonResponse({'error': 'Invalid credentials'}, status=401)

            # Create JWT token
            payload = {
                'user_id': user.id,
                'exp': datetime.datetime.now(datetime.timezone.utc) + settings.JWT_EXPIRATION_DELTA,
                'iat': datetime.datetime.now(datetime.timezone.utc),
                'fresh': True
            }
            token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
            token = token.decode('utf-8') if isinstance(token, bytes) else token

            # Update last login
            user.last_login = datetime.datetime.now(datetime.timezone.utc)
            user.save()

            return JsonResponse({
                'message': 'Login successful',
                'token': token,
                'user_id': user.id
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON request.'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Method not allowed'}, status=405)

# -------------------- Token Management ------------------------------


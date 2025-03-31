from django.db import models
from django.utils import timezone

class User(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100, unique=True)
    phone = models.CharField(max_length=15)
    password_hash = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    is_verified = models.BooleanField(default=False)
    last_login = models.DateTimeField(blank=True, null=True)
    upi_id = models.CharField(max_length=50, blank=True, null=True,unique=True)
    def __str__(self):
        return self.name
    
class Wallet(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE)  # Foreign key to User
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=3, default='INR')
    last_updated = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f'{self.user.name} - {self.balance} {self.currency}'
    

    
class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('SEND', 'Send'),
        ('REQUEST', 'Request'),
        ('ADD_MONEY', 'Add Money'),
        ('BILL_PAYMENT', 'Bill Payment')
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed')
    ]

    sender = models.ForeignKey('User', related_name='sent_transactions', on_delete=models.CASCADE)
    receiver = models.ForeignKey('User', related_name='received_transactions', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    note = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now)
    upi_id = models.CharField(max_length=50, blank=True, null=True)
    reference_id = models.CharField(max_length=100, unique=True, blank=True, null=True)

    def __str__(self):
        return f'Transaction {self.id} - {self.amount}'


class BillPayment(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('FAILED', 'Failed')
    ]

    user = models.ForeignKey('User', on_delete=models.CASCADE)  # References the User model
    biller_type = models.CharField(max_length=50)  # e.g., ELECTRICITY, MOBILE
    biller_name = models.CharField(max_length=100)
    customer_id = models.CharField(max_length=100)  # e.g., electricity account number
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    due_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    payment_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"BillPayment {self.id} - {self.biller_name} - {self.status}"
    
class BankAccount(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE)  # References the User model
    account_number = models.CharField(max_length=30)
    ifsc_code = models.CharField(max_length=20)
    bank_name = models.CharField(max_length=100)
    is_verified = models.BooleanField(default=False)
    linked_at = models.DateTimeField(default=timezone.now)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"BankAccount {self.account_number} - {self.bank_name}"
    

class Notification(models.Model):
    TYPE_CHOICES = [
        ('TRANSACTION', 'Transaction'),
        ('OFFER', 'Offer'),
        ('ALERT', 'Alert'),
    ]

    user = models.ForeignKey('User', on_delete=models.CASCADE)  # References the User model
    message = models.TextField()
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Notification for {self.user.name} - {self.type}"
    
class TwoFactorAuth(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE)  # References the User model
    secret_key = models.TextField()
    is_enabled = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"TwoFactorAuth for {self.user.name} - Enabled: {self.is_enabled}"
    
class LoginAttempt(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE)  # References the User model
    ip_address = models.CharField(max_length=45)
    attempted_at = models.DateTimeField(default=timezone.now)
    is_successful = models.BooleanField(default=False)

    def __str__(self):
        return f"LoginAttempt by {self.user.name} - Success: {self.is_successful}"


class JWTBlacklist(models.Model):
    token = models.TextField()
    expires_at = models.DateTimeField()

    def __str__(self):
        return f"Blacklisted Token {self.id} - Expires at {self.expires_at}"
from django.db import models
# from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser
from django.conf import settings




class Profile(models.Model):
    # user = models.OneToOneField(User, on_delete=models.CASCADE)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    mobile_number = models.CharField(max_length=15, null=True, blank=True)

    def __str__(self):
        return self.user.username

class Address(models.Model):
    # user = models.ForeignKey(User, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    postcode = models.CharField(max_length=20)
    mobile = models.CharField(max_length=15)
    house_no = models.CharField(max_length=20)
    street_address = models.CharField(max_length=200)
    region = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)  


    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.street_address}"
    
class Wallet(models.Model):
    # user = models.OneToOneField(User, on_delete=models.CASCADE)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.user.username}'s Wallet - Balance: {self.balance}"
    

class Transaction(models.Model):
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    # transaction_type = models.CharField(max_length=10, choices=(('credit', 'Credit'), ('debit', 'Debit')))
    transaction_type = models.CharField(
        max_length=10, 
        choices=(('credit', 'Credit'), ('debit', 'Debit'), ('refund', 'Refund'))  # Added 'refund'
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type.capitalize()} - ₹{self.amount} on {self.timestamp}"
    



class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)


    def __str__(self):
        return self.username
    

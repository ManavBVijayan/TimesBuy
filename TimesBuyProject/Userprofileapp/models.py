from django.db import models
from django.core.validators import RegexValidator
from Authenticate.models import CustomUser
from django.db.models.signals import post_save
from django.dispatch import receiver



class UserAddress(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.EmailField(max_length=254)
    phone_regex = RegexValidator(regex=r'^[1-9]\d{9}$', message="Phone number must be a 10-digit number without leading zeros.")
    phone_number = models.CharField(validators=[phone_regex], max_length=10, blank=True, null=True)
    address_line_1 = models.CharField(max_length=500)
    address_line_2 = models.CharField(max_length=500, blank=True, null=True)
    postal_code = models.CharField(max_length=10)
    city = models.CharField(max_length=150)
    state = models.CharField(max_length=150)
    country = models.CharField(max_length=50)
    is_delivery_address = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.first_name}, {self.email}, {self.state}"

class Wallet(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def str(self):
        return f"{self.user.username}'s Wallet: {self.balance}"

@receiver(post_save, sender=CustomUser)
def create_wallet(sender, instance, created, **kwargs):
    if created:
        Wallet.objects.create(user=instance)
class WalletTransaction(models.Model):
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)
    order_id = models.ForeignKey('orderapp.Order', on_delete=models.CASCADE,blank=True, null=True)
    deleted = models.BooleanField(default=False)
    transaction_type = models.CharField(max_length=20, choices=(
        ('PURCHASE', 'Purchase'),
        ('CANCEL', 'Cancel'),
        ('RETURN', 'Return'),
    ))

    def __str__(self):
        return f"Wallet Transaction: {self.amount} - {self.date}"
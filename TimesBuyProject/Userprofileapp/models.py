from django.db import models
from django.core.validators import RegexValidator
from Authenticate.models import CustomUser

class UserAddress(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.EmailField(max_length=254)
    phone_regex = RegexValidator(regex=r'^[1-9]\d{9}$', message="Phone number must be a 10-digit number without leading zeros.")
    phone_number = models.CharField(validators=[phone_regex], max_length=10, blank=True, null=True)
    address_line_1 = models.CharField(max_length=250)
    address_line_2 = models.CharField(max_length=250, blank=True, null=True)
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

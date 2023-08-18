from datetime import timedelta

from django.core.validators import RegexValidator
from django.utils import timezone
from django.db import models
from Authenticate.models import CustomUser
from Store.models import ProductVariant


class Order(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('REFUNDED', 'Refunded'),
        ('REFUND IN PROGRESS','Refund in progress'),
        ('NO PAYMENT','No payment')
    ]
    ORDER_STATUS_CHOICES = [
        ('CANCELLED', 'Cancelled'),
        ('DELIVERED', 'Delivered'),
        ('SHIPPED', 'Shipped'),
        ('RETURNED', 'Returned'),
        ('REQUESTED FOR RETURN','Requested for return'),
        ('ORDERED', 'Ordered'),
    ]
    PAYMENT_METHOD_CHOICES = [
        ('NET BANKING', 'Net banking'),
        ('CASH ON DELIVERY', 'Cash on delivery'),
        ('WALLET PAY','Wallet pay'),
    ]
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=150,null=True)
    last_name = models.CharField(max_length=150,null=True)
    email = models.EmailField(max_length=254,null=True)
    phone_regex = RegexValidator(regex=r'^[1-9]\d{9}$', message="Phone number must be a 10-digit number without leading zeros.")
    phone_number = models.CharField(validators=[phone_regex], max_length=10, blank=True, null=True)
    address_line_1 = models.CharField(max_length=250,null=True)
    address_line_2 = models.CharField(max_length=250, blank=True, null=True)
    postal_code = models.CharField(max_length=10,null=True)
    city = models.CharField(max_length=150,null=True)
    state = models.CharField(max_length=150,null=True)
    country = models.CharField(max_length=50,null=True)
    total_price = models.FloatField(null=False)
    payment_status = models.CharField(max_length=25, choices=PAYMENT_STATUS_CHOICES, default='Pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    order_status = models.CharField(max_length=50, choices=ORDER_STATUS_CHOICES, default='Ordered', null=True, blank=True)
    message = models.TextField(null=True)
    tracking_no = models.CharField(max_length=150, null=True)
    order_date = models.DateTimeField(default=timezone.now)
    delivery_date = models.DateTimeField(blank=True, null=True)
    cancelled_date = models.DateTimeField(blank=True, null=True)
    returned_date = models.DateTimeField(blank=True, null=True)
    return_request_date = models.DateTimeField(blank=True, null=True)
    shipping_date = models.DateTimeField(blank=True, null=True)
    return_period_expired=models.DateTimeField(blank=True, null=True)
    applied_coupon = models.ForeignKey('Cartapp.Coupon', on_delete=models.CASCADE, null=True)
    razor_pay_order_id = models.CharField(max_length=150, null=True, blank=True)
    razor_pay_payment_id = models.CharField(max_length=150, null=True, blank=True)
    razor_pay_payment_signature = models.CharField(max_length=150, null=True, blank=True)
    shipping_charge=models.IntegerField(null=True)



    def __str__(self):
        return f"{self.id, self.tracking_no}", f"{self.id}  {self.user.username}"

    def save(self, *args, **kwargs):
        if not self.order_date:
            self.order_date = timezone.now()  # Set the order date to the current time if it's not set
        super().save(*args, **kwargs)




class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    price = models.FloatField(null=False)
    quantity = models.IntegerField(null=False)
    def __str__(self):
        return f"{self.order.id, self.order.tracking_no}"
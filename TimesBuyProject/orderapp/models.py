from datetime import timedelta
from django.utils import timezone


from django.db import models
from Authenticate.models import CustomUser
from Store.models import ProductVariant
from Userprofileapp.models import UserAddress

class Order(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('PENDING','pending'),
        ('PAID','paid')]
    ORDER_STATUS_CHOICES =[
        ('CANCELLED', 'cancelled'),
        ('DELIVERED', 'Delivered'),
        ('SHIPPED', 'Shipped'),
        ('RETURNED', 'Returned'),
        ('ORDERED', 'Ordered'),
    ]
    PAYMENT_METHOD_CHOICES = [
        ('RAZORPAY', 'razorpay'),
        ('CASH_ON_DELIVERY', 'Cash on Delivery'),
    ]
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    address = models.ForeignKey(UserAddress, on_delete=models.CASCADE)
    total_price = models.FloatField(null=False)
    payment_status = models.CharField(max_length=25, choices=PAYMENT_STATUS_CHOICES, default='ordered')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    order_status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='ordered',null=True,blank=True)
    message = models.TextField(null=True)
    tracking_no = models.CharField(max_length=150,null=True)
    order_date = models.DateTimeField(default=timezone.now)
    delivery_date = models.DateTimeField(blank=True, null=True)
    applied_coupon = models.CharField(max_length=50, blank=True, null=True)
    razor_pay_order_id = models.CharField(max_length=150, null=True, blank=True)
    razor_pay_payment_id = models.CharField(max_length=150, null=True, blank=True)
    razor_pay_payment_signature = models.CharField(max_length=150, null=True, blank=True)

    @property
    def return_period_expired(self):
        return_period_end_date = self.delivery_date + timezone.timedelta(days=5)
        return timezone.now() > return_period_end_date
    def __str__(self):
        return f"{self.id, self.tracking_no}", f"{self.id}  {self.user.username}"

    def save(self, *args, **kwargs):
        if not self.order_date:
            self.order_date = timezone.now()  # Set the order date to the current time if it's not set
        if not self.delivery_date:
            self.delivery_date = self.order_date + timedelta(hours=24)
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    price = models.FloatField(null=False)
    quantity = models.IntegerField(null=False)
    def __str__(self):
        return f"{self.order.id, self.order.tracking_no}"
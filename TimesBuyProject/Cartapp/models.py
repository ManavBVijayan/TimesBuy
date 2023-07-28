from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save
from Authenticate.models import CustomUser
from Store.models import ProductVariant
from Userprofileapp.models import UserAddress


class Cart(models.Model):
    user_id= models.OneToOneField(CustomUser, on_delete=models.CASCADE, null=True)
    delivery_address = models.ForeignKey(UserAddress, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f'{self.id}-{self.user_id.username}'

@receiver(post_save, sender=CustomUser)
def create_cart(sender, instance, created, **kwargs):
    if created:
        Cart.objects.create(user_id=instance)

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.id} - {self.cart} - {self.product}'

    @property
    def subtotal(self):
        return self.quantity * self.price


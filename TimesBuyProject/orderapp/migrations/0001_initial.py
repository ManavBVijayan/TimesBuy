# Generated by Django 4.2.2 on 2023-08-15 05:48

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('Store', '__first__'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('Cartapp', '0002_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=150, null=True)),
                ('last_name', models.CharField(max_length=150, null=True)),
                ('email', models.EmailField(max_length=254, null=True)),
                ('phone_number', models.CharField(blank=True, max_length=10, null=True, validators=[django.core.validators.RegexValidator(message='Phone number must be a 10-digit number without leading zeros.', regex='^[1-9]\\d{9}$')])),
                ('address_line_1', models.CharField(max_length=250, null=True)),
                ('address_line_2', models.CharField(blank=True, max_length=250, null=True)),
                ('postal_code', models.CharField(max_length=10, null=True)),
                ('city', models.CharField(max_length=150, null=True)),
                ('state', models.CharField(max_length=150, null=True)),
                ('country', models.CharField(max_length=50, null=True)),
                ('total_price', models.FloatField()),
                ('payment_status', models.CharField(choices=[('PENDING', 'Pending'), ('PAID', 'Paid'), ('REFUNDED', 'Refunded'), ('REFUND IN PROGRESS', 'Refund in progress'), ('NO PAYMENT', 'No payment')], default='Pending', max_length=25)),
                ('payment_method', models.CharField(choices=[('NET BANKING', 'Net banking'), ('CASH ON DELIVERY', 'Cash on delivery'), ('WALLET PAY', 'Wallet pay')], max_length=20)),
                ('order_status', models.CharField(blank=True, choices=[('CANCELLED', 'Cancelled'), ('DELIVERED', 'Delivered'), ('SHIPPED', 'Shipped'), ('RETURNED', 'Returned'), ('REQUESTED FOR RETURN', 'Requested for return'), ('ORDERED', 'Ordered')], default='Ordered', max_length=50, null=True)),
                ('message', models.TextField(null=True)),
                ('tracking_no', models.CharField(max_length=150, null=True)),
                ('order_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('delivery_date', models.DateTimeField(blank=True, null=True)),
                ('cancelled_date', models.DateTimeField(blank=True, null=True)),
                ('returned_date', models.DateTimeField(blank=True, null=True)),
                ('return_request_date', models.DateTimeField(blank=True, null=True)),
                ('shipping_date', models.DateTimeField(blank=True, null=True)),
                ('return_period_expired', models.DateTimeField(blank=True, null=True)),
                ('razor_pay_order_id', models.CharField(blank=True, max_length=150, null=True)),
                ('razor_pay_payment_id', models.CharField(blank=True, max_length=150, null=True)),
                ('razor_pay_payment_signature', models.CharField(blank=True, max_length=150, null=True)),
                ('shipping_charge', models.IntegerField(null=True)),
                ('applied_coupon', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='Cartapp.coupon')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('price', models.FloatField()),
                ('quantity', models.IntegerField()),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='orderapp.order')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Store.productvariant')),
            ],
        ),
    ]

# Generated by Django 4.2.2 on 2023-07-13 06:43

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('Userprofileapp', '0001_initial'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='User_address',
            new_name='UserAddress',
        ),
    ]
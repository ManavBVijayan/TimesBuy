from django.contrib import admin

from .models import Category,Brand,GenderType,Product,ProductVariant,ProductImage,Color,Banner

# Register your models here.
admin.site.register(Category)
admin.site.register(Brand)
admin.site.register(GenderType)
admin.site.register(Product)
admin.site.register(ProductVariant)
admin.site.register(ProductImage)
admin.site.register(Color)
admin.site.register(Banner)

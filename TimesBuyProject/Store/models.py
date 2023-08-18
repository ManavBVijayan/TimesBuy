from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='category_images')
    slug = models.SlugField(blank=True, max_length=250, unique=True)
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'Category'  # Replace 'your_table_name' with the actual table name


    def __str__(self):
        return self.name


class Brand(models.Model):
    name = models.CharField(max_length=50)
    image = models.ImageField(upload_to='brand_images')
    is_active = models.BooleanField(default=True)

    # Fields for the active offer
    offer_title = models.CharField(max_length=100, blank=True, null=True)
    offer_percentage = models.PositiveIntegerField(blank=True, null=True)
    offer_is_active = models.BooleanField(default=False)

    def __str__(self):
        return self.name
class GenderType(models.Model):
    name = models.CharField(max_length=50)
    image=models.ImageField(upload_to='brand_images')

    def __str__(self):
        return self.name
class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    category = models.ForeignKey(Category,on_delete=models.CASCADE)
    brandName = models.ForeignKey(Brand,on_delete=models.CASCADE,null=True)
    gender=models.ForeignKey(GenderType,on_delete=models.CASCADE,null=True)
    slug = models.SlugField(blank=True)
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    def get_absolute_url(self):
        return reverse('product_detail',kwargs={'slug': self.slug})

class Color(models.Model):
    color = models.CharField(max_length=15)

    def __str__(self):
        return self.color
class ProductVariant(models.Model):
    product=models.ForeignKey(Product,on_delete=models.CASCADE)
    model_name=models.CharField(max_length=250)
    model_number=models.CharField(max_length=100)
    dial_shape=models.TextField(max_length=50)
    water_proof=models.BooleanField()
    touch_screen=models.BooleanField()
    color = models.ForeignKey(Color,on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10,decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    slug = models.SlugField(blank=True,unique=True,max_length=100)
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(f"{self.product.name[:20]} {self.color}")
            unique_slug = base_slug
            suffix = 1
            while ProductVariant.objects.filter(slug=unique_slug).exists():
                unique_slug = f"{base_slug}-{suffix}"
                suffix += 1
            self.slug = unique_slug
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} - {self.color}"
class ProductImage(models.Model):
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='product_images/')

    def __str__(self):
        return f"Image for {self.variant.product.name} - {self.variant.color}"

class Banner(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='banner_images')
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, default=None, null=True)

    def __str__(self):
        return self.name

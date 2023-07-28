from django.shortcuts import render, get_object_or_404
from django.utils.text import slugify
from .models import Category, Brand,Product,ProductVariant,ProductImage


def home(request):
    categories = Category.objects.filter(is_active=True)
    brands = Brand.objects.filter(is_active=True)
    return render(request, 'home.html', {'categories': categories, 'brands': brands})

from django.shortcuts import render
from .models import Product, Category

def shop(request):
    category_id = request.GET.get('category')

    # Filter active categories only
    categories = Category.objects.filter(is_active=True).order_by('name')

    if category_id == 'all':
        products = Product.objects.filter(category__is_active=True, is_active=True)  # Filter active products in all categories
        current_category = 'All Products'
    elif category_id:
        current_category = Category.objects.get(id=category_id, is_active=True)  # Retrieve the selected active category
        products = Product.objects.filter(category=current_category, is_active=True)
    else:
        products = Product.objects.filter(category__is_active=True, is_active=True)  # Filter active products in all categories
        current_category = 'All Products'

    context = {
        'products': products,
        'categories': categories,
        'current_category': current_category,
    }
    return render(request, 'shop.html', context)

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    selected_variant = product.productvariant_set.first()  # Assuming you want to display the first color variant initially
    images = selected_variant.images.all()  # Retrieve the images associated with the selected variant

    if request.method == 'POST':
        selected_variant_id = request.POST.get('variant_id')
        selected_variant = product.productvariant_set.get(id=selected_variant_id)
        images = selected_variant.images.all()  # Retrieve the images associated with the newly selected variant

    variants = product.productvariant_set.all()  # Retrieve all variants for the product

    context = {
        'product': product,
        'selected_variant': selected_variant,
        'images': images,
        'variants': variants,
    }
    return render(request, 'product_detail.html', context)


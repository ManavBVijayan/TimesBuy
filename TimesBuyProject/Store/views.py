from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, get_object_or_404
from django.utils.text import slugify
from django.views.decorators.cache import cache_control

from .models import Category, Brand,Product,ProductVariant,ProductImage,Banner,Color
from Cartapp.models import WishListItem
from decimal import Decimal
import math
from decimal import Decimal, ROUND_HALF_UP
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def home(request):
    categories = Category.objects.filter(is_active=True)
    brands = Brand.objects.filter(is_active=True)
    all_banners = Banner.objects.all()
    return render(request, 'home.html', {'categories': categories, 'brands': brands,'all_banners':all_banners})




def shop(request):
    category_id = request.GET.get('category', 'all')
    brand_id = request.GET.get('brand', 'all')

    brands = Brand.objects.filter(is_active=True)
    categories = Category.objects.filter(is_active=True).order_by('name')
    products = Product.objects.filter(category__is_active=True, is_active=True)
    all_variants = ProductVariant.objects.filter(is_active=True, product__in=products)
    distinct_colors = Color.objects.filter(productvariant__in=all_variants).distinct()
    current_category = 'All Products'

    # Price Range Filter Logic
    price_range_filters = {
        '0-2000': (0, 2000),
        '2000-5000': (2000, 5000),
        '5000-15000': (5000, 15000),
        '15000-30000': (15000, 30000),
        '30000': (30000, None),
    }

    selected_price_range = request.GET.get('price_range', None)

    if request.method == 'POST':
        selected_brands = request.POST.getlist('brands[]', [])
        if 'all' in selected_brands:
            selected_brands.remove('all')
        if not selected_brands:
            products = Product.objects.filter(is_active=True)
        else:
            products = Product.objects.filter(category__is_active=True, is_active=True,
                                              brandName__pk__in=selected_brands)

        selected_variants = all_variants.filter(product__in=products)
    else:
        if category_id == 'all':
            current_category = 'All Products'
            products = Product.objects.filter(is_active=True).order_by('name')
        elif category_id:
            current_category = Category.objects.get(id=category_id, is_active=True)
            products = Product.objects.filter(category=current_category, is_active=True)
        else:
            products = Product.objects.filter(category__is_active=True, is_active=True)
            current_category = 'All Products'

        selected_variants = all_variants.filter(product__in=products)

    # Brand Filtering Logic
    if brand_id == 'all':
        selected_brands = []
    else:
        selected_brands = [brand_id]

    if selected_brands:
        selected_variants = selected_variants.filter(product__brandName__pk__in=selected_brands)

    selected_colors = request.GET.getlist('colors[]', [])
    if selected_colors:
        selected_variants = selected_variants.filter(color__pk__in=selected_colors)
    search_query = request.GET.get('search', None)
    if search_query:
        selected_variants = selected_variants.filter(
            Q(product__name__icontains=search_query) |
            Q(product__brandName__name__icontains=search_query) |
            Q(color__color__icontains=search_query)
        )
    if selected_price_range:
        min_price, max_price = price_range_filters.get(selected_price_range, (0, None))
        if max_price is None:
            selected_variants = selected_variants.filter(price__lt=min_price)
        else:
            selected_variants = selected_variants.filter(price__gte=min_price, price__lte=max_price)

    if current_category != 'All Products':
        title = current_category
    elif search_query:
        title = f"Search Results for '{search_query}'"
    else:
        title = "All Products"

    active_offers = {}
    for brand in brands:
        if brand.offer_is_active:
            active_offers[brand.pk] = Decimal(brand.offer_percentage)

    for variant in selected_variants:
        brand_pk = variant.product.brandName.pk
        if brand_pk in active_offers:
            offer_percentage = active_offers[brand_pk]
            offer_price = variant.price - (variant.price * (offer_percentage / 100))
            offer_price = offer_price.to_integral_value(rounding=ROUND_HALF_UP)
            variant.offer_price = '{:.2f}'.format(offer_price)
        else:
            variant.offer_price = None

    paginator = Paginator(selected_variants, 9)
    page_number = request.GET.get('page')
    page_variants = paginator.get_page(page_number)

    context = {
        'products': products,
        'categories': categories,
        'current_category': current_category,
        'brands': brands,
        'page_variants': page_variants,
        'distinct_colors': distinct_colors,
        'category_id': category_id,
        'brand_id': brand_id,
        'selected_colors': selected_colors,
        'title': title,
        'active_offers': active_offers,
        'selected_brands': selected_brands,
        'selected_price_range': selected_price_range,
    }
    return render(request, 'shop.html', context)
def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    selected_variant = product.productvariant_set.first()  # Assuming you want to display the first color variant initially
    images = selected_variant.images.all()  # Retrieve the images associated with the selected variant

    if request.method == 'POST':
        selected_variant_id = request.POST.get('variant_id')
        try:
            selected_variant = product.productvariant_set.get(id=selected_variant_id)
            images = selected_variant.images.all()  # Retrieve the images associated with the newly selected variant
        except ProductVariant.DoesNotExist:
            # Handle the case where the selected variant doesn't exist for the product
            pass

    variants = product.productvariant_set.all()  # Retrieve all variants for the product

    context = {
        'product': product,
        'selected_variant': selected_variant,
        'images': images,
        'variants': variants,
        'is_in_wishlist': WishListItem.objects.filter(wishlist__user=request.user,
                                                      product=selected_variant).exists() if request.user.is_authenticated else False,
    }
    brand = selected_variant.product.brandName
    if brand.offer_is_active:
        offer_percentage = Decimal(brand.offer_percentage)
        offer_price = selected_variant.price * (1 - offer_percentage / 100)
        offer_price=offer_price.to_integral_value(rounding=ROUND_HALF_UP)
        offer_price= '{:.2f}'.format(offer_price)
        context['offer_price'] = offer_price
    return render(request, 'product_detail.html', context)

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDate
from django.http import HttpResponseBadRequest
from django.shortcuts import render, redirect, get_object_or_404
from Authenticate.models import CustomUser
from Store.models import Category,Brand,GenderType,Product,ProductVariant,ProductImage,Color
from orderapp.models import Order,OrderItem
from datetime import timedelta
from django.utils import timezone

def admin_home(request):
    if request.method == 'GET':
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        if not start_date and not end_date:
            # Calculate the current date
            current_date = timezone.now().date()

            # Calculate the date 30 days back from the current date
            default_start_date = current_date - timedelta(days=30)
            default_end_date = current_date

            # Convert to string format (YYYY-MM-DD)
            start_date = default_start_date.strftime('%Y-%m-%d')
            end_date = default_end_date.strftime('%Y-%m-%d')

        if start_date and end_date:
            # Corrected query filter for start_date and end_date using 'date' lookup
            order_count_date = Order.objects.filter(
                Q(order_date__date__gte=start_date, order_date__date__lte=end_date) |
                Q(order_date__date=end_date, order_date__isnull=True)
            ).exclude(payment_status='CANCELLED').count()

            total_price_date = Order.objects.filter(
                Q(order_date__date__gte=start_date, order_date__date__lte=end_date) |
                Q(order_date__date=end_date, order_date__isnull=True)
            ).exclude(payment_status='CANCELLED').aggregate(total=Sum('total_price'))['total']

            daily_totals = Order.objects.filter(
                Q(order_date__date__gte=start_date, order_date__date__lte=end_date) |
                Q(order_date__date=end_date, order_date__isnull=True)
            ).exclude(payment_status='CANCELLED').annotate(date=TruncDate('order_date')).values('date').annotate(
                total=Sum('total_price')).order_by('date')

            order_count = Order.objects.exclude(payment_status='CANCELLED').count()
            total_price = Order.objects.exclude(payment_status='CANCELLED').aggregate(total=Sum('total_price'))['total']
            today = timezone.now().date()
            today_orders = Order.objects.filter(order_date__date=today)
            order_count_today = today_orders.count()
            total_price_today = sum(order.total_price for order in today_orders)
            recent_orders = Order.objects.order_by('-order_date')[:3]

            # Corrected query for top_selling_products using 'product_id' and 'product__name'
            top_selling_products = OrderItem.objects.values('product__product__name').annotate(
                total_quantity=Sum('quantity')
            ).order_by('-total_quantity')[:5]

            categories = Category.objects.all()
            data = []

            for category in categories:
                product_count = Product.objects.filter(category=category).count()
                data.append(product_count)

            context = {
                'order_count_date': order_count_date,
                'total_price_date': total_price_date,
                'start_date': start_date,
                'end_date': end_date,
                'daily_totals': daily_totals,
                'order_count': order_count,
                'total_price': total_price,
                'categories': categories,
                'data': data,
                'order_count_today': order_count_today,
                'total_price_today': total_price_today,
                'recent_orders': recent_orders,
                'top_selling_products': top_selling_products,
            }

            return render(request, 'adminhome.html', context)

        else:
            order_count = Order.objects.exclude(payment_status='CANCELLED').count()
            total_price = Order.objects.exclude(payment_status='CANCELLED').aggregate(total=Sum('total_price'))['total']

            today = timezone.now().date()
            today_orders = Order.objects.filter(order_date__date=today)
            order_count_today = today_orders.count()
            total_price_today = sum(order.total_price for order in today_orders)

            categories = Category.objects.all()
            data = []

            for category in categories:
                product_count = Product.objects.filter(category=category).count()
                data.append(product_count)

            recent_orders = Order.objects.order_by('-order_date')[:3]

            # Corrected query for top_selling_products using 'product_id' and 'product__name'
            top_selling_products = OrderItem.objects.values('product__product__name').annotate(
                total_quantity=Sum('quantity')
            ).order_by('-total_quantity')[:5]

            context = {
                'order_count': order_count,
                'total_price': total_price,
                'start_date': start_date,
                'end_date': end_date,
                'order_count_today': order_count_today,
                'total_price_today': total_price_today,
                'categories': categories,
                'data': data,
                'recent_orders': recent_orders,
                'top_selling_products': top_selling_products,
            }

            return render(request, 'adminhome.html', context)

    return HttpResponseBadRequest("Invalid request method.")

def admin_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        admin = authenticate(username=username, password=password)
        if admin is not None and admin.is_superuser:
            login(request, admin)
            return redirect('admin-home')
        else:
            messages.error(request, "Sorry, you are not an admin.")
            return redirect('admin-login')

    return render(request, 'adminlogin.html')

def admin_logout(request):
    logout(request)
    return redirect('admin-login')

def user_list(request):
    if request.user.is_superuser:
        users =CustomUser.objects.order_by('username')
        context = {
            'users': users
        }
        return render(request, 'userlist.html', context)
def block_user(request,id):

    if request.user.is_superuser:

        user = get_object_or_404(CustomUser, id=id, is_superuser=False)
        user.is_active = False
        user.save()
        return redirect('user-list')
    else:
        return redirect('user-list')

def unblock_user(request,id):
    if request.user.is_superuser:
        user = get_object_or_404(CustomUser, id=id, is_superuser=False)
        user.is_active = True
        user.save()
        return redirect('user-list')
    else:
        return redirect('user-list')
def category_list(request):
    if request.user.is_superuser:
        categories = Category.objects.order_by('name')
        context = {
            'categories':categories
        }
        return render(request,'categorylist.html',context)
def disable_category(request, id):
    if request.user.is_superuser:
        cat = Category.objects.get(id=id)
        cat.is_active = False
        cat.save()
        return redirect('category-list')
def enable_category(request, id):
    if request.user.is_superuser:
        cat = Category.objects.get(id=id)
        cat.is_active = True
        cat.save()
        return redirect('category-list')

def edit_category(request, id):
    if request.user.is_superuser:
        category = get_object_or_404(Category, id=id)

        if request.method == 'POST':
            category_name = request.POST['name']
            image = request.FILES.get('image')

            category.name = category_name
            if image:
                category.image = image

            category.save()

            return redirect('category-list')

        return render(request, 'editcategory.html', {'category': category})
    else:
        return redirect('category-list')


def add_category(request):
    if request.user.is_superuser:
        if request.method == "POST":
            category_name = request.POST['name']
            image = request.FILES.get('image')

            new_category =Category.objects.create(name=category_name,image=image)
            new_category.save()

            return redirect('category-list')
        else:
            return render(request, 'addcategory.html')
    else:
        return redirect('category-list')


def product_list(request):
    if request.user.is_superuser:
        products = Product.objects.order_by('name')
        context = {'products': products}
        return render(request, 'productlist.html', context)


def disable_product(request, product_id):
    if request.user.is_superuser:
        product = Product.objects.get(id=product_id)
        product.is_active = False
        product.save()
    return redirect('product-list')

def enable_product(request, product_id):
    if request.user.is_superuser:
        product = Product.objects.get(id=product_id)
        product.is_active = True
        product.save()
    return redirect('product-list')


def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    categories = Category.objects.all()
    brands = Brand.objects.all()
    genders = GenderType.objects.all()

    if request.method == 'POST':
        product.name = request.POST.get('name')
        product.description = request.POST.get('description')
        category_id = request.POST.get('category')
        brand_id = request.POST.get('brand')
        gender_id = request.POST.get('gender')

        # Print the brand ID to debug
        print("Selected brand ID:", brand_id)

        product.category = get_object_or_404(Category, id=category_id)
        product.brandName = get_object_or_404(Brand, id=brand_id)
        product.gender = get_object_or_404(GenderType, id=gender_id)
        # Update other fields as needed
        product.save()
        return redirect('product-list')

    context = {'product': product, 'categories': categories, 'brands': brands, 'genders': genders}
    return render(request, 'editproduct.html', context)


def add_product(request):
    if request.method == 'POST':
        # Get form input values
        name = request.POST.get('name')
        description = request.POST.get('description')
        category_id = request.POST.get('category')
        brand_id = request.POST.get('brand')
        gender_id = request.POST.get('gender')
        images = request.FILES.getlist('images')
        model_name = request.POST.get('model_name')
        model_number = request.POST.get('model_number')
        dial_shape = request.POST.get('dial_shape')
        water_proof = bool(request.POST.get('water_proof'))
        touch_screen = bool(request.POST.get('touch_screen'))
        price = request.POST.get('price')
        stock = request.POST.get('stock')
        color_id = request.POST.get('color')  # Assuming color input field name is 'color'

        # Create the product object
        product = Product.objects.create(
            name=name,
            description=description,
            category_id=category_id,
            brandName_id=brand_id,
            gender_id=gender_id
        )

        # Create the product variant with color and associate it with the product
        variant = ProductVariant.objects.create(
            product=product,
            model_name=model_name,
            model_number=model_number,
            dial_shape=dial_shape,
            water_proof=water_proof,
            touch_screen=touch_screen,
            price=price,
            stock=stock,
            color_id=color_id  # Assign the selected color to the variant
        )

        # Create and associate the images with the variant
        for image in images:
            ProductImage.objects.create(variant=variant, image=image)

        return redirect('product-list')  # Replace 'product-list' with the appropriate URL name for your product list view

    # Fetch brands, categories, genders, and colors for the form
    brands = Brand.objects.all()
    categories = Category.objects.all()
    genders = GenderType.objects.all()
    colors = Color.objects.all()

    context = {
        'brands': brands,
        'categories': categories,
        'genders': genders,
        'colors': colors
    }
    return render(request, 'addproduct.html', context)


def product_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    variants = product.productvariant_set.all().order_by('model_name')
    context = {
        'product': product,
        'variants': variants,
    }
    return render(request, 'productview.html', context)

def enable_variant(request, product_id, variant_id):
    if request.user.is_superuser:
        variant = get_object_or_404(ProductVariant, id=variant_id)
        variant.is_active = True
        variant.save()
        return redirect('product-view', product_id=product_id)

def disable_variant(request, product_id, variant_id):
    if request.user.is_superuser:
        variant = get_object_or_404(ProductVariant, id=variant_id)
        variant.is_active = False
        variant.save()
        return redirect('product-view',product_id=product_id)


def add_variant(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        # Process the form data and create a new variant
        model_name = request.POST['model_name']
        model_number = request.POST['model_number']
        dial_shape = request.POST['dial_shape']
        water_proof = request.POST.get('water_proof', False) == 'on'  # Convert to boolean
        touch_screen = request.POST.get('touch_screen', False) == 'on'  # Convert to boolean
        color_id = request.POST['color']
        price = request.POST['price']
        stock = request.POST['stock']

        color = get_object_or_404(Color, id=color_id)

        variant = ProductVariant.objects.create(
            product=product,
            model_name=model_name,
            model_number=model_number,
            dial_shape=dial_shape,
            water_proof=water_proof,
            touch_screen=touch_screen,
            color=color,
            price=price,
            stock=stock
        )

        # Handle multiple images upload
        images = request.FILES.getlist('images')
        for image in images:
            ProductImage.objects.create(variant=variant, image=image)

        return redirect('product-view', product_id=product_id)

    context = {
        'product': product,
        'colors': Color.objects.all()
    }
    return render(request, 'addvariant.html', context)


def edit_variant(request, product_id, variant_id):
    product = get_object_or_404(Product, id=product_id)
    variant = get_object_or_404(ProductVariant, id=variant_id)

    if request.method == 'POST':
        # Process the form data and update the variant
        # Retrieve the updated values from the form
        model_name = request.POST['model_name']
        model_number = request.POST['model_number']
        dial_shape = request.POST['dial_shape']
        water_proof = request.POST.get('water_proof', False) == 'on'  # Convert to boolean
        touch_screen = request.POST.get('touch_screen', False) == 'on'  # Convert to boolean
        color_id = request.POST['color']
        price = request.POST['price']
        stock = request.POST['stock']

        color = get_object_or_404(Color, id=color_id)

        # Update the variant with the new values
        variant.model_name = model_name
        variant.model_number = model_number
        variant.dial_shape = dial_shape
        variant.water_proof = water_proof
        variant.touch_screen = touch_screen
        variant.color = color
        variant.price = price
        variant.stock = stock
        variant.save()

        # Handle multiple images upload (if required)
        images = request.FILES.getlist('images')
        if images:
            # New images are selected, remove existing images
            variant.images.all().delete()

            # Add the new images
            for image in images:
                ProductImage.objects.create(variant=variant, image=image)

        return redirect('product-view', product_id=product_id)

    context = {
        'product': product,
        'variant': variant,
        'colors': Color.objects.all()
    }
    return render(request, 'editvariant.html', context)


def admin_orders(request):
    if request.user.is_authenticated and request.user.is_superuser:
        orders = Order.objects.order_by('-id')
        return render(request, 'allorder.html', {'orders': orders})
    else:
        return render(request, 'home.html')




def admin_order_view(request, order_id):
    if request.user.is_superuser:
        view_order = get_object_or_404(Order, id=order_id)
        order = OrderItem.objects.filter(order=view_order)

        context = {
            'order': order,
            'view_order': view_order,
        }
        return render(request, 'adminorderview.html', context)
    else:
        return render(request, 'home.html')

def order_shipped(request, order_id):
    if request.user.is_superuser:
        order = get_object_or_404(Order, id=order_id)
        order.payment_status = 'SHIPPED'
        order.save()
        return redirect('admin_orders')
    else:
        return render(request, 'home.html')

def order_delivered(request, order_id):
    if request.user.is_superuser:
        order = get_object_or_404(Order, id=order_id)

        # Make sure the order is in the 'SHIPPED' status before marking it as 'DELIVERED'
        if order.payment_status == 'SHIPPED':
            order.payment_status = 'DELIVERED'
            order.save()

    return redirect('admin_orders')

def admin_order_cancel(request, order_id):
    if request.user.is_superuser:
        order = get_object_or_404(Order, id=order_id)
        if order.payment_status != 'DELIVERED' and order.payment_status != 'RETURNED':
            order_items = OrderItem.objects.filter(order=order)
            for item in order_items:
                variant = item.product
                variant.stock += item.quantity
                variant.save()
            order.payment_status = 'CANCELLED'
            order.save()

        return redirect('admin_orders')

    else:
        return render(request, 'home.html')
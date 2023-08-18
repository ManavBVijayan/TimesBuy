from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDate
from django.http import HttpResponseBadRequest, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from Authenticate.models import CustomUser
from Store.models import Category,Brand,GenderType,Product,ProductVariant,ProductImage,Color,Banner
from django.template.loader import render_to_string
from orderapp.models import Order,OrderItem
from datetime import timedelta
from django.utils import timezone
from django.db import IntegrityError
from Userprofileapp.models import UserAddress,Wallet,WalletTransaction
from decimal import Decimal
from xhtml2pdf import pisa

def admin_home(request):
    if request.method == 'GET':
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        if not start_date and not end_date:
            current_date = timezone.now().date()
            default_start_date = current_date - timedelta(days=30)
            default_end_date = current_date
            start_date = default_start_date.strftime('%Y-%m-%d')
            end_date = default_end_date.strftime('%Y-%m-%d')

        if start_date and end_date:
            order_count_date = Order.objects.filter(
                Q(order_date__date__gte=start_date, order_date__date__lte=end_date) |
                Q(order_date__date=end_date, order_date__isnull=True)
            ).exclude(
                Q(payment_status='Refunded') |
                Q(payment_status='Pending') |
                Q(payment_status='No payment')
            ).count()

            total_price_date = Order.objects.filter(
                Q(order_date__date__gte=start_date, order_date__date__lte=end_date) |
                Q(order_date__date=end_date, order_date__isnull=True)
            ).exclude(
                Q(payment_status='Refunded') |
                Q(payment_status='Pending') |
                Q(payment_status='No payment')
            ).aggregate(total=Sum('total_price'))['total']

            daily_totals = Order.objects.filter(
                Q(order_date__date__gte=start_date, order_date__date__lte=end_date) |
                Q(order_date__date=end_date, order_date__isnull=True)
            ).exclude(
                Q(payment_status='Refunded') |
                Q(payment_status='Pending') |
                Q(payment_status='No payment')
            ).annotate(date=TruncDate('order_date')).values('date').annotate(
                total=Sum('total_price')).order_by('date')

            order_count = Order.objects.exclude(
                Q(payment_status='Refunded') |
                Q(payment_status='No payment')
            ).count()

            total_price = Order.objects.exclude(
                Q(payment_status='Refunded') |
                Q(payment_status='No payment')
            ).aggregate(total=Sum('total_price'))['total']

            today = timezone.now().date()
            today_orders = Order.objects.filter(order_date__date=today)
            order_count_today = today_orders.count()
            total_price_today = sum(order.total_price for order in today_orders)

            recent_orders = Order.objects.order_by('-order_date')[:3]

            top_selling_products = OrderItem.objects.values('product__product__name').annotate(
                total_quantity=Sum('quantity')
            ).order_by('-total_quantity')[:5]

            cancelled_products = OrderItem.objects.filter(
                order__payment_status__in=['Cancelled', 'Refunded']
            ).aggregate(total_cancelled=Sum('quantity'))['total_cancelled']

            returned_products = OrderItem.objects.filter(
                order__payment_status='RETURNED'
            ).aggregate(total_returned=Sum('quantity'))['total_returned']

            categories = Category.objects.all()  # Make sure to replace Category with your actual category model

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
                'order_count_today': order_count_today,
                'total_price_today': total_price_today,
                'recent_orders': recent_orders,
                'top_selling_products': top_selling_products,
                'cancelled_products': cancelled_products,
                'returned_products': returned_products,
                'categories': categories,
                'data': data,
            }
            return render(request, 'adminhome.html', context)
        else:
            order_count = Order.objects.exclude(
                Q(payment_status='Refunded') |
                Q(payment_status='No payment')).count()
            total_price = Order.objects.exclude(
                Q(payment_status='Refunded') |
                Q(payment_status='No payment')
            ).aggregate(total=Sum('total_price'))['total']
            today = timezone.now().date()
            today_orders = Order.objects.filter(order_date__date=today)
            order_count_today = today_orders.count()
            total_price_today = sum(order.total_price for order in today_orders)
            cancelled_products = OrderItem.objects.filter(
                order__payment_status__in=['Cancelled', 'Refunded']
            ).aggregate(total_cancelled=Sum('quantity'))['total_cancelled']
            returned_products = OrderItem.objects.filter(
                order__payment_status='RETURNED'
            ).aggregate(total_returned=Sum('quantity'))['total_returned']
            categories = Category.objects.all()  # Make sure to replace Category with your actual category model
            data = []

            for category in categories:
                product_count = Product.objects.filter(category=category).count()
                data.append(product_count)

            recent_orders = Order.objects.order_by('-order_date')[:3]
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
                'cancelled_products': cancelled_products,
                'returned_products': returned_products,
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
            color_id=color_id
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
        try:
            for image in images:
                ProductImage.objects.create(variant=variant, image=image)
        except IntegrityError as e:
            print(f"Error saving images: {e}")

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

        # Configure the number of orders per page
        paginator = Paginator(orders, 10)  # 10 orders per page

        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context = {'page_obj': page_obj}
        return render(request, 'allorder.html', context)
    else:
        return render(request, 'home.html')




def admin_order_view(request, order_id):
    if request.user.is_superuser:
        view_order = get_object_or_404(Order, id=order_id)
        order = OrderItem.objects.filter(order=view_order)
        expected_delivery_date = view_order.order_date + timedelta(days=3)

        context = {
            'order': order,
            'view_order': view_order,
            'expected_delivery_date':expected_delivery_date
        }
        return render(request, 'adminorderview.html', context)
    else:
        return render(request, 'home.html')

def order_shipped(request, order_id):
    if request.user.is_superuser:
        order = get_object_or_404(Order, id=order_id)
        order.order_status = 'Shipped'
        order.shipping_date=timezone.now()
        order.save()
        return redirect(request.META.get('HTTP_REFERER'))
    else:
        return render(request, 'home.html')

def order_delivered(request, order_id):
    if request.user.is_superuser:
        order = get_object_or_404(Order, id=order_id)

        # Make sure the order is in the 'SHIPPED' status before marking it as 'DELIVERED'
        if order.order_status == 'Shipped':
            order.order_status = 'Delivered'
            order.delivery_date=timezone.now()
            order.return_period_expired=timezone.now()+timezone.timedelta(days=5)
            if order.payment_status=='Pending':
                order.payment_status='Paid'
            order.save()

    return redirect(request.META.get('HTTP_REFERER'))

def admin_order_cancel(request, order_id):
    if request.user.is_superuser:
        order = get_object_or_404(Order, id=order_id)
        user = order.user
        if order.order_status != 'Delivered' and order.order_status != 'Returned'and order.order_status !='Cancelled' and order.order_status != 'Requested for return ':
            order_items = OrderItem.objects.filter(order=order)
            for item in order_items:
                variant = item.product
                variant.stock += item.quantity
                variant.save()
            if order.payment_method in ['Net banking', 'Wallet pay']:
                user_wallet = Wallet.objects.get(user=user)
                # Refund the amount to the user's wallet
                refund_amount = order.total_price  # Assuming you want to refund the full amount
                user_wallet.balance += Decimal(refund_amount)
                user_wallet.save()
                transaction_type = 'Cancelled'
                WalletTransaction.objects.create(
                    wallet=user_wallet,
                    amount=refund_amount,
                    order_id=order,
                    transaction_type=transaction_type,
                )
            if order.payment_status=='Pending':
                order.payment_status='No payment'
            else:
                order.payment_status='Refunded'
            order.order_status='Cancelled'
            Order.cancelled_date=timezone.now()
            order.save()

        return redirect(request.META.get('HTTP_REFERER'))

    else:
        return render(request, 'home.html')

def return_orders(request, order_id):
    if request.user.is_superuser:
        order = get_object_or_404(Order, id=order_id)
        user = order.user
        user_wallet, created = Wallet.objects.get_or_create(user=user)
        refund_amount = order.total_price  # Assuming you want to refund the full amount
        user_wallet.balance += Decimal(refund_amount)
        user_wallet.save()
        transaction_type = 'Return'
        WalletTransaction.objects.create(
            wallet=user_wallet,
            amount=refund_amount,
            order_id=order,
            transaction_type=transaction_type,
        )
        if order.order_status != 'Cancelled':
            order.payment_status = 'Refunded'
            order.order_status = 'Returned'
            order.returned_date=timezone.now()
            order.save()

        return redirect(request.META.get('HTTP_REFERER'))


def sales_view(request):
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    today_orders = Order.objects.filter(order_date__date=today, payment_status='Paid').exclude(order_status__in=['Returned', 'Cancelled'])
    order_count_today = today_orders.count()
    total_price_today = today_orders.aggregate(Sum('total_price'))['total_price__sum'] or 0

    week_orders = Order.objects.filter(order_date__range=[week_ago, today], payment_status='Paid').exclude(order_status__in=['Returned', 'Cancelled'])
    order_count_week = week_orders.count()
    total_price_week = week_orders.aggregate(Sum('total_price'))['total_price__sum'] or 0

    month_orders = Order.objects.filter(order_date__range=[month_ago, today], payment_status='Paid').exclude(order_status__in=['Returned', 'Cancelled'])
    order_count_month = month_orders.count()
    total_price_month = month_orders.aggregate(Sum('total_price'))['total_price__sum'] or 0

    top_selling_variants_today = OrderItem.objects.filter(order__in=today_orders).values(
        'product__model_name', 'product__color__color').annotate(total_quantity=Sum('quantity')).order_by(
        '-total_quantity')[:5]
    top_selling_variants_week = OrderItem.objects.filter(order__in=week_orders).values(
        'product__model_name', 'product__color__color').annotate(total_quantity=Sum('quantity')).order_by(
        '-total_quantity')[:5]
    top_selling_variants_month = OrderItem.objects.filter(order__in=month_orders).values(
        'product__model_name', 'product__color__color').annotate(total_quantity=Sum('quantity')).order_by(
        '-total_quantity')[:5]

    context = {
        'order_count_today': order_count_today,
        'total_price_today': total_price_today,
        'order_count_week': order_count_week,
        'total_price_week': total_price_week,
        'order_count_month': order_count_month,
        'total_price_month': total_price_month,
        'top_selling_variants_today': top_selling_variants_today,
        'top_selling_variants_week': top_selling_variants_week,
        'top_selling_variants_month': top_selling_variants_month,
    }

    return render(request, 'sales_view.html', context)

def generate_pdf(request):
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    today_orders = Order.objects.filter(order_date__date=today, payment_status='Paid').exclude(
        order_status__in=['Returned', 'Cancelled'])
    order_count_today = today_orders.count()
    total_price_today = today_orders.aggregate(Sum('total_price'))['total_price__sum'] or 0

    week_orders = Order.objects.filter(order_date__range=[week_ago, today], payment_status='Paid').exclude(
        order_status__in=['Returned', 'Cancelled'])
    order_count_week = week_orders.count()
    total_price_week = week_orders.aggregate(Sum('total_price'))['total_price__sum'] or 0

    month_orders = Order.objects.filter(order_date__range=[month_ago, today], payment_status='Paid').exclude(
        order_status__in=['Returned', 'Cancelled'])
    order_count_month = month_orders.count()
    total_price_month = month_orders.aggregate(Sum('total_price'))['total_price__sum'] or 0

    top_selling_variants_today = OrderItem.objects.filter(order__in=today_orders).values(
        'product__model_name', 'product__color__color').annotate(total_quantity=Sum('quantity')).order_by(
        '-total_quantity')[:5]
    top_selling_variants_week = OrderItem.objects.filter(order__in=week_orders).values(
        'product__model_name', 'product__color__color').annotate(total_quantity=Sum('quantity')).order_by(
        '-total_quantity')[:5]
    top_selling_variants_month = OrderItem.objects.filter(order__in=month_orders).values(
        'product__model_name', 'product__color__color').annotate(total_quantity=Sum('quantity')).order_by(
        '-total_quantity')[:5]

    context = {
        'order_count_today': order_count_today,
        'total_price_today': total_price_today,
        'order_count_week': order_count_week,
        'total_price_week': total_price_week,
        'order_count_month': order_count_month,
        'total_price_month': total_price_month,
        'top_selling_variants_today': top_selling_variants_today,
        'top_selling_variants_week': top_selling_variants_week,
        'top_selling_variants_month': top_selling_variants_month,
    }

    template = 'sales_report_pdf.html'
    html_string = render_to_string(template, context)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'filename="sales_report.pdf"'

    pisa_status = pisa.CreatePDF(html_string, dest=response)

    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html_string + '</pre>')
    return response
def list_all_brands(request):
    order_by = request.GET.get('order_by', 'name')
    all_brands = Brand.objects.all().order_by(order_by)
    context = {
        'brands': all_brands,
    }
    return render(request, 'brand_list.html', context)
def enable_brand(request, brand_id):
    brand = get_object_or_404(Brand, id=brand_id)
    brand.is_active = True
    brand.save()
    return redirect('list-all-brands')  # Redirect to the list of all brands

# View to disable a brand
def disable_brand(request, brand_id):
    brand = get_object_or_404(Brand, id=brand_id)
    brand.is_active = False
    brand.save()
    return redirect('list-all-brands')


def add_brand(request):
    if request.method == 'POST':
        name = request.POST['name']
        image = request.FILES['image']
        is_active = bool(request.POST.get('is_active', False))
        offer_title = request.POST.get('offer_title')
        offer_percentage_str = request.POST.get('offer_percentage', '')
        if offer_percentage_str.isdigit():
            offer_percentage = int(offer_percentage_str)
        else:
            offer_percentage = 0

        offer_is_active = bool(request.POST.get('offer_is_active', False))

        brand = Brand.objects.create(
            name=name,
            image=image,
            is_active=is_active,
            offer_title=offer_title,
            offer_percentage=offer_percentage,
            offer_is_active=offer_is_active,
        )

        return redirect('list-all-brands')  # Redirect to the list of all brands

    return render(request, 'add_brand.html')
def edit_brand(request, brand_id):
    brand = get_object_or_404(Brand, id=brand_id)

    if request.method == 'POST':
        brand.name = request.POST['name']
        brand.image = request.FILES.get('image', brand.image)
        brand.is_active = bool(request.POST.get('is_active', False))
        brand.offer_title = request.POST.get('offer_title')
        brand.offer_percentage = int(request.POST.get('offer_percentage', 0))
        brand.offer_is_active = bool(request.POST.get('offer_is_active', False))
        brand.save()

        return redirect('list-all-brands')  # Redirect to the list of all brands

    context = {
        'brand': brand,
    }
    return render(request, 'edit_brand.html', context)


def add_banner(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        image = request.FILES.get('image')
        brand_id = request.POST.get('brand')

        banner = Banner(name=name, image=image, brand_id=brand_id)
        banner.save()

        return redirect('list-banners')

    active_brands = Brand.objects.filter(is_active=True)
    return render(request, 'add_banner.html', {'active_brands': active_brands})

def list_banners(request):
    banners = Banner.objects.all()
    return render(request, 'list_banner.html', {'banners': banners})


def edit_banner(request, banner_id):
    banner = get_object_or_404(Banner, pk=banner_id)

    if request.method == 'POST':
        banner.name = request.POST.get('name')
        image = request.FILES.get('image')
        if image:
            banner.image = image
        banner.brand_id = request.POST.get('brand')
        banner.save()
        return redirect('list-banners')

    active_brands = Brand.objects.filter(is_active=True)
    return render(request, 'edit_banner.html', {'banner': banner, 'active_brands': active_brands})
def delete_banner(request, banner_id):
    banner = get_object_or_404(Banner, pk=banner_id)
    banner.delete()
    return redirect('list-banners')

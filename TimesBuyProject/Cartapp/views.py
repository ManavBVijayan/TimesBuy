from decimal import Decimal
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.db.models import F, Sum, Q
from django.shortcuts import HttpResponseRedirect, get_object_or_404, render, redirect
from django.urls import reverse
from django.views.decorators.cache import cache_control
from .models import Cart, CartItem
from Store.models import ProductVariant,Product
from Userprofileapp.models import UserAddress,Wallet
from .models import WishList, WishListItem,Coupon
from django.core.paginator import Paginator
from django.utils import timezone
from django.utils.timezone import make_aware
from django.db import IntegrityError



def add_to_cart(request, variant_id):
    variant = get_object_or_404(ProductVariant, id=variant_id)
    user = request.user

    if user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user_id=user)
    else:
        cart_id = request.session.get('cart_id')
        if cart_id:
            cart = Cart.objects.get(id=cart_id)
        else:
            cart = Cart.objects.create()

    item = cart.cartitem_set.filter(product=variant).first()

    if item:
        available_stock = variant.stock - item.quantity
        requested_quantity = 1
        if requested_quantity <= available_stock:
            item.quantity += requested_quantity
            item.save()
            messages.success(request, 'Item added to cart.')
        else:
            messages.error(request, 'Requested quantity exceeds available stock.')
    else:
        if variant.product.brandName and variant.product.brandName.offer_is_active:  # Check if the brand's offer is active
            offer_percentage = Decimal(variant.product.brandName.offer_percentage)
            offer_price = variant.price * (1 - offer_percentage / 100)
            if 1 <= variant.stock:
                CartItem.objects.create(cart=cart, product=variant, quantity=1, price=offer_price)
                messages.success(request, 'Item added to cart.')
            else:
                messages.error(request, 'Requested quantity exceeds available stock.')
        else:
            if 1 <= variant.stock:
                CartItem.objects.create(cart=cart, product=variant, quantity=1, price=variant.price)
                messages.success(request, 'Item added to cart.')
            else:
                messages.error(request, 'Requested quantity exceeds available stock.')

    if not user.is_authenticated:
        request.session['cart_id'] = cart.id

    return HttpResponseRedirect(request.META['HTTP_REFERER'])

@cache_control(no_cache=True,must_revalidate=True,no_store=True)
def view_cart(request):
    user = request.user

    if user.is_authenticated:
        cart = Cart.objects.get(user_id=user)
    else:
        cart_id = request.session.get('cart_id')
        if cart_id:
            cart = Cart.objects.get(id=cart_id)
        else:
            cart = Cart.objects.create()
            request.session['cart_id'] = cart.id

    cart_items = cart.cartitem_set.annotate(subtotal=F('quantity') * F('price'))
    subtotal = cart_items.aggregate(subtotal_price=Sum('subtotal'))['subtotal_price'] or Decimal('0.00')
    total_item_count = cart_items.aggregate(total_count=Sum('quantity'))['total_count'] or 0


    Q1 = Q(single_use_per_user=False)
    Q2 = (~Q(single_use_per_user=True) | ~Q(order__user=request.user)) if request.user.is_authenticated else Q()
    Q3 = Q(is_active=True) & Q(valid_from__lte=timezone.now()) & (Q(valid_to__gte=timezone.now()) | Q(valid_to__isnull=True)) & (Q(minimum_order_amount__isnull=True) | Q(minimum_order_amount__lte=subtotal))
    Q4 = Q(quantity__gte=1)
    valid_coupons = Coupon.objects.filter(Q1 | Q2, Q3, Q4)

    # Get the applied coupon from the session or set a default value
    applied_coupon = request.session.get('applied_coupon', {
        'id': None,
        'code': None,
        'discount': '0.00',
    })

    discount_price = Decimal(applied_coupon.get('discount', '0.00'))
    total_price = subtotal - discount_price if discount_price <= subtotal else Decimal('0.00')

    page_number = request.GET.get('page')
    items_per_page = 7
    paginator = Paginator(cart.cartitem_set.all(), items_per_page)
    cart_items = paginator.get_page(page_number)
    context = {
        'cart': cart,
        'subtotal': subtotal,
        'discount_amount': discount_price,
        'total_price': total_price,
        'cart_items': cart_items,
        'valid_coupons': valid_coupons,
        'applied_coupon': applied_coupon,
        'total_item_count':total_item_count,
    }

    return render(request, 'cart.html', context)
def remove_from_cart(request):
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        cart_item = CartItem.objects.get(id=item_id)
        cart_item.delete()

        messages.success(request, 'Item removed from cart.')
        page_number = request.GET.get('page', 1)

        # Create a new QueryDict to preserve other query parameters
        query_dict = QueryDict(mutable=True)
        query_dict.update({'page': page_number})

        # Construct the URL using reverse and append the query string
        url = reverse('view_cart') + '?' + query_dict.urlencode()

        return redirect(url)

    return render(request, 'cart_view.html')


from django.http import JsonResponse, QueryDict


def update_quantity(request):
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        quantity = int(request.POST.get('quantity'))

        cart_item = CartItem.objects.get(id=item_id)
        variant = cart_item.product
        available_stock = variant.stock - cart_item.quantity

        if quantity <= 0:
            messages.error(request, 'Quantity must be greater than zero.')
        elif quantity <= available_stock + cart_item.quantity:
            cart_item.quantity = quantity
            cart_item.save()

            # Update the quantity in the session for non-authenticated users
            if not request.user.is_authenticated:
                cart_session = request.session.get('cart', {})
                cart_session[item_id] = quantity
                request.session['cart'] = cart_session

            # Check if the cart's subtotal meets the minimum requirement for the applied coupon (if any)
            cart = Cart.objects.get_or_create(user_id=request.user)[0] if request.user.is_authenticated else None
            if cart:
                cart_items = cart.cartitem_set.annotate(subtotal=F('quantity') * F('product__price'))
                subtotal = cart_items.aggregate(subtotal_price=Sum('subtotal'))['subtotal_price'] or 0

                applied_coupon = request.session.get('applied_coupon', None)

                if applied_coupon:
                    coupon_id = applied_coupon.get('id', None)
                    coupon = Coupon.objects.filter(id=coupon_id, is_active=True).first()

                    if coupon and coupon.minimum_order_amount is not None and subtotal < coupon.minimum_order_amount:
                        # Remove the applied coupon from the session
                        request.session.pop('applied_coupon', None)
                        messages.warning(request, "The applied coupon's criteria no longer met. Coupon removed.")
                    elif coupon and coupon.discount > subtotal:
                        # Remove the applied coupon from the session
                        request.session.pop('applied_coupon', None)
                        messages.warning(request, "The applied coupon's discount is greater than the order subtotal. Coupon removed.")

            return JsonResponse({'success': True, 'stock': variant.stock})

        else:
            messages.error(request, 'Requested quantity exceeds available stock.')

    return JsonResponse({'success': False})

@login_required(login_url='custom_login')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def checkout(request):
    user = request.user
    cart = Cart.objects.get(user_id=user)
    cart_items = cart.cartitem_set.all()
    user_wallet = Wallet.objects.get(user=request.user)
    if not cart_items:
        return redirect('shop')

    # Check if any address is selected as the delivery address
    selected_address = UserAddress.objects.filter(user=user, is_delivery_address=True).first()
    if not selected_address:
        messages.error(request, "Please select a delivery address.")
        return redirect('add_address')

    out_of_stock_products = [f"{item.product.product.name} - {item.product.color}" for item in cart_items if
                             item.product.stock <= 0]
    if out_of_stock_products:
        error_message = ", ".join(out_of_stock_products) + " is/are out of stock. Please remove them from your cart."
        messages.error(request, error_message)
        return redirect('view_cart')

    subtotal = cart_items.aggregate(subtotal=Sum(F('quantity') * F('product__price')))['subtotal'] or Decimal('0.00')
    shipping_charge = Decimal('50') if subtotal < Decimal('1000') else Decimal('0.00')

    applied_coupon = request.session.get('applied_coupon', {'discount': '0.00'})
    discount_amount = Decimal(applied_coupon.get('discount', '0.00'))

    # Calculate the total_price directly without using the session
    total_price = subtotal + shipping_charge - discount_amount

    addresses = UserAddress.objects.filter(user=user)

    context = {
        'cart': cart,
        'subtotal': subtotal,
        'shipping_charge': shipping_charge,
        'discount_amount': discount_amount,
        'total_price': total_price,
        'cart_items': cart_items,
        'addresses': addresses,
        'selected_address': selected_address,
        'wallet_amount': user_wallet.balance,
    }

    return render(request, 'checkout.html', context)


def apply_coupon(request):
    if request.method == 'POST':
        coupon_id = request.POST.get('coupon_id')
        try:
            coupon_id = int(coupon_id)
            coupon = get_object_or_404(Coupon, id=coupon_id)
            discount = coupon.discount
            request.session['applied_coupon'] = {
                'id': coupon.id,
                'code': coupon.code,
                'discount': discount,
            }

            cart = Cart.objects.get(user_id=request.user)
            cart_items = cart.cartitem_set.annotate(subtotal=F('quantity') * F('product__price'))
            subtotal = cart_items.aggregate(subtotal_price=Sum('subtotal'))['subtotal_price'] or Decimal('0.00')
            shipping_charge = Decimal('50') if subtotal < Decimal('1000') else Decimal('0.00')
            discount_amount = Decimal(discount)
            total_price = subtotal + shipping_charge - discount_amount

            if total_price < coupon.minimum_order_amount:
                request.session.pop('applied_coupon', None)
                messages.warning(request, f"The coupon '{coupon.code}' requires a minimum total of '{coupon.discount}'. Coupon removed.")
            else:
                messages.success(request, f"Coupon '{coupon.code}' applied successfully!")

        except (ValueError, TypeError, Coupon.DoesNotExist):
            # Remove the applied coupon from the session
            request.session.pop('applied_coupon', None)
            messages.error(request, "Invalid coupon. Coupon not applied.")

    return redirect('view_cart')

def custom_login_view(request):
    if 'username' in request.session:
        return redirect('home')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            request.session['username'] = username
            login(request, user)
            guest_cart_id = request.session.get('cart_id')
            if guest_cart_id:
                try:
                    guest_cart = Cart.objects.get(id=guest_cart_id)
                    user_cart, created = Cart.objects.get_or_create(user_id=user)

                    for guest_item in guest_cart.cartitem_set.all():
                        try:
                            user_item = CartItem.objects.get(cart=user_cart, product=guest_item.product)
                            available_stock = guest_item.product.stock - user_item.quantity
                            if guest_item.quantity <= available_stock:
                                user_item.quantity += guest_item.quantity
                                user_item.save()
                            else:
                                # Display an error message if the requested quantity exceeds the available stock
                                messages.error(request, f"Requested quantity for '{guest_item.product}' exceeds available stock.")
                        except CartItem.DoesNotExist:
                            # If the item is not in the cart, create a new cart item
                            CartItem.objects.create(
                                cart=user_cart,
                                product=guest_item.product,
                                quantity=guest_item.quantity,
                                price=guest_item.product.price
                            )

                    # Delete the guest cart after merging
                    guest_cart.delete()
                    # Clear the cart_id from the session since the guest cart is no longer needed
                    del request.session['cart_id']

                except Cart.DoesNotExist:
                    # Handle the case when the guest cart does not exist or is already deleted
                    pass

            return redirect('view_cart')

        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'guest_login.html')


@login_required
def add_to_wishlist(request, variant_id):
    if request.method == 'POST' and request.user.is_authenticated:
        variant = get_object_or_404(ProductVariant, id=variant_id)
        wishlist, created = WishList.objects.get_or_create(user=request.user)
        WishListItem.objects.get_or_create(wishlist=wishlist, product=variant)
        messages.success(request, 'Item added to wishlist.')
    return redirect('product_detail', slug=variant.product.slug)

def remove_from_wishlist(request, variant_id):
    if request.method == 'POST' and request.user.is_authenticated:
        variant = get_object_or_404(ProductVariant, id=variant_id)
        try:
            wishlist = WishList.objects.get(user=request.user)
            wishlist_item = WishListItem.objects.get(wishlist=wishlist, product=variant)
            wishlist_item.delete()
            messages.error(request, 'Item removed from wishlist')
        except WishList.DoesNotExist:
            pass
    return redirect('product_detail', slug=variant.product.slug)

def wishlist_view(request):
    if request.user.is_authenticated:
        wishlist = WishList.objects.filter(user=request.user).first()
        if wishlist:
            wishlist_items = wishlist.wishlistitem_set.all()
        else:
            wishlist_items = []

        # Fetch the cart items for the current user
        cart_items = CartItem.objects.filter(cart__user_id=request.user.id)

        # Extract the product IDs of the cart items
        cart_product_ids = [item.product.id for item in cart_items]

        # Implement pagination for wishlist items
        paginator = Paginator(wishlist_items, per_page=4)
        page_number = request.GET.get('page')
        wishlist_items_paginated = paginator.get_page(page_number)
    else:
        wishlist_items_paginated = []
        cart_product_ids = []

    context = {
        'wishlist_items': wishlist_items_paginated,
        'cart_product_ids': cart_product_ids,
    }
    return render(request, 'wishlist.html', context)


def remove_wishlist(request, wishlist_item_id):
    wishlist_item = get_object_or_404(WishListItem, id=wishlist_item_id)

    # Check if the wishlist item belongs to the current user
    if request.user == wishlist_item.wishlist.user:
        wishlist_item.delete()
        messages.error(request, 'Item removed from wishlist')
    page_number = request.GET.get('page', 1)

    # Create a new QueryDict to preserve other query parameters
    query_dict = QueryDict(mutable=True)
    query_dict.update({'page': page_number})

    # Construct the URL using reverse and append the query string
    url = reverse('wishlist') + '?' + query_dict.urlencode()

    return redirect(url)

def add_coupon(request):
    if request.method == 'POST':
        code = request.POST.get('code').upper()
        discount = request.POST.get('discount')
        valid_from = request.POST.get('valid_from')
        valid_to = request.POST.get('valid_to')
        minimum_order_amount = request.POST.get('minimum_order_amount')
        is_active = 'is_active' in request.POST
        single_use_per_user = 'single_use_per_user' in request.POST
        quantity = request.POST.get('quantity')

        if not code or not discount or not valid_from or not quantity:
            return render(request, 'add_coupon.html', {'error': 'All fields are required.'})

        try:
            discount = float(discount)
            valid_from = timezone.make_aware(timezone.datetime.strptime(valid_from, '%Y-%m-%d'))
            valid_to = timezone.make_aware(timezone.datetime.strptime(valid_to, '%Y-%m-%d')) if valid_to else None
            quantity = int(quantity)
        except (ValueError, TypeError):
            return render(request, 'add_coupon.html', {'error': 'Invalid data format.'})

        now = timezone.now()
        if valid_from < now:
            return render(request, 'add_coupon.html', {'error': 'Valid from date must be in the future.'})

        if valid_from >= now and (valid_to and valid_to < now):
            return render(request, 'add_coupon.html', {'error': 'Valid to date must be in the future.'})

        if valid_to and valid_from >= valid_to:
            return render(request, 'add_coupon.html', {'error': 'Valid from date must be before valid to date.'})

        if Coupon.objects.filter(code=code).exists():
            return render(request, 'add_coupon.html', {'error': 'Coupon code already exists.'})

        new_coupon = Coupon(
            code=code,
            discount=discount,
            valid_from=valid_from,
            minimum_order_amount=minimum_order_amount,
            is_active=is_active,
            single_use_per_user=single_use_per_user,
            quantity=quantity,
        )

        if valid_to:
            new_coupon.valid_to = valid_to

        try:
            new_coupon.save()
        except IntegrityError as e:
            print("Error:", e)
            return render(request, 'add_coupon.html', {'error': 'Error saving the coupon. Please try again.'})

        return redirect('view_coupon')

    return render(request, 'add_coupon.html')



def view_coupon(request):
    coupons = Coupon.objects.all().order_by('id')

    # Pagination
    paginator = Paginator(coupons, 5)  # Show 10 coupons per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'view_coupon.html', {'coupons': page_obj})
def enable_coupon(request, coupon_id):
    coupon = Coupon.objects.get(pk=coupon_id)
    coupon.is_active = True
    coupon.save()
    return redirect('view_coupon')

def disable_coupon(request, coupon_id):
    coupon = Coupon.objects.get(pk=coupon_id)
    coupon.is_active = False
    coupon.save()
    return redirect('view_coupon')
def edit_coupon(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)

    if request.method == 'POST':
        discount = request.POST.get('discount')
        valid_to = request.POST.get('valid_to')
        minimum_order_amount = request.POST.get('minimum_order_amount')
        quantity = request.POST.get('quantity')

        try:
            discount = float(discount)
            valid_to = make_aware(timezone.datetime.strptime(valid_to, '%Y-%m-%d')) if valid_to else None
            minimum_order_amount = float(minimum_order_amount)
            quantity = int(quantity)
        except (ValueError, TypeError):
            return render(request, 'editcoupon.html', {'error': 'Invalid data format.', 'coupon': coupon})

        now = timezone.now()
        if valid_to and valid_to < now:
            return render(request, 'editcoupon.html', {'error': 'Valid to date must be in the future.', 'coupon': coupon})

        coupon.discount = discount
        coupon.valid_to = valid_to
        coupon.minimum_order_amount = minimum_order_amount
        coupon.quantity = quantity

        coupon.save()
        return redirect('view_coupon')

    return render(request, 'editcoupon.html', {'coupon': coupon})


def remove_coupon(request):
    # Remove the applied coupon from the session
    if 'applied_coupon' in request.session:
        del request.session['applied_coupon']
        messages.success(request, "Coupon removed successfully!")
    else:
        messages.warning(request, "No coupon applied.")

    # Get the URL of the previous page and redirect
    previous_page = request.META.get('HTTP_REFERER', None)
    return redirect(previous_page) if previous_page else redirect('view_cart')
def remove_applied_coupon(request):
    applied_coupon = request.session.get('applied_coupon')
    if applied_coupon:
        subtotal = request.session.get('cart_subtotal', Decimal('0.00'))
        coupon_id = applied_coupon.get('id')
        coupon = get_object_or_404(Coupon, id=coupon_id)
        if coupon.minimum_order_amount is not None and subtotal < coupon.minimum_order_amount:
            del request.session['applied_coupon']




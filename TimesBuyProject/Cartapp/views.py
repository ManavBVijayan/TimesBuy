from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import F, Sum
from django.http import JsonResponse
from django.shortcuts import HttpResponseRedirect, get_object_or_404, render, redirect
from django.urls import reverse
from .models import Cart, CartItem
from Store.models import ProductVariant
from Userprofileapp.models import UserAddress


def add_to_cart(request, variant_id):
    variant = get_object_or_404(ProductVariant, id=variant_id)
    user = request.user

    if user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user_id=user)
    else:
        cart_id = request.session.get('cart_id')
        print(cart_id)
        if cart_id:
            cart = Cart.objects.get(id=cart_id)
        else:
            cart = Cart.objects.create()

    item = cart.cartitem_set.filter(product=variant).first()

    if item:
        available_stock = variant.stock - item.quantity
        # Check if the requested quantity is available in stock
        requested_quantity = 1
        if requested_quantity <= available_stock:
            item.quantity += requested_quantity  # Increase the quantity by requested_quantity
            item.save()
            messages.success(request, 'Item added to cart.')
        else:
            # Display an error message to the user
            messages.error(request, 'Requested quantity exceeds available stock.')
    else:
        # Check if the requested quantity is available in stock
        if 1 <= variant.stock:
            CartItem.objects.create(cart=cart, product=variant, quantity=1, price=variant.price)
            messages.success(request, 'Item added to cart.')
        else:
            # Display an error message to the user
            messages.error(request, 'Requested quantity exceeds available stock.')

    if not user.is_authenticated:
        request.session['cart_id'] = cart.id

    return HttpResponseRedirect(request.META['HTTP_REFERER'])


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

    cart_items = cart.cartitem_set.annotate(subtotal=F('quantity') * F('product__price'))
    subtotal = cart_items.aggregate(subtotal_price=Sum('subtotal'))['subtotal_price'] or Decimal('0.00')
    discount = request.GET.get('discount','0.00' )
    print(3,discount)
    discount_price = Decimal(discount)
    # Calculate discount amount based on the difference between subtotal and total_price
    total_price = subtotal - discount_price if discount_price <= subtotal else Decimal('0.00')

    context = {
        'cart': cart,
        'subtotal': subtotal,
        'discount_amount': discount_price,
        'total_price': total_price,
        'cart_items': cart_items,
    }

    return render(request, 'cart.html', context)
def remove_from_cart(request):
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        cart_item = CartItem.objects.get(id=item_id)
        cart_item.delete()

        messages.success(request, 'Item removed from cart.')
        return redirect('view_cart')

    return render(request, 'cart_view.html')


from django.http import JsonResponse

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
            messages.info(request, 'Quantity updated.')
        else:
            messages.error(request, 'Requested quantity exceeds available stock.')

        return JsonResponse({'success': True, 'stock': variant.stock})

    return JsonResponse({'success': False})


@login_required
def checkout(request):
    user = request.user
    cart = Cart.objects.get(user_id=user)
    cart_items = cart.cartitem_set.all()

    out_of_stock_products = [f"{item.product.product.name} - {item.product.color}" for item in cart_items if item.product.stock <= 0]
    if out_of_stock_products:
        error_message = ", ".join(out_of_stock_products) + " is/are out of stock. Please remove them from your cart."
        messages.error(request, error_message)
        return redirect('view_cart')

    subtotal = cart_items.aggregate(subtotal=Sum(F('quantity') * F('product__price')))['subtotal'] or Decimal('0.00')
    shipping_charge = Decimal('50') if subtotal < Decimal('1000') else Decimal('0.00')

    discount_amount = Decimal(request.GET.get('discount', '0.00'))

    total_price = subtotal + shipping_charge - discount_amount
    request.session['total_price'] = str(total_price)
    addresses = UserAddress.objects.filter(user=user)
    selected_address = addresses.filter(is_delivery_address=True).first()

    context = {
        'cart': cart,
        'subtotal': subtotal,
        'shipping_charge': shipping_charge,
        'discount_amount': discount_amount,
        'total_price': total_price,
        'cart_items': cart_items,
        'addresses': addresses,
        'selected_address': selected_address,
    }

    return render(request, 'checkout.html', context)

def apply_coupon(request):
    if request.method == 'POST':
        coupon_code = request.POST.get('coupon_code')
        discount = Decimal('100.00') if coupon_code == 'coupon' else Decimal('0.00')
        request.session['applied_coupon'] = coupon_code
        cart_url = reverse('view_cart') + f'?discount={discount}'
        return redirect(cart_url)
    else:
        return redirect('view_cart')





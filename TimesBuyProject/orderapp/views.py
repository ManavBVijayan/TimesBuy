from decimal import Decimal
from django.http import HttpResponse, JsonResponse

from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from .models import Order, OrderItem
from Cartapp.models import Cart, CartItem
from Userprofileapp.models import UserAddress,Wallet
import razorpay

def placeorder(request, add_id):
    user_address = get_object_or_404(UserAddress, id=add_id, user=request.user)
    cart = Cart.objects.get(user_id=request.user)
    cart_items = cart.cartitem_set.all()

    total_price = request.session.get('total_price', Decimal('0.00'))
    applied_coupon = request.session.get('applied_coupon', None)

        # Check if a delivery address is selected
    if not user_address:
            # Redirect to the checkout view with an error message indicating that no delivery address is selected
        return redirect('checkout')

    order = Order.objects.create(
        user=request.user,
        address=user_address,
        total_price=total_price,
        payment_status='ORDERED',
        payment_method='CASH_ON_DELIVERY',
        applied_coupon=applied_coupon,
        )

    for cart_item in cart_items:
        OrderItem.objects.create(
            order=order,
            product=cart_item.product,
            price=cart_item.price,
            quantity=cart_item.quantity
            )
        variant = cart_item.product
        variant.stock -= cart_item.quantity
        variant.save()

    cart_items.delete()

    return render(request, 'orderplaced.html')


def initiate_payment(request):
    print('helowwww')
    if request.method == 'POST':
        # Retrieve the total price and other details from the backend
        cart = Cart.objects.get(user_id=request.user)
        cart_items = cart.cartitem_set.all()

        total_price_str = request.session.get('total_price', '0.00')
        total_price = Decimal(total_price_str)

        total_amount_in_cents = int(total_price*100)
        applied_coupon = request.session.get('applied_coupon', None)

        client = razorpay.Client(auth=(settings.RAZOR_KEY_ID, settings.RAZOR_KEY_SECRET))
        payment = client.order.create({

            'amount': total_amount_in_cents,
            'currency': 'INR',
            'payment_capture': 1

        })

        response_data = {
            'order_id': payment['id'],
            'amount': payment['amount'],
            'currency': payment['currency'],
            'key': settings.RAZOR_KEY_ID,

        }
        return JsonResponse(response_data)

    # Return an error response if the request method is not POST
    return JsonResponse({'error': 'Invalid request method'})


def online_payment_order(request, add_id):
    if request.method == 'POST':
        payment_id = request.POST.getlist('payment_id')[0]
        orderId = request.POST.getlist('orderId')[0]
        signature = request.POST.getlist('signature')[0]
        user_address = get_object_or_404(UserAddress, id=add_id, user=request.user)
        cart = Cart.objects.get(user_id=request.user)
        cart_items = cart.cartitem_set.all()

        total_price = request.session.get('total_price', Decimal('0.00'))
        applied_coupon = request.session.get('applied_coupon', None)



        order = Order.objects.create(
            user=request.user,
            address=user_address,
            total_price=total_price,
            payment_status='PAID',
            payment_method='RAZORPAY',
            order_status='ORDERED',
            razor_pay_payment_id=payment_id,
            razor_pay_payment_signature=signature,
            razor_pay_order_id=orderId,
            applied_coupon=applied_coupon,
        )

        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                price=cart_item.price,
                quantity=cart_item.quantity
            )
            variant = cart_item.product
            variant.stock -= cart_item.quantity
            variant.save()

        cart_items.delete()
        orderId = order.id


        return JsonResponse({'message': 'Order placed successfully', 'orderId': orderId})
    else:
        # Handle invalid request method (GET, etc.)
        return JsonResponse({'error': 'Invalid request method'})


def order_list(request):
    # Get the logged-in user
    user = request.user

    # Retrieve all orders for the logged-in user
    orders = Order.objects.filter(user=user)

    context = {
        'tab': 'orders',
        'orders': orders,
    }

    return render(request, 'viewprofile.html', context)


def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order_items = OrderItem.objects.filter(order=order)

    context = {
        'order': order,
        'order_items': order_items,
    }

    return render(request, 'orderdetail.html', context)

def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if order.payment_status != 'CANCELLED':
        order_items = OrderItem.objects.filter(order=order)

        for item in order_items:
            variant = item.product
            variant.stock = variant.stock + item.quantity
            variant.save()

        order.payment_status = 'CANCELLED'
        order.save()

    return redirect(request.META.get('HTTP_REFERER'))

def return_orders(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    user = order.user
    refund = Decimal(order.total_price)
    user_wallet, created = Wallet.objects.get_or_create(user=user)
    user_wallet.balance += refund
    user_wallet.save()
    if order.payment_status != 'CANCELLED':
        order.payment_status = 'RETURNED'
        order.save()

    return redirect(request.META.get('HTTP_REFERER'))

def pay_wallet(request):
    pass
def order_success(request):
    return render(request,'orderplaced.html')
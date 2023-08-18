from decimal import Decimal
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Sum, F
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import Order, OrderItem
from Cartapp.models import Cart, CartItem, Coupon
from Userprofileapp.models import UserAddress,Wallet,WalletTransaction
import razorpay
from datetime import timedelta
from django.template.loader import render_to_string
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from io import BytesIO

def placeorder(request, add_id):
    user_address = get_object_or_404(UserAddress, id=add_id, user=request.user)
    cart = Cart.objects.get(user_id=request.user)
    cart_items = cart.cartitem_set.all()
    subtotal = cart_items.aggregate(subtotal=Sum(F('quantity') * F('product__price')))['subtotal'] or Decimal('0.00')
    shipping_charge = Decimal('50') if subtotal < Decimal('1000') else Decimal('0.00')
    applied_coupon_id = request.session.get('applied_coupon', {}).get('id')
    discount_amount = Decimal('0.00')
    coupon = None

    # If an applied_coupon_id exists, attempt to retrieve the coupon
    if applied_coupon_id is not None:
        try:
            coupon = get_object_or_404(Coupon, id=applied_coupon_id)
            discount_amount = Decimal(coupon.discount)
        except Coupon.DoesNotExist:
            # Handle the case when the coupon with the stored ID no longer exists
            coupon = None

    # Calculate the total price based on the discount amount
    total_price = subtotal + shipping_charge - discount_amount

    out_of_stock_products = [item.product for item in cart_items if item.product.stock < item.quantity]
    if out_of_stock_products:
        error_message = "The following products are out of stock or not available in the requested quantity: "
        error_message += ", ".join([f"{product.name} ({product.color})" for product in out_of_stock_products])
        messages.error(request, error_message)
        return redirect('checkout')


    with transaction.atomic():
        order = Order.objects.create(
            user=request.user,
            first_name=user_address.first_name,
            last_name=user_address.last_name,
            email=user_address.email,
            phone_number=user_address.phone_number,
            address_line_1=user_address.address_line_1,
            address_line_2=user_address.address_line_2,
            postal_code=user_address.postal_code,
            city=user_address.city,
            state=user_address.state,
            country=user_address.country,
            total_price=total_price,
            payment_status='Pending',
            payment_method='Cash on delivery',
            applied_coupon=coupon,
            shipping_charge=shipping_charge,
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
        if coupon:
            if coupon.quantity >= 1:
                coupon.quantity -=1
                coupon.save()

        cart_items.delete()
        request.session.pop('applied_coupon', None)
    return redirect('order_success')


def initiate_payment(request):
    if request.method == 'POST':
        cart = Cart.objects.get(user_id=request.user)
        cart_items = cart.cartitem_set.all()

        subtotal = cart_items.aggregate(subtotal=Sum(F('quantity') * F('product__price')))['subtotal'] or Decimal('0.00')
        shipping_charge = Decimal('50') if subtotal < Decimal('1000') else Decimal('0.00')

        applied_coupon = request.session.get('applied_coupon', {'discount': '0.00'})
        discount_amount = Decimal(applied_coupon.get('discount', '0.00'))
        total_price = subtotal + shipping_charge - discount_amount

        # Check if the requested quantities are available in stock
        out_of_stock_products = [item.product for item in cart_items if item.product.stock < item.quantity]
        if out_of_stock_products:
            error_message = "The following products are out of stock or not available in the requested quantity: "
            error_message += ", ".join([f"{product.name} ({product.color})" for product in out_of_stock_products])
            messages.error(request, error_message)
            return redirect('checkout')

        total_amount_in_cents = int(total_price * 100)
        applied_coupon = request.session.get('applied_coupon', None)

        # Proceed with initiating the payment
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

        subtotal = cart_items.aggregate(subtotal=Sum(F('quantity') * F('product__price')))['subtotal'] or Decimal('0.00')
        shipping_charge = Decimal('50') if subtotal < Decimal('1000') else Decimal('0.00')

        applied_coupon_id = request.session.get('applied_coupon', {}).get('id')

        discount_amount = Decimal('0.00')
        coupon = None

        # If an applied_coupon_id exists, attempt to retrieve the coupon
        if applied_coupon_id is not None:
            try:
                coupon = get_object_or_404(Coupon, id=applied_coupon_id)
                discount_amount = Decimal(coupon.discount)
            except Coupon.DoesNotExist:
                # Handle the case when the coupon with the stored ID no longer exists
                coupon = None

        # Calculate the total price based on the discount amount
        total_price = subtotal + shipping_charge - discount_amount



        order = Order.objects.create(
            user=request.user,
            first_name=user_address.first_name,
            last_name=user_address.last_name,
            email=user_address.email,
            phone_number=user_address.phone_number,
            address_line_1=user_address.address_line_1,
            address_line_2=user_address.address_line_2,
            postal_code=user_address.postal_code,
            city=user_address.city,
            total_price=total_price,
            state=user_address.state,
            country=user_address.country,
            payment_status='Paid',
            payment_method='Net banking',
            razor_pay_payment_id=payment_id,
            razor_pay_payment_signature=signature,
            razor_pay_order_id=orderId,
            applied_coupon=coupon,
            shipping_charge=shipping_charge,
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
        if coupon:
            if coupon.quantity >= 1:
                coupon.quantity -= 1
                coupon.save()
        cart_items.delete()
        orderId = order.id
        request.session.pop('applied_coupon', None)


        return JsonResponse({'message': 'Order placed successfully', 'orderId': orderId})
    else:
        return JsonResponse({'error': 'Invalid request method'})


def order_list(request):
    # Get the logged-in user
    user = request.user

    # Retrieve all orders for the logged-in user, ordered by order date (latest first)
    orders = Order.objects.filter(user_id=user).order_by('-order_date')

    # Pagination
    page_number = request.GET.get('page')  # Get the current page number from the query parameter
    items_per_page = 10  # Number of orders to display per page

    paginator = Paginator(orders, items_per_page)  # Create a Paginator instance
    page_orders = paginator.get_page(page_number)  # Get the current page using the page number

    context = {
        'tab': 'orders',
        'orders': page_orders,  # Pass the paginated page object to the context
    }

    return render(request, 'viewprofile.html', context)


def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order_items = OrderItem.objects.filter(order=order)
    expected_delivery_date=order.order_date + timedelta(days=3)
    current_date=timezone.now()


    context = {
        'order': order,
        'order_items': order_items,
        'expected_delivery_date':expected_delivery_date,
        'current_date':current_date
    }

    return render(request, 'orderdetail.html', context)

def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if order.order_status != 'Cancelled':
        # Check if the order was paid using NETBANKING or WALLET_PAY
        if order.payment_method in ['Net banking', 'Wallet pay']:
            user_wallet = Wallet.objects.get(user=request.user)
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
        if order.payment_status == 'Pending':
            order.payment_status='No payment'
        else:
            order.payment_status='Refunded'
        order.order_status='Cancelled'
        order.cancelled_date=timezone.now()
        order.save()

        # Restore the stock for the cancelled order items
        order_items = OrderItem.objects.filter(order=order)
        for item in order_items:
            variant = item.product
            variant.stock = variant.stock + item.quantity
            variant.save()

    return redirect(request.META.get('HTTP_REFERER'))


def order_success(request):
    return render(request,'orderplaced.html')


def return_request(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if order.order_status != 'Cancelled':  # The error might be here, incorrect status check.
        order.order_status = 'Requested for return'
        order.payment_status='Refund in progress'
        order.return_request_date = timezone.now()
        order.save()

    return redirect(request.META.get('HTTP_REFERER'))

def pay_wallet(request,add_id):
    user_address = get_object_or_404(UserAddress, id=add_id, user=request.user)
    cart = Cart.objects.get(user_id=request.user)
    cart_items = cart.cartitem_set.all()
    subtotal = cart_items.aggregate(subtotal=Sum(F('quantity') * F('product__price')))['subtotal'] or Decimal('0.00')
    shipping_charge = Decimal('50') if subtotal < Decimal('1000') else Decimal('0.00')

    applied_coupon_id = request.session.get('applied_coupon', {}).get('id')

    discount_amount = Decimal('0.00')
    coupon = None

    if applied_coupon_id is not None:
        try:
            coupon = get_object_or_404(Coupon, id=applied_coupon_id)
            discount_amount = Decimal(coupon.discount)
        except Coupon.DoesNotExist:
            coupon = None

    total_price = subtotal + shipping_charge - discount_amount

    out_of_stock_products = [item.product for item in cart_items if item.product.stock < item.quantity]
    if out_of_stock_products:
        error_message = "The following products are out of stock or not available in the requested quantity: "
        error_message += ", ".join([f"{product.name} ({product.color})" for product in out_of_stock_products])
        messages.error(request, error_message)
        return redirect('checkout')
    user_wallet = Wallet.objects.get(user=request.user)

    if user_wallet.balance >= total_price:
        user_wallet.balance -= total_price
        user_wallet.save()

    with transaction.atomic():
        order = Order.objects.create(
            user=request.user,
            first_name=user_address.first_name,
            last_name=user_address.last_name,
            email=user_address.email,
            phone_number=user_address.phone_number,
            address_line_1=user_address.address_line_1,
            address_line_2=user_address.address_line_2,
            postal_code=user_address.postal_code,
            city=user_address.city,
            state=user_address.state,
            country=user_address.country,
            total_price=total_price,
            payment_status='Paid',
            payment_method='Wallet pay',
            applied_coupon=coupon,
            shipping_charge=shipping_charge,
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
        transaction_type = 'Purchased'
        WalletTransaction.objects.create(
            wallet=user_wallet,
            amount=total_price,
            order_id=order,
            transaction_type=transaction_type,
        )
        if coupon:
            coupon_quantity_to_reduce = 1
            if coupon.quantity >= coupon_quantity_to_reduce:
                coupon.quantity -= coupon_quantity_to_reduce
                coupon.save()
        cart_items.delete()
        request.session.pop('applied_coupon', None)
    return redirect('order_success')


def download_invoice(request, order_id):
    order = Order.objects.get(pk=order_id)
    order_items = OrderItem.objects.filter(order=order)

    # Render HTML template to a string
    html_content = render_to_string('invoice_pdf.html', {'order': order, 'order_items': order_items})

    # Create a PDF using ReportLab
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{order_id}.pdf"'

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    # Convert HTML content to PDF
    from xhtml2pdf import pisa
    pisa_status = pisa.CreatePDF(html_content, dest=response, link_callback=None)
    if pisa_status.err:
        return HttpResponse('PDF generation error.')

    return response
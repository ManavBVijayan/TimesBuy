from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import UserAddress,Wallet
from Cartapp.models import Cart
from django.contrib.auth import update_session_auth_hash
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
@login_required
def profile_view(request):
    user = request.user
    addresses = UserAddress.objects.filter(user=user)
    selected_address = addresses.filter(is_delivery_address=True).first()
    return render(request, 'viewprofile.html', {'tab': 'profile', 'addresses': addresses, 'user': user, 'selected_address': selected_address})

@login_required
def choose_delivery_address(request, address_id):
    user = request.user
    address = get_object_or_404(UserAddress, id=address_id, user=user)
    UserAddress.objects.filter(user=user, is_delivery_address=True).update(is_delivery_address=False)
    address.is_delivery_address = True
    address.save()
    try:
        cart = Cart.objects.get(user_id=user)
    except Cart.DoesNotExist:
        return redirect('cart_empty_view')
    cart.delivery_address = address
    cart.save()

    messages.success(request, 'Delivery address selected successfully.')
    if 'checkout' in request.META.get('HTTP_REFERER', ''):
        return redirect('checkout')
    return redirect('profile_view')


@login_required
def delete_address(request, address_id):
    user = request.user
    address = get_object_or_404(UserAddress, id=address_id, user=user)
    address.delete()
    messages.success(request, 'Address deleted successfully.')
    return redirect('profile_view')

@login_required
def show_address(request):
    user = request.user
    addresses = UserAddress.objects.filter(user=user)
    return render(request, 'viewprofile.html', {'tab': 'address', 'addresses': addresses})

@login_required
def add_address(request):
    if request.method == 'POST':
        first_name = request.POST['fname']
        last_name = request.POST['lname']
        address_line_1 = request.POST['address1']
        address_line_2 = request.POST['address2']
        city = request.POST['city']
        state = request.POST['state']
        postal_code = request.POST['pincode']
        country = request.POST['country']
        phone_number = request.POST['phone']
        email = request.POST['email']

        is_delivery_address = request.POST.get('is_delivery_address', False) == 'true'


        if is_delivery_address:
            UserAddress.objects.filter(user=request.user).update(is_delivery_address=False)

        address = UserAddress(
            user=request.user,
            first_name=first_name,
            last_name=last_name,
            address_line_1=address_line_1,
            address_line_2=address_line_2,
            city=city,
            state=state,
            postal_code=postal_code,
            country=country,
            phone_number=phone_number,
            email=email,
            is_delivery_address=is_delivery_address
        )
        address.save()
        messages.success(request, 'Address added successfully.')

        # Redirect back to the previous page
        previous_page = request.session.get('previous_page')
        if previous_page:
            del request.session['previous_page']
            return redirect(previous_page)

        # Store the previous page URL in the session
    request.session['previous_page'] = request.META.get('HTTP_REFERER')

    return render(request, 'addaddress.html')



from django.urls import reverse
from django.shortcuts import redirect

@login_required
def change_password_view(request):
    if request.method == 'POST':
        old_password = request.POST['old_password']
        new_password = request.POST['new_password']
        confirm_password = request.POST['confirm_password']

        if request.user.check_password(old_password) and new_password == confirm_password:
            try:
                # Validate the new password for strength
                validate_password(new_password, user=request.user)

                # If validation passes, set the new password for the user
                request.user.set_password(new_password)
                request.user.save()

                # Update the user's session to prevent automatic logout
                update_session_auth_hash(request, request.user)

                messages.success(request, 'Password changed successfully.')

                # Redirect to the 'profile_view' URL pattern
                profile_view_url = reverse('profile_view')
                return redirect(profile_view_url)
            except ValidationError as e:
                # If the new password doesn't meet the strength requirements, display an error message
                messages.error(request, '\n'.join(e))
        else:
            messages.error(request, 'Invalid old password or passwords do not match.')

    return render(request, 'changepassword.html')


@login_required
def edit_address(request, address_id):
    try:
        user_address = UserAddress.objects.get(id=address_id, user=request.user)
    except UserAddress.DoesNotExist:
        return HttpResponse('Address not found.')

    if request.method == 'POST':
        # Retrieve form data
        first_name = request.POST['fname']
        last_name = request.POST['lname']
        address_line_1 = request.POST['address1']
        address_line_2 = request.POST['address2']
        city = request.POST['city']
        state = request.POST['state']
        postal_code = request.POST['pincode']
        country = request.POST['country']
        phone_number = request.POST['phone']

        is_delivery_address = request.POST.get('is_delivery_address', False)
        print(is_delivery_address)

        if is_delivery_address:
            print(1)
            UserAddress.objects.filter(user=request.user, is_delivery_address=True).update(is_delivery_address=False)

        user_address.first_name = first_name
        user_address.last_name = last_name
        user_address.address_line_1 = address_line_1
        user_address.address_line_2 = address_line_2
        user_address.city = city
        user_address.state = state
        user_address.postal_code = postal_code
        user_address.country = country
        user_address.phone_number = phone_number
        user_address.is_delivery_address = is_delivery_address

        user_address.save()
        return redirect('profile_view')

    context = {
        'user_address': user_address,
        'address_id': address_id,
        'user': user_address.user,
    }
    return render(request, 'editaddress.html', context)
def view_wallet(request):
    # Assuming the user is logged in, get their wallet
    wallet = Wallet.objects.get(user=request.user)
    return render(request, 'viewprofile.html', {'tab': 'wallet', 'wallet': wallet})

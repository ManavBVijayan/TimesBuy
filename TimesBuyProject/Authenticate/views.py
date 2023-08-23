import datetime
import re
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages, auth
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views.decorators.cache import cache_control
from django.contrib.sessions.backends.db import SessionStore
from .models import CustomUser
import pyotp
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from Cartapp.models import Cart, CartItem


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def signin(request):
    if 'username' in request.session:
        return redirect('home')
    if request.method == 'POST':
        username_or_email = request.POST['username_or_email']


        try:
            user = CustomUser.objects.get(username=username_or_email)
        except CustomUser.DoesNotExist:
            try:
                user = CustomUser.objects.get(email=username_or_email)
            except CustomUser.DoesNotExist:
                # Handle the case where the user is not found
                messages.error(request, 'Invalid username or email.')
                return render(request, 'signin.html')

        if user is not None:
            otp_secret = pyotp.random_base32()
            totp = pyotp.TOTP(otp_secret)
            otp = totp.now()
            expiration_time = datetime.datetime.now() + datetime.timedelta(minutes=5)
            session = SessionStore(request.session.session_key)
            request.session['otp'] = otp
            request.session['user_id'] = user.id
            request.session['otp_expiration_time'] = expiration_time.timestamp()

            subject = 'OTP verification'
            message = f'Hello {user.username},\n\n' \
                      f'Please use the following OTP to verify your email: {otp}\n\n' \
                      f'Thank you!\n\n' \
                      f'By, Team TimesBuy'

            from_email = settings.EMAIL_HOST_USER
            recipient_list = [user.email]

            send_mail(subject, message, from_email, recipient_list)

            return redirect('otp-verification')

        else:
            messages.error(request, 'Invalid username or email')
            return redirect('signin')

    return render(request, 'signin.html')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def otp_verification(request):
    if request.method == 'POST':
        otp = request.POST.get('otp')
        session_otp = request.session.get('otp')
        user_id = request.session.get('user_id')
        expiration_time = request.session.get('otp_expiration_time')

        if session_otp == otp:
            if datetime.datetime.now().timestamp() < expiration_time:

                my_users = CustomUser.objects.get(id=user_id)
                login(request, my_users)
                request.session['otp'] = None
                request.session['user_id'] = None
                guest_cart_id = request.session.get('cart_id')
                if guest_cart_id:
                    try:
                        guest_cart = Cart.objects.get(id=guest_cart_id)
                        user_cart, created = Cart.objects.get_or_create(user_id=my_users)

                        for guest_item in guest_cart.cartitem_set.all():
                            try:
                                user_item = CartItem.objects.get(cart=user_cart, product=guest_item.product)
                                available_stock = guest_item.product.stock - user_item.quantity
                                if guest_item.quantity <= available_stock:
                                    user_item.quantity += guest_item.quantity
                                    user_item.save()
                                else:
                                    messages.error(request,
                                                   f"Requested quantity for '{guest_item.product}' exceeds available stock.")
                            except CartItem.DoesNotExist:
                                CartItem.objects.create(
                                    cart=user_cart,
                                    product=guest_item.product,
                                    quantity=guest_item.quantity,
                                    price=guest_item.product.price
                                )
                        guest_cart.delete()
                        del request.session['cart_id']

                    except Cart.DoesNotExist:
                        pass

                return redirect('home')

            else:
                request.session['otp'] = None
                request.session['user_id'] = None
                request.session['otp_expiration_time'] = None
                messages.error(request, 'OTP has expired. Please request a new one.')
                return redirect('otp-verification')


        elif request.user.is_authenticated:
            messages.error(request, 'Invalid OTP')
    messages.success(request, "We have sent an OTP to your email.")
    return render(request, 'otp_verification.html')

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def signup(request):
    if 'username' in request.session:
        return redirect('home')

    if request.method == "POST":
        # Get form data
        username = request.POST['username']
        email = request.POST['email']
        phone_number = request.POST['phone_number']
        pass1 = request.POST['password']
        cpassword = request.POST['cpassword']
        if ' ' in username:
            messages.error(request, 'Username cannot contain spaces')
            return redirect('signup')
        if len(username) > 15:
            messages.error(request, 'Username cannot exceed 15 characters')
            return redirect('signup')
        if pass1 != cpassword:
            messages.error(request, 'Passwords do not match')
            return redirect('signup')

        try:
            validate_password(pass1)
        except ValidationError as error:
            messages.error(request, error.messages[0])
            return redirect('signup')

        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, 'Username taken')
            return redirect('signup')
        if CustomUser.objects.filter(phone_number=phone_number).exists():
            messages.error(request, 'Phone number already used')
            return redirect('signup')

        if not re.match(r'^\d{10}$', phone_number):
            messages.error(request, 'Invalid phone number. Phone number must contain 10 digits.')
            return redirect('signup')

        if phone_number.startswith('0'):
            messages.error(request, 'Invalid phone number. Phone number cannot start with zero.')
            return redirect('signup')

        myuser = CustomUser.objects.create_user(
            username=username,
            password=pass1,
            email=email,
            phone_number=phone_number,
            is_active=False,
        )
        myuser.save()

        token = default_token_generator.make_token(myuser)

        current_site = get_current_site(request)
        uidb64 = urlsafe_base64_encode(force_bytes(myuser.pk))
        verification_url = reverse('verify_email', kwargs={'uidb64': uidb64, 'token': token})
        verification_url = f"{request.scheme}://{current_site}{verification_url}"

        mail_subject = 'Activate your account'
        message = render_to_string('verification_email.html', {
            'user': myuser,
            'verification_url': verification_url
        })
        send_mail(mail_subject, message, 'timesbuyeshop@gmail.com', [email])

        return redirect('verification_mail_sent')

    return render(request, 'signup.html')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def verify_email(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        auth.login(request, user)
        user.save()
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
                            messages.error(request,
                                           f"Requested quantity for '{guest_item.product}' exceeds available stock.")
                    except CartItem.DoesNotExist:
                        CartItem.objects.create(
                            cart=user_cart,
                            product=guest_item.product,
                            quantity=guest_item.quantity,
                            price=guest_item.product.price
                        )
                guest_cart.delete()
                del request.session['cart_id']

            except Cart.DoesNotExist:
                pass
        return redirect('home')
    return render(request, 'verification_failed.html')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def logout_view(request):
    if 'username' in request.session:
        request.session.flush()
    if request.user.is_authenticated:
        logout(request)
    return redirect('/')

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def verification_mail_sent(requset):
    return render(requset,'verification_mail_sent.html')

def forgot_password(request):
    if request.method == 'POST':
        username_or_email = request.POST.get('username_or_email')

        try:
            user = CustomUser.objects.get(username=username_or_email)
        except CustomUser.DoesNotExist:
            try:
                user = CustomUser.objects.get(email=username_or_email)
            except CustomUser.DoesNotExist:
                messages.error(request, 'Invalid username or email.')
                return render(request, 'forgot_password.html')

        token = default_token_generator.make_token(user)

        request.session['user_id'] = user.pk

        current_site = get_current_site(request)
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        verification_url = reverse('verify-email-fp', kwargs={'uidb64': uidb64, 'token': token})
        verification_url = f"{request.scheme}://{current_site}{verification_url}"

        mail_subject = 'Reset your password'
        message = render_to_string('forgotmail.html', {
            'user': user,
            'verification_url': verification_url
        })
        send_mail(mail_subject, message, 'timesbuyeshop@gmail.com', [user.email])

        return redirect('verification_mail_sent')

    return render(request, 'forgotpassword.html')
def forgot_pw_verify_mail(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        # Store user ID in session
        request.session['user_id'] = user.pk

        return redirect('reset-password')

    # Handle invalid token or user not found
    return render(request, 'verification_failed.html')

def reset_password(request):
    if request.method == 'POST':
        new_password1 = request.POST['new_password1']
        new_password2 = request.POST['new_password2']

        if new_password1 != new_password2:
            return render(request, 'resetpassword.html', {'error_message': 'Passwords do not match.'})

        try:
            validate_password(new_password1, user=CustomUser())
        except ValidationError as error:
            error_message = error.messages[0]
            return render(request, 'resetpassword.html', {'error_message': error_message})

        user_id = request.session.get('user_id')
        if not user_id:
            return render(request, 'resetpassword.html', {'error_message': 'User ID not found in session.'})

        try:
            user = CustomUser.objects.get(pk=user_id)
        except CustomUser.DoesNotExist:
            return render(request, 'resetpassword.html', {'error_message': 'User not found.'})

        user.set_password(new_password1)
        user.save()

        del request.session['user_id']

        return redirect('password-reset-success')

    return render(request, 'resetpassword.html')

def password_reset_success(request):

    return render(request,'pwresetsuccess.html')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def password_login(request):
    if 'username' in request.session:
        return redirect('home')
    if request.method=='POST':
        username=request.POST['username']
        password=request.POST['password']
        user=authenticate(username=username,password=password)
        if user is not None:
            request.session['username']=username
            auth.login(request,user)
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
                                messages.error(request,
                                               f"Requested quantity for '{guest_item.product}' exceeds available stock.")
                        except CartItem.DoesNotExist:
                            CartItem.objects.create(
                                cart=user_cart,
                                product=guest_item.product,
                                quantity=guest_item.quantity,
                                price=guest_item.product.price
                            )
                    guest_cart.delete()
                    del request.session['cart_id']

                except Cart.DoesNotExist:
                    pass
            return redirect('home')
        else:
            messages.error(request,'invalid credentials')
            return redirect('password-login')
    return render(request,'passwordlogin.html')

from twilio.rest import Client
from django.conf import settings
import phonenumbers
import random


def send_predefined_twilio_message(request):
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        user = CustomUser.objects.get(phone_number=phone_number)

        if not user:
            return HttpResponse("User not found")

        try:
            parsed_phone_number = phonenumbers.parse(phone_number, 'IN')

            if not phonenumbers.is_valid_number(parsed_phone_number):
                return HttpResponse("Invalid phone number")

            formatted_phone_number = phonenumbers.format_number(parsed_phone_number,
                                                                phonenumbers.PhoneNumberFormat.E164)

            otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            message_body = f"Your OTP is: {otp}"

            expiration_time = datetime.datetime.now() + datetime.timedelta(minutes=5)
            session = SessionStore(request.session.session_key)
            request.session['user_id'] = user.id
            request.session['otp'] = otp
            request.session['otp_expiration_time'] = expiration_time.timestamp()

            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            try:
                message = client.messages.create(
                    body=message_body,
                    from_=settings.TWILIO_PHONE_NUMBER,
                    to=formatted_phone_number
                )
                return redirect('otp-verification')
            except Exception as e:
                return HttpResponse(f"Error: {str(e)}")
        except phonenumbers.NumberParseException as e:
            return HttpResponse(f"Error parsing phone number: {str(e)}")

    return render(request, 'mobile_otp.html')




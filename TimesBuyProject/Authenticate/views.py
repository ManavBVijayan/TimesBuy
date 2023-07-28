import datetime
import re
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
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



def signin(request):
    if request.method == 'POST':
        username_or_email = request.POST['username_or_email']
        print(username_or_email)

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
            print(3)
            # Generate OTP secret
            otp_secret = pyotp.random_base32()

            # Create a PyOTP object
            totp = pyotp.TOTP(otp_secret)

            # Get the current OTP
            otp = totp.now()

            # Set the expiration time for OTP
            expiration_time = datetime.datetime.now() + datetime.timedelta(minutes=5)

            # Store OTP in the session
            session = SessionStore(request.session.session_key)
            request.session['otp'] = otp
            request.session['user_id'] = user.id
            request.session['otp_expiration_time'] = expiration_time.timestamp()

            # Compose the email content
            subject = 'OTP verification'
            message = f'Hello {user.username},\n\n' \
                      f'Please use the following OTP to verify your email: {otp}\n\n' \
                      f'Thank you!\n\n' \
                      f'By, Team TimesBuy'

            from_email = settings.EMAIL_HOST_USER
            recipient_list = [user.email]

            # Send the email
            send_mail(subject, message, from_email, recipient_list)

            return redirect('otp-verification')

        else:
            messages.error(request, 'Invalid username or email')
            return redirect('signin')

    return render(request, 'signin.html')
def otp_verification(request):
    if request.method == 'POST':
        otp = request.POST.get('otp')
        # Retrieve OTP from session
        session_otp = request.session.get('otp')
        print(1,session_otp)
        user_id = request.session.get('user_id')
        expiration_time = request.session.get('otp_expiration_time')

        if session_otp == otp:
            if datetime.datetime.now().timestamp() < expiration_time:

                my_users = CustomUser.objects.get(id=user_id)
                login(request, my_users)
                # Clear OTP from session
                request.session['otp'] = None
                request.session['user_id'] = None

                return redirect('home')

            else:
                # expired otp
                request.session['otp'] = None
                request.session['user_id'] = None
                request.session['otp_expiration_time'] = None
                messages.error(request, 'OTP has expired. Please request a new one.')
                return redirect('otp-verification')


        elif request.user.is_authenticated:
            # OTP is invalid, display an error message
            messages.error(request, 'Invalid OTP')

        # OTP verification not completed or authentication failed
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

        # Check if passwords match
        if pass1 != cpassword:
            messages.error(request, 'Passwords do not match')
            return redirect('signup')

        # Validate password complexity
        try:
            validate_password(pass1)
        except ValidationError as error:
            messages.error(request, error.messages[0])
            return redirect('signup')

        # Check if username or email already exists
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, 'Username taken')
            return redirect('signup')

        # Validate phone number
        if not re.match(r'^\d{10}$', phone_number):
            messages.error(request, 'Invalid phone number. Phone number must contain 10 digits.')
            return redirect('signup')

        if phone_number.startswith('0'):  # Check if the phone number starts with zero
            messages.error(request, 'Invalid phone number. Phone number cannot start with zero.')
            return redirect('signup')

        # Create the user
        myuser = CustomUser.objects.create_user(
            username=username,
            password=pass1,
            email=email,
            phone_number=phone_number,
            is_active=False,  # Set is_active to False initially
        )
        myuser.save()

        # Generate verification token
        token = default_token_generator.make_token(myuser)

        # Build verification URL
        current_site = get_current_site(request)
        uidb64 = urlsafe_base64_encode(force_bytes(myuser.pk))
        verification_url = reverse('verify_email', kwargs={'uidb64': uidb64, 'token': token})
        verification_url = f"{request.scheme}://{current_site}{verification_url}"

        # Send verification email
        mail_subject = 'Activate your account'
        message = render_to_string('verification_email.html', {
            'user': myuser,
            'verification_url': verification_url
        })
        send_mail(mail_subject, message, 'timesbuyeshop@gmail.com', [email])

        return redirect('verification_mail_sent')

    return render(request, 'signup.html')
def verify_email(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        return redirect('password-login')

    # Handle invalid token or user not found
    return render(request, 'verification_failed.html')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def logout_view(request):
    if request.user.is_authenticated:
        # User is logged in, perform logout
        logout(request)
    return redirect('/')
def verification_mail_sent(requset):
    return render(requset,'verification_mail_sent.html')

def forgot_password(request):
    if request.method == 'POST':
        username_or_email = request.POST.get('username_or_email')

        # Find the user by username or email
        try:
            user = CustomUser.objects.get(username=username_or_email)
        except CustomUser.DoesNotExist:
            try:
                user = CustomUser.objects.get(email=username_or_email)
            except CustomUser.DoesNotExist:
                # Handle the case where the user is not found
                messages.error(request, 'Invalid username or email.')
                return render(request, 'forgot_password.html')

        # Generate verification token
        token = default_token_generator.make_token(user)

        # Store user ID in session
        request.session['user_id'] = user.pk

        # Build verification URL
        current_site = get_current_site(request)
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        verification_url = reverse('verify-email-fp', kwargs={'uidb64': uidb64, 'token': token})
        verification_url = f"{request.scheme}://{current_site}{verification_url}"

        # Send verification email
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

        # Password validation
        if new_password1 != new_password2:
            return render(request, 'resetpassword.html', {'error_message': 'Passwords do not match.'})

        # Validate password complexity
        try:
            validate_password(new_password1, user=CustomUser())
        except ValidationError as error:
            error_message = error.messages[0]
            return render(request, 'resetpassword.html', {'error_message': error_message})

        # Retrieve user ID from session
        user_id = request.session.get('user_id')
        if not user_id:
            return render(request, 'resetpassword.html', {'error_message': 'User ID not found in session.'})

        try:
            user = CustomUser.objects.get(pk=user_id)
        except CustomUser.DoesNotExist:
            return render(request, 'resetpassword.html', {'error_message': 'User not found.'})

        # Set the new password
        user.set_password(new_password1)
        user.save()

        # Clear user ID from session
        del request.session['user_id']

        # Redirect to password reset success page
        return redirect('password-reset-success')

    return render(request, 'resetpassword.html')

def password_reset_success(request):

    return render(request,'pwresetsuccess.html')
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
            return redirect('home')
        else:
            messages.error(request,'invalid credentials')
            return redirect('password-login')
    return render(request,'passwordlogin.html')




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
from .models import CustomUser

def signin(request):
    if 'username' in request.session:
        return redirect('home')
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = auth.authenticate(username=username, password=password)
        if user is not None:
            request.session['username'] = username
            auth.login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid credentials')
            return redirect('signin')
    return render(request, 'signin.html')

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def signup(request):
    if 'username' in request.session:
        return redirect('home')

    if request.method == "POST":
        # Get form data
        username = request.POST['username']
        fname = request.POST['fname']
        lname = request.POST['lname']
        email = request.POST['email']
        phone_number = request.POST['phone_number']
        pass1 = request.POST['password']
        cpassword = request.POST['cpassword']

        # Check if passwords match
        if pass1 != cpassword:
            messages.error(request, 'Passwords do not match')
            return redirect('signup')

        # Check if username or email already exists
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, 'Username taken')
            return redirect('signup')
        # elif CustomUser.objects.filter(email=email).exists():
        #     messages.error(request, 'Email already taken')
        #     return redirect('signup')

        # Create the user
        myuser = CustomUser.objects.create_user(
            username=username,
            first_name=fname,
            last_name=lname,
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

        return redirect('signin')

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
        return redirect('signin')

    # Handle invalid token or user not found
    return render(request, 'verification_failed.html')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def logout(request):
    if 'username' in request.session:
        request.session.flush()
    return redirect('/')

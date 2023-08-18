from django.urls import path
from . import views
urlpatterns = [
    path('signin/',views.signin,name='signin'),
    path('password-login/',views.password_login,name='password-login'),
    path('signup/',views.signup,name='signup'),
    path('logout', views.logout_view,name='logout'),
    path('verify-email/<str:uidb64>/<str:token>/', views.verify_email, name='verify_email'),
    path('verification-mail-sent/',views.verification_mail_sent,name='verification_mail_sent'),
    path('otp-verification/', views.otp_verification, name='otp-verification'),
    path('forgot-password/',views.forgot_password,name='forgot-password'),
    path('reset-password/',views.reset_password,name='reset-password'),
    path('verify-email-fp/<str:uidb64>/<str:token>/', views.forgot_pw_verify_mail, name='verify-email-fp'),
    path('password-reset-success/',views.password_reset_success,name='password-reset-success'),
    path('send-predefined-sms/', views.send_predefined_twilio_message, name='send_predefined_sms'),
]
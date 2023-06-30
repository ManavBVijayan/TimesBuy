from django.urls import path
from . import views
urlpatterns = [
    path('signin/',views.signin,name='signin'),
    path('signup/',views.signup,name='signup'),
    path('logout', views.logout,name='logout'),
    path('verify-email/<str:uidb64>/<str:token>/', views.verify_email, name='verify_email'),
]
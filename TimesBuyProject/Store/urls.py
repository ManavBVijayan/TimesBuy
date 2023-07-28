from django.urls import path
from . import views





urlpatterns = [
    path('',views.home,name='home'),
    path('shop/',views.shop,name='shop'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),


]
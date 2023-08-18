from . import views
from django.urls import path

urlpatterns = [
    path('add-to-cart/<int:variant_id>/', views.add_to_cart, name='add_to_cart'),
    path('view-cart/', views.view_cart, name='view_cart'),
    path('remove-from-cart/', views.remove_from_cart, name='remove_from_cart'),
    path('update-quantity/', views.update_quantity, name='update_quantity'),
    path('checkout/', views.checkout, name='checkout'),
    path('apply-coupon/', views.apply_coupon, name='apply_coupon'),
    path('custom-login/', views.custom_login_view, name='custom_login'),
    path('add-to-wishlist/<int:variant_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('remove-from-wishlist/<int:variant_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('remove-wishlist/<int:wishlist_item_id>/', views.remove_wishlist, name='remove_wishlist'),
    path('add-coupon/', views.add_coupon, name='add_coupon'),
    path('view-coupon/', views.view_coupon, name='view_coupon'),
    path('enable-coupon/<int:coupon_id>/', views.enable_coupon, name='enable_coupon'),
    path('disable-coupon/<int:coupon_id>/', views.disable_coupon, name='disable_coupon'),
    path('edit-coupon/<int:coupon_id>/', views.edit_coupon, name='edit_coupon'),
    path('remove_coupon/', views.remove_coupon, name='remove_coupon'),
    path('remove-applied-coupon/', views.remove_applied_coupon, name='remove_applied_coupon'),
]

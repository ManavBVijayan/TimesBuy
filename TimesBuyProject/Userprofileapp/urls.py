from django.urls import path
from . import views

urlpatterns = [
    path('profile/', views.profile_view, name='profile_view'),
    path('address/', views.show_address, name='show_address'),
    path('address/add/', views.add_address, name='add_address'),
    path('address/edit/<int:address_id>/', views.edit_address, name='edit_address'),
    path('address/delete/<int:address_id>/', views.delete_address, name='delete_address'),
    path('address/choose/<int:address_id>/', views.choose_delivery_address, name='choose_delivery_address'),
    path('view_wallet/', views.view_wallet, name='view_wallet'),
    path('change_password/', views.change_password_view, name='change_password'),
    path('soft_delete_transaction/<int:transaction_id>/', views.soft_delete_transaction, name='soft_delete_transaction'),
]

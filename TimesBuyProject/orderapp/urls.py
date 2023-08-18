from django.urls import path
from . import views

urlpatterns = [
    path('placeorder/<int:add_id>/', views.placeorder, name='placeorder'),
    path('paywallett/<int:add_id>/', views.pay_wallet, name='pay_wallet'),
    path('orders/', views.order_list, name='order-list'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('cancel_order/<int:order_id>/', views.cancel_order, name='cancel_order'),
    path('return_request/<int:order_id>/', views.return_request, name='return_request'),
    path('initiate_payment/', views.initiate_payment, name='initiate_payment'),
    path('online_payment_order/<int:add_id>',views.online_payment_order,name='online_payment_order'),
    path('ordersuccuss/', views.order_success,name='order_success'),
    path('download_invoice/<int:order_id>/', views.download_invoice, name='download_invoice'),
]



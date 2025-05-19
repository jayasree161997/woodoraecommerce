from django.urls import path
from payment import views
from django.contrib import admin


app_name = 'payment'

urlpatterns = [
    path("initiate-payment/", views.initiate_payment, name="initiate_payment"),
    path("payment-success/", views.payment_success, name="payment_success"),
    path("payment-failed/", views.payment_failure, name="payment_failed"),
    # path('razorpay-payment-success/<int:order_id>/', views.razorpay_payment_success, name='razorpay_payment_success'),
   
    
    
]
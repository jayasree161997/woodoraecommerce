from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from .views import CustomPasswordResetConfirmView




urlpatterns = [
    # Example:
    path('', views.index, name='index'),
    path('index/', views.index, name='index'),
    path("signup/", views.signup, name="signup"),
    path("login/",views.user_login,name='login'),
    path("otp_verification/",views.otp_verification,name='otp_verification'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    path('logout/', views.logout_view, name='logout'),  
    path('profile/',views.profile,name="user_profile"),
    path('change_password/', views.change_password, name='change_password'),
    path('add_address/', views.add_address, name='add_Address'),
    path('edit_address/<int:address_id>/', views.edit_address, name='edit_address'),
    path('delete_address/<int:address_id>/', views.delete_address, name='delete_address'),
    path('cart/',views.cart,name='cart'),
    path('checkout/', views.checkout, name='checkoutpage'),
    path('order_confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    path('place_order/', views.place_order, name='place_order'),
    path('my-orders/', views.my_orders, name='my_orders'),
    path('return_order/<int:order_id>/', views.return_order, name='return_order'),
    path('retry-payment/<int:order_id>/', views.retry_payment, name='retry_payment'),
    path("forget-password/", views.custom_password_reset_request, name="password_reset"),
    path("password-reset-sent/", views.custom_password_reset_sent, name="password_reset_done"),
    path("reset-password/<uidb64>/<token>/", views.custom_password_reset_confirm, name="password_reset_confirm"),
    path("password-reset-complete/", views.custom_password_reset_complete, name="password_reset_complete"),
    path('wallet/', views.wallet_view, name='wallet'),
    path('cancel_order/<int:order_id>/', views.cancel_order, name='cancel_order'),
    path('product-offers/', views.product_offers, name='product_offers'),
    path('category-offers/', views.category_offers, name='category_offers'),
    path('referral-offers/', views.referral_offers, name='referral_offers'),
    path('create_order/', views.create_order, name='create_order'),
    path('verify_payment/', views.verify_payment, name='verify_payment'),
    path('order-confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    path('download_invoice/<int:order_id>/', views.download_invoice, name='download_invoice'),
    path('payment-failed/', views.payment_failed, name='payment_failed'),
    path('payment_callback/', views.payment_callback, name='payment_callback'),
    path('create_payment/', views.create_payment, name='create_payment'),
    path('payment/cancel/', views.payment_cancel, name='payment_cancel'),
    path(' google_login_redirect/',views. google_login_redirect,name=' google_login_redirect'),
    # path('create-paypal-payment/', views.create_paypal_payment, name='create_paypal_payment'),
    # path('payment-success/', views.paypal_success, name='payment_success'),
    path('payment-cancel/', views.payment_cancel, name='payment_cancel'),
    path('payment-failure/', views.payment_failure, name='payment_failure'),
    path('cancel_order/<int:order_id>/', views.cancel_order, name='cancel_order'),
    path('order-details/<int:order_id>/', views.view_order_details, name='view_order_details'),
    path('track-order/<int:order_id>/', views.track_order, name='track_order'),
    path('offers/', views.available_offers, name='available_offers'),
    path('reset/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
   
   


]

   

    

    
   
   
     





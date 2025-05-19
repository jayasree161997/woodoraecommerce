from django.urls import path
from . import views
from django.conf import settings



urlpatterns = [
    path('products/',views.products,name='products'),
    path('products_details/<int:product_id>/',views.product_details,name='products_details'),
    path('thumbnails/', views.thumbnail_list, name='thumbnail_list'),
    path('categories/', views.category_list, name='category_list'),
    path('category/<int:category_id>/', views.category_detail, name='category_detail'),
    path('add_to_cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart_detail, name='cart_detail'),
    path('remove_from_cart/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('wishlist/', views.wishlist, name='wishlist'),
    path('wishlist/add/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('move-to-wishlist/<int:product_id>/', views.move_to_wishlist, name='move_to_wishlist'),
    path('cart/', views.cart_page, name='cart_page'),
    path("apply-coupon/", views.apply_coupon, name="apply_coupon"),
    path('remove-coupon/',views. remove_coupon, name='remove_coupon'),
    path('continue-payment/<int:order_id>/', views.continue_payment, name='continue_payment'),
    path('update-cart-quantity/', views.update_cart_quantity, name='update_cart_quantity'),
    path('product/<int:product_id>/purchase/',views.purchase_product, name='purchase_product'),
    path('available-coupons/', views.get_available_coupons, name='available_coupons'),
    path('check_stock_updates/', views.check_stock_updates, name='check_stock_updates'),
    path('cart/remove-unavailable/', views.remove_unavailable_products, name='remove_unavailable_products'),

    
    
]

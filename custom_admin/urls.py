from django.urls import path
from . import views


app_name = 'custom_admin'

urlpatterns = [
    path('', views.signin, name="signin"),
    path('index/', views.index, name='index'),  
    path('home/', views.home, name='home'), 
    path('logout/', views.admin_logout, name='logout'),
    path('users/', views.user_management, name='users'), 
    path('block_unblock_user/', views.block_unblock_user, name='block_unblock_user'),  
    path('products/', views.products_view, name='products_view'), 
    path('products/add/', views.add_product, name='add_products'),  
    path('products/edit/<int:product_id>/', views.edit_product, name='edit_products'),  
    path('products/delete/<int:product_id>/', views.delete_product, name='delete_products'),  
    path('products/<int:product_id>/', views.products_details, name='products_details'), 
    path('productmanagement/',views.productmanagement,name='productmanagement'),
    path('product_view/',views.product_view,name='product_view'),
    path('categories/', views.category_list, name='category_list'),
    path('add_category/', views.add_category, name='add_category'),
    path('edit_category/<int:category_id>/', views.edit_category, name='edit_category'),
    path('delete_category/<int:category_id>/', views.delete_category, name='delete_category'),
    path('add_variant/', views.add_variant, name='add_variant'),
    path('variants/', views.variant_list, name='variant_list'),
    path('order/', views.order_list, name='order_list'),
    path('orders/manage/', views.order_management, name='order_management'),  
    path('orders/change-status/<int:order_id>/<str:status>/', views.change_order_status, name='change_order_status'),
    path('products/<int:product_id>/add_offer/', views.add_offer, name='add_offer'),
    path('products/<int:offer_id>/edit_offer/', views.edit_offer, name='edit_offer'),
    path('products/<int:product_id>/remove_offer/', views.remove_offer, name='remove_offer'),
    path('categories/<int:category_id>/add_offer/', views.add_category_offer, name='add_category_offer'),
    path('offers/<int:offer_id>/edit/', views.edit_category_offer, name='edit_category_offer'),
    path('offers/<int:offer_id>/delete/', views.delete_category_offer, name='delete_category_offer'),
    path('coupon_management/', views.coupon_management, name='coupon_management'), 
    path('add/', views.add_coupon, name='add_coupon'), 
    path('coupons/edit/<int:coupon_id>/', views.edit_coupon, name='edit_coupon'),
    path('coupons/delete/<int:coupon_id>/', views.delete_coupon, name='delete_coupon'),
    path('admin/sales-report/', views.sales_report_view, name='sales_report'),
    path('sales-data/', views.get_sales_data, name='get_sales_data'),
    path('api/sales/', views.get_sales_data, name='get_sales_data'),
    path('ledger/', views.generate_ledger_book, name='generate_ledger_book'),
    path('dashboard/',views.dashboard,name='dashboard'),
    path('sales_report/', views.sales_report_view, name='sales_report'),
    path('download_report/<str:report_type>/', views.download_report, name='download_report'),
    path('order/<int:order_id>/details/', views.view_order_details, name='view_order_details'),
    path('order/<int:order_id>/status/<str:status>/', views.change_order_status, name='change_order_status'),
    path('restore-category/<int:category_id>/', views.restore_category, name='restore_category'),
    path('ajax/check-category/', views.check_category_duplicate, name='check_category_duplicate'),

    
    
   
   
    
]




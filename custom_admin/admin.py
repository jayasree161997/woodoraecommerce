from django.contrib import admin
from django.urls import path

from products. models import Product, ProductVariant,Category,ProductThumbnail,Cart, CartItem,Order,Coupon,ProductOffer, CategoryOffer, ReferralOffer,Sales,OrderItem
from home.models import Profile
from datetime import timedelta, date
from django.utils import timezone
from django.template.response import TemplateResponse
from rangefilter.filters import DateRangeFilter
from . import views
from home.models import Wallet, Transaction
from django.utils.html import format_html


# Register your models here.


admin.site.register(Product)
admin.site.register( ProductVariant)
admin.site.register( ProductThumbnail)
admin.site.register(Category)
admin.site.register(Profile)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Order)
admin.site.register(Coupon)
admin.site.register(ProductOffer)
admin.site.register(CategoryOffer)
admin.site.register(ReferralOffer)
admin.site.register(Sales)
admin.site.register(OrderItem)



class ProductThumbnailAdmin(admin.ModelAdmin):
    list_display = ('alt_text', 'image')  # Display fields in the admin panel
    search_fields = ('alt_text',)

class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']

class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'variant_name', 'variant_value')
    list_filter = ('product',)
    search_fields = ('variant_name', 'variant_value')

class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "mobile_number") 
    search_fields = ("user__username", "mobile_number") 
    list_filter = ("user",)


class CartAdmin(admin.ModelAdmin):
    list_display = ('user',)  


class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'product', 'quantity')  
    list_filter = ('cart', 'product')  
    search_fields = ('product__name',) 
    list_filter = (DateRangeFilter)



class OrderAdmin(admin.ModelAdmin):
    readonly_fields = ['razorpay_order_id', 'razorpay_payment_id']
    list_display = ['id', 'user', 'address', 'total_price', 'payment_method', 'created_at','payment_status','razorpay_payment_id','delivery_date']
    list_filter = ['payment_method', 'created_at',('created_at', DateRangeFilter) ]
    search_fields = ['user__username', 'address__street']
    actions = ['approve_return']

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('sales-report/', self.admin_site.admin_view(self.sales_report_view)),
            path('get-sales-data/', self.admin_site.admin_view(views.get_sales_data))
        ]
        return custom_urls + urls
    
    
    def approve_return(self, request, queryset):
        """Admin action to approve return and process refunds."""
        for order in queryset:
            if order.status == "Return Completed":
                self.process_refund(order)

        self.message_user(request, " Selected orders have been marked as returned and refunded.")

    def refund_status(self, obj):
        """Displays refund status in the admin panel."""
        refund = Transaction.objects.filter(wallet__user=obj.user, transaction_type="refund", amount=obj.total_price).exists()
        return format_html('<span style="color:green;"> Refunded</span>' if refund else '<span style="color:red;"> Not Refunded</span>')

    refund_status.short_description = "Refund Status"


 

    def sales_report_view(self, request):
        orders = Order.objects.all()
        total_sales = sum(order.total_price for order in orders)
        total_discount = sum(order.discount_amount for order in orders)
        total_coupons = sum(order.discount_amount for order in orders if order.coupon_code)

        context = {
            'total_sales': total_sales,
            'total_discount': total_discount,
            'total_coupons': total_coupons,
        }
        return TemplateResponse(request, 'admin/sales_report.html',context )


class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount', 'valid_from', 'valid_until', 'usage_limit', 'active']
    search_fields = ['code']
    list_filter = ['active', 'valid_from', 'valid_until']
    # filter_horizontal = ['products', 'categories']


class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'stock','stock_status')
    filter_horizontal = ('coupons',)




class ProductOfferAdmin(admin.ModelAdmin):
    list_display = ('product', 'discount_amount', 'start_date', 'end_date', 'offer_type')

    def save_model(self, request, obj, form, change):
        obj.full_clean()  # this will trigger the clean() method inside the model
        super().save_model(request, obj, form, change)


class CategoryOfferAdmin(admin.ModelAdmin):
    list_display = ('category', 'discount_percentage', 'start_date', 'end_date', 'offer_type')

    def save_model(self, request, obj, form, change):
        obj.full_clean()  # triggers the clean() method inside the model
        super().save_model(request, obj, form, change)


class ReferralOfferAdmin(admin.ModelAdmin):
    list_display = ('referrer', 'referred', 'discount_amount', 'status')



class DateRangeFilter(admin.SimpleListFilter):
    title = 'date range'
    parameter_name = 'date_range'

    def lookups(self, request, model_admin):
        return (
            ('1_day', '1 Day'),
            ('1_week', '1 Week'),
            ('1_month', '1 Month'),
            ('custom', 'Custom Date Range'),
        )

    def queryset(self, request, queryset):
        today = timezone.now().date()
        if self.value() == '1_day':
            return queryset.filter(created_at__gte=today - timedelta(days=1))
        elif self.value() == '1_week':
            return queryset.filter(created_at__gte=today - timedelta(weeks=1))
        elif self.value() == '1_month':
            return queryset.filter(created_at__gte=today - timedelta(weeks=4))
        elif self.value() == 'custom':
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            if start_date and end_date:
                start_date = date.fromisoformat(start_date)
                end_date = date.fromisoformat(end_date)
                return queryset.filter(created_at__range=[start_date, end_date])
        return queryset
    





class SalesAdmin(admin.ModelAdmin):
    list_display = ('product', 'date', 'amount')



class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity', 'order')
    ordering = ('-quantity',)
from django.utils.deprecation import MiddlewareMixin
from .models import Coupon

class CouponMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if 'coupon_id' in request.session:
            try:
                coupon = Coupon.objects.get(id=request.session['coupon_id'])
                request.coupon = coupon
            except Coupon.DoesNotExist:
                request.coupon = None
        else:
            request.coupon = None
        response = self.get_response(request)
        return response
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render

# Custom error views
def custom_bad_request(request, exception):
    return render(request, 'user/404.html', status=404)

def custom_server_error(request):
    return render(request, 'user/500.html', status=500)

# URL patterns
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('home.urls')),
    path('products/', include('products.urls')),
    path('accounts/', include('allauth.urls')),
    path('custom_admin/', include('custom_admin.urls')),
    path('payment/', include('payment.urls', namespace='payment')),
]

# Media file serving in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Error handlers (must be at module level)
handler404 = 'Ecommerce.urls.custom_bad_request'
handler500 = 'Ecommerce.urls.custom_server_error'
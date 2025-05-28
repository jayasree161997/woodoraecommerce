from django.shortcuts import render,get_list_or_404
from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404
from products.models import Product,ProductVariant,Category,Order, ProductOffer,CategoryOffer,Coupon,Sales,Order,OrderItem
from django.contrib.auth import authenticate, login
# from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
User = get_user_model()
from django.contrib import messages
from django.contrib.auth.decorators import login_required,user_passes_test
from django.views.decorators.cache import cache_control
from django.db.models import Q
from custom_admin.forms import ProductForm,CategoryForm,ProductVariantForm,ProductOfferForm,CategoryOfferForm
from home.forms import UserUpdateForm, ProfileUpdateForm
from datetime import datetime, timedelta
from django.urls import reverse
from .forms import CouponForm
from django.utils import timezone
from django.core.paginator import Paginator
import io
from django.core.cache import cache
from django.utils.dateparse import parse_date
import xlsxwriter
from django.contrib.auth import logout
from reportlab.pdfgen import canvas
from django.http import HttpResponse,JsonResponse
from django.db.models import Sum,Count
import json
from django.views.decorators.csrf import csrf_exempt

import logging
from django.contrib.auth.decorators import user_passes_test, login_required
from functools import wraps


from django.db.models.functions import TruncMonth, TruncYear
from datetime import datetime, timedelta
from products.models import Category 
from home.models import Address
from django.utils.timezone import now
from collections import Counter
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from django.utils.timezone import make_aware
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.views.decorators.cache import never_cache

User = get_user_model()







def superuser_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login') 
        if not request.user.is_superuser:
            return redirect('login')  
        return view_func(request, *args, **kwargs)
    return _wrapped_view


# Create your views here 

@never_cache
def signin(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_superuser:
                login(request, user)
                return redirect('custom_admin:index')  
            else:
                messages.error(request, 'You do not have permission to access the admin panel.')
                return redirect('custom_admin:signin')  
            
       
        messages.error(request, 'Invalid credentials.')
        return redirect('custom_admin:signin')  
    
    return render(request, 'custom_admin/signin.html')


@login_required
def admin_logout(request):
    logout(request)
    return redirect('custom_admin:signin')


@superuser_required
@login_required
def home(request):
    return render(request, 'home.html') 


@superuser_required
@login_required
def products_view(request):
    query = request.GET.get('query', '')
    
    if query:
        # products = Product.objects.filter(name__icontains=query)
        products = Product.objects.filter(name__icontains=query, is_deleted=False, is_active=True).order_by('-created_at')

    else:
        # products = Product.objects.all()
        products = Product.objects.filter(is_deleted=False, is_active=True).order_by('-created_at')

    inactive_products = Product.objects.filter(is_active=False).order_by('-created_at')
    
    context = {
        'products': products,
        'query': query,
        'inactive_products': inactive_products,

    }
    return render(request, 'custom_admin/products_view.html', context)



@superuser_required
@login_required
def products_details(request, product_id):
    try:
        product = Product.objects.get(id=product_id, is_deleted=False)
    except Product.DoesNotExist:
        return render(request, 'user/404.html', status=404)  
    return render(request, 'user/products_details.html', {'product': product})



@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required
def index(request):
    return render(request,'custom_admin/index.html') 




def superuser_required(view_func):
    decorated_view_func = user_passes_test(
        lambda u: u.is_superuser,
        login_url='custom_admin:signin'  
    )(view_func)
    return decorated_view_func



# @login_required
# def toggle_product_status(request, product_id):
#     product = get_object_or_404(Product, id=product_id)
#     product.is_active = not product.is_active
#     product.save()
#     return redirect('custom_admin:products_view')  



@superuser_required
@login_required
def user_management(request):
    query = request.GET.get('search', '')  
    if query:
        users = User.objects.exclude(is_superuser=True).filter(
            Q(username__icontains=query) | Q(email__icontains=query)  
        )
    else:
        users = User.objects.exclude(is_superuser=True)  

    return render(request, 'custom_admin/users.html', {
        'users': users,
        'search_query': query,  
    })

@superuser_required
@login_required
def block_unblock_user(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        action = request.POST.get('action')
        
        try:
            user = User.objects.get(id=user_id)
            if action == 'block':
                user.is_active = False
                messages.success(request, f'User {user.username} has been blocked.')
            elif action == 'activate':
                user.is_active = True
                messages.success(request, f'User {user.username} has been activated.')
            user.save()
        except User.DoesNotExist:
            messages.error(request, 'User does not exist.')
    
    return redirect('custom_admin:users')



@superuser_required
@login_required
def edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    profile = user.profile  

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, f"User {user.username} updated successfully.")
            return redirect('custom_admin:users')

    else:
        user_form = UserUpdateForm(instance=user)
        profile_form = ProfileUpdateForm(instance=profile)

    return render(request, 'custom_admin/edit_user.html', {
        'user_form': user_form,
        'profile_form': profile_form,
    })





@superuser_required
@login_required
def add_product(request):
    print("Request Method:", request.method)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        print("POST data:", request.POST)
        print("FILES data:", request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Product added successfully!")
            print("Form is valid")
            return redirect('custom_admin:products_view')  
        else:
            print("Form errors:", form.errors)
    else:
        form = ProductForm()
    return render(request, 'custom_admin/add_product.html', {'form': form})



@superuser_required
@login_required
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "Product updated successfully!")
            return redirect('custom_admin:products_view')  # Adjust URL as needed
        else:
            print(form.errors)

    else:
        form = ProductForm(instance=product)
    return render(request, 'custom_admin/edit_product.html', {'form': form})


@superuser_required
@login_required

# def delete_product(request, product_id):
#     try:
#         product = Product.objects.get(id=product_id)
#     except Product.DoesNotExist:
#         messages.error(request, "Product not found.")
#         return redirect('custom_admin:products_view')  # Redirect to list page

#     if request.method == 'POST':
#         product.delete()
#         messages.success(request, "Product deleted successfully.")
#         return redirect('custom_admin:products_view')  # Redirect after delete

#     return render(request, 'custom_admin/delete_product.html', {'product': product})
def delete_product(request, product_id):
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        messages.error(request, "Product not found.")
        return redirect('custom_admin:products_view')

    if request.method == 'POST':
        product.is_active = False
        product.is_deleted = True
        product.save()
        messages.success(request, "Product soft-deleted successfully.")
        return redirect('custom_admin:products_view')

    return render(request, 'custom_admin/delete_product.html', {'product': product})



def restore_product(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id, is_active=False)
        product.is_active = True
        product.is_deleted = False
        product.save()
        messages.success(request, "Product restored successfully!")
        print(f"Restored Product: {product.id}, is_active: {product.is_active}")
    else:
        messages.error(request, "Invalid request method.")
    return redirect('custom_admin:products_view')


@superuser_required


@superuser_required
@login_required
def productmanagement(request):
    products = Product.objects.all()
    return render(request,'custom_admin/productmanagement.html', {'products': products})


@superuser_required
@login_required
def product_view(request):
    return render(request,'custom_Admin/products_view.html')

@superuser_required
@login_required
def category_list(request):
    active_categories = Category.objects.filter(is_active=True)
    inactive_categories = Category.objects.filter(is_active=False)
    return render(request, 'custom_admin/category_list.html', {
        'categories': active_categories,
        'inactive_categories': inactive_categories,
    })


@superuser_required
@login_required
def add_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category_name = form.cleaned_data['name'].strip()

            # Case-insensitive duplicate check
            if Category.objects.filter(name__iexact=category_name).exists():
                messages.error(request, "Category with this name already exists (case-insensitive check).")
                return redirect('custom_admin:add_category')

            # If no duplicate, save
            form.save()
            messages.success(request, "Category added successfully!")
            return redirect('custom_admin:category_list')
    else:
        form = CategoryForm()
    return render(request, 'custom_admin/add_category.html', {'form': form})



@login_required
def check_category_duplicate(request):
    category_name = request.GET.get('name', '').strip()
    exists = Category.objects.filter(name__iexact=category_name).exists()
    return JsonResponse({'exists': exists})




@login_required
def edit_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            new_name = form.cleaned_data['name'].strip()

            # Check for duplicates (excluding the current category)
            if Category.objects.filter(name__iexact=new_name).exclude(id=category_id).exists():
                messages.error(request, "Category with this name already exists (case-insensitive check).")
                return redirect('custom_admin:edit_category', category_id=category_id)

            form.save()
            messages.success(request, "Category updated successfully!")
            return redirect('custom_admin:category_list')
    else:
        form = CategoryForm(instance=category)
    
    return render(request, 'custom_admin/edit_category.html', {'form': form})

@login_required
def delete_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        category.is_active = False  # Soft delete
        category.save()
        messages.success(request, "Category deleted successfully!")
        return redirect('custom_admin:category_list')
    return render(request, 'custom_admin/delete_category.html', {'category': category})

def restore_category(request, category_id):
    category = get_object_or_404(Category, id=category_id, is_active=False)
    category.is_active = True
    category.save()
    messages.success(request, "Category restored successfully!")
    return redirect('custom_admin:category_list')



def add_variant(request):
    if request.method == 'POST':
        form = ProductVariantForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Variant added successfully!")
            return redirect('custom_admin:variant_list')
    else:
        form = ProductVariantForm()
    return render(request, 'custom_admin/add_variant.html', {'form': form})

def variant_list(request):
    variants = ProductVariant.objects.all()
    return render(request, 'custom_admin/variant_list.html', {'variants': variants})




@login_required
def order_list(request):
    orders = Order.objects.all().select_related('user', 'address')
    return render(request, 'custom_admin/order_management.html', {'orders': orders})

@login_required
def order_management(request):
    orders = Order.objects.all().select_related('user', 'address').prefetch_related('order_items__product').order_by('-created_at')
    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    orders = paginator.get_page(page_number)
    return render(request, 'custom_admin/order_management.html', {'orders': orders})




@login_required
def view_order_details(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    # Ensure transaction ID is correctly fetched
    transaction_id = None
    if order.payment_method == "RAZORPAY":
        transaction_id = order.razorpay_payment_id
    elif order.payment_method == "PAYPAL":
        transaction_id = order.paypal_transaction_id

    return render(request, 'custom_admin/order_details.html', {'order': order, 'transaction_id': transaction_id})


@login_required

def change_order_status(request, order_id, status):
    order = get_object_or_404(Order, id=order_id)

    if order.payment_method == 'RAZORPAY' and order.payment_status == 'Pending':
        messages.error(request, "This online payment isn't completed.")
        return redirect('custom_admin:order_management')


    # Prevent changes if the order is already cancelled
    if order.status == "Cancelled":
        messages.error(request, "This order was already cancelled. Status cannot be changed.")
        return redirect('custom_admin:order_management')

    # return request process
    if status == "Return Requested":
        if order.status == "Delivered":
            order.status = "Return Requested"
            order.save()
            messages.success(request, f"Return request placed for Order {order.id}.")
        else:
            messages.error(request, "Only delivered orders can be requested for return.")
        return redirect('custom_admin:order_management')

    elif status == "Return Accepted":
        if order.status == "Return Requested":
            order.status = "Return Accepted"
            order.save()
            messages.success(request, f"Return accepted for Order {order.id}.")
        else:
            messages.error(request, "Order must be in 'Return Requested' status to accept a return.")
        return redirect('custom_admin:order_management')

    elif status == "Return Rejected":
        if order.status == "Return Requested":
            order.status = "Return Rejected"
            order.save()
            messages.success(request, f"Return rejected for Order {order.id}.")
        else:
            messages.error(request, "Order must be in 'Return Requested' status to reject a return.")
        return redirect('custom_admin:order_management')

    elif status == "Return Completed":
        if order.status == "Return Accepted":
            order.status = "Return Completed"
            order.save()
            messages.success(request, f"Return process completed for Order {order.id}.")
        else:
            messages.error(request, "Order must be in 'Return Accepted' status to complete the return.")
        return redirect('custom_admin:order_management')

    
    if status in ["Processing", "Delivered", "Cancelled"]:
        order.status = status
        order.save()
        messages.success(request, f"Order status changed to {status}.")
    else:
        messages.error(request, "Invalid status update.")

    return redirect('custom_admin:order_management')



@login_required
def add_offer(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        form = ProductOfferForm(request.POST)
        if form.is_valid():
            offer = form.save(commit=False)
            offer.product = product
            try:
                offer.full_clean()  
                offer.save()
                messages.success(request, f'Offer added to {product.name}.')
                return redirect('custom_admin:products_view')
            except ValidationError as e:
                form.add_error(None, e) 
    else:
        form = ProductOfferForm(initial={'product': product})
    return render(request, 'custom_admin/add_offer.html', {'form': form, 'product': product})


@login_required
def edit_offer(request, offer_id):
    offer = get_object_or_404(ProductOffer, id=offer_id)
    if request.method == 'POST':
        form = ProductOfferForm(request.POST, instance=offer)
        if form.is_valid():
            updated_offer = form.save(commit=False)
            try:
                updated_offer.full_clean()
                updated_offer.save()
                messages.success(request, f'Offer for {updated_offer.product.name} updated.')
                return redirect('custom_admin:products_view')
            except ValidationError as e:
                form.add_error(None, e)
    else:
        form = ProductOfferForm(instance=offer)
    return render(request, 'custom_admin/edit_offers.html', {'form': form, 'offer': offer})



@login_required
def remove_offer(request, product_id):
    offers = ProductOffer.objects.filter(product_id=product_id)
    
    if not offers.exists():
        messages.error(request, 'No offers found for the specified product.')
        return redirect('custom_admin:products_view')
    
    product_name = offers.first().product.name  
    for offer in offers:
        offer.delete()
    
    messages.info(request, f'All offers removed from {product_name}.')
    return redirect('custom_admin:products_view')

@login_required
def add_category_offer(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        form = CategoryOfferForm(request.POST)
        if form.is_valid():
            offer = form.save(commit=False)
            offer.category = category  # Assign the offer to the category
            offer.save()
            messages.success(request, f'Offer added to {category.name}.')
            return redirect('custom_admin:category_list')
    else:
        form = CategoryOfferForm(initial={'category': category})
    return render(request, 'custom_admin/add_category_offer.html', {'form': form, 'category': category})


@login_required
def edit_category_offer(request, offer_id):
    offer = get_object_or_404(CategoryOffer, id=offer_id)
    
    if request.method == 'POST':
        form = CategoryOfferForm(request.POST, instance=offer)
        if form.is_valid():
            form.save()
            return redirect('category_list') 
    else:
        form = CategoryOfferForm(instance=offer)

    return render(request, 'custom_admin/edit_category_offer.html', {'form': form, 'offer': offer})





@login_required
def delete_category_offer(request, offer_id):
    offer = get_object_or_404(CategoryOffer, id=offer_id)
    
    if request.method == 'POST':
        # For debugging
        print("Deleting offer:", offer.id)
        offer.delete()
        return redirect('custom_admin:category_list') 
    return render(request, 'custom_admin/delete_category_offer.html', {'offer': offer})


@login_required
def coupon_management(request):
    coupons = Coupon.objects.all() 
    return render(request, 'custom_admin/coupon_management.html', {'coupons': coupons})

@login_required
def apply_coupon(request):
    now = timezone.now()
    form = CouponForm(request.POST or None)
    if form.is_valid():
        code = form.cleaned_data['code']
        try:
            coupon = Coupon.objects.get(code=code, valid_from__lte=now, valid_until__gte=now, active=True)
            if coupon.usage_limit > 0:
                request.session['coupon_id'] = coupon.id
                messages.success(request, f"Coupon '{coupon.code}' applied successfully!")
                coupon.usage_limit -= 1
                coupon.save()
                return redirect('cart_detail') 
            else:
                form.add_error('code', 'This coupon has reached its usage limit.')
        except Coupon.DoesNotExist:
            form.add_error('code', 'This coupon does not exist or is not valid.')
    return render(request, 'custom_admin/apply_coupon.html', {'form': form})




def remove_coupon(request):
    if 'coupon_id' in request.session:
        del request.session['coupon_id']
    return redirect('cart_detail') 



@login_required
def add_coupon(request):
    if request.method == 'POST':
        form = CouponForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Coupon added successfully.')
            return redirect('custom_admin:coupon_management')
    else:
        form = CouponForm()
    return render(request, 'custom_admin/add_coupon.html', {'form': form})



def is_staff(user):
    return user.is_staff
@login_required
@user_passes_test(is_staff)
def edit_coupon(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)
    if request.method == "POST":
        form = CouponForm(request.POST, instance=coupon)
        if form.is_valid():
            form.save()
            messages.success(request, "Coupon updated successfully.")
            return redirect('custom_admin:coupon_management')
    else:
        form = CouponForm(instance=coupon)
    return render(request, 'custom_admin/edit_coupon.html', {'form': form, 'coupon': coupon})

@login_required
@user_passes_test(is_staff)
def delete_coupon(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)
    if request.method == "POST":
        coupon.delete()
        messages.success(request, "Coupon deleted successfully.")
        return redirect('custom_admin:coupon_management')
    return render(request, 'custom_admin/delete_coupon.html', {'coupon': coupon})




def generate_pdf(context):
    buffer = io.BytesIO()
    pdf = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph("Sales Report", styles["Title"]))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph(f"Report Date Range: {context['start_date']} to {context['end_date']}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    summary_data = [
        ["Total Sales:", f"₹{context['total_sales']}"],
        ["Total Discounts:", f"₹{context['total_discount']}"],
        ["Total Coupons Deduction:", f"₹{context['total_coupons']}"]
    ]
    summary_table = Table(summary_data, colWidths=[200, 200])
    summary_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold')
    ]))

    elements.append(summary_table)
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("Products Sold:", styles["Heading2"]))
    elements.append(Spacer(1, 12))

    table_data = [["Product Name", "Quantity Sold"]]
    for product in context['sold_products']:
        table_data.append([product['name'], product['quantity_sold']])

    table = Table(table_data, colWidths=[400, 100])
    table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold')
    ]))

    elements.append(table)
    pdf.build(elements)
    buffer.seek(0)
    return buffer



def generate_excel(context):
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet()

    bold = workbook.add_format({'bold': True})

    worksheet.write('A1', 'Report Date Range', bold)
    worksheet.write('B1', f"{context['start_date']} to {context['end_date']}")

    worksheet.write('A3', 'Metric', bold)
    worksheet.write('B3', 'Amount', bold)

    data = [
        ("Total Sales", context['total_sales']),
        ("Total Discounts", context['total_discount']),
        ("Total Coupons Deduction", context['total_coupons']),
    ]

    row = 3
    for metric, amount in data:
        row += 1
        worksheet.write(row, 0, metric)
        worksheet.write(row, 1, amount)

    row += 2
    worksheet.write(row, 0, 'Products Sold', bold)
    row += 1
    worksheet.write(row, 0, 'Product Name', bold)
    worksheet.write(row, 1, 'Quantity Sold', bold)

    for product in context['sold_products']:
        row += 1
        worksheet.write(row, 0, product['name'])
        worksheet.write(row, 1, product['quantity_sold'])

    workbook.close()
    output.seek(0)
    return output




@login_required
def sales_report_view(request):
    today = datetime.today().date()
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    filter_option = request.GET.get('filter_option')

    # Start with delivered orders
    orders = Order.objects.filter(status='Delivered')

    # Determine the date filters based on filter_option
    if filter_option == 'daily':
        orders = orders.filter(created_at__date=today)
        start_date_display = end_date_display = today.strftime("%d-%m-%Y")
    elif filter_option == 'weekly':
        start_week = today - timedelta(days=today.weekday())
        end_week = start_week + timedelta(days=6)
        orders = orders.filter(created_at__date__range=[start_week, end_week])
        start_date_display = start_week.strftime("%d-%m-%Y")
        end_date_display = end_week.strftime("%d-%m-%Y")
    elif filter_option == 'yearly':
        start_year = datetime(today.year, 1, 1).date()
        end_year = datetime(today.year, 12, 31).date()
        orders = orders.filter(created_at__date__range=[start_year, end_year])
        start_date_display = start_year.strftime("%d-%m-%Y")
        end_date_display = end_year.strftime("%d-%m-%Y")
    elif filter_option == 'custom' and start_date and end_date:
        orders = orders.filter(created_at__date__range=[start_date, end_date])
        try:
            start_date_display = datetime.strptime(start_date, "%Y-%m-%d").strftime("%d-%m-%Y")
            end_date_display = datetime.strptime(end_date, "%Y-%m-%d").strftime("%d-%m-%Y")
        except ValueError:
            start_date_display = end_date_display = "Invalid Date"
    else:
        start_date_display = end_date_display = "Not specified"

    # Filter only non-returned items
    order_items = OrderItem.objects.filter(order__in=orders, returned=False)

    product_counter = Counter()
    total_sales = 0
    total_discount = 0
    total_coupons = 0

    for item in order_items:
        product_counter[item.product] += item.quantity
        total_sales += item.total_price
        total_discount += item.discount_amount
        if item.order.coupon_code:
            total_coupons += item.discount_amount

    sold_products = [
        {
            'name': product.name,
            'image': product.main_image.url if product.main_image and hasattr(product.main_image, 'url') else None,
            'quantity_sold': quantity
        }
        for product, quantity in product_counter.items()
    ]

    context = {
        'total_sales': total_sales,
        'total_discount': total_discount,
        'total_coupons': total_coupons,
        'filter_option': filter_option,
        'start_date': start_date,
        'end_date': end_date,
        'start_date_display': start_date_display,
        'end_date_display': end_date_display,
        'sold_products': sold_products
    }

    # Download logic
    if 'download' in request.GET:
        report_type = request.GET.get('download')
        return download_report(request, report_type, context)

    return render(request, 'custom_admin/salesReport.html', context)





def download_report(request, report_type, context):
    if report_type == "pdf":
        pdf_file = generate_pdf(context)
        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="sales_report.pdf"'
        return response

    elif report_type == "excel":
        excel_file = generate_excel(context)
        response = HttpResponse(excel_file, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="sales_report.xlsx"'
        return response

    return HttpResponse("Invalid report type", status=400)




@login_required
def get_sales_data(request):
    filter_option = request.GET.get('filter_option', 'yearly')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    labels = []
    values = []

    today = datetime.now().date()

    if filter_option == 'yearly':
        data = Sales.objects.filter(date__year=today.year).values('date__month').annotate(
            total_sales=Sum('amount')
        ).order_by('date__month')
        labels = [str(entry['date__month']) for entry in data]
        values = [entry['total_sales'] for entry in data]

    elif filter_option == 'daily':
        # Daily = today's data
        data = Sales.objects.filter(date__date=today).values('date__hour').annotate(
            total_sales=Sum('amount')
        ).order_by('date__hour')
        labels = [str(entry['date__hour']) for entry in data]
        values = [entry['total_sales'] for entry in data]

    elif filter_option == 'weekly':
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        data = Sales.objects.filter(date__date__range=[start_of_week, end_of_week]).values('date__date').annotate(
            total_sales=Sum('amount')
        ).order_by('date__date')
        labels = [entry['date__date'].strftime('%Y-%m-%d') for entry in data]
        values = [entry['total_sales'] for entry in data]

    elif filter_option == 'custom' and start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1)  # inclusive end date

            data = Sales.objects.filter(date__range=[start_date, end_date]).values('date__date').annotate(
                total_sales=Sum('amount')
            ).order_by('date__date')

            labels = [entry['date__date'].strftime('%Y-%m-%d') for entry in data]
            values = [entry['total_sales'] for entry in data]
        except Exception as e:
            print("Invalid custom range:", e)

    return JsonResponse({'labels': labels, 'values': values})






@login_required
def generate_ledger_book(request):
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="ledger_book.pdf"'

    p = canvas.Canvas(response)
    p.drawString(100, 800, "Ledger Book")
   
    p.showPage()
    p.save()
    
    return response




@login_required
def dashboard(request):
    filter_type = request.GET.get('filter', 'yearly')

    if filter_type == 'yearly':
        date_from = datetime(datetime.now().year, 1, 1)
    elif filter_type == 'monthly':
        date_from = datetime(datetime.now().year, datetime.now().month, 1)
    else:
        date_from = None

    # ✅ Best-selling products: Delivered only, exclude returned and cancelled
    top_selling_products_query = OrderItem.objects.filter(
        order__status='Delivered',
        returned=False,
        order__created_at__gte=date_from if date_from else datetime(2000, 1, 1)
    )

    top_selling_products = list(
        top_selling_products_query
        .values('product__name')
        .annotate(total_sold=Sum('quantity'))
        .order_by('-total_sold')[:5]
    )

    # ✅ Best-selling categories: Only from delivered orders, not returned
    top_selling_categories_query = Category.objects.annotate(
        total_sold=Sum(
            'products__order_products__quantity',
            filter=Q(products__order_products__order__status='Delivered') &
                   Q(products__order_products__returned=False) &
                   (Q(products__order_products__order__created_at__gte=date_from) if date_from else Q())
        )
    ).values('name', 'total_sold').order_by('-total_sold')[:5]

    top_selling_categories = list(top_selling_categories_query)

    context = {
        'top_selling_products': json.dumps(top_selling_products),
        'top_selling_categories': json.dumps(top_selling_categories),
        'filter_type': filter_type
    }

    return render(request, 'custom_admin/dashboard.html', context)




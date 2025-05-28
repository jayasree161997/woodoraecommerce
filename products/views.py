from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.shortcuts import render, get_object_or_404
from .models import Product,Wishlist
from products.models import Product,ProductVariant,Category,ProductThumbnail, ProductOffer, CategoryOffer
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required,permission_required
from .models import Product, Cart, CartItem,Coupon,Order
from django.utils import timezone
from custom_admin.forms import CouponForm
from .forms import CouponApplyForm
from django.contrib import messages
from django.http import JsonResponse
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now
from datetime import date
from decimal import Decimal
import traceback




@login_required
def products(request):
    category_id = request.GET.get('category_id')
    sort_option = request.GET.get('sort')
    search_query = request.GET.get('search', '').strip()

    
    # products = Product.objects.filter(is_active=True, category__is_active=True).order_by('id')
    products = Product.objects.filter(is_active=True, category__is_active=True).order_by('-id')
 

    if category_id:
        category = get_object_or_404(Category, id=category_id, is_active=True)
        products = products.filter(category=category)


    # Apply search filter
    if search_query:
        products = products.filter(name__icontains=search_query)

    # Apply sorting
    if sort_option == 'price_low_to_high':
        products = products.order_by('price')
    elif sort_option == 'price_high_to_low':
        products = products.order_by('-price')
    elif sort_option == 'name_asc':
        products = products.order_by('name')
    elif sort_option == 'name_desc':
        products = products.order_by('-name')
    else:
        products = products.order_by('-id') 

    # Pagination
    paginator = Paginator(products, 9)
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)

    # categories = Category.objects.all()
    categories = Category.objects.filter(is_active=True)


    return render(request, 'user/products.html', {
        'products': products,
        'categories': categories,
        'selected_category': category_id,
        'selected_sort': sort_option,
        'search_query': search_query
    })


@login_required
def product_details(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True, category__is_active=True)
    variants = ProductVariant.objects.filter(product=product)
    related_products = Product.objects.filter(category=product.category,is_active=True).exclude(id=product.id)[:6]

    now = timezone.now()
    offer_price = None
    discount_percentage = 0

    # Product Offer
    product_offer = ProductOffer.objects.filter(
        product=product,
        start_date__lte=now,
        end_date__gte=now
    ).first()

    # Category Offer
    category_offer = CategoryOffer.objects.filter(
        category=product.category,
        start_date__lte=now,
        end_date__gte=now
    ).first()

    # Calculate best discount
    original_price = product.price
    if product_offer:
        offer_price = original_price - product_offer.discount_amount
        discount_percentage = (product_offer.discount_amount / original_price) * 100
    elif category_offer:
        discount_amount = (category_offer.discount_percentage / 100) * original_price
        offer_price = original_price - discount_amount
        discount_percentage = category_offer.discount_percentage

    context = {
        'product': product,
        'variants': variants,
        'related_products': related_products,
        'is_out_of_stock': product.stock == 0,
        'offer_price': round(offer_price, 2) if offer_price else None,
        'original_price': original_price,
        'discount_percentage': round(discount_percentage, 2) if discount_percentage else None,
    }
    return render(request, 'user/products_details.html', context)



@login_required
def product_view(request):
    products = Product.objects.all()
    return render(request, 'custom_admin/product_view.html', {'products': products})


def thumbnail_list(request):
    thumbnails = ProductThumbnail.objects.all()
    return render(request, "thumbnails.html", {"thumbnails": thumbnails})


def category_list(request):
    # categories = Category.objects.all()
    categories = Category.objects.filter(is_active=True)

    return render(request, 'custom_Admin/category_list.html', {'categories': categories})



def category_detail(request, category_id):
    category = get_object_or_404(Category, id=category_id, is_active=True)
    products = Product.objects.filter(category=category)
    return render(request, 'user/category_detail.html', {'category': category, 'products': products})



@login_required
def add_to_cart(request, product_id):
    # if not request.user.is_authenticated:
    #     return redirect('login')
    
    product = get_object_or_404(Product, id=product_id)

    if product.stock == 0:
        return redirect('cart_detail')  

   
    now = timezone.now()
    offer_price = product.price  

    # Check for Product Offer
    product_offer = ProductOffer.objects.filter(
        product=product, start_date__lte=now, end_date__gte=now
    ).first()

    if product_offer:
        offer_price -= product_offer.discount_amount
        if offer_price < 0:  # Prevent negative price
            offer_price = 0
    else:
        # Check for Category Offer if no product offer is found
        category_offer = CategoryOffer.objects.filter(
            category=product.category, start_date__lte=now, end_date__gte=now
        ).first()
        if category_offer:
            offer_price -= (category_offer.discount_percentage / 100) * product.price
            if offer_price < 0:  # Prevent negative price
                offer_price = 0

    # Get or create the cart for the user
    cart, created = Cart.objects.get_or_create(user=request.user)

    # Get or create the cart item for the product and ensure the price is set when creating
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart, product=product,
        defaults={'price': round(offer_price, 2)}  # Ensure price is set on creation
    )

    # If cart item already exists, update the quantity and recalculate price
    if not created:
        max_quantity_per_person = 5
        # Ensure quantity does not exceed stock or max allowed per person
        new_quantity = min(cart_item.quantity + 1, product.stock, max_quantity_per_person)
        cart_item.quantity = new_quantity
        
       
        cart_item.price = round(offer_price, 2)


    # Save the cart item with the updated price and quantity
    cart_item.save()  # Save the cart item

    # Redirect to the cart detail page
    return redirect('cart_detail')


def cart_detail(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = CartItem.objects.filter(cart=cart)



    if not cart_items.exists():
        request.session.pop('coupon_id', None)
        request.session.pop('applied_coupon', None)
        cart.coupon_code = ''
        cart.discount_amount = 0
        cart.save()

    # Update stock dynamically
    updated_items = []
    unavailable_items = [] 


    for item in cart_items:
        product = item.product
        category_active = product.category.is_active if product.category else True

        # if not item.product.category.is_active:
        # if not (product.is_active and category_active and product.stock > 0):
        #     unavailable_items.append(item)

        # elif item.product.stock == 0:
        #     unavailable_items.append(item)
        if product.is_deleted or not (product.is_active and category_active and product.stock > 0):
            unavailable_items.append(item)

        else:
            item.quantity = min(item.quantity, item.product.stock)
            item.save()
            updated_items.append(item)
        

    # Re-fetch updated items
    total_after_offer = sum(item.quantity * item.price for item in updated_items)
    total_items = sum(item.quantity for item in updated_items)

    coupon_form = CouponApplyForm(request.POST or None)
    discount_amount = 0
    

    # Handle coupon discounts
    coupon_id = request.session.get("coupon_id")
    if coupon_id and not cart.coupon_code and total_after_offer >= 30000 :
        try:
            
            coupon = Coupon.objects.get(
                id=coupon_id,
                valid_from__lte=timezone.now(),
                valid_until__gte=timezone.now(),
                usage_limit__gt=0
                
            )
            discount_amount = (coupon.discount / 100) * total_after_offer
            cart.discount_amount = discount_amount
            cart.coupon_code = coupon.code
            cart.coupon = coupon
            cart.save()

            request.session['applied_coupon'] = {
            'code': coupon.code,
            'discount_amount': float(discount_amount),
            'coupon_id': coupon.id
        }
            
        except Coupon.DoesNotExist:
            del request.session["coupon_id"]
    

    #  Only show the discount if already applied
    if cart.coupon_code and cart.discount_amount:
        discount_amount = cart.discount_amount
    else:
        discount_amount = 0

    final_price = total_after_offer - discount_amount
    
    all_coupons = Coupon.objects.filter(
        active=True,
        valid_from__lte=date.today(),
        valid_until__gte=date.today()
    )

    available_coupons = []
    for coupon in all_coupons:
        if coupon.code.lower() == "monsoon" and total_after_offer < 30000:
            continue  # hide "Monsoon" if not eligible
        available_coupons.append(coupon)

    context = {
        'cart_items': updated_items + unavailable_items,
        'total_after_offer': total_after_offer,
        'total_items': total_items,
        'coupon_form': coupon_form,
        'cart': cart,
        'discount_amount': discount_amount,
        # 'available_items': updated_items,  
        # 'unavailable_items': unavailable_items,
        'final_price': final_price,
        'available_coupons': available_coupons,
    }

    return render(request, 'user/cart_detail.html', context)





def get_available_coupons(request):
    """ Return available coupons as JSON """
    coupons = Coupon.objects.filter(valid_from__lte=now(), valid_until__gte=now()).values('id', 'code', 'discount')
    
    return JsonResponse({'coupons': list(coupons)})

# @csrf_exempt
def update_cart_quantity(request):
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "error": "User not authenticated"}, status=401)
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            item_id = data.get("item_id")
            quantity = int(data.get("quantity"))

            cart_item = CartItem.objects.get(id=item_id, cart__user=request.user)



            if cart_item.product.category and not cart_item.product.category.is_active:
                cart_item.delete()  # Remove item from cart if the category was deleted
                return JsonResponse({"success": False, "error": "This product's category has been deleted, and it was removed from your cart."})

            # Check available stock (variant vs product)
            stock = cart_item.variant.stock if cart_item.variant else cart_item.product.stock
            if quantity > stock:
                quantity = stock

            cart_item.quantity = quantity
            cart_item.save()

            # Recalculate total price and total items in the cart
            # cart_items = CartItem.objects.filter(cart=cart_item.cart)
            cart_items = CartItem.objects.filter(cart=cart_item.cart, product__stock__gt=0, product__category__is_active=True)  # Only count available products
           
            total_price = sum(item.quantity * item.price for item in cart_items)

            total_items = sum(item.quantity for item in cart_items)

            return JsonResponse({
                "success": True, 
                "total_price": float(total_price),
                "total_items": total_items
            })
        except Exception as e:
            print("Error in update_cart_quantity:", e)
            traceback.print_exc()
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request"})






@login_required
def remove_from_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item = CartItem.objects.filter(cart=cart, product=product).first()

    if cart_item:
        #  If product category is inactive, delete 
        if not product.category.is_active or product.stock == 0:
            cart_item.delete()
            messages.success(request, f"{product.name} has been removed from your cart.")
        else:
            #  If the product is active, just reduce quantity as needed
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
            else:
                cart_item.delete()
            
            messages.success(request, f"{product.name} quantity updated in your cart.")

    else:
        messages.error(request, "Product not found in cart.")

    return redirect('cart_detail')


@login_required
def remove_unavailable_products(request):
    cart = Cart.objects.get(user=request.user)
    CartItem.objects.filter(cart=cart, product__category__is_active=False).delete()  # ✅ Removes all inactive products
    messages.success(request, "All unavailable products have been removed from your cart.")
    return redirect('cart_detail')







@login_required
def cart_page(request):
    cart = Cart.objects.get_or_create(user=request.user)
    cart_items = CartItem.objects.filter(cart=cart)

    if request.method == 'POST':
        for item in cart_items:
            quantity = int(request.POST.get(f'quantity-{item.id}', item.quantity))
            if quantity > item.product.stock:
                quantity = item.product.stock

            item.quantity = quantity
            if item.quantity == 0 or item.product.stock == 0:
                item.delete()
            else:
                item.save()

        return redirect('cart_page')  

    total_cost = sum(item.quantity * item.product.price for item in cart_items)
    total_items = sum(item.quantity for item in cart_items)

    return render(request, 'user/cart_detail.html', {
        'cart_items': cart_items,
        'total_cost': total_cost,
        'total_items': total_items
    })



@login_required
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    Wishlist.objects.get_or_create(user=request.user, product=product)
    return redirect('wishlist')

@login_required
def remove_from_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    Wishlist.objects.filter(user=request.user, product=product).delete()
    return redirect('wishlist')

@login_required
def wishlist(request):
    wishlist_items = Wishlist.objects.filter(user=request.user)
    return render(request, 'user/wishlist.html', {'wishlist_items': wishlist_items})

@login_required
def move_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    # Remove the item from the cart (if it exists)
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item = CartItem.objects.filter(cart=cart, product=product).first()
    if cart_item:
        cart_item.delete()
    
    # Add the product to the wishlist if it isn't already there
    wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    if created:
        messages.success(request, f"{product.name} has been added to your wishlist.")
    else:
        messages.info(request, f"{product.name} is already in your wishlist.")
    
    return redirect('cart_detail')


def apply_coupon(request):
    if request.method == "POST":
        form = CouponApplyForm(request.POST)
        if form.is_valid():
            cart = request.user.cart
            code = form.cleaned_data["code"]
            now = timezone.now()

            try:
                coupon = Coupon.objects.get(
                    code=code,
                    valid_from__lte=now.date(),
                    valid_until__gte=now.date(),
                    active=True
                )
                

                if coupon.usage_limit <= 0:
                    messages.error(request, "Coupon usage limit has been reached.")
                    return redirect("cart_page")

                # Store in session
                # request.session["coupon_id"] = coupon.id 
                request.session["coupon_id"] = coupon.id

                request.session["applied_coupon"] = {
                "id": coupon.id,
                "code": coupon.code,
                "discount_type": coupon.discount_type,
                "discount": str(coupon.discount),
                # "discount_amount": str(coupon.discount_amount)
            }
                coupon.usage_limit -= 1
                coupon.save()
                cart.coupon_applied = True
                cart.save()

                messages.success(request, f"Coupon '{coupon.code}' applied successfully!")
            except Coupon.DoesNotExist:
                messages.error(request, "Invalid or expired coupon.")

        return redirect("cart_page")
# In apply_coupon view



@login_required
@permission_required('yourapp.can_manage_coupons', raise_exception=True)
def coupon_management(request):
    coupons = Coupon.objects.all()
    return render(request, 'user/coupon_management.html', {'coupons': coupons})

@login_required
@permission_required('yourapp.can_view_coupons', raise_exception=True)

def available_coupons(request):
    today = timezone.now().date()
    coupons = Coupon.objects.filter(valid_from__lte=today, valid_until__gte=today, active=True)
    return render(request, 'user/available_coupons.html', {'coupons': coupons})


# @login_required
# def remove_coupon(request):
@login_required
def remove_coupon(request):
    # Remove coupon from session
    request.session.pop("coupon_id", None)
    request.session.pop("applied_coupon", None)

    # Update the cart instance
    try:
        cart = Cart.objects.get(user=request.user)
        cart.coupon_code = ""
        cart.discount_amount = 0
        cart.coupon_applied = False
        cart.save()
    except Cart.DoesNotExist:
        pass  # Optional: handle missing cart

    messages.success(request, "Coupon removed successfully.")
    return redirect("cart_page")
     
    # if "coupon_id" in request.session:
    #     del request.session["coupon_id"]  # Remove coupon from session
    # Optionally, update the cart instance if you’re storing coupon details in the DB


    #new views

    # if "applied_coupon" in request.session:
    #     del request.session["applied_coupon"]
    # cart, created = Cart.objects.get_or_create(user=request.user)
    # cart.coupon_code = ""
    # cart.discount_amount = 0
    # cart.save()
    # messages.success(request, "Coupon removed successfully.")
    # return redirect("cart_detail")
   # new views

# @login_required
# def remove_coupon(request):
#     if 'coupon_id' in request.session:
#         del request.session['coupon_id']
#         messages.success(request, "Coupon removed successfully.")
#     return redirect('cart_detail')





@login_required
def continue_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.payment_status == 'Failed':
        # Logic to redirect to payment gateway
        return redirect('payment_gateway', order_id=order.id)
    return HttpResponse("Invalid request")


def purchase_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))

    try:
        order = Order.objects.create(product=product, quantity=quantity, user=request.user)
        messages.success(request, 'Purchase successful! Stock updated.')
    except ValueError as e:
        messages.error(request, str(e))

    return redirect('product_detail', product_id=product_id)




def check_stock_updates(request):
    latest_stock_update = Product.objects.order_by('-updated_at').first()
    
    # If stock was updated in the last 5 seconds, notify the frontend
    if latest_stock_update and (now() - latest_stock_update.updated_at).seconds < 5:
        return JsonResponse({"updated": True})
    
    return JsonResponse({"updated": False})
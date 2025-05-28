import logging
import razorpay 
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from products.models import Order,OrderItem,Cart,CartItem, Coupon
from home.models import Address
from django.contrib import messages
import paypalrestsdk
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import decimal
from decimal import Decimal,InvalidOperation,ROUND_HALF_UP
from datetime import datetime, timedelta
from django.utils.timezone import now
from datetime import timedelta, date
import os



RAZORPAY_KEY_ID = "rzp_test_MAimzLa32DUYt6"
RAZORPAY_SECRET = "qbDDZBXaEQPNG72T9ZPVPytC"


razorpay_client = razorpay.Client(auth=("rzp_test_MAimzLa32DUYt6", "qbDDZBXaEQPNG72T9ZPVPytC"))




logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@login_required
def initiate_payment(request):
    if request.method == "GET":
        try:
            #  user cart
            cart, created = Cart.objects.get_or_create(user=request.user)
            cart_items = CartItem.objects.filter(cart=cart)

            if not cart_items.exists():
                messages.error(request, "Your cart is empty.")
                return redirect('cart_detail')

            # active and unavailable items
            valid_cart_items = []
            unavailable_items = []

            for item in cart_items:
                if not item.product.category.is_active or item.product.stock == 0:
                    unavailable_items.append(item)  
                else:
                    valid_cart_items.append(item) 

            #  Prevent payment for all  unavailable items
            if not valid_cart_items:
                messages.error(request, "All items in your cart are unavailable. Please update your cart.")
                return redirect('cart_detail')

          
            total_cost = sum(
                Decimal(item.quantity or 0) * Decimal(item.price or 0) for item in valid_cart_items
            )

            discount_amount = Decimal(str(cart.discount_amount or "0.00"))

            coupon_instance = None
            print('is coupoun applied', cart.coupon_applied)
            if cart.coupon_applied:
               
                try:
                    coupon_instance = Coupon.objects.get(code=cart.coupon_code)
                    logger.info(f"Coupon Retrieved: {coupon_instance} | Code: {coupon_instance.code}")
                except Coupon.DoesNotExist:
                    logger.warning("Coupon does not exist!")
                    coupon_instance = None
            
            delivery_charge = Decimal("60.00")

            # final price is not negative
            final_price = max(total_cost - discount_amount + delivery_charge, Decimal("0.00")).quantize(Decimal("1.00"))

            if final_price <= 0:
                return JsonResponse({"error": "Final amount must be greater than zero."}, status=400)

            
            amount_in_paise = int((final_price * 100).quantize(Decimal("1")))

            # Create Razorpay order
            client = razorpay.Client(auth=("rzp_test_MAimzLa32DUYt6", "qbDDZBXaEQPNG72T9ZPVPytC"))
            order_data = {"amount": amount_in_paise, "currency": "INR", "payment_capture": "1"}
            razorpay_order = client.order.create(order_data)
            logger.debug(f"Order created successfully: {razorpay_order}")

           
            user_address = Address.objects.filter(user=request.user).first()
            if not user_address:
                messages.error(request, "No address found for the user.")
                return redirect('cart_detail')
            
            

            # ✅ Create Order 
            django_order = Order.objects.create(
                user=request.user,
                address=user_address,
                first_name=user_address.first_name,
                last_name=user_address.last_name,
                postcode=user_address.postcode,
                mobile=user_address.mobile,
                house_no=user_address.house_no,
                street_address=user_address.street_address,
                total_price=final_price,
                payment_method='RAZORPAY',
                
                razorpay_order_id=razorpay_order["id"],
                payment_status='Pending',
                status='Pending',

                coupon=coupon_instance,
              
                # coupon_code=cart.coupon_code if cart.coupon_applied else None 
                coupon_code=coupon_instance.code if coupon_instance else None,
                discount_amount=discount_amount,     
                
                

            )
             
            

            # request.session.pop('coupon_id', None)
            # request.session.pop('applied_coupon', None)


            #  Create OrderItems 

            for cart_item in valid_cart_items:
                OrderItem.objects.create(
                    order=django_order,
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                    price=cart_item.price
                )

            request.session.pop('coupon_id', None)
            request.session.pop('applied_coupon', None)
 
            context = {
                "amount": amount_in_paise,
                "order_id": razorpay_order["id"],
                "razorpay_key": 'rzp_test_MAimzLa32DUYt6',
                "callback_url": request.build_absolute_uri('/payment/payment-status/'),
            }
            return render(request, "user/payment.html", context)
        

        except InvalidOperation:
            return JsonResponse({"error": "Invalid decimal operation. Please check the price values."}, status=400)

        except razorpay.errors.BadRequestError as bad_request_error:
            logger.error(f"Bad request error: {bad_request_error}")
            return JsonResponse({"error": "Payment initiation failed: " + str(bad_request_error)}, status=400)

        except Exception as e:
            logger.error(f"Error during payment initiation: {e}")
            return JsonResponse({"error": str(e)}, status=500)

    return redirect('cart_detail')





def set_delivery_date(order):
    """Set the delivery date dynamically based on order status."""
    
    if order.status == "Shipped" and not order.delivery_date:
        order.delivery_date = now() + timedelta(days=7)  
        order.save(update_fields=["delivery_date"])

    elif order.payment_method == "cash_on_delivery" and not order.delivery_date:
        order.delivery_date = now() + timedelta(days=10) 
        order.save(update_fields=["delivery_date"])

logger = logging.getLogger(__name__)






@csrf_exempt
@login_required
def payment_success(request):
    razorpay_payment_id = request.GET.get("razorpay_payment_id")
    razorpay_order_id = request.GET.get("razorpay_order_id")

    logger.info(f"Payment Success Called - Order ID: {razorpay_order_id}, Payment ID: {razorpay_payment_id}")

    if not (razorpay_order_id and razorpay_payment_id):
        logger.error("Missing payment details")
        return render(request, "user/payment_success.html", {"error": "Missing payment details."})

    try:
        # Fetch the order using Razorpay order ID
        order = get_object_or_404(Order, razorpay_order_id=razorpay_order_id)

        
        logger.info(f"Fetched Order - ID: {order.id}, Razorpay Payment ID: {order.razorpay_payment_id}")

        #  order details
        order.razorpay_payment_id = razorpay_payment_id
        order.payment_status = "Success"
        order.status = "Pending"
        set_delivery_date(order)
        order.save()

        # Remove coupon from session
        request.session.pop('coupon_id', None)
        request.session.pop('applied_coupon', None)
        # if "coupon_id" in request.session:
        #     del request.session["coupon_id"]
        #     logger.info(f"Coupon session removed for user {request.user}")


        # Reduce stock at  each pruchased product
        order_items = order.order_items.all()  
        for item in order.order_items.all():
            product = item.product
            product.stock -= item.quantity
            product.save()

        # Clear user's cart
        try:
            cart = Cart.objects.get(user=request.user)
            cart.cartitem_set.all().delete()  
            cart.delete()
            logger.info(f"Cart for user {request.user} cleared successfully.") 
        except Cart.DoesNotExist:
            logger.warning(f"No cart found for user {request.user}")

            
        # Fetch  products
        purchased_products = order.order_items.all()
        if not purchased_products:
            logger.warning(f"Order {order.id} has no items!")

        if not order.delivery_date:
            order.delivery_date = date.today() + timedelta(days=7) 
            order.save()


        

        context = {
            "order": order,
            "transaction_id": razorpay_payment_id,
            "total_amount": order.total_price,
            "payment_status": order.payment_status,
            "payment_method": "Razorpay",
            "payment_state": "Success",
            "shipping_address": order.address,
            "purchased_products": order_items,
            "coupon": order.coupon_code,
            # "purchased_products": purchased_products
        }

        logger.debug(f"Context Data: {context}")

        return render(request, "user/payment_success.html", context)

    except Exception as e:
        logger.error(f"Error updating order: {e}")
        return render(request, "user/payment_success.html", {"error": str(e)})


#razorpay failure 
@login_required
def payment_failure(request):
    return render(request, "user/payment-failed.html", {"error": "Payment failed. Please try again "})








    





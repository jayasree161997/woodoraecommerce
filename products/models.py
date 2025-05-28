from django.db import models

from home.models import Address
from datetime import date
from decimal import Decimal,InvalidOperation
import uuid
from django.utils.timezone import now
from datetime import timedelta
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings



# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Category Name", blank=True, null=True)
    description = models.TextField(verbose_name="Category Description", blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Category", default=1, related_name="products")
    name = models.CharField(max_length=200, verbose_name="Product Name")
    description = models.TextField(verbose_name="Product Description")
    brand = models.CharField(max_length=100, verbose_name="Brand", blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Price")
    # quantity = models.IntegerField(null=False , blank=False)
    stock = models.PositiveIntegerField(default=0)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Original Price", blank=True, null=True)
    # discount_percentage = models.IntegerField(verbose_name="Discount Percentage", blank=True, null=True, default=0)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Discount Percentage", blank=True, null=True, default=0)
    stock_status = models.BooleanField(default=True, verbose_name="In Stock")
    sold = models.PositiveIntegerField(verbose_name="Units Sold", default=0)
    coupons = models.ManyToManyField('Coupon', related_name='coupon_products',blank=True)
    
    main_image = models.ImageField(upload_to="products/main_images/", verbose_name="Main Image",default="products/main_images/default.jpg")
    thumbnail_images = models.ManyToManyField("ProductThumbnail", related_name="product_thumbnails", verbose_name="Thumbnail Images")

    material = models.CharField(max_length=100, verbose_name="Material", blank=True, null=True)
    dimensions = models.CharField(max_length=100, verbose_name="Dimensions", blank=True, null=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Weight (kg)", blank=True, null=True)
    warranty = models.CharField(max_length=100, verbose_name="Warranty", blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True) 
    is_deleted = models.BooleanField(default=False)

    def get_thumbnail(self):
        # This method will return the first thumbnail related to the product
        thumbnail = self.thumbnails.first()
        if thumbnail:
            return thumbnail.image.url
        return None
    
    def reduce_stock(self, quantity):
        if self.stock >= quantity:
            self.stock -= quantity
            self.sold += quantity
            self.save()
        else:
            raise ValueError("Not enough stock")   
        
    def save(self, *args, **kwargs):
        # Validate Decimal fields
        for field in ['price', 'original_price', 'discount_percentage']:
            value = getattr(self, field)
            if value is not None:
                try:
                    Decimal(value)
                except InvalidOperation:
                    raise ValueError(f"Invalid decimal value for {field}: {value}")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


    
class ProductVariant(models.Model):
    product = models.ForeignKey(Product, related_name="variants", on_delete=models.CASCADE)
    variant_name = models.CharField(max_length=50, null=False, blank=False) 
    variant_value = models.CharField(max_length=50, null=True, blank=True)  
    color_image = models.ImageField(upload_to="products/color_variants", verbose_name="Color Image")
    stock = models.IntegerField(default=0)
    

    def __str__(self):
        return f"{self.variant_name}: {self.variant_value or 'N/A'} ({self.product.name})"
    

class ProductThumbnail(models.Model):
    product = models.ForeignKey(Product, related_name='thumbnails', on_delete=models.CASCADE)
    image = models.ImageField(upload_to="products/thumbnails", verbose_name="Thumbnail Image")
    alt_text = models.CharField(max_length=100, verbose_name="Alt Text", blank=True, null=True)

    def __str__(self):
        return self.alt_text or "Thumbnail"
    

class ProductOffer(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    offer_type = models.CharField(max_length=50)

    
    
    def clean(self):
        # Check maximum discount amount
        if self.discount_amount > 2000:
            raise ValidationError("Product offer discount amount cannot exceed ₹2000.")
        
        # Check discount percentage
        if self.product and self.product.price:  # make sure product and price exist
            percentage = (self.discount_amount / self.product.price) * 100
            if percentage > 30:
                raise ValidationError("Product offer discount cannot exceed 30% of product price.")
            
        if self.end_date and self.start_date:
            if self.end_date < self.start_date:
                raise ValidationError("End date cannot be before start date.")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Offer on {self.product.name}"


class CategoryOffer(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    offer_type = models.CharField(max_length=50)

    def __str__(self):
        return f"Offer on {self.category.name}"
    
    def clean(self):
        if self.discount_percentage > 30:
            raise ValidationError("Category offer discount cannot exceed 30%.")


class ReferralOffer(models.Model):
    # referrer = models.ForeignKey(User, related_name='referrals', on_delete=models.CASCADE)
    # referred = models.ForeignKey(User, related_name='referred_by', on_delete=models.CASCADE)
    

    referrer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='referrals',
        on_delete=models.CASCADE
    )
    referred = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='referred_by',
        on_delete=models.CASCADE
    )
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50)

    def __str__(self):
        return f"Referral by {self.referrer.username}"
    


class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart')
    coupon_code = models.CharField(max_length=50, blank=True, null=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    coupon_applied= models.BooleanField(default= False)

    def __str__(self):
        return f"{self.user.username}'s Cart"
    
    def total_items(self):
        return sum(item.quantity for item in self.cartitem_set.all())
    

    def get_total_cost(self):
        total = sum(item.get_cost() for item in self.cartitem_set.all())
        return total - self.discount_amount


    def get_total_cost(self):
        total_cost = sum(item.quantity * item.product.price for item in self.cartitem_set.all())
        discount = getattr(self, 'discount_amount', 0)  # Ensure discount_amount exists
        return total_cost - discount
    
    def apply_coupon(self, coupon):
        """Apply a valid coupon to the cart"""
        if coupon.valid_from <= date.today() <= coupon.valid_until and coupon.usage_limit > 0:
            self.discount_amount = (self.get_total_cost() * coupon.discount) / 100
            self.coupon_code = coupon.code
            coupon.usage_limit -= 1  # Decrease the usage count
            coupon.save()
            self.save()
            return True
        return False
    
    



class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)


    def get_cost(self):
        if self.variant:
            return self.quantity * self.variant.product.price 
        return self.quantity * self.product.price

    def __str__(self):
        if self.variant:
            return f"{self.quantity} of {self.product.name} ({self.variant.variant_name})"
        return f"{self.quantity} of {self.product.name}"
       
    
class Order(models.Model):
    # user = models.ForeignKey(User, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    address = models.ForeignKey(Address, null=True, blank=True, on_delete=models.SET_NULL)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    postcode = models.CharField(max_length=20, blank=True, null=True)
    mobile = models.CharField(max_length=20, blank=True, null=True)
    house_no = models.CharField(max_length=50, blank=True, null=True)
    street_address = models.CharField(max_length=255, blank=True, null=True)
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Shipped", "Shipped"),
        ("Delivered", "Delivered"),
        ("Cancelled", "Cancelled"),
        ("Return Requested", "Return Requested"),
        ("Return Accepted", "Return Accepted"),
        ("Return Rejected", "Return Rejected"),
    ]
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending',)
    payment_method = models.CharField(max_length=100, choices=[('COD', 'Cash on Delivery'),('RAZORPAY', 'Razorpay'),('PAYPAL', 'PayPal'),])
    cod_transaction_id = models.CharField(max_length=100, blank=True, null=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    paypal_payment_id = models.CharField(max_length=100, blank=True, null=True)
    transaction_details = models.JSONField(blank=True, null=True)
    payment_status = models.CharField(max_length=20, default='Pending')  # New field
    paypal_transaction_id = models.CharField(max_length=100, blank=True, null=True)
    delivery_date = models.DateTimeField(blank=True, null=True)
    delivery_charge = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    date = models.DateTimeField(auto_now_add=True)
    coupon = models.ForeignKey('Coupon', on_delete=models.SET_NULL, null=True, blank=True)
    coupon_code = models.CharField(max_length=50, null=True, blank=True)



    def cancel_order(self):
        """Method to cancel order"""
        self.status = 'Cancelled'
        self.save(update_fields=['status']) 

    def generate_cod_transaction_id(self):
        """Generate a unique transaction ID for Cash on Delivery (COD)."""
        return f"COD-{uuid.uuid4().hex[:10].upper()}"

    def reduce_stock(self):
        for item in self.order_items.all():
            item.product.reduce_stock(item.quantity)
        

    def save(self, *args, **kwargs):
        # Validate Decimal fields
        for field in ['total_price', 'discount_amount']:
            value = getattr(self, field)
            if value is not None:
                try:
                    Decimal(value)
                except InvalidOperation:
                    raise ValueError(f"Invalid decimal value for {field}: {value}")
        super().save(*args, **kwargs)






    def record_sales(self):
        for item in self.order_items.all():
            Sales.objects.create(
                product=item.product,
                quantity=item.quantity,
                amount=item.price * item.quantity,
                date=self.date
             )             
                 

    # def save(self, *args, **kwargs):
    #     is_new = self.pk is None
    #     super().save(*args, **kwargs)
    #     if is_new:
    #         self.reduce_stock()
    #         self.record_sales()

    def save(self, *args, **kwargs):
        from home.models import Wallet, Transaction  # Avoid circular import issues
        
        if self.pk:  # Ensure the instance already exists
            previous_status = Order.objects.get(pk=self.pk).status
            
            # Only credit wallet when transitioning from "Return Accepted" to "Return Completed"
            if previous_status == "Return Accepted" and self.status == "Return Completed":
                print(f"Processing refund for Order ID: {self.pk}")  # Debugging

                wallet, created = Wallet.objects.get_or_create(user=self.user)
                print(f"Old Wallet Balance: {wallet.balance}")  # Debugging

                wallet.balance += self.total_price
                wallet.save()

                print(f"New Wallet Balance: {wallet.balance}")  # Debugging

                # Log transaction
                Transaction.objects.create(
                    wallet=wallet,
                    amount=self.total_price,
                    transaction_type="refund"
                )

                print(f"Refund Transaction Created for {self.total_price}")  # Debugging

        super(Order, self).save(*args, **kwargs)              




















def save(self, *args, **kwargs):
    is_new = self.pk is None  # Check if it's a new order

    # Validate Decimal fields
    for field in ['total_price', 'discount_amount']:
        value = getattr(self, field)
        if value is not None:
            try:
                Decimal(value)
            except InvalidOperation:
                raise ValueError(f"Invalid decimal value for {field}: {value}")

    # Generate COD transaction ID if payment is Cash on Delivery
    if self.payment_method == "COD" and not self.cod_transaction_id:
        self.cod_transaction_id = self.generate_cod_transaction_id()

    # if self.status == "Shipped" and not self.delivery_date:
    #         self.delivery_date = now() + timedelta(days=7) 
    

    super().save(*args, **kwargs)

    # Reduce stock and record sales only for new orders
    if is_new:
        self.reduce_stock()
        self.record_sales()


    def __str__(self):
        return f"Order {self.id} - {self.user.username}"
    












    
    


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="order_items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="order_products")
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    status = models.CharField(max_length=20, default="Pending")  
    cancel_reason = models.TextField(blank=True, null=True) 
    returned = models.BooleanField(default=False) 


    @property
    def total_price(self):
        return self.price * self.quantity
    
    @property
    def discount_amount(self):
        return self.price * Decimal ('0.10')


    def save(self, *args, **kwargs):
        if not self.price:
             self.price = self.product.price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} in Order {self.order.id}"
    
class Wishlist(models.Model):   
    # user = models.ForeignKey(User, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'product')


class Coupon(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed'),
    ]
    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE_CHOICES, default='percentage')
    discount = models.DecimalField(max_digits=5, decimal_places=2)
    valid_from = models.DateField()
    valid_until = models.DateField()
    usage_limit = models.IntegerField()
    active = models.BooleanField(default=True) 



    def __str__(self):
        return self.code


    # def is_valid_for_product(self, product):
    #     """Check if the coupon is valid for a specific product"""
    #     return self.products.filter(id=product.id).exists() or self.categories.filter(id=product.category.id).exists()
    def is_valid(self):
        today = timezone.now().date()
        return self.active and self.valid_from <= today <= self.valid_until and self.usage_limit > 0

class Sales(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Sales for {self.product.name} on {self.date}"
    




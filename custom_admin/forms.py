from django import forms
from products.models import Product,ProductVariant,Category, ProductOffer,CategoryOffer,Coupon,ProductThumbnail
from home.models import Profile
from django.contrib.auth.models import User
# ,ProductThumbnail
from django.core.exceptions import ValidationError
from django.contrib import admin


class ProductForm(forms.ModelForm):

    thumbnail_images = forms.ModelMultipleChoiceField(
        queryset=ProductThumbnail.objects.all(),
        required=False, 
        widget=forms.CheckboxSelectMultiple,
        label="Select Thumbnails"
    )


    class Meta:
        model = Product
        fields = [
            'name', 'description', 'brand', 'price', 'stock',
              'sold', 'main_image', 
            'material', 'dimensions', 'weight', 'warranty','category','is_active',
        ]
        # ,ProductThumbnail
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'main_image': forms.ClearableFileInput(),
            
        }
        # 'thumbnail_images': forms.CheckboxSelectMultiple(),
        labels = {
            'name': 'Product Name',
            'description': 'Product Description',
            'main_image': 'Main Product Image',
            'is_active': 'Product Status (Active/Inactive)'
        }

            
class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']




# Form for the ProductVariant model
class ProductVariantForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = ['product', 'variant_name', 'variant_value', 'color_image']
        widgets = {
            'color_image': forms.ClearableFileInput(),
        }
        labels = {
            'variant_name': 'Variant Name',
            'variant_value': 'Variant Value (e.g., Color or Size)',
            'color_image': 'Image for Variant (if applicable)',
        }


class ProductThumbnailForm(forms.ModelForm):
    class Meta:
        model = ProductThumbnail
        fields = ['alt_text', 'image', 'product']






class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "email"]

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["mobile_number"]



class ProductOfferForm(forms.ModelForm):
    class Meta:
        model = ProductOffer
        fields = ['product', 'discount_amount', 'start_date', 'end_date', 'offer_type']
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
        
    def clean(self):
        cleaned_data = super().clean()
        discount_amount = cleaned_data.get('discount_amount')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        product = cleaned_data.get('product')

       
        if product and discount_amount:
            percentage = (discount_amount / product.price) * 100
            if percentage > 30:
                raise ValidationError("Product offer discount cannot exceed 30%.")

        if start_date and end_date:
            if end_date < start_date:
                raise ValidationError("End date cannot be before start date.")
            
        return cleaned_data
    

class CategoryOfferForm(forms.ModelForm):
    class Meta:
        model = CategoryOffer
        fields = ['category', 'discount_percentage', 'start_date', 'end_date','offer_type']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }


    def clean(self):
        cleaned_data = super().clean()
        discount_percentage = cleaned_data.get('discount_percentage')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        # Check discount percentage
        if discount_percentage and discount_percentage > 30:
            raise ValidationError("Category offer discount cannot exceed 30%.")

        # Check start date and end date
        if start_date and end_date and start_date > end_date:
            raise ValidationError("Start date cannot be after end date.")

        return cleaned_data

class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = ['code', 'discount', 'valid_from', 'valid_until', 'usage_limit']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }
        
    def clean_discount(self):
        discount = self.cleaned_data.get('discount')
        if discount < 1 or discount > 20:
            raise forms.ValidationError('Discount must be between 1% and 20%.')
        return discount


class SalesReportForm(forms.Form):
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
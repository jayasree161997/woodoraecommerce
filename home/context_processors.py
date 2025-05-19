from django.urls import resolve
from django.utils.text import slugify
from products.models import Product

# def breadcrumbs(request):
#     """Generate breadcrumbs dynamically based on the URL."""
#     path_parts = request.path.strip('/').split('/')
    
#     # Define the base breadcrumb
#     breadcrumbs = [{'title': 'Home', 'url': '/'}]

#     if not path_parts or path_parts == ['']:
#         return {'breadcrumbs': breadcrumbs}

#     url = ''
#     for part in path_parts:
#         url += f'/{part}'
#         title = part.replace('-', ' ').title()  # Convert slug to readable text
#         breadcrumbs.append({'title': title, 'url': url})

#     return {'breadcrumbs': breadcrumbs}
def breadcrumbs(request):
    """Generate breadcrumbs dynamically based on the URL."""
    path_parts = request.path.strip('/').split('/')
    
    # Define the base breadcrumb
    breadcrumbs = [{'title': 'Home', 'url': '/'}]

    if not path_parts or path_parts == ['']:
        return {'breadcrumbs': breadcrumbs}

    url = ''
    for i, part in enumerate(path_parts):
        url += f'/{part}'
        title = part.replace('-', ' ').title()  # Convert slug to readable text
        
        # If it's the product details page and the part is a number (product ID)
        if path_parts[0] == 'products' and path_parts[1] == 'products_details' and part.isdigit():
            try:
                product = Product.objects.get(id=part)
                title = product.name  # Replace ID with the product name
            except Product.DoesNotExist:
                title = 'Product Not Found'

        breadcrumbs.append({'title': title, 'url': url})

    return {'breadcrumbs': breadcrumbs}

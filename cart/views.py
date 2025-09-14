from django.shortcuts import render, redirect, get_object_or_404
from store.models import Product, Variation
from .models import Cart, Cartitem
from django.core.exceptions import ObjectDoesNotExist

# Get or create cart_id for session
def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart

# Add product to cart

def add_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product_variations = []

    if request.method == 'POST':
        for key, value in request.POST.items():
            if key != 'csrfmiddlewaretoken':
                variation = Variation.objects.filter(
                    product=product,
                    variation_category__iexact=key,
                    variation_value__iexact=value
                ).first()  # first() से सिर्फ एक variation मिलेगा
                if variation:
                    product_variations.append(variation)

    cart, created = Cart.objects.get_or_create(cart_id=_cart_id(request))

    # पहले से मौजूद cart items लीजिए
    cart_items = Cartitem.objects.filter(product=product, cart=cart)

    for item in cart_items:
        existing_variations = list(item.variations.all())
        if existing_variations == product_variations:
            item.quantity += 1
            item.save()
            return redirect('cart')

    # अगर कोई match नहीं मिला तो नया cart item बनाइए
    cart_item = Cartitem.objects.create(
        product=product,
        quantity=1,
        cart=cart
    )
    if product_variations:
        cart_item.variations.add(*product_variations)
    cart_item.save()

    return redirect('cart')

# Remove 1 quantity from cart
def remove_cart(request, product_id,cart_item_id):
    cart = get_object_or_404(Cart, cart_id=_cart_id(request))
    product = get_object_or_404(Product, id=product_id)

    try:
        cart_item = Cartitem.objects.filter(product=product, cart=cart,id=cart_item_id).first()
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    except Cartitem.DoesNotExist:
        pass

    return redirect('cart')

# Remove entire cart item
def remove_cart_item(request, cart_item_id):
    cart_item = get_object_or_404(Cartitem, id=cart_item_id)
    cart_item.delete()
    return redirect('cart')

# Show cart page
def cart(request):
    total = 0
    quantity = 0
    tax = 0
    grand_total = 0

    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = Cartitem.objects.filter(cart=cart, is_active=True)
    except Cart.DoesNotExist:
        cart_items = []

    for item in cart_items:
        total += item.product.price * item.quantity
        quantity += item.quantity

    if total > 0:
        tax = (2 * total) / 100
        grand_total = total + tax

    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total,
    }
    return render(request, 'store/cart.html', context)




# tt50932sl8fkbt1873ef72vi68gn7xnm
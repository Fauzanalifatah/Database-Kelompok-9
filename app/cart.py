from .models import Keranjang, ItemKeranjang, Produk


def _get_or_create_cart(request):
    """Get or create a cart for the current user or session."""
    if request.user.is_authenticated:
        cart, _ = Keranjang.objects.get_or_create(pengguna=request.user)
        return cart

    # Guest cart via session
    if not request.session.session_key:
        request.session.create()
    session_key = request.session.session_key
    cart, _ = Keranjang.objects.get_or_create(session_key=session_key, pengguna=None)
    return cart


def get_cart(request):
    """Return the cart for the current request (user or guest)."""
    return _get_or_create_cart(request)


def add_to_cart(request, produk, jumlah=1):
    """Add a product to the cart (or increase qty)."""
    cart = _get_or_create_cart(request)
    item, created = ItemKeranjang.objects.get_or_create(
        keranjang=cart, produk=produk, defaults={"jumlah": jumlah}
    )
    if not created:
        item.jumlah += jumlah
        item.save()
    return item


def update_cart_item(item_id, jumlah):
    """Update quantity of a cart item."""
    item = ItemKeranjang.objects.get(pk=item_id)
    if jumlah <= 0:
        item.delete()
    else:
        item.jumlah = jumlah
        item.save()
    return item


def remove_from_cart(item_id):
    """Remove an item from the cart."""
    ItemKeranjang.objects.filter(pk=item_id).delete()


def get_cart_total_items(request):
    """Return total item count in the cart."""
    try:
        cart = _get_or_create_cart(request)
        return cart.total_item
    except Exception:
        return 0


def merge_guest_cart(request):
    """After login, merge guest cart items into user cart."""
    session_key = request.session.session_key
    if not session_key:
        return
    try:
        guest_cart = Keranjang.objects.get(session_key=session_key, pengguna=None)
    except Keranjang.DoesNotExist:
        return

    user_cart, _ = Keranjang.objects.get_or_create(pengguna=request.user)

    for guest_item in guest_cart.item.all():
        user_item, created = ItemKeranjang.objects.get_or_create(
            keranjang=user_cart,
            produk=guest_item.produk,
            defaults={"jumlah": guest_item.jumlah},
        )
        if not created:
            user_item.jumlah += guest_item.jumlah
            user_item.save()

    guest_cart.delete()


import hashlib
import hmac

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def _client():
    if not settings.MIDTRANS_SERVER_KEY or not settings.MIDTRANS_CLIENT_KEY:
        raise ImproperlyConfigured(
            "MIDTRANS_SERVER_KEY dan MIDTRANS_CLIENT_KEY harus dikonfigurasi. "
            "Tambahkan kedua key Sandbox ke environment."
        )
    try:
        import midtransclient
    except ImportError as error:
        raise ImproperlyConfigured(
            "Paket midtransclient belum terpasang. Jalankan pip install -r requirements.txt."
        ) from error
    return midtransclient.Snap(
        is_production=settings.MIDTRANS_IS_PRODUCTION,
        server_key=settings.MIDTRANS_SERVER_KEY,
    )


def create_snap_transaction(order, customer, items):
    snap = _client()
    gross_amount = int(order.total)
    params = {
        "transaction_details": {
            "order_id": str(order.nomor),
            "gross_amount": gross_amount,
        },
        "item_details": [
            {
                "id": str(item.produk_id),
                "price": int(item.harga_satuan),
                "quantity": item.jumlah,
                "name": item.nama_produk[:50],
            }
            for item in items
        ],
        "customer_details": {
            "first_name": customer["name"][:50],
            "email": customer["email"][:50],
            "phone": customer["phone"][:20],
        },
    }
    return snap.create_transaction(params)


def is_valid_signature(payload):
    signature = payload.get("signature_key", "")
    raw = (
        f"{payload.get('order_id', '')}"
        f"{payload.get('status_code', '')}"
        f"{payload.get('gross_amount', '')}"
        f"{settings.MIDTRANS_SERVER_KEY}"
    )
    expected = hashlib.sha512(raw.encode("utf-8")).hexdigest()
    return bool(signature) and hmac.compare_digest(signature, expected)

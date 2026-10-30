from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


@register.filter
def idr(value):
    try:
        amount = Decimal(str(value)).quantize(Decimal("1"))
    except (InvalidOperation, TypeError, ValueError):
        return value

    return f"{amount:,.0f}".replace(",", ".")

from django.conf import settings

from .models import tb_register


def shop(request):
    cart = request.session.get('cart', {})
    person = None
    uid = request.session.get('id')
    if uid:
        person = tb_register.objects.filter(id=uid).first()
    return {
        'person': person, 'cart_count': sum(cart.values()),
        'site': {'name': settings.SITE_NAME, 'email': settings.SITE_EMAIL,
                 'phone': settings.SITE_PHONE, 'address': settings.SITE_ADDRESS},
    }

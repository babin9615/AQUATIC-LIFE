# Aquatic Life (Aquraim)

Django aquarium marketplace: browse fish/plants, cart, cash-on-delivery checkout, plus a custom admin panel.

## Run
```
pip install -r requirements.txt
# MySQL (default, see settings.py / DB_* env vars)  -- or for a quick start:  set USE_SQLITE=1
python manage.py migrate
python manage.py seed          # sample categories + products from the bundled images
python manage.py runserver
```
- Shop: http://127.0.0.1:8000/  (sign up first, then log in)
- Admin panel: http://127.0.0.1:8000/aquraimadmin/  (ADMIN_EMAIL / ADMIN_PASSWORD in settings.py, default babinjose@gmail.com / babinjose)
- Django admin: http://127.0.0.1:8000/admin/ (`python manage.py createsuperuser`)

## Pages
**Shop:** `/` home, `/fish/`, `/plants/`, `/categories/`, product page (Add to cart / Buy now), `/cart/`, `/checkout/`, `/orders/` (+ detail & cancel), `/profile/`, `/signup/`, `/login/`.
**Admin (`/aquraimadmin/`):** dashboard; Fish and Aquatic plants (view / add / edit / delete); categories; orders (filter, detail, status); users (details + order history, delete).

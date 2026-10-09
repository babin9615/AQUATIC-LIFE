# Aquatic Life (Aquraim) - Django + Bootstrap 5

Aquarium fish & live plants shop: responsive Bootstrap storefront, cart, cash-on-delivery checkout,
blogs, contact form, and a custom admin panel.

## Run
```
pip install -r requirements.txt
python manage.py migrate
python manage.py seed          # optional: sample categories, products and blog posts
python manage.py runserver
```
Uses **SQLite by default** (nothing to configure). To use MySQL: `pip install mysqlclient`, then set
`USE_MYSQL=1` (and optionally `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`) before running.

Bootstrap 5 and Bootstrap Icons are bundled in `Aquraimuser/static/vendor/`, so no internet/CDN is needed.

## URLs
| Area | URL |
|---|---|
| Shop home | `/` |
| Fish / Plants / All products | `/fish/`, `/plants/`, `/products/` |
| Categories, one category | `/categories/`, `/category/<slug>/` |
| Product page | `/product/<id>/` |
| Blogs | `/blogs/`, `/blogs/<slug>/` |
| About / Contact | `/about/`, `/contact/` |
| Sign up / Log in | `/signup/`, `/login/` |
| Cart, checkout, orders, profile | `/cart/`, `/checkout/`, `/orders/`, `/profile/` |
| **Admin login** | `/aquraimadmin/` -> redirects to `/aquraimadmin/dashboard/` |
| Django's built-in admin (optional) | `/admin/` (`python manage.py createsuperuser`) |

## Admin panel (`/aquraimadmin/`)
Default login: **babinjose@gmail.com / babinjose** - change it with the `ADMIN_EMAIL` / `ADMIN_PASSWORD`
environment variables (see `Aquraim/settings.py`).

1. **Categories -> Add category**: name, type (fish or plant) and an image. The slug is created automatically.
2. **Fish / Aquatic plants -> Add fish / Add plant**: choose a category, name, price, optional MRP (shows a discount
   badge), stock, description and an image (required). The category list only shows categories of the chosen type.
3. Images are shown on the shop's product list, category pages and product page.
4. Also manage: blog posts (with image), orders (change status), users, and contact-form messages.

## Edit your shop details
`SITE_EMAIL`, `SITE_PHONE`, `SITE_ADDRESS` in `Aquraim/settings.py` appear in the footer, About and Contact pages.

## Tests
```
python manage.py test
```

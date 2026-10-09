import shutil
import tempfile
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from .models import BlogPost, Category, ContactMessage, Order, Product, tb_register

TMP_MEDIA = tempfile.mkdtemp()


def img(name='t.jpg', color=(30, 120, 200)):
    b = BytesIO()
    Image.new('RGB', (60, 40), color).save(b, 'JPEG')
    return SimpleUploadedFile(name, b.getvalue(), content_type='image/jpeg')


@override_settings(MEDIA_ROOT=TMP_MEDIA, ADMIN_EMAIL='admin@test.com', ADMIN_PASSWORD='secret123')
class SiteFlowTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TMP_MEDIA, ignore_errors=True)

    # ---- public pages ----
    def test_public_pages_load(self):
        for name in ['home', 'categories', 'products', 'fish', 'plants', 'blogs', 'about', 'contact', 'login', 'signup']:
            r = self.client.get(reverse(name))
            self.assertEqual(r.status_code, 200, name)

    def test_contact_form_saves_message(self):
        r = self.client.post(reverse('contact'), {'name': 'Ann', 'email': 'ann@x.com', 'subject': 'Hi', 'message': 'Hello there'})
        self.assertRedirects(r, reverse('contact'))
        self.assertEqual(ContactMessage.objects.count(), 1)
        bad = self.client.post(reverse('contact'), {'name': '', 'email': 'nope', 'subject': '', 'message': ''})
        self.assertEqual(bad.status_code, 200)
        self.assertContains(bad, 'is-invalid')

    # ---- register / login ----
    def test_register_and_login(self):
        r = self.client.post(reverse('registeraction'), {
            'name': 'Babin', 'age': 25, 'email': 'b@x.com', 'password': 'pass1234', 'confirm_password': 'pass1234', 'image': img()})
        self.assertRedirects(r, reverse('login'))
        u = tb_register.objects.get(email='b@x.com')
        self.assertNotEqual(u.password, 'pass1234')          # stored hashed
        self.assertTrue(u.image)
        bad = self.client.post(reverse('loginaction'), {'email': 'b@x.com', 'password': 'wrong'})
        self.assertEqual(bad.status_code, 401)
        ok = self.client.post(reverse('loginaction'), {'email': 'B@X.com', 'password': 'pass1234'})
        self.assertRedirects(ok, reverse('home'))

    def test_register_validation(self):
        base = {'name': 'Bo', 'age': 25, 'email': 'a@x.com', 'password': 'pass1234', 'confirm_password': 'different'}
        r = self.client.post(reverse('registeraction'), base)
        self.assertContains(r, 'Passwords do not match')
        tb_register.objects.create(name='X', age=20, email='a@x.com', password='x')
        r = self.client.post(reverse('registeraction'), {**base, 'confirm_password': 'pass1234'})
        self.assertContains(r, 'already registered')

    def test_login_next_redirect(self):
        r = self.client.get(reverse('cart'))
        self.assertRedirects(r, f"{reverse('login')}?next=/cart/")

    # ---- admin ----
    def admin(self):
        self.client.post(reverse('adminaction'), {'email': 'admin@test.com', 'password': 'secret123'})

    def test_admin_protected_and_login_redirects_to_dashboard(self):
        self.assertRedirects(self.client.get(reverse('dashboard')), reverse('adminhome'))
        bad = self.client.post(reverse('adminaction'), {'email': 'admin@test.com', 'password': 'nope'})
        self.assertRedirects(bad, reverse('adminhome'))
        ok = self.client.post(reverse('adminaction'), {'email': 'admin@test.com', 'password': 'secret123'})
        self.assertRedirects(ok, reverse('dashboard'))
        self.assertContains(self.client.get(reverse('dashboard')), 'Dashboard')

    def test_admin_adds_category_and_products_with_images_shown_on_site(self):
        self.admin()
        r = self.client.post(reverse('a_category_new'), {'name': 'Betta Fish', 'kind': 'fish', 'image': img()})
        self.assertRedirects(r, reverse('a_categories'))
        r = self.client.post(reverse('a_category_new'), {'name': 'Carpet Plants', 'kind': 'plant', 'image': img()})
        fish_cat, plant_cat = Category.objects.get(slug='betta-fish'), Category.objects.get(slug='carpet-plants')

        # image is required for a new product
        r = self.client.post(reverse('a_product_new') + '?kind=fish', {'category': fish_cat.pk, 'name': 'Halfmoon', 'price': '250', 'stock': 5})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Product.objects.count(), 0)

        r = self.client.post(reverse('a_product_new') + '?kind=fish', {
            'category': fish_cat.pk, 'name': 'Halfmoon Betta', 'price': '250', 'old_price': '300', 'stock': 5,
            'description': 'Blue', 'image': img()})
        self.assertRedirects(r, reverse('a_fish'))
        r = self.client.post(reverse('a_product_new') + '?kind=plant', {
            'category': plant_cat.pk, 'name': 'Hairgrass', 'price': '99', 'stock': 8, 'image': img('p.jpg')})
        self.assertRedirects(r, reverse('a_plants'))

        fish = Product.objects.get(name='Halfmoon Betta')
        self.assertTrue(fish.image)
        self.assertEqual(fish.discount, 17)
        # a fish form must not accept a plant category
        r = self.client.post(reverse('a_product_new') + '?kind=fish', {
            'category': plant_cat.pk, 'name': 'Bad', 'price': '1', 'stock': 1, 'image': img()})
        self.assertEqual(r.status_code, 200)

        # public product list, category page and product page show the uploaded image
        self.client.get(reverse('adminlogout'))
        self.assertContains(self.client.get(reverse('fish')), fish.image.url)
        self.assertContains(self.client.get(reverse('category', args=['betta-fish'])), fish.image.url)
        self.assertContains(self.client.get(reverse('categories')), fish_cat.image.url)
        self.assertNotContains(self.client.get(reverse('plants')), fish.image.url)
        self.assertEqual(self.client.get(reverse('product', args=[fish.pk])).status_code, 200)

    def test_admin_blog_and_messages(self):
        self.admin()
        r = self.client.post(reverse('a_blog_new'), {'title': 'Fish Care 101', 'content': 'Hello\n\nWorld', 'published': 'on', 'image': img()})
        self.assertRedirects(r, reverse('a_blogs'))
        post = BlogPost.objects.get()
        self.assertEqual(post.slug, 'fish-care-101')
        ContactMessage.objects.create(name='A', email='a@x.com', subject='S', message='M')
        m = ContactMessage.objects.get()
        self.assertContains(self.client.get(reverse('a_messages')), 'New')
        self.client.get(reverse('a_message', args=[m.pk]))
        m.refresh_from_db()
        self.assertTrue(m.is_read)
        self.client.get(reverse('adminlogout'))
        self.assertContains(self.client.get(reverse('blogs')), 'Fish Care 101')
        self.assertEqual(self.client.get(reverse('blog', args=['fish-care-101'])).status_code, 200)

    # ---- shopping ----
    def test_cart_checkout_and_cancel(self):
        cat = Category.objects.create(name='Barbs', slug='barbs', kind='fish')
        p = Product.objects.create(category=cat, name='Tiger Barb', price=60, stock=5)
        u = tb_register.objects.create(name='U', age=20, email='u@x.com', password='x')
        s = self.client.session
        s['id'] = u.id
        s.save()
        self.client.post(reverse('cart_add', args=[p.pk]), {'qty': 2})
        self.assertContains(self.client.get(reverse('cart')), 'Tiger Barb')
        bad = self.client.post(reverse('checkout'), {'full_name': 'U'})        # missing fields: must not crash
        self.assertEqual(bad.status_code, 200)
        r = self.client.post(reverse('checkout'), {'full_name': 'U', 'phone': '9876543210', 'address': 'Road 1', 'city': 'Town', 'pincode': '629251'})
        o = Order.objects.get()
        self.assertRedirects(r, reverse('order', args=[o.pk]))
        self.assertEqual(float(o.total), 120.0)
        p.refresh_from_db()
        self.assertEqual(p.stock, 3)
        self.client.post(reverse('order_cancel', args=[o.pk]))
        p.refresh_from_db()
        self.assertEqual(p.stock, 5)

    def test_product_list_filters(self):
        cat = Category.objects.create(name='Barbs', slug='barbs', kind='fish')
        for i in range(14):
            Product.objects.create(category=cat, name=f'Fish {i}', price=10 + i, stock=1)
        r = self.client.get(reverse('products'))
        self.assertEqual(len(r.context['page']), 12)
        self.assertEqual(len(self.client.get(reverse('products') + '?page=2').context['page']), 2)
        self.assertEqual(self.client.get(reverse('products') + '?q=Fish 13').context['total'], 1)

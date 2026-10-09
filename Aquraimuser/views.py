from decimal import Decimal
from functools import wraps

from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import CheckoutForm, ContactForm, ProfileForm, RegisterForm
from .models import BlogPost, Category, Order, OrderItem, Product, tb_register


def _safe_next(request, default=None):
    nxt = request.POST.get('next') or request.GET.get('next') or ''
    if nxt and url_has_allowed_host_and_scheme(nxt, {request.get_host()}):
        return nxt
    return default


def user_required(view):
    @wraps(view)
    def wrapper(request, *a, **kw):
        if 'id' not in request.session:
            messages.info(request, 'Please log in to continue.')
            return redirect(f"{reverse('login')}?next={request.get_full_path()}")
        return view(request, *a, **kw)
    return wrapper


# ---------- public pages ----------
def home(request):
    ctx = {
        'fish_cats': Category.objects.filter(kind='fish')[:8],
        'plant_cats': Category.objects.filter(kind='plant')[:8],
        'fish': Product.objects.select_related('category').filter(category__kind='fish').order_by('-featured', '-created')[:8],
        'plants': Product.objects.select_related('category').filter(category__kind='plant').order_by('-featured', '-created')[:4],
        'blogs': BlogPost.objects.filter(published=True)[:3],
    }
    return render(request, 'home.html', ctx)


def categories_view(request):
    cats = Category.objects.annotate(n=Count('products'))
    return render(request, 'categories.html', {
        'fish_cats': cats.filter(kind='fish'), 'plant_cats': cats.filter(kind='plant')})


def products(request, slug=None, kind=None):
    qs = Product.objects.select_related('category')
    cat = None
    if slug:
        cat = get_object_or_404(Category, slug=slug)
        qs = qs.filter(category=cat)
        kind = cat.kind
    elif kind:
        qs = qs.filter(category__kind=kind)
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(description__icontains=q) | Q(category__name__icontains=q))
    if request.GET.get('instock'):
        qs = qs.filter(stock__gt=0)
    sort = request.GET.get('sort', '')
    qs = qs.order_by({'low': 'price', 'high': '-price', 'name': 'name'}.get(sort, '-created'))

    page = Paginator(qs, 12).get_page(request.GET.get('page'))
    params = request.GET.copy()
    params.pop('page', None)
    sidebar = Category.objects.annotate(n=Count('products'))
    if kind:
        sidebar = sidebar.filter(kind=kind)
    return render(request, 'products.html', {
        'page': page, 'cat': cat, 'q': q, 'sort': sort, 'kind': kind, 'instock': request.GET.get('instock'),
        'sidebar': sidebar, 'qs_keep': params.urlencode(), 'total': page.paginator.count})


def product_detail(request, pk):
    p = get_object_or_404(Product.objects.select_related('category'), pk=pk)
    related = Product.objects.select_related('category').filter(category=p.category).exclude(pk=pk)[:4]
    return render(request, 'product_detail.html', {'p': p, 'related': related})


def about(request):
    return render(request, 'about.html', {
        'n_products': Product.objects.count(), 'n_cats': Category.objects.count(),
        'n_customers': tb_register.objects.count(), 'n_orders': Order.objects.count()})


def blogs(request):
    qs = BlogPost.objects.filter(published=True)
    page = Paginator(qs, 6).get_page(request.GET.get('page'))
    return render(request, 'blogs.html', {'page': page})


def blog_detail(request, slug):
    post = get_object_or_404(BlogPost, slug=slug, published=True)
    more = BlogPost.objects.filter(published=True).exclude(pk=post.pk)[:3]
    return render(request, 'blog_detail.html', {'post': post, 'more': more})


def contact(request):
    form = ContactForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Thank you! Your message has been sent. We will get back to you soon.')
        return redirect('contact')
    return render(request, 'contact.html', {'form': form})


# ---------- cart (session based) ----------
def _cart_items(request):
    cart = request.session.get('cart', {})
    prods = Product.objects.select_related('category').filter(pk__in=[int(k) for k in cart])
    items = [{'p': p, 'qty': min(cart[str(p.pk)], p.stock) or 0, 'sub': p.price * min(cart[str(p.pk)], p.stock)}
             for p in prods]
    items = [i for i in items if i['qty'] > 0]
    return items, sum((i['sub'] for i in items), Decimal('0'))


@user_required
def cart_view(request):
    items, total = _cart_items(request)
    return render(request, 'cart.html', {'items': items, 'total': total})


@user_required
def cart_add(request, pk):
    p = get_object_or_404(Product, pk=pk)
    cart = request.session.get('cart', {})
    try:
        qty = max(1, int(request.POST.get('qty', 1)))
    except ValueError:
        qty = 1
    if p.stock == 0:
        messages.error(request, f'{p.name} is out of stock.')
    else:
        cart[str(pk)] = min(cart.get(str(pk), 0) + qty, p.stock)
        request.session['cart'] = cart
        messages.success(request, f'{p.name} added to cart.')
    if request.POST.get('buy') and p.stock:
        return redirect('checkout')
    return redirect(_safe_next(request) or 'cart')


@user_required
def cart_update(request, pk):
    p = get_object_or_404(Product, pk=pk)
    cart = request.session.get('cart', {})
    try:
        qty = int(request.POST.get('qty', 1))
    except ValueError:
        qty = 1
    if qty <= 0:
        cart.pop(str(pk), None)
    else:
        cart[str(pk)] = min(qty, p.stock)
    request.session['cart'] = cart
    return redirect('cart')


@user_required
def cart_remove(request, pk):
    cart = request.session.get('cart', {})
    cart.pop(str(pk), None)
    request.session['cart'] = cart
    return redirect('cart')


@user_required
def checkout(request):
    items, total = _cart_items(request)
    if not items:
        messages.info(request, 'Your cart is empty.')
        return redirect('cart')
    user = get_object_or_404(tb_register, pk=request.session['id'])
    form = CheckoutForm(request.POST or None, initial={'full_name': user.name})
    if request.method == 'POST' and form.is_valid():
        d = form.cleaned_data
        with transaction.atomic():
            lines, grand = [], Decimal('0')
            for i in items:
                p = Product.objects.select_for_update().get(pk=i['p'].pk)
                qty = min(i['qty'], p.stock)
                if qty:
                    lines.append((p, qty))
                    grand += p.price * qty
            if not lines:
                messages.error(request, 'Sorry, those items just went out of stock.')
                request.session['cart'] = {}
                return redirect('cart')
            order = Order.objects.create(user=user, total=grand, **d)
            for p, qty in lines:
                OrderItem.objects.create(order=order, product=p, name=p.name, price=p.price, quantity=qty)
                p.stock -= qty
                p.save(update_fields=['stock'])
        request.session['cart'] = {}
        messages.success(request, f'Order #{order.pk} placed! Pay cash on delivery.')
        return redirect('order', pk=order.pk)
    return render(request, 'checkout.html', {'items': items, 'total': total, 'form': form})


@user_required
def my_orders(request):
    orders = Order.objects.filter(user_id=request.session['id']).prefetch_related('items')
    return render(request, 'orders.html', {'orders': orders})


@user_required
def order_detail(request, pk):
    o = get_object_or_404(Order, pk=pk, user_id=request.session['id'])
    return render(request, 'order_detail.html', {'o': o, 'steps': ['placed', 'shipped', 'delivered']})


@user_required
def order_cancel(request, pk):
    o = get_object_or_404(Order, pk=pk, user_id=request.session['id'])
    if request.method == 'POST' and o.status == 'placed':
        with transaction.atomic():
            for i in o.items.select_related('product'):
                if i.product:
                    i.product.stock += i.quantity
                    i.product.save(update_fields=['stock'])
            o.status = 'cancelled'
            o.save(update_fields=['status'])
        messages.success(request, f'Order #{o.pk} cancelled.')
    return redirect('order', pk=pk)


# ---------- auth ----------
def login(request):
    if 'id' in request.session:
        return redirect('home')
    return render(request, 'login.html', {'next': _safe_next(request, '')})


def loginaction(request):
    if request.method != 'POST':
        return redirect('login')
    email, pw = request.POST.get('email', '').strip(), request.POST.get('password', '')
    u = None
    for cand in tb_register.objects.filter(email__iexact=email).order_by('id'):
        if check_password(pw, cand.password):
            u = cand
        elif cand.password == pw:  # legacy plaintext account: upgrade to a hash
            cand.password = make_password(pw)
            cand.save(update_fields=['password'])
            u = cand
        if u:
            break
    nxt = _safe_next(request, '')
    if not u:
        messages.error(request, 'Invalid email or password.')
        return render(request, 'login.html', {'next': nxt, 'email': email}, status=401)
    request.session.cycle_key()
    request.session['id'] = u.id
    request.session['name'] = u.name
    messages.success(request, f'Welcome back, {u.name}!')
    return redirect(nxt or 'home')


def signup(request):
    if 'id' in request.session:
        return redirect('home')
    return render(request, 'signup.html', {'form': RegisterForm()})


def registeraction(request):
    if request.method != 'POST':
        return redirect('signup')
    form = RegisterForm(request.POST, request.FILES)
    if not form.is_valid():
        return render(request, 'signup.html', {'form': form})
    d = form.cleaned_data
    u = tb_register(name=d['name'], age=d['age'], email=d['email'], password=make_password(d['password']))
    if d.get('image'):
        u.image = d['image']
    u.save()
    messages.success(request, 'Account created successfully. Please log in.')
    return redirect('login')


def logoutaction(request):
    request.session.flush()
    messages.info(request, 'You have been logged out.')
    return redirect('login')


@user_required
def profile(request):
    u = get_object_or_404(tb_register, pk=request.session['id'])
    form = ProfileForm(request.POST or None, request.FILES or None, user=u,
                       initial={'name': u.name, 'age': u.age})
    if request.method == 'POST' and form.is_valid():
        d = form.cleaned_data
        u.name, u.age = d['name'], d['age']
        if d.get('image'):
            u.image = d['image']
        if d.get('new_password'):
            u.password = make_password(d['new_password'])
        u.save()
        request.session['name'] = u.name
        messages.success(request, 'Profile updated.')
        return redirect('profile')
    orders = u.orders.all()
    spent = sum((o.total for o in orders if o.status != 'cancelled'), Decimal('0'))
    return render(request, 'profile.html', {'u': u, 'form': form, 'recent': orders[:3],
                                            'order_count': orders.count(), 'spent': spent})

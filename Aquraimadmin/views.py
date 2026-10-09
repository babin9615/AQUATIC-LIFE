import hmac
from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from Aquraimuser.models import BlogPost, Category, ContactMessage, Order, Product, tb_register

from .forms import BlogForm, CategoryForm, ProductForm

PER_PAGE = 12


def admin_required(view):
    @wraps(view)
    def wrapper(request, *a, **kw):
        if not request.session.get('is_admin'):
            messages.info(request, 'Please sign in as admin.')
            return redirect('adminhome')
        return view(request, *a, **kw)
    return wrapper


def _page(request, qs, per=PER_PAGE):
    params = request.GET.copy()
    params.pop('page', None)
    return Paginator(qs, per).get_page(request.GET.get('page')), params.urlencode()


def _unread():
    return ContactMessage.objects.filter(is_read=False).count()


def _render(request, template, ctx, tab):
    ctx.update({'tab': tab, 'unread': _unread()})
    return render(request, template, ctx)


# ---------- login / logout ----------
def adminhome(request):
    if request.session.get('is_admin'):
        return redirect('dashboard')
    return render(request, 'adminlogin.html')


def adminlogin(request):
    if request.method != 'POST':
        return redirect('adminhome')
    email = request.POST.get('email', '').strip().lower()
    pw = request.POST.get('password', '')
    ok_email = hmac.compare_digest(email.encode(), settings.ADMIN_EMAIL.lower().encode())
    ok_pw = hmac.compare_digest(pw.encode(), settings.ADMIN_PASSWORD.encode())
    if ok_email and ok_pw:
        request.session.cycle_key()
        request.session['is_admin'] = True
        messages.success(request, 'Welcome back, admin!')
        return redirect('dashboard')
    messages.error(request, 'Invalid admin email or password.')
    return redirect('adminhome')


def adminlogout(request):
    request.session.pop('is_admin', None)
    messages.info(request, 'You have been logged out.')
    return redirect('adminhome')


# ---------- dashboard ----------
@admin_required
def dashboard(request):
    ctx = {
        'users': tb_register.objects.count(),
        'fish': Product.objects.filter(category__kind='fish').count(),
        'plants': Product.objects.filter(category__kind='plant').count(),
        'cats': Category.objects.count(),
        'blogs': BlogPost.objects.count(),
        'orders': Order.objects.count(),
        'revenue': Order.objects.exclude(status='cancelled').aggregate(t=Sum('total'))['t'] or 0,
        'recent': Order.objects.select_related('user')[:5],
        'low': Product.objects.select_related('category').filter(stock__lte=3)[:6],
        'latest_msgs': ContactMessage.objects.all()[:4],
    }
    return _render(request, 'a_dashboard.html', ctx, 'dashboard')


# ---------- products: fish, plants, all ----------
@admin_required
def products(request, kind=None):
    qs = Product.objects.select_related('category')
    if kind:
        qs = qs.filter(category__kind=kind)
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(category__name__icontains=q))
    page, keep = _page(request, qs)
    title = {'fish': 'Fish', 'plant': 'Aquatic plants'}.get(kind, 'All products')
    return _render(request, 'a_products.html', {'page': page, 'qs_keep': keep, 'q': q, 'kind': kind, 'title': title},
                   {'fish': 'fish', 'plant': 'plant'}.get(kind, 'products'))


@admin_required
def product_view(request, pk):
    p = get_object_or_404(Product.objects.select_related('category'), pk=pk)
    return _render(request, 'a_product_view.html', {'p': p}, p.category.kind)


@admin_required
def product_edit(request, pk=None):
    obj = get_object_or_404(Product, pk=pk) if pk else None
    kind = request.GET.get('kind') or (obj.category.kind if obj else None)
    if kind not in ('fish', 'plant'):
        kind = 'fish'
    form = ProductForm(request.POST or None, request.FILES or None, instance=obj, kind=kind)
    if request.method == 'POST' and form.is_valid():
        p = form.save()
        messages.success(request, f'“{p.name}” saved.')
        return redirect('a_plants' if p.category.kind == 'plant' else 'a_fish')
    label = 'plant' if kind == 'plant' else 'fish'
    ctx = {'form': form, 'obj': obj, 'kind': kind, 'has_cats': form.fields['category'].queryset.exists(),
           'back': reverse('a_plants' if kind == 'plant' else 'a_fish'),
           'title': f'Edit {obj.name}' if obj else f'Add {label}', 'is_product': True}
    return _render(request, 'a_form.html', ctx, kind)


@admin_required
def product_delete(request, pk):
    p = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        back = 'a_plants' if p.category.kind == 'plant' else 'a_fish'
        p.delete()
        messages.success(request, 'Product deleted.')
        return redirect(back)
    return redirect('a_product_view', pk=pk)


# ---------- categories ----------
@admin_required
def categories(request):
    return _render(request, 'a_categories.html',
                   {'items': Category.objects.annotate(n=Count('products')).order_by('kind', 'name')}, 'categories')


@admin_required
def category_edit(request, pk=None):
    obj = get_object_or_404(Category, pk=pk) if pk else None
    form = CategoryForm(request.POST or None, request.FILES or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Category saved.')
        return redirect('a_categories')
    return _render(request, 'a_form.html', {'form': form, 'obj': obj, 'back': reverse('a_categories'),
                   'title': 'Edit category' if obj else 'Add category'}, 'categories')


@admin_required
def category_delete(request, pk):
    if request.method == 'POST':
        get_object_or_404(Category, pk=pk).delete()
        messages.success(request, 'Category and its products deleted.')
    return redirect('a_categories')


# ---------- blogs ----------
@admin_required
def blogs(request):
    return _render(request, 'a_blogs.html', {'items': BlogPost.objects.all()}, 'blogs')


@admin_required
def blog_edit(request, pk=None):
    obj = get_object_or_404(BlogPost, pk=pk) if pk else None
    form = BlogForm(request.POST or None, request.FILES or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Blog post saved.')
        return redirect('a_blogs')
    return _render(request, 'a_form.html', {'form': form, 'obj': obj, 'back': reverse('a_blogs'),
                   'title': 'Edit blog post' if obj else 'Add blog post'}, 'blogs')


@admin_required
def blog_delete(request, pk):
    if request.method == 'POST':
        get_object_or_404(BlogPost, pk=pk).delete()
        messages.success(request, 'Blog post deleted.')
    return redirect('a_blogs')


# ---------- contact messages ----------
@admin_required
def contact_messages(request):
    page, keep = _page(request, ContactMessage.objects.all(), 15)
    return _render(request, 'a_messages.html', {'page': page, 'qs_keep': keep}, 'messages')


@admin_required
def message_detail(request, pk):
    m = get_object_or_404(ContactMessage, pk=pk)
    if not m.is_read:
        m.is_read = True
        m.save(update_fields=['is_read'])
    return _render(request, 'a_message.html', {'m': m}, 'messages')


@admin_required
def message_delete(request, pk):
    if request.method == 'POST':
        get_object_or_404(ContactMessage, pk=pk).delete()
        messages.success(request, 'Message deleted.')
    return redirect('a_messages')


# ---------- orders ----------
@admin_required
def orders(request):
    if request.method == 'POST':
        o = get_object_or_404(Order, pk=request.POST.get('order'))
        if request.POST.get('status') in dict(Order.STATUS):
            o.status = request.POST['status']
            o.save(update_fields=['status'])
            messages.success(request, f'Order #{o.pk} marked {o.get_status_display().lower()}.')
        back = request.POST.get('back', '')
        return redirect(back if back.startswith('/aquraimadmin/') else 'a_orders')
    status = request.GET.get('status')
    qs = Order.objects.select_related('user').prefetch_related('items')
    if status in dict(Order.STATUS):
        qs = qs.filter(status=status)
    page, keep = _page(request, qs, 15)
    return _render(request, 'a_orders.html', {'page': page, 'qs_keep': keep, 'statuses': Order.STATUS, 'status': status}, 'orders')


@admin_required
def order_detail(request, pk):
    o = get_object_or_404(Order.objects.select_related('user').prefetch_related('items'), pk=pk)
    return _render(request, 'a_order.html', {'o': o, 'statuses': Order.STATUS}, 'orders')


# ---------- users ----------
@admin_required
def users(request):
    q = request.GET.get('q', '').strip()
    qs = tb_register.objects.annotate(n=Count('orders'))
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(email__icontains=q))
    page, keep = _page(request, qs.order_by('-id'), 15)
    return _render(request, 'a_users.html', {'page': page, 'qs_keep': keep, 'q': q}, 'users')


@admin_required
def user_detail(request, pk):
    u = get_object_or_404(tb_register, pk=pk)
    orders_ = u.orders.prefetch_related('items')
    spent = orders_.exclude(status='cancelled').aggregate(t=Sum('total'))['t'] or 0
    return _render(request, 'a_user.html', {'u': u, 'orders': orders_, 'spent': spent}, 'users')


@admin_required
def user_delete(request, pk):
    if request.method == 'POST':
        get_object_or_404(tb_register, pk=pk).delete()
        messages.success(request, 'User deleted.')
    return redirect('a_users')

from django.urls import path
from . import views as v

urlpatterns = [
    path('', v.adminhome, name='adminhome'),
    path('adminaction', v.adminlogin, name='adminaction'),
    path('logout/', v.adminlogout, name='adminlogout'),
    path('dashboard/', v.dashboard, name='dashboard'),

    path('fish/', v.products, {'kind': 'fish'}, name='a_fish'),
    path('plants/', v.products, {'kind': 'plant'}, name='a_plants'),
    path('products/', v.products, name='a_products'),
    path('products/new/', v.product_edit, name='a_product_new'),
    path('products/<int:pk>/', v.product_view, name='a_product_view'),
    path('products/<int:pk>/edit/', v.product_edit, name='a_product_edit'),
    path('products/<int:pk>/delete/', v.product_delete, name='a_product_delete'),

    path('categories/', v.categories, name='a_categories'),
    path('categories/new/', v.category_edit, name='a_category_new'),
    path('categories/<int:pk>/edit/', v.category_edit, name='a_category_edit'),
    path('categories/<int:pk>/delete/', v.category_delete, name='a_category_delete'),

    path('blogs/', v.blogs, name='a_blogs'),
    path('blogs/new/', v.blog_edit, name='a_blog_new'),
    path('blogs/<int:pk>/edit/', v.blog_edit, name='a_blog_edit'),
    path('blogs/<int:pk>/delete/', v.blog_delete, name='a_blog_delete'),

    path('messages/', v.contact_messages, name='a_messages'),
    path('messages/<int:pk>/', v.message_detail, name='a_message'),
    path('messages/<int:pk>/delete/', v.message_delete, name='a_message_delete'),

    path('orders/', v.orders, name='a_orders'),
    path('orders/<int:pk>/', v.order_detail, name='a_order'),
    path('users/', v.users, name='a_users'),
    path('users/<int:pk>/', v.user_detail, name='a_user'),
    path('users/<int:pk>/delete/', v.user_delete, name='a_user_delete'),
]

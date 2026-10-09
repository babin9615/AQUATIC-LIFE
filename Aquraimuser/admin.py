from django.contrib import admin
from .models import BlogPost, Category, ContactMessage, Order, OrderItem, Product, tb_register

admin.site.register([Category, Product, tb_register, BlogPost, ContactMessage])


class ItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'total', 'status', 'created']
    inlines = [ItemInline]

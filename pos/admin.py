from django.contrib import admin
from .models import Product, Order, OrderItem, Invoice, Customer, Payment, OrderSplit

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price')
    search_fields = ('name',)

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at')
    search_fields = ('customer__name', 'customer__email')
    raw_id_fields = ('customer',)
    inlines = [OrderItemInline]

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('product', 'order', 'quantity', 'price_at_time_of_order')

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'order', 'status', 'is_split', 'issued_at')
    search_fields = ('invoice_number',)
    list_filter = ('status', 'is_split', 'issued_at')

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'phone', 'created_at')
    search_fields = ('name', 'email', 'phone')
    list_filter = ('created_at',)

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'invoice', 'customer', 'amount', 'payment_method', 'reference', 'paid_at')
    search_fields = ('invoice__invoice_number', 'customer__name', 'reference')
    list_filter = ('payment_method', 'paid_at')

@admin.register(OrderSplit)
class OrderSplitAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'customer', 'amount', 'note')
    search_fields = ('order__id', 'customer__name', 'note')
    list_filter = ('customer',)


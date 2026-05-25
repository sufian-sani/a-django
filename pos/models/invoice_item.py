from decimal import Decimal

from django.db import models
from django.core.exceptions import ValidationError

from .invoice import Invoice
from .order_item import OrderItem


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, related_name='invoice_items', on_delete=models.CASCADE)
    order_item = models.ForeignKey(OrderItem, related_name='invoice_items', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'invoice_items'
        constraints = [
            models.UniqueConstraint(fields=['invoice', 'order_item'], name='uniq_invoice_order_item'),
        ]

    def clean(self):
        if self.invoice_id and self.order_item_id and self.invoice.order_id != self.order_item.order_id:
            raise ValidationError({'order_item': 'Order item must belong to the same order as the invoice.'})

        if self.quantity <= 0:
            raise ValidationError({'quantity': 'Quantity must be greater than zero.'})

        if self.order_item_id and self.quantity > self.order_item.quantity:
            raise ValidationError({'quantity': 'Quantity cannot exceed order item quantity.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        self.subtotal = self.quantity * self.unit_price
        self.total_amount = self.subtotal + self.tax_amount - self.discount_amount
        if self.total_amount < Decimal('0.00'):
            self.total_amount = Decimal('0.00')
        super().save(*args, **kwargs)
        self.invoice.recalculate(save=True)

    def delete(self, *args, **kwargs):
        invoice = self.invoice
        super().delete(*args, **kwargs)
        invoice.recalculate(save=True)

    def __str__(self):
        return f"InvoiceItem #{self.id} (Invoice #{self.invoice_id})"

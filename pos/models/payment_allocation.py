from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum


class PaymentAllocation(models.Model):
    payment = models.ForeignKey('Payment', related_name='allocations', on_delete=models.CASCADE)
    invoice_item = models.ForeignKey('InvoiceItem', related_name='payment_allocations', on_delete=models.CASCADE)
    allocated_amount = models.DecimalField(max_digits=10, decimal_places=2)
    allocated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'payment_allocations'
        constraints = [
            models.UniqueConstraint(fields=['payment', 'invoice_item'], name='uniq_payment_invoice_item'),
        ]

    def clean(self):
        if self.allocated_amount <= Decimal('0.00'):
            raise ValidationError({'allocated_amount': 'Allocated amount must be greater than zero.'})

        if self.payment_id and self.invoice_item_id and self.payment.invoice_id != self.invoice_item.invoice_id:
            raise ValidationError({'invoice_item': 'Invoice item must belong to the same invoice as payment.'})

        if self.payment_id:
            allocated_for_payment = self.payment.allocations.exclude(pk=self.pk).aggregate(
                total=Sum('allocated_amount')
            )['total'] or Decimal('0.00')
            if allocated_for_payment + self.allocated_amount > self.payment.amount:
                raise ValidationError({'allocated_amount': 'Allocated amount exceeds payment amount.'})

        if self.invoice_item_id:
            allocated_for_item = self.invoice_item.payment_allocations.exclude(pk=self.pk).aggregate(
                total=Sum('allocated_amount')
            )['total'] or Decimal('0.00')
            if allocated_for_item + self.allocated_amount > self.invoice_item.total_amount:
                raise ValidationError({'allocated_amount': 'Allocated amount exceeds invoice item total.'})

    @staticmethod
    def sync_invoice_item_payment_state(invoice_item):
        paid = invoice_item.payment_allocations.aggregate(total=Sum('allocated_amount'))['total'] or Decimal('0.00')
        if paid < Decimal('0.00'):
            paid = Decimal('0.00')
        if paid > invoice_item.total_amount:
            paid = invoice_item.total_amount

        balance = invoice_item.total_amount - paid
        if balance < Decimal('0.00'):
            balance = Decimal('0.00')

        invoice_item.__class__.objects.filter(pk=invoice_item.pk).update(
            paid_amount=round(paid, 2),
            balance_amount=round(balance, 2),
        )

    @classmethod
    def sync_invoice_payment_state(cls, invoice):
        for invoice_item in invoice.invoice_items.all():
            cls.sync_invoice_item_payment_state(invoice_item)
        invoice.recalculate(save=True)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        self.sync_invoice_payment_state(self.payment.invoice)

    def delete(self, *args, **kwargs):
        invoice = self.payment.invoice
        invoice_item = self.invoice_item
        super().delete(*args, **kwargs)
        self.sync_invoice_item_payment_state(invoice_item)
        invoice.recalculate(save=True)

    def __str__(self):
        return f"Allocation {self.id}: Payment #{self.payment_id} -> InvoiceItem #{self.invoice_item_id}"
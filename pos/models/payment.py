from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Sum
from .invoice import Invoice
from .customer import Customer

class Payment(models.Model):
    invoice = models.ForeignKey(Invoice, related_name='payments', on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, related_name='payments', on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20)
    reference = models.CharField(max_length=100, blank=True, null=True)
    paid_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.amount <= 0:
            raise ValidationError({'amount': 'Payment amount must be greater than zero.'})

        if not self.invoice_id:
            return

        self.invoice.recalculate(save=False)
        existing_paid = self.invoice.payments.exclude(pk=self.pk).aggregate(total=Sum('amount'))['total'] or 0
        next_paid = existing_paid + self.amount
        if next_paid > self.invoice.total_amount:
            raise ValidationError({'amount': 'Payment exceeds invoice balance. Overpayment is not allowed.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        self.invoice.recalculate(save=True)

    def delete(self, *args, **kwargs):
        invoice = self.invoice
        super().delete(*args, **kwargs)
        invoice.recalculate(save=True)

    def __str__(self):
        return f"Payment {self.id} - {self.payment_method} - ${self.amount}"

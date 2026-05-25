from django.db import models
from django.db.models import Sum, F
from .order import Order


TWO_DP = 2

class Invoice(models.Model):
    order = models.ForeignKey(Order, related_name='invoice', on_delete=models.CASCADE)
    invoice_number = models.CharField(max_length=50, unique=True)
    split_type = models.CharField(max_length=20, default='full', help_text='full | item_wise | amount_wise')
    status = models.CharField(
        max_length=20,
        default='Unpaid',
        choices=(
            ('Paid', 'Paid'),
            ('Unpaid', 'Unpaid'),
            ('Overdue', 'Overdue'),
            ('Cancelled', 'Cancelled'),
        ),
        help_text='Paid | Unpaid | Overdue | Cancelled',
    )
    is_split = models.BooleanField(default=False, help_text='Whether this invoice is a split payment')
    subtotal_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    balance_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    issued_at = models.DateTimeField(auto_now_add=True)

    @property
    def items(self):
        """Return invoice-specific items when split-by-item is used, otherwise order items."""
        if self.invoice_items.exists():
            return self.invoice_items.select_related('order_item')
        return self.order.items.all()

    def recalculate_totals(self):
        invoice_items_qs = self.invoice_items.all()
        if invoice_items_qs.exists():
            subtotal = invoice_items_qs.aggregate(total=Sum('subtotal'))['total'] or 0
            tax = invoice_items_qs.aggregate(total=Sum('tax_amount'))['total'] or 0
            discount = invoice_items_qs.aggregate(total=Sum('discount_amount'))['total'] or 0
        else:
            subtotal = self.order.items.aggregate(
                total=Sum(F('quantity') * F('price_at_time_of_order'))
            )['total'] or 0
            tax = 0
            discount = 0

        total = subtotal + tax - discount
        if total < 0:
            total = 0

        self.subtotal_amount = round(subtotal, TWO_DP)
        self.tax_amount = round(tax, TWO_DP)
        self.discount_amount = round(discount, TWO_DP)
        self.total_amount = round(total, TWO_DP)

    def recalculate_payment_state(self):
        paid = self.payments.aggregate(total=Sum('amount'))['total'] or 0
        balance = self.total_amount - paid
        if balance < 0:
            balance = 0

        self.paid_amount = round(paid, TWO_DP)
        self.balance_amount = round(balance, TWO_DP)
        self.status = 'Paid' if self.balance_amount <= 0 else 'Unpaid'
        self.is_split = self.invoice_items.exists() or self.payments.count() > 1

    def recalculate(self, *, save=True):
        self.recalculate_totals()
        self.recalculate_payment_state()
        if save:
            self.save(update_fields=[
                'subtotal_amount',
                'tax_amount',
                'discount_amount',
                'total_amount',
                'paid_amount',
                'balance_amount',
                'status',
                'is_split',
            ])

    def __str__(self):
        return self.invoice_number

from django.db import models
from .order import Order

class Invoice(models.Model):
    order = models.OneToOneField(Order, related_name='invoice', on_delete=models.CASCADE)
    invoice_number = models.CharField(max_length=50, unique=True)
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
    issued_at = models.DateTimeField(auto_now_add=True)

    @property
    def items(self):
        """Return OrderItems associated with this invoice via its order."""
        return self.order.items.all()

    def __str__(self):
        return self.invoice_number

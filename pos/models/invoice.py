from django.db import models
from .order import Order

class Invoice(models.Model):
    order = models.OneToOneField(Order, related_name='invoice', on_delete=models.CASCADE)
    invoice_number = models.CharField(max_length=50, unique=True)
    issued_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.invoice_number

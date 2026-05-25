from django.db import models
from .order import Order
from .customer import Customer

class OrderSplit(models.Model):
    order = models.ForeignKey(Order, related_name='splits', on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, related_name='splits', on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    note = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        customer_name = self.customer.name if self.customer else "Walk-in"
        return f"Split for Order #{self.order.id} - {customer_name}: ${self.amount}"

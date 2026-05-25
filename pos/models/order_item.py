from django.db import models
from .order import Order
from .product import Product

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    product_name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(default=1)
    price_at_time_of_order = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        if not self.product_name and self.product_id:
            self.product_name = self.product.name
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity} x {self.product_name} (Order #{self.order.id})"

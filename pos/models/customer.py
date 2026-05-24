from django.db import models

class Customer(models.Model):
    name = models.CharField(max_length=255, null=False)
    email = models.EmailField(max_length=255, unique=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} <{self.email}>"

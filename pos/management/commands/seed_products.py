from django.core.management.base import BaseCommand
from pos.models import Product

class Command(BaseCommand):
    help = 'Seeds the database with initial products'

    def handle(self, *args, **kwargs):
        products_data = [
            {"name": "Laptop", "description": "High performance laptop", "price": 1200.00},
            {"name": "Mouse", "description": "Wireless optical mouse", "price": 25.50},
            {"name": "Keyboard", "description": "Mechanical keyboard", "price": 75.00},
            {"name": "Monitor", "description": "27-inch 4K monitor", "price": 300.00},
            {"name": "Desk", "description": "Standing desk", "price": 450.00},
            {"name": "Chair", "description": "Ergonomic office chair", "price": 250.00},
        ]

        self.stdout.write("Seeding products...")
        
        created_count = 0
        for item in products_data:
            # Using get_or_create to avoid duplicates if run multiple times
            obj, created = Product.objects.get_or_create(
                name=item["name"],
                defaults={
                    "description": item["description"],
                    "price": item["price"]
                }
            )
            if created:
                created_count += 1
                
        self.stdout.write(self.style.SUCCESS(f'Successfully seeded {created_count} products.'))

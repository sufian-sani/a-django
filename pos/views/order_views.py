import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.db import transaction
from django.db.models import Sum, F
from pos.models import Product, Order, OrderItem

def order_list(request):
    # Fetch orders and calculate their total price by summing item quantities * prices
    orders = Order.objects.annotate(
        total_price=Sum(F('items__quantity') * F('items__price_at_time_of_order'))
    ).order_by('-created_at')
    
    context = {
        'orders': orders
    }
    return render(request, 'pos/order_list.html', context)

def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    items = order.items.select_related('product').all()
    
    # Calculate the subtotal for each item and the total for the order
    order_total = 0
    for item in items:
        item.subtotal = item.quantity * item.price_at_time_of_order
        order_total += item.subtotal
        
    context = {
        'order': order,
        'items': items,
        'order_total': order_total
    }
    return render(request, 'pos/order_detail.html', context)

@ensure_csrf_cookie
def mark_order_completed(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        order.status = 'Completed'
        order.save()
        return JsonResponse({"message": "Order marked as completed", "status": order.status})
    return JsonResponse({"error": "Method not allowed"}, status=405)

@ensure_csrf_cookie
def create_order(request):
    if request.method == 'GET':
        products = Product.objects.all()
        # Passing serialized products to avoid extra queries and simplify frontend
        products_data = [
            {"id": p.id, "name": p.name, "price": str(p.price)} for p in products
        ]
        context = {
            'products_json': json.dumps(products_data)
        }
        return render(request, 'pos/create_order.html', context)
        
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            items = data.get('items', [])
            
            if not items:
                return JsonResponse({"error": "No items in order"}, status=400)
                
            with transaction.atomic():
                # Create Order
                order = Order.objects.create(status='Pending')
                
                # Create Order Items
                for item in items:
                    product = Product.objects.get(id=item['product_id'])
                    quantity = int(item['quantity'])
                    
                    if quantity <= 0:
                        raise ValueError(f"Invalid quantity for {product.name}")
                        
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=quantity,
                        price_at_time_of_order=product.price
                    )
                    
            return JsonResponse({"message": "Order created successfully!", "order_id": order.id}, status=201)
            
        except Product.DoesNotExist:
            return JsonResponse({"error": "Product not found"}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
            
    return JsonResponse({"error": "Method not allowed"}, status=405)

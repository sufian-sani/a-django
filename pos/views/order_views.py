import json
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.csrf import ensure_csrf_cookie
from django.db import transaction
from django.db.models import Sum, F
from pos.models import Product, Order, OrderItem, Invoice, Customer, Payment

def order_list(request):
    # Fetch orders and calculate their total price by summing item quantities * prices
    orders = Order.objects.select_related('customer').annotate(
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
        
        # Create Invoice
        invoice, created = Invoice.objects.get_or_create(
            order=order,
            defaults={'invoice_number': f'INV-{order.id}'}
        )
        
        return JsonResponse({"message": "Order marked as completed", "status": order.status})
    return JsonResponse({"error": "Method not allowed"}, status=405)

def order_invoice(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    items = order.items.select_related('product').all()
    
    # Ensure invoice exists (for any old completed orders)
    invoice, created = Invoice.objects.get_or_create(
        order=order,
        defaults={'invoice_number': f'INV-{order.id}'}
    )
    
    order_total = 0
    for item in items:
        item.subtotal = item.quantity * item.price_at_time_of_order
        order_total += item.subtotal
        
    context = {
        'order': order,
        'invoice': invoice,
        'items': items,
        'order_total': order_total
    }
    return render(request, 'pos/invoice.html', context)

@ensure_csrf_cookie
def order_payment(request, order_id):
    """Render a simple payment page and process payment.
    On GET: show total and a Pay button.
    On POST: mark order as completed, create invoice, then redirect to invoice view.
    """
    order = get_object_or_404(Order, id=order_id)
    items = order.items.select_related('product').all()
    # calculate totals
    order_total = sum(item.quantity * item.price_at_time_of_order for item in items)
    if request.method == 'POST':
        # Here you would integrate a real payment gateway.
        # For this demo we just assume payment succeeded.
        # Mark the order as completed
        # Determine payment method from request (default to Cash) and capitalize to match choices (Card, Cash)
        payment_method = request.POST.get('payment_method', 'Cash').capitalize()
        if payment_method not in dict(Order.PAYMENT_METHOD_CHOICES):
            payment_method = 'Cash'
            
        order.status = 'Completed'
        order.payment_method = payment_method
        order.save()
        # Create or get Invoice
        invoice, created = Invoice.objects.get_or_create(
            order=order,
            defaults={'invoice_number': f'INV-{order.id}', 'status': 'Unpaid'}
        )
        # Create Payment record using selected method
        Payment.objects.create(
            invoice=invoice,
            customer=order.customer,
            amount=order_total,
            method=payment_method,
            reference='auto-generated'
        )
        # Redirect to printable invoice page
        return redirect('order_detail', order_id=order.id)
    else:
        context = {
            'order': order,
            'items': items,
            'order_total': order_total,
            'payment_methods': Order.PAYMENT_METHOD_CHOICES,
        }
        return render(request, 'pos/payment.html', context)

def create_order(request):
    if request.method == 'GET':
        products = Product.objects.all()
        customers = Customer.objects.all().order_by('name')
        products_data = [
            {"id": p.id, "name": p.name, "price": str(p.price)} for p in products
        ]
        context = {
            'products_json': json.dumps(products_data),
            'customers': customers,
        }
        return render(request, 'pos/create_order.html', context)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            items = data.get('items', [])
            
            if not items:
                return JsonResponse({"error": "No items in order"}, status=400)
            
            customer_id = data.get('customer_id')
            customer = None
            if customer_id:
                try:
                    customer = Customer.objects.get(id=customer_id)
                except Customer.DoesNotExist:
                    pass

            with transaction.atomic():
                # Create Order (optionally linked to a customer)
                order = Order.objects.create(status='Pending', customer=customer)
                
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
                
                # Calculate total for the order
                total_amount = sum(
                    Product.objects.get(id=item['product_id']).price * int(item['quantity'])
                    for item in items
                )
                # Create Invoice
                invoice = Invoice.objects.create(
                    order=order,
                    invoice_number=f'INV-{order.id}',
                    status='Unpaid'
                )

                
            return JsonResponse({"message": "Order created successfully!", "order_id": order.id}, status=201)
        except Product.DoesNotExist:
            return JsonResponse({"error": "Product not found"}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    else:
        return JsonResponse({"error": "Method not allowed"}, status=405)

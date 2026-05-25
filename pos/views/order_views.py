import json
from decimal import Decimal
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
        
    invoice = getattr(order, 'invoice', None)
    payments = invoice.payments.all() if invoice else []
    
    context = {
        'order': order,
        'items': items,
        'order_total': order_total,
        'invoice': invoice,
        'payments': payments,
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
    On GET: show total, paid amount, remaining balance, and options.
    On POST: record a payment of specified amount and update order/invoice states.
    """
    order = get_object_or_404(Order, id=order_id)
    items = order.items.select_related('product').all()
    # calculate totals
    order_total = sum(item.quantity * item.price_at_time_of_order for item in items)
    
    # Create or get Invoice
    invoice, created = Invoice.objects.get_or_create(
        order=order,
        defaults={'invoice_number': f'INV-{order.id}', 'status': 'Unpaid'}
    )
    
    # Calculate already paid and remaining amount
    paid_amount = invoice.payments.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    remaining_amount = Decimal(order_total) - Decimal(paid_amount)
    
    if request.method == 'POST':
        # Determine payment method from request (default to Cash) and capitalize
        payment_method = request.POST.get('payment_method', 'Cash').capitalize()
        if payment_method not in ('Cash', 'Card'):
            payment_method = 'Cash'
            
        # Get payment amount from post, fallback to remaining_amount
        amount_str = request.POST.get('amount')
        if amount_str:
            try:
                amount_to_pay = Decimal(amount_str)
            except ValueError:
                amount_to_pay = remaining_amount
        else:
            amount_to_pay = remaining_amount
            
        # Ensure it is positive and doesn't exceed the remaining balance
        if amount_to_pay <= 0 or amount_to_pay > remaining_amount:
            amount_to_pay = remaining_amount
            
        if amount_to_pay > 0:
            # Create Payment record using selected method
            Payment.objects.create(
                invoice=invoice,
                customer=order.customer,
                amount=amount_to_pay,
                payment_method=payment_method,
                reference='auto-generated'
            )
            
        # Re-evaluate payment status and split flag
        total_paid = invoice.payments.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        payments_count = invoice.payments.count()
        
        if total_paid >= Decimal(order_total):
            # Fully paid
            invoice.status = 'Paid'
            order.status = 'Completed'
            invoice.is_split = (payments_count > 1)
        else:
            # Partial payment — still unpaid, mark as split
            invoice.status = 'Unpaid'
            invoice.is_split = True
            
        invoice.save()
        
        # Determine what to store as the order's payment_method
        if payments_count > 1:
            # Check if all payments used the same method
            distinct_methods = invoice.payments.values_list('payment_method', flat=True).distinct()
            if distinct_methods.count() == 1:
                order.payment_method = distinct_methods.first()
            else:
                order.payment_method = 'Split'
        else:
            order.payment_method = payment_method
        order.save()
        
        # If still unpaid, redirect back to payment page for the next installment
        if invoice.status == 'Unpaid':
            return redirect('order_payment', order_id=order.id)
        return redirect('order_detail', order_id=order.id)
    else:
        context = {
            'order': order,
            'items': items,
            'order_total': order_total,
            'paid_amount': paid_amount,
            'remaining_amount': remaining_amount,
            'payment_methods': [('Cash', 'Cash'), ('Card', 'Card')],
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

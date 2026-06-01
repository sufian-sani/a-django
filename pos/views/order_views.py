import json
from decimal import Decimal, InvalidOperation
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.csrf import ensure_csrf_cookie
from django.db import transaction
from django.db.models import Sum, F
from pos.models import Product, Order, OrderItem, Invoice, InvoiceItem, Customer, Payment, PaymentAllocation


def _create_invoice_for_order(order):
    invoice_count = order.invoice.count() + 1
    invoice = Invoice.objects.create(
        order=order,
        invoice_number=f'INV-{order.id}-{invoice_count}',
        status='Unpaid',
    )
    for item in order.items.all():
        subtotal = item.quantity * item.price_at_time_of_order
        InvoiceItem.objects.create(
            invoice=invoice,
            order_item=item,
            quantity=item.quantity,
            unit_price=item.price_at_time_of_order,
            subtotal=subtotal,
            tax_amount=Decimal('0.00'),
            discount_amount=Decimal('0.00'),
            total_amount=subtotal,
        )
    invoice.recalculate(save=True)
    return invoice


def _get_active_invoice(order):
    active_invoice = order.invoice.filter(status__in=('Unpaid', 'Overdue')).order_by('-issued_at', '-id').first()
    if active_invoice:
        return active_invoice
    latest_invoice = order.invoice.order_by('-issued_at', '-id').first()
    if latest_invoice:
        return latest_invoice
    return _create_invoice_for_order(order)


def _allocate_payment_to_invoice_items(payment, amount, selected_item_ids=None):
    invoice = payment.invoice
    remaining = amount
    invoice_items = invoice.invoice_items.select_for_update().order_by('id')
    if selected_item_ids:
        invoice_items = invoice_items.filter(id__in=selected_item_ids)

    for invoice_item in invoice_items:
        if remaining <= Decimal('0.00'):
            break

        item_balance = invoice_item.balance_amount
        if item_balance <= Decimal('0.00'):
            continue

        applied = min(item_balance, remaining)
        PaymentAllocation.objects.create(
            payment=payment,
            invoice_item=invoice_item,
            allocated_amount=applied,
        )
        remaining -= applied

    if remaining > Decimal('0.00'):
        raise ValidationError('Unable to allocate payment to invoice items.')


def _get_selected_invoice_items(invoice, selected_item_ids):
    if not selected_item_ids:
        return invoice.invoice_items.all()
    return invoice.invoice_items.filter(id__in=selected_item_ids)

def order_list(request):
    # Fetch orders and calculate their total price by summing item quantities * prices
    orders = (
        Order.objects.select_related('customer')
        .prefetch_related('invoice__payments')
        .annotate(
            total_price=Sum(F('items__quantity') * F('items__price_at_time_of_order'))
        )
        .order_by('-created_at')
    )

    for order in orders:
        invoices = list(order.invoice.all())
        if not invoices:
            order.payment_method = None
            continue

        methods = []
        for inv in invoices:
            methods.extend([payment.payment_method for payment in inv.payments.all() if payment.payment_method])
        order.payment_method = ' + '.join(methods) if methods else None
    
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
        
    invoice = order.invoice.order_by('-issued_at', '-id').first()
    payments = Payment.objects.filter(invoice__order=order).select_related('invoice').order_by('-paid_at')

    method_list = [payment.payment_method for payment in payments if payment.payment_method]
    order.payment_method = ' + '.join(method_list) if method_list else None
    
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
        
        # Ensure at least one invoice exists
        if not order.invoice.exists():
            _create_invoice_for_order(order)
        
        return JsonResponse({"message": "Order marked as completed", "status": order.status})
    return JsonResponse({"error": "Method not allowed"}, status=405)

def order_invoice(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    items = order.items.select_related('product').all()
    
    # Use latest invoice, or create one if none exists.
    invoice = order.invoice.order_by('-issued_at', '-id').first() or _create_invoice_for_order(order)
    
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
    
    # Get active invoice (supports multiple invoices per order)
    invoice = _get_active_invoice(order)
    invoice.recalculate(save=True)
    
    # Calculate already paid and remaining amount
    paid_amount = invoice.paid_amount
    remaining_amount = invoice.balance_amount
    invoice_items = invoice.invoice_items.select_related('order_item').order_by('id')
    
    if request.method == 'POST':
        with transaction.atomic():
            # Lock invoice row so concurrent payment attempts cannot overpay.
            invoice = Invoice.objects.select_for_update().get(pk=invoice.pk)
            invoice.recalculate(save=True)
            remaining_amount = invoice.balance_amount

            if remaining_amount <= 0:
                return redirect('order_detail', order_id=order.id)

            split_mode = request.POST.get('split_amount_mode') == '1'
            payment_mode = (request.POST.get('payment_mode', 'full') or 'full').strip().lower()
            selected_item_ids = [
                int(v) for v in request.POST.getlist('invoice_item_ids') if str(v).isdigit()
            ]
            selected_items = _get_selected_invoice_items(invoice, selected_item_ids)
            selected_balance = selected_items.aggregate(total=Sum('balance_amount'))['total'] or Decimal('0.00')
            payable_items_qs = invoice.invoice_items.filter(balance_amount__gt=0)
            payable_items_count = payable_items_qs.count()
            selected_payable_count = selected_items.filter(balance_amount__gt=0).count()

            invoice.set_split_type_from_payment_mode(
                payment_mode,
                split_mode=split_mode,
                has_partial_item_selection=(payable_items_count > 0 and selected_payable_count < payable_items_count),
                save=True,
            )

            if split_mode:
                card_amount_raw = request.POST.get('card_amount', '0')
                cash_amount_raw = request.POST.get('cash_amount', '0')

                try:
                    card_amount = Decimal(card_amount_raw or '0')
                except (ValueError, InvalidOperation):
                    card_amount = Decimal('0.00')

                try:
                    cash_amount = Decimal(cash_amount_raw or '0')
                except (ValueError, InvalidOperation):
                    cash_amount = Decimal('0.00')

                card_amount = max(card_amount, Decimal('0.00'))
                cash_amount = max(cash_amount, Decimal('0.00'))
                split_total = card_amount + cash_amount

                if split_total <= 0:
                    return redirect('order_payment', order_id=order.id)

                if split_total > remaining_amount:
                    return redirect('order_payment', order_id=order.id)

                if split_total > selected_balance:
                    return redirect('order_payment', order_id=order.id)

                if card_amount > 0:
                    card_payment = Payment.objects.create(
                        invoice=invoice,
                        customer=order.customer,
                        amount=card_amount,
                        payment_method='Card',
                        reference='split-card'
                    )
                    _allocate_payment_to_invoice_items(card_payment, card_amount, selected_item_ids)

                if cash_amount > 0:
                    cash_payment = Payment.objects.create(
                        invoice=invoice,
                        customer=order.customer,
                        amount=cash_amount,
                        payment_method='Cash',
                        reference='split-cash'
                    )
                    _allocate_payment_to_invoice_items(cash_payment, cash_amount, selected_item_ids)
            else:
                payment_method = (request.POST.get('payment_method', 'Cash') or 'Cash').strip().title()

                amount_str = request.POST.get('amount')
                if amount_str:
                    try:
                        amount_to_pay = Decimal(amount_str)
                    except (ValueError, InvalidOperation):
                        return redirect('order_payment', order_id=order.id)
                else:
                    return redirect('order_payment', order_id=order.id)

                if amount_to_pay <= 0:
                    return redirect('order_payment', order_id=order.id)

                if amount_to_pay > remaining_amount:
                    return redirect('order_payment', order_id=order.id)

                if amount_to_pay > selected_balance:
                    return redirect('order_payment', order_id=order.id)

                try:
                    payment = Payment.objects.create(
                        invoice=invoice,
                        customer=order.customer,
                        amount=amount_to_pay,
                        payment_method=payment_method,
                        reference='auto-generated'
                    )
                    _allocate_payment_to_invoice_items(payment, amount_to_pay, selected_item_ids)
                except ValidationError:
                    return redirect('order_payment', order_id=order.id)

            invoice.refresh_from_db()
            invoice.recalculate(save=True)

            has_unpaid_invoices = order.invoice.exclude(status='Paid').exists()
            order.status = 'Pending' if has_unpaid_invoices else 'Completed'
            order.save(update_fields=['status', 'updated_at'])

        # If still unpaid, redirect back to payment page for the next installment
        if invoice.status == 'Unpaid':
            return redirect('order_payment', order_id=order.id)
        return redirect('order_detail', order_id=order.id)
    else:
        context = {
            'order': order,
            'invoice': invoice,
            'items': items,
            'order_total': order_total,
            'paid_amount': paid_amount,
            'remaining_amount': remaining_amount,
            'invoice_items': invoice_items,
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
                        product_name=product.name,
                        quantity=quantity,
                        price_at_time_of_order=product.price
                    )
                
                # Calculate total for the order
                total_amount = sum(
                    Product.objects.get(id=item['product_id']).price * int(item['quantity'])
                    for item in items
                )
                # Create first invoice with item snapshots.
                _create_invoice_for_order(order)

                
            return JsonResponse({"message": "Order created successfully!", "order_id": order.id}, status=201)
        except Product.DoesNotExist:
            return JsonResponse({"error": "Product not found"}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    else:
        return JsonResponse({"error": "Method not allowed"}, status=405)

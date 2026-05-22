from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('create-order/', views.create_order, name='create_order'),
    path('orders/', views.order_list, name='order_list'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('orders/<int:order_id>/complete/', views.mark_order_completed, name='mark_order_completed'),
    path('orders/<int:order_id>/invoice/', views.order_invoice, name='order_invoice'),
]

from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('create-order/', views.create_order, name='create_order'),
    path('orders/', views.order_list, name='order_list'),
]

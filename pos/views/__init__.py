from django.shortcuts import render
from django.http import JsonResponse

def index(request):
    return JsonResponse({"message": "Welcome to the POS API"})

from .order_views import create_order, order_list, order_detail

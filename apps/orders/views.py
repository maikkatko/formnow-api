from django.shortcuts import render

from rest_framework import viewsets
from rest_framework.response import Response
from django.db.models import Count
from .models import Order, OrderItem
from .serializers import (
    OrderListSerializer,
    OrderDetailSerializer,
    OrderCreateSerializer,
    OrderItemSerializer
)

class OrderViewSet(viewsets.ModelViewSet):
    """
    Manages Orders.
    
    Queryset Optimization:
    - prefetch_related('items__material'): Loads items and their specific material 
      in one go to prevent N+1 queries when viewing details.
    """
    queryset = Order.objects.all().prefetch_related('items__material')

    def get_serializer_class(self):
        if self.action == 'create':
            # Uses the heavy write-logic serializer (nested creation)
            return OrderCreateSerializer
        if self.action == 'list':
            # Uses the lightweight serializer (no nested items)
            return OrderListSerializer
        # Default (retrieve, update, destroy) uses the full detail view
        return OrderDetailSerializer

    def get_queryset(self):
        """
        Optional: Optimize the 'item_count' for the list view.
        """
        queryset = super().get_queryset()
        if self.action == 'list':
            # This allows filtering/sorting by item count if needed in the future
            return queryset.annotate(item_count_annotated=Count('items'))
        return queryset


class OrderItemViewSet(viewsets.ModelViewSet):
    """
    Direct access to Order Items.
    Useful for updating specific item status (e.g. quantity_completed)
    without re-saving the entire Order.
    """
    queryset = OrderItem.objects.all().select_related('order', 'material')
    serializer_class = OrderItemSerializer

    # If you need to restrict what can be updated on an item level
    # (e.g., only allow patching quantity_completed), you can override update/partial_update

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count

from .models import PrintJob, PrintJobItem
from .serializers import (
    PrintJobListSerializer,
    PrintJobDetailSerializer,
    PrintJobUpdateSerializer,
    PrintJobItemSerializer
)

class PrintJobViewSet(viewsets.ModelViewSet):
    """
    Manages the Print Queue.
    
    Optimizations:
    - List View: Fetches printer, batch, and assigned employee info.
    - Detail View: Deeply prefetches items -> batch_item -> order_item -> order 
      to populate the nested item fields without N+1 queries.
    """
    queryset = PrintJob.objects.all().select_related(
        'printer', 
        'batch', 
        'assigned_to__user'
    )

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == 'list':
            # Annotate item count for the list view
            return queryset.annotate(item_count=Count('items'))
        
        # For detail view, we need deep nesting for the items
        if self.action == 'retrieve':
            return queryset.prefetch_related(
                'items__batch_item__order_item__order'
            )
        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return PrintJobListSerializer
        
        # Use the specific state-transition serializer for updates
        if self.action in ['update', 'partial_update']:
            return PrintJobUpdateSerializer
            
        return PrintJobDetailSerializer

    @action(detail=True, methods=['post'])
    def claim(self, request, pk=None):
        """
        Quick action for an operator to 'Claim' a job (assign to self).
        """
        job = self.get_object()
        # Assuming request.user has an employee profile
        if hasattr(request.user, 'employee'):
            job.assigned_to = request.user.employee
            job.save()
            return Response({'status': 'job claimed', 'assigned_to': str(request.user.employee)})
        return Response({'error': 'User is not an employee'}, status=400)


class PrintJobItemViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only access to individual job items.
    Useful for looking up a specific label/part on the floor.
    """
    queryset = PrintJobItem.objects.all().select_related(
        'batch_item__order_item__order'
    )
    serializer_class = PrintJobItemSerializer

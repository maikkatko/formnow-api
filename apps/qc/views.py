from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import QCInspection, QCItemResult
from .serializers import (
    QCInspectionSerializer, 
    QCItemResultSerializer, 
    QCInspectionSubmitSerializer
)

class QCInspectionViewSet(viewsets.ModelViewSet):
    """
    Manages QC Inspections.
    
    Query Optimization:
    - select_related: Fetches the PrintJob and the Employee who inspected it.
    - prefetch_related: Deeply fetches the item results -> print_job_item -> 
      batch_item -> order_item. This is required to show 'model_name' 
      on the item results without hitting the DB for every single item.
    """
    queryset = QCInspection.objects.all().select_related(
        'print_job', 
        'inspected_by__user'
    ).prefetch_related(
        'item_results__print_job_item__batch_item__order_item'
    )
    
    def get_serializer_class(self):
        if self.action == 'submit':
            return QCInspectionSubmitSerializer
        return QCInspectionSerializer

    def perform_create(self, serializer):
        # Automatically assign the logged-in employee when starting an inspection
        if self.request.user.is_authenticated and hasattr(self.request.user, 'employee'):
            serializer.save(inspected_by=self.request.user.employee) # type: ignore
        else:
            serializer.save()

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """
        Custom action to finalize the inspection.
        Expects a payload with 'result', 'notes', and a list of 'item_results'.
        """
        inspection = self.get_object()
        
        # Initialize the Submit Serializer with the instance and incoming data
        serializer = QCInspectionSubmitSerializer(inspection, data=request.data)
        
        if serializer.is_valid():
            # This triggers the specific 'update' method in your SubmitSerializer
            # which sets status='COMPLETED' and updates/creates child items.
            updated_inspection = serializer.save()
            
            # Return the full read-only representation of the updated inspection
            # so the frontend can update its UI immediately.
            read_serializer = QCInspectionSerializer(updated_inspection)
            return Response(read_serializer.data, status=status.HTTP_200_OK)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class QCItemResultViewSet(viewsets.ModelViewSet):
    """
    Direct access to specific item results.
    Useful if you want to update just ONE item's failure reason 
    without re-submitting the whole inspection.
    """
    queryset = QCItemResult.objects.all().select_related(
        'print_job_item__batch_item__order_item'
    )
    serializer_class = QCItemResultSerializer

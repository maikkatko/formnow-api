# apps/production/views.py - ENHANCED with custom actions

from django.utils import timezone
from rest_framework import viewsets, status
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
    
    Standard CRUD + custom actions for production workflow.
    """
    queryset = PrintJob.objects.all().select_related(
        'printer', 
        'batch', 
        'assigned_to__user'
    )

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by printer
        printer = self.request.query_params.get('printer')
        if printer:
            queryset = queryset.filter(printer_id=printer)
        
        # Filter by batch
        batch = self.request.query_params.get('batch')
        if batch:
            queryset = queryset.filter(batch_id=batch)
        
        if self.action == 'list':
            return queryset.annotate(item_count=Count('items'))
        
        if self.action == 'retrieve':
            return queryset.prefetch_related('items__batch_item__order_item__order')
        
        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return PrintJobListSerializer
        if self.action in ['update', 'partial_update']:
            return PrintJobUpdateSerializer
        return PrintJobDetailSerializer

    @action(detail=True, methods=['post'])
    def claim(self, request, pk=None):
        """
        POST /api/v1/print-jobs/{id}/claim/
        
        Operator claims this job (assigns to themselves).
        """
        job = self.get_object()
        
        if not hasattr(request.user, 'employee'):
            return Response(
                {'error': 'User is not an employee'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        job.assigned_to = request.user.employee
        job.save()
        
        return Response({
            'status': 'job claimed',
            'job_id': str(job.id),
            'assigned_to': str(request.user.employee),
        })

    @action(detail=True, methods=['post'])
    def assign_printer(self, request, pk=None):
        """
        POST /api/v1/print-jobs/{id}/assign_printer/
        
        Assign a printer to this job.
        Body: { "printer_id": "PRINTER-001" }
        """
        job = self.get_object()
        printer_id = request.data.get('printer_id')
        
        if not printer_id:
            return Response(
                {'error': 'printer_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate printer exists and is available
        from apps.fleet.models import Printer
        try:
            printer = Printer.objects.get(pk=printer_id)
        except Printer.DoesNotExist:
            return Response(
                {'error': f'Printer {printer_id} not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        if printer.status not in ['IDLE', 'OFFLINE']:
            return Response(
                {'error': f'Printer {printer.name} is not available (status: {printer.status})'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        job.printer = printer
        job.status = 'QUEUED'
        job.queued_at = timezone.now()
        job.save()
        
        return Response({
            'status': 'printer assigned',
            'job_id': str(job.id),
            'printer_id': printer_id,
            'printer_name': printer.name,
        })

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """
        POST /api/v1/print-jobs/{id}/start/
        
        Mark job as started (printing).
        """
        job = self.get_object()
        
        if job.status not in ['QUEUED', 'READY']:
            return Response(
                {'error': f'Cannot start job with status {job.status}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not job.printer:
            return Response(
                {'error': 'No printer assigned to this job'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update job
        job.status = 'PRINTING'
        job.started_at = timezone.now()
        if hasattr(request.user, 'employee'):
            job.started_by = request.user.employee
        job.save()
        
        # Update printer status
        job.printer.status = 'PRINTING'
        job.printer.save()
        
        return Response({
            'status': 'job started',
            'job_id': str(job.id),
            'started_at': job.started_at.isoformat(),
        })

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """
        POST /api/v1/print-jobs/{id}/complete/
        
        Mark job as completed successfully.
        """
        job = self.get_object()
        
        if job.status != 'PRINTING':
            return Response(
                {'error': f'Cannot complete job with status {job.status}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        job.status = 'COMPLETED'
        job.completed_at = timezone.now()
        job.save()
        
        # Update printer status back to idle
        if job.printer:
            job.printer.status = 'IDLE'
            job.printer.save()
        
        # Update print job items
        job.items.update(status='PRINTED')
        
        return Response({
            'status': 'job completed',
            'job_id': str(job.id),
            'completed_at': job.completed_at.isoformat(),
        })

    @action(detail=True, methods=['post'])
    def fail(self, request, pk=None):
        """
        POST /api/v1/print-jobs/{id}/fail/
        
        Mark job as failed.
        Body: { "reason": "description of failure" }
        """
        job = self.get_object()
        reason = request.data.get('reason', '')
        
        if job.status not in ['PRINTING', 'QUEUED']:
            return Response(
                {'error': f'Cannot fail job with status {job.status}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        job.status = 'FAILED'
        job.failure_reason = reason
        job.completed_at = timezone.now()
        job.save()
        
        # Update printer status
        if job.printer:
            job.printer.status = 'ERROR' if not reason else 'IDLE'
            job.printer.save()
        
        # Update print job items
        job.items.update(status='FAILED')
        
        return Response({
            'status': 'job marked as failed',
            'job_id': str(job.id),
            'failure_reason': reason,
        })

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        POST /api/v1/print-jobs/{id}/cancel/
        
        Cancel a pending or queued job.
        """
        job = self.get_object()
        
        if job.status not in ['PENDING', 'READY', 'QUEUED']:
            return Response(
                {'error': f'Cannot cancel job with status {job.status}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        job.status = 'CANCELLED'
        job.save()
        
        return Response({
            'status': 'job cancelled',
            'job_id': str(job.id),
        })


class PrintJobItemViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only access to individual job items.
    """
    queryset = PrintJobItem.objects.all().select_related(
        'batch_item__order_item__order'
    )
    serializer_class = PrintJobItemSerializer
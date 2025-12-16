# apps/dashboard/views.py
"""
Dashboard views providing aggregated stats for the MES frontend.
"""

from datetime import datetime, timedelta
from django.db.models import Sum, Avg
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from apps.orders.models import Order
from apps.production.models import PrintJob
from apps.fleet.models import Printer
from apps.batching.models import PrintBatch


class DashboardStatsView(APIView):
    """
    GET /api/v1/dashboard/stats/
    
    Returns aggregated statistics for the dashboard.
    """
    
    def get(self, request):
        today = timezone.now().date()
        today_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
        today_end = timezone.make_aware(datetime.combine(today, datetime.max.time()))
        
        # Order stats
        active_orders = Order.objects.exclude(
            status__in=['SHIPPED', 'CANCELLED']
        ).count()
        
        orders_received_today = Order.objects.filter(
            received_at__range=(today_start, today_end)
        ).count()
        
        # Printer stats
        printers_total = Printer.objects.filter(is_connected=True).count()
        printers_printing = Printer.objects.filter(status='PRINTING').count()
        printers_idle = Printer.objects.filter(status='IDLE', is_connected=True).count()
        printers_error = Printer.objects.filter(status='ERROR').count()
        printers_maintenance = Printer.objects.filter(status='MAINTENANCE').count()
        
        # Production stats (today)
        jobs_completed_today = PrintJob.objects.filter(
            completed_at__range=(today_start, today_end),
            status='COMPLETED'
        ).count()
        
        jobs_in_progress = PrintJob.objects.filter(
            status='PRINTING'
        ).count()
        
        jobs_queued = PrintJob.objects.filter(
            status__in=['PENDING', 'READY', 'QUEUED']
        ).count()
        
        # Parts produced today (sum of quantities from completed jobs)
        parts_produced_today = PrintJob.objects.filter(
            completed_at__range=(today_start, today_end),
            status='COMPLETED'
        ).aggregate(
            total=Sum('items__quantity')
        )['total'] or 0
        
        # Average print time today (completed jobs)
        avg_print_time = PrintJob.objects.filter(
            completed_at__range=(today_start, today_end),
            status='COMPLETED',
            estimated_print_time_s__isnull=False
        ).aggregate(
            avg=Avg('estimated_print_time_s')
        )['avg']
        
        avg_print_time_minutes = round(avg_print_time / 60) if avg_print_time else 0
        
        # Batches stats
        batches_collecting = PrintBatch.objects.filter(status='COLLECTING').count()
        batches_ready = PrintBatch.objects.filter(status='READY').count()
        batches_running = PrintBatch.objects.filter(status='RUNNING').count()
        
        # Alerts
        alerts = self._get_alerts()
        
        return Response({
            # Orders
            'active_orders': active_orders,
            'orders_received_today': orders_received_today,
            
            # Printers
            'printers_total': printers_total,
            'printers_printing': printers_printing,
            'printers_idle': printers_idle,
            'printers_error': printers_error,
            'printers_maintenance': printers_maintenance,
            'printer_utilization': round(
                (printers_printing / printers_total * 100) if printers_total > 0 else 0
            ),
            
            # Production
            'jobs_completed_today': jobs_completed_today,
            'jobs_in_progress': jobs_in_progress,
            'jobs_queued': jobs_queued,
            'parts_produced_today': parts_produced_today,
            'avg_print_time_minutes': avg_print_time_minutes,
            
            # Batches
            'batches_collecting': batches_collecting,
            'batches_ready': batches_ready,
            'batches_running': batches_running,
            
            # Alerts
            'alerts': alerts,
            'alert_count': len(alerts),
        })
    
    def _get_alerts(self):
        """Generate list of alerts that need attention"""
        alerts = []
        
        # Printers with errors
        error_printers = Printer.objects.filter(status='ERROR')
        for printer in error_printers:
            alerts.append({
                'type': 'error',
                'severity': 'critical',
                'title': f'Printer Error: {printer.name}',
                'message': f'{printer.name} has an error and needs attention',
                'link': f'/printers/{printer.id}',
            })
        
        # Printers offline (but expected to be connected)
        offline_printers = Printer.objects.filter(
            status='OFFLINE',
            is_connected=False
        ).exclude(status='MAINTENANCE')[:5]  # Limit to 5
        for printer in offline_printers:
            alerts.append({
                'type': 'warning',
                'severity': 'medium',
                'title': f'Printer Offline: {printer.name}',
                'message': f'{printer.name} is offline',
                'link': f'/printers/{printer.id}',
            })
        
        # Overdue orders
        overdue_orders = Order.objects.filter(
            due_date__lt=timezone.now(),
            status__in=['RECEIVED', 'PROCESSING', 'IN_PRODUCTION', 'POST_PROCESSING', 'QC']
        )[:5]  # Limit to 5
        for order in overdue_orders:
            alerts.append({
                'type': 'warning',
                'severity': 'high',
                'title': f'Overdue Order: {order.external_id}',
                'message': f'Order {order.external_id} is past due date',
                'link': f'/orders/{order.id}',
            })
        
        # Failed print jobs (not re-queued)
        failed_jobs = PrintJob.objects.filter(
            status='FAILED',
            completed_at__gte=timezone.now() - timedelta(days=1)
        )[:5]
        for job in failed_jobs:
            alerts.append({
                'type': 'error',
                'severity': 'high',
                'title': f'Failed Print Job: {job.job_name}',
                'message': job.failure_reason or 'Print job failed',
                'link': f'/production/{job.id}',
            })
        
        # Rush orders not yet in production
        rush_orders = Order.objects.filter(
            priority='RUSH',
            status__in=['RECEIVED', 'PROCESSING']
        )[:3]
        for order in rush_orders:
            alerts.append({
                'type': 'info',
                'severity': 'medium',
                'title': f'Rush Order Pending: {order.external_id}',
                'message': f'Rush order {order.external_id} not yet in production',
                'link': f'/orders/{order.id}',
            })
        
        return alerts


class ProductionQueueView(APIView):
    """
    GET /api/v1/dashboard/queue/
    
    Returns aggregated production queue grouped by status.
    """
    
    def get(self, request):
        # Ready to print (pending/ready but not yet queued to printer)
        ready_to_print = PrintJob.objects.filter(
            status__in=['PENDING', 'READY']
        ).select_related(
            'batch', 'batch__material', 'assigned_to__user'
        ).order_by('created_at')[:20]
        
        # Currently printing
        currently_printing = PrintJob.objects.filter(
            status='PRINTING'
        ).select_related(
            'printer', 'batch', 'batch__material'
        )
        
        # Queued to printer (waiting for printer)
        queued = PrintJob.objects.filter(
            status='QUEUED'
        ).select_related(
            'printer', 'batch', 'batch__material'
        ).order_by('queued_at')[:20]
        
        # Recently completed (last 2 hours for post-processing tracking)
        two_hours_ago = timezone.now() - timedelta(hours=2)
        recently_completed = PrintJob.objects.filter(
            status='COMPLETED',
            completed_at__gte=two_hours_ago
        ).select_related(
            'printer', 'batch', 'batch__material'
        ).order_by('-completed_at')[:10]
        
        return Response({
            'ready_to_print': self._serialize_jobs(ready_to_print),
            'queued': self._serialize_jobs(queued),
            'currently_printing': self._serialize_jobs(currently_printing),
            'recently_completed': self._serialize_jobs(recently_completed),
            'counts': {
                'ready': ready_to_print.count(),
                'queued': PrintJob.objects.filter(status='QUEUED').count(),
                'printing': currently_printing.count(),
            }
        })
    
    def _serialize_jobs(self, jobs):
        """Simple serialization for queue view"""
        result = []
        for job in jobs:
            result.append({
                'id': str(job.id),
                'job_name': job.job_name,
                'status': job.status,
                'printer_id': job.printer_id,
                'printer_name': job.printer.name if job.printer else None,
                'batch_id': str(job.batch_id),
                'material_code': job.batch.material_id if job.batch else None,
                'material_label': job.batch.material.label if job.batch and job.batch.material else None,
                'estimated_print_time_s': job.estimated_print_time_s,
                'assigned_to': job.assigned_to.user.get_full_name() if job.assigned_to else None,
                'created_at': job.created_at.isoformat() if job.created_at else None,
                'queued_at': job.queued_at.isoformat() if job.queued_at else None,
                'started_at': job.started_at.isoformat() if job.started_at else None,
                'completed_at': job.completed_at.isoformat() if job.completed_at else None,
            })
        return result


class ProductionMetricsView(APIView):
    """
    GET /api/v1/dashboard/metrics/
    
    Returns production metrics for charts/analytics.
    Query params:
      - days: number of days to look back (default 7)
    """
    
    def get(self, request):
        days = int(request.query_params.get('days', 7))
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days - 1)
        
        # Build daily stats
        daily_stats = []
        current_date = start_date
        
        while current_date <= end_date:
            day_start = timezone.make_aware(datetime.combine(current_date, datetime.min.time()))
            day_end = timezone.make_aware(datetime.combine(current_date, datetime.max.time()))
            
            # Jobs completed
            jobs = PrintJob.objects.filter(
                completed_at__range=(day_start, day_end),
                status='COMPLETED'
            )
            jobs_count = jobs.count()
            
            # Parts produced
            parts = jobs.aggregate(total=Sum('items__quantity'))['total'] or 0
            
            # Orders received
            orders_received = Order.objects.filter(
                received_at__range=(day_start, day_end)
            ).count()
            
            # Orders shipped
            orders_shipped = Order.objects.filter(
                shipped_at__range=(day_start, day_end)
            ).count()
            
            daily_stats.append({
                'date': current_date.isoformat(),
                'jobs_completed': jobs_count,
                'parts_produced': parts,
                'orders_received': orders_received,
                'orders_shipped': orders_shipped,
            })
            
            current_date += timedelta(days=1)
        
        return Response({
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
                'days': days,
            },
            'daily': daily_stats,
            'totals': {
                'jobs_completed': sum(d['jobs_completed'] for d in daily_stats),
                'parts_produced': sum(d['parts_produced'] for d in daily_stats),
                'orders_received': sum(d['orders_received'] for d in daily_stats),
                'orders_shipped': sum(d['orders_shipped'] for d in daily_stats),
            }
        })
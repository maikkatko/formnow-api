import uuid
from django.db import models

class QCInspection(models.Model):
    """QC inspection of a completed print job"""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
    ]
    
    RESULT_CHOICES = [
        ('PASSED', 'Passed'),
        ('PARTIAL', 'Partial Pass'),
        ('FAILED', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    print_job = models.OneToOneField(
        'production.PrintJob', 
        on_delete=models.CASCADE, 
        related_name='qc_inspection'
    )
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    result = models.CharField(max_length=20, choices=RESULT_CHOICES, blank=True)
    
    inspected_by = models.ForeignKey('employees.Employee', on_delete=models.SET_NULL, null=True)
    started_at = models.DateTimeField(null=True)
    completed_at = models.DateTimeField(null=True)
    
    notes = models.TextField(blank=True)


class QCItemResult(models.Model):
    """Per-item QC results"""
    
    inspection = models.ForeignKey(QCInspection, on_delete=models.CASCADE, related_name='item_results')
    print_job_item = models.ForeignKey(
        'production.PrintJobItem', 
        on_delete=models.CASCADE,
        related_name='qc_results'
    )
    
    quantity_passed = models.PositiveIntegerField(default=0)
    quantity_failed = models.PositiveIntegerField(default=0)
    failure_reason = models.TextField(blank=True)
    
    # Photo documentation
    photos = models.JSONField(default=list)  # List of file paths


class QCChecklist(models.Model):
    """Checklist template for QC inspections"""
    name = models.CharField(max_length=100)
    material = models.ForeignKey('core.Material', on_delete=models.CASCADE, null=True, blank=True)
    is_active = models.BooleanField(default=True)


class QCChecklistItem(models.Model):
    """Individual check in a checklist"""
    checklist = models.ForeignKey(QCChecklist, on_delete=models.CASCADE, related_name='items')
    description = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)
    is_required = models.BooleanField(default=True)

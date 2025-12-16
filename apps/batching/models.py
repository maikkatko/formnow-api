import uuid
from django.db import models

class PrintBatch(models.Model):
    """Group of items with same material/settings"""
    
    STATUS_CHOICES = [
        ('COLLECTING', 'Collecting'),
        ('READY', 'Ready to Schedule'),
        ('SCHEDULED', 'Scheduled'),
        ('RUNNING', 'Running'),
        ('CLOSED', 'Closed')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    
    # Print settings for this batch
    material = models.ForeignKey('core.Material', on_delete=models.PROTECT)
    layer_thickness_mm = models.CharField(max_length=20)
    machine_type = models.ForeignKey('core.MachineType', on_delete=models.PROTECT)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='COLLECTING')
    priority = models.CharField(max_length=20, default='STANDARD')
    must_schedule_by = models.DateTimeField(null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    scheduled_at = models.DateTimeField(null=True)


class BatchItem(models.Model):
    """Links order items to batches"""
    batch = models.ForeignKey(PrintBatch, on_delete=models.CASCADE, related_name='items')
    order_item = models.ForeignKey('orders.OrderItem', on_delete=models.CASCADE, related_name='batch_items')
    quantity = models.PositiveIntegerField()
    
    # Is this a reprint?
    is_reprint = models.BooleanField(default=False)
    original_failure = models.ForeignKey(
        'production.FailedPartRecord', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    
    class Meta:
        unique_together = ['batch', 'order_item']

import uuid
from django.db import models

class Scene(models.Model):
    """PreFormServer scene for a print job"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    preform_scene_id = models.CharField(max_length=100, blank=True)  # ID from API
    
    machine_type = models.ForeignKey('core.MachineType', on_delete=models.PROTECT)
    material = models.ForeignKey('core.Material', on_delete=models.PROTECT)
    layer_thickness_mm = models.CharField(max_length=20)
    
    # Computed values from PreFormServer
    layer_count = models.IntegerField(null=True)
    volume_ml = models.FloatField(null=True)
    
    form_file_path = models.CharField(max_length=500, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)


class SceneModel(models.Model):
    """A model placed in a scene"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    scene = models.ForeignKey(Scene, on_delete=models.CASCADE, related_name='models')
    batch_item = models.ForeignKey('batching.BatchItem', on_delete=models.CASCADE)
    
    # Position
    position_x = models.FloatField(default=0)
    position_y = models.FloatField(default=0)
    position_z = models.FloatField(default=0)
    
    # Orientation (Euler angles)
    orientation_x = models.FloatField(default=0)
    orientation_y = models.FloatField(default=0)
    orientation_z = models.FloatField(default=0)
    
    scale = models.FloatField(default=1.0)
    has_supports = models.BooleanField(default=False)
    in_bounds = models.BooleanField(default=True)


class PrintJob(models.Model):
    """A single print run"""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('READY', 'Ready'),
        ('QUEUED', 'Queued'),
        ('PRINTING', 'Printing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    batch = models.ForeignKey('batching.PrintBatch', on_delete=models.CASCADE, related_name='jobs')
    scene = models.ForeignKey(Scene, on_delete=models.PROTECT, null=True)
    printer = models.ForeignKey('fleet.Printer', on_delete=models.SET_NULL, null=True)
    
    job_name = models.CharField(max_length=255)
    formlabs_job_id = models.CharField(max_length=100, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    failure_reason = models.TextField(blank=True)
    
    # Time estimates
    estimated_print_time_s = models.IntegerField(null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    queued_at = models.DateTimeField(null=True)
    started_at = models.DateTimeField(null=True)
    completed_at = models.DateTimeField(null=True)

    progress_percent = models.FloatField(default=0.0)
    current_layer = models.IntegerField(default=0)
    total_layers = models.IntegerField(null=True)
    
    # Who worked on it
    assigned_to = models.ForeignKey(
        'employees.Employee', 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='assigned_jobs'
    )
    started_by = models.ForeignKey(
        'employees.Employee', 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='started_jobs'
    )


class PrintJobItem(models.Model):
    """Parts on a build plate"""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PRINTING', 'Printing'),
        ('PRINTED', 'Printed'),
        ('FAILED', 'Failed'),
    ]
    
    job = models.ForeignKey(PrintJob, on_delete=models.CASCADE, related_name='items')
    batch_item = models.ForeignKey('batching.BatchItem', on_delete=models.CASCADE, related_name='job_items')
    scene_model = models.ForeignKey(SceneModel, on_delete=models.SET_NULL, null=True)
    
    quantity = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')


class FailedPartRecord(models.Model):
    """Tracks parts that need reprinting"""
    
    FAILURE_TYPE_CHOICES = [
        ('PRINT_FAILED', 'Print Failed'),
        ('QC_DEFECT', 'QC Defect'),
        ('POST_PROCESS_DAMAGE', 'Post-Processing Damage'),
        ('SHIPPING_DAMAGE', 'Shipping Damage')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    order_item = models.ForeignKey('orders.OrderItem', on_delete=models.CASCADE, related_name='failures')
    original_job = models.ForeignKey(PrintJob, on_delete=models.SET_NULL, null=True)
    
    quantity = models.PositiveIntegerField()
    failure_type = models.CharField(max_length=30, choices=FAILURE_TYPE_CHOICES)
    failure_reason = models.TextField(blank=True)
    
    requeued = models.BooleanField(default=False)
    requeued_to_batch = models.ForeignKey(
        'batching.PrintBatch', 
        on_delete=models.SET_NULL, 
        null=True,
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('employees.Employee', on_delete=models.SET_NULL, null=True)


class AsyncOperation(models.Model):
    """Track long-running PreFormServer operations"""
    
    STATUS_CHOICES = [
        ('IN_PROGRESS', 'In Progress'),
        ('SUCCEEDED', 'Succeeded'),
        ('FAILED', 'Failed'),
    ]
    
    OPERATION_TYPES = [
        ('AUTO_ORIENT', 'Auto Orient'),
        ('AUTO_SUPPORT', 'Auto Support'),
        ('AUTO_LAYOUT', 'Auto Layout'),
        ('IMPORT_MODEL', 'Import Model'),
        ('PRINT', 'Print'),
        ('SAVE_FORM', 'Save Form File'),
    ]
    
    operation_id = models.UUIDField(primary_key=True)
    operation_type = models.CharField(max_length=30, choices=OPERATION_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='IN_PROGRESS')
    progress = models.FloatField(default=0.0)
    
    scene = models.ForeignKey(Scene, on_delete=models.CASCADE, null=True)
    print_job = models.ForeignKey(PrintJob, on_delete=models.CASCADE, null=True)
    
    result = models.JSONField(null=True)
    error_message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True)

import uuid
from django.db import models

class Order(models.Model):
    """Order received from now.formlabs.com"""
    
    STATUS_CHOICES = [
        ('RECEIVED', 'Received'),
        ('PROCESSING', 'Processing'),
        ('IN_PRODUCTION', 'In Production'),
        ('POST_PROCESSING', 'Post Processing'),
        ('QC', 'Quality Check'),
        ('PACKING', 'Packing'),
        ('SHIPPED', 'Shipped'),
        ('CANCELLED', 'Cancelled'),
    ]
        
    PRIORITY_CHOICES = [
        ('STANDARD', 'Standard'),
        ('RUSH', 'Rush'),
        ('EXPEDITED', 'Expedited'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    external_id = models.CharField(max_length=100, unique=True)  # From web app
    
    # Customer info (denormalized)
    customer_email = models.EmailField()
    customer_name = models.CharField(max_length=200)
    shipping_address = models.TextField()
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='RECEIVED')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='STANDARD')
    due_date = models.DateTimeField(null=True)
    
    received_at = models.DateTimeField(auto_now_add=True)
    shipped_at = models.DateTimeField(null=True)
    
    raw_payload = models.JSONField(null=True)  # Original request from web app


class OrderItem(models.Model):
    """Line item in an order"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    
    # File info
    model_file_url = models.URLField()
    model_file_name = models.CharField(max_length=255)
    local_file_path = models.CharField(max_length=500, blank=True)
    
    # What they want
    quantity = models.PositiveIntegerField()
    material = models.ForeignKey('core.Material', on_delete=models.PROTECT)
    layer_thickness_mm = models.CharField(max_length=20)
    
    # Geometry (populated after file analysis)
    bounding_box_x = models.FloatField(null=True)
    bounding_box_y = models.FloatField(null=True)
    bounding_box_z = models.FloatField(null=True)
    volume_ml = models.FloatField(null=True)
    
    # Progress tracking
    quantity_completed = models.PositiveIntegerField(default=0)
    
    @property
    def quantity_remaining(self):
        return self.quantity - self.quantity_completed
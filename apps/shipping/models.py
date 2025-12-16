import uuid
from django.db import models

class Shipment(models.Model):
    """A shipment to a customer"""
    
    STATUS_CHOICES = [
        ('PACKING', 'Packing'),
        ('READY', 'Ready to Ship'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
    ]
    
    CARRIER_CHOICES = [
        ('USPS', 'USPS'),
        ('UPS', 'UPS'),
        ('FEDEX', 'FedEx'),
        ('DHL', 'DHL'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE, related_name='shipments')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PACKING')
    carrier = models.CharField(max_length=20, choices=CARRIER_CHOICES, blank=True)
    tracking_number = models.CharField(max_length=100, blank=True)
    
    weight_oz = models.FloatField(null=True)
    
    packed_by = models.ForeignKey('employees.Employee', on_delete=models.SET_NULL, null=True)
    packed_at = models.DateTimeField(null=True)
    shipped_at = models.DateTimeField(null=True)


class ShipmentItem(models.Model):
    """What's in the shipment"""
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='items')
    order_item = models.ForeignKey('orders.OrderItem', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
from django.db import models

class Printer(models.Model):
    """Physical printer on the factory floor"""
    CONNECTION_CHOICES = [
        ('USB', 'USB'),
        ('WIFI', 'WiFi'),
        ('ETHERNET', 'Ethernet'),
    ]
    
    STATUS_CHOICES = [
        ('IDLE', 'Idle'),
        ('PRINTING', 'Printing'),
        ('OFFLINE', 'Offline'),
        ('MAINTENANCE', 'Maintenance'),
        ('ERROR', 'Error'),
    ]
    
    id = models.CharField(max_length=100, primary_key=True)  # Serial number
    name = models.CharField(max_length=100) 
    machine_type = models.ForeignKey('core.MachineType', on_delete=models.PROTECT)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OFFLINE')
    is_connected = models.BooleanField(default=False)
    connection_type = models.CharField(max_length=20, choices=CONNECTION_CHOICES, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    firmware_version = models.CharField(max_length=50, blank=True)
    
    # Current material loaded
    tank_material = models.ForeignKey(
        'core.Material', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    
    last_seen = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)


class CartridgeData(models.Model):
    """Resin cartridge in a printer"""
    printer = models.ForeignKey(Printer, on_delete=models.CASCADE, related_name='cartridges')
    slot = models.CharField(max_length=10)
    material = models.ForeignKey('core.Material', on_delete=models.PROTECT)
    volume_dispensed_ml = models.FloatField()
    original_volume_ml = models.FloatField()
    
    @property
    def volume_remaining_ml(self):
        return self.original_volume_ml - self.volume_dispensed_ml


class PrinterMaintenanceLog(models.Model):
    """Track printer maintenance history"""

    MAINTENANCE_TYPES = [
        ('PREVENTITIVE', 'Preventative Maintenanve'),
        ('PREDICTIVE', 'Predictive Maintenance'),
        ('CORRECTIVE', 'Corrective Maintenance'),
        ('CONDITIONS', 'Conditions Maintenance')
    ]

    printer = models.ForeignKey(Printer, on_delete=models.CASCADE, related_name='maintenance_logs')
    performed_by = models.ForeignKey('employees.Employee', on_delete=models.SET_NULL, null=True)
    maintenance_type = models.CharField(max_length=50, choices=MAINTENANCE_TYPES)
    notes = models.TextField(blank=True)
    performed_at = models.DateTimeField(auto_now_add=True)

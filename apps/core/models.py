from django.db import models

class Material(models.Model):
    """Available materials/resins"""
    code = models.CharField(max_length=20, primary_key=True)
    label = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    material_type = models.CharField(max_length=20)  # SLA, SLS


class PrintSetting(models.Model):
    """Valid machine/material/layer thickness combinations"""
    machine_type = models.CharField(max_length=20)
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    print_setting_name = models.CharField(max_length=50, default='DEFAULT')
    layer_thickness_mm = models.CharField(max_length=20)
    
    class Meta:
        unique_together = ['machine_type', 'material', 'layer_thickness_mm']


class MachineType(models.Model):
    PRINTER_FAMILY = [
        ('SLA', 'Stereolithography'),
        ('SLS', 'Selective Laser Sintering')
    ]

    """Printer model types"""
    code = models.CharField(max_length=20, primary_key=True)  # FORM-4-0
    label = models.CharField(max_length=50)  # Form 4
    build_volume_x = models.FloatField()
    build_volume_y = models.FloatField()
    build_volume_z = models.FloatField()
    printer_family = models.CharField(max_length=20, choices=PRINTER_FAMILY)
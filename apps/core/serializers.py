# core/serializers.py

from rest_framework import serializers
from .models import Material, PrintSetting, MachineType


class MaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Material
        fields = ['code', 'label', 'description', 'material_type']


class MachineTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MachineType
        fields = ['code', 'label', 'build_volume_x', 'build_volume_y', 'build_volume_z', 'printer_family']


class PrintSettingSerializer(serializers.ModelSerializer):
    material = MaterialSerializer(read_only=True)
    
    class Meta:
        model = PrintSetting
        fields = ['id', 'machine_type', 'material', 'print_setting_name', 'layer_thickness_mm']
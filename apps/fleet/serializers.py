# fleet/serializers.py

from rest_framework import serializers
from .models import Printer, CartridgeData, PrinterMaintenanceLog
from core.serializers import MachineTypeSerializer, MaterialSerializer


class CartridgeDataSerializer(serializers.ModelSerializer):
    material = MaterialSerializer(read_only=True)
    volume_remaining_ml = serializers.ReadOnlyField()
    
    class Meta:
        model = CartridgeData
        fields = ['slot', 'material', 'volume_dispensed_ml', 'original_volume_ml', 'volume_remaining_ml']


class PrinterListSerializer(serializers.ModelSerializer):
    machine_type_label = serializers.CharField(source='machine_type.label', read_only=True)
    
    class Meta:
        model = Printer
        fields = ['id', 'name', 'machine_type_label', 'status', 'is_connected', 'last_seen']


class PrinterDetailSerializer(serializers.ModelSerializer):
    machine_type = MachineTypeSerializer(read_only=True)
    tank_material = MaterialSerializer(read_only=True)
    cartridges = CartridgeDataSerializer(many=True, read_only=True)
    
    # Current job info
    current_job = serializers.SerializerMethodField()
    
    class Meta:
        model = Printer
        fields = [
            'id', 'name', 'machine_type', 'status', 'is_connected',
            'connection_type', 'ip_address', 'firmware_version',
            'tank_material', 'cartridges', 'last_seen', 'current_job'
        ]
    
    def get_current_job(self, obj):
        job = obj.printjob_set.filter(status='PRINTING').first()
        if job:
            return {
                'id': str(job.id),
                'job_name': job.job_name,
                'started_at': job.started_at
            }
        return None
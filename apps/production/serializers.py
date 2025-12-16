# production/serializers.py

from rest_framework import serializers
from .models import PrintJob, PrintJobItem, FailedPartRecord


class PrintJobItemSerializer(serializers.ModelSerializer):
    order_item_name = serializers.CharField(
        source='batch_item.order_item.model_file_name', 
        read_only=True
    )
    order_external_id = serializers.CharField(
        source='batch_item.order_item.order.external_id',
        read_only=True
    )
    
    class Meta:
        model = PrintJobItem
        fields = ['id', 'quantity', 'status', 'order_item_name', 'order_external_id']


class PrintJobListSerializer(serializers.ModelSerializer):
    """For job queue list view"""
    printer_name = serializers.CharField(source='printer.name', read_only=True)
    batch_id = serializers.UUIDField(source='batch.id', read_only=True)
    item_count = serializers.IntegerField(source='items.count', read_only=True)
    
    class Meta:
        model = PrintJob
        fields = [
            'id', 'job_name', 'status', 'printer_name', 'batch_id',
            'estimated_print_time_s', 'item_count', 'created_at'
        ]


class PrintJobDetailSerializer(serializers.ModelSerializer):
    """For job detail view"""
    items = PrintJobItemSerializer(many=True, read_only=True)
    printer_name = serializers.CharField(source='printer.name', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.user.get_full_name', read_only=True)
    
    class Meta:
        model = PrintJob
        fields = [
            'id', 'job_name', 'status', 'failure_reason',
            'printer', 'printer_name', 'formlabs_job_id',
            'estimated_print_time_s', 'assigned_to', 'assigned_to_name',
            'created_at', 'queued_at', 'started_at', 'completed_at',
            'items'
        ]


class PrintJobUpdateSerializer(serializers.ModelSerializer):
    """For operators updating job status"""
    
    class Meta:
        model = PrintJob
        fields = ['status', 'printer', 'assigned_to', 'failure_reason']
    
    def validate_status(self, value):
        instance = self.instance
        valid_transitions = {
            'PENDING': ['READY', 'CANCELLED'],
            'READY': ['QUEUED', 'CANCELLED'],
            'QUEUED': ['PRINTING', 'CANCELLED'],
            'PRINTING': ['COMPLETED', 'FAILED'],
        }
        
        if instance and value not in valid_transitions.get(instance.status, []):
            raise serializers.ValidationError(
                f"Cannot transition from {instance.status} to {value}"
            )
        
        return value
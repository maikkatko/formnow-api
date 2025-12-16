# qc/serializers.py

from datetime import datetime
from rest_framework import serializers
from .models import QCInspection, QCItemResult


class QCItemResultSerializer(serializers.ModelSerializer):
    print_job_item_id = serializers.UUIDField(source='print_job_item.id', read_only=True)
    model_name = serializers.CharField(
        source='print_job_item.batch_item.order_item.model_file_name',
        read_only=True
    )
    
    class Meta:
        model = QCItemResult
        fields = [
            'id', 'print_job_item', 'print_job_item_id', 'model_name',
            'quantity_passed', 'quantity_failed', 'failure_reason', 'photos'
        ]


class QCInspectionSerializer(serializers.ModelSerializer):
    item_results = QCItemResultSerializer(many=True, read_only=True)
    inspected_by_name = serializers.CharField(
        source='inspected_by.user.get_full_name',
        read_only=True
    )
    
    class Meta:
        model = QCInspection
        fields = [
            'id', 'print_job', 'status', 'result',
            'inspected_by', 'inspected_by_name',
            'started_at', 'completed_at', 'notes', 'item_results'
        ]


class QCInspectionSubmitSerializer(serializers.Serializer):
    """For submitting QC results"""
    result = serializers.ChoiceField(choices=['PASSED', 'PARTIAL', 'FAILED'])
    notes = serializers.CharField(required=False, allow_blank=True)
    item_results = QCItemResultSerializer(many=True)
    
    def update(self, instance, validated_data):
        item_results_data = validated_data.pop('item_results')
        
        instance.result = validated_data.get('result', instance.result)
        instance.notes = validated_data.get('notes', instance.notes)
        instance.status = 'COMPLETED'
        instance.completed_at = datetime.now()
        instance.save()
        
        for item_data in item_results_data:
            QCItemResult.objects.update_or_create(
                inspection=instance,
                print_job_item=item_data['print_job_item'],
                defaults={
                    'quantity_passed': item_data['quantity_passed'],
                    'quantity_failed': item_data['quantity_failed'],
                    'failure_reason': item_data.get('failure_reason', ''),
                    'photos': item_data.get('photos', [])
                }
            )
        
        return instance
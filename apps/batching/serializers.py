from rest_framework import serializers
from .models import PrintBatch, BatchItem

from apps.core.serializers import MaterialSerializer, MachineTypeSerializer
from apps.orders.serializers import OrderItemSerializer
# from apps.production.serializers import FailedPartRecordSerializer

class BatchItemSerializer(serializers.ModelSerializer):
    # Read-only fields for display purposes
    order_item_details = serializers.SerializerMethodField()
    
    class Meta:
        model = BatchItem
        fields = [
            'id', 
            'batch', 
            'order_item', # Write-only (accepts ID)
            'order_item_details', # Read-only (shows object)
            'quantity', 
            'is_reprint', 
            'original_failure'
        ]
        read_only_fields = ['id']

    def get_order_item_details(self, obj):
        # Return a simplified dictionary or use the actual OrderItemSerializer
        # form apps.orders.serializers import OrderItemSerializer
        # return OrderItemSerializer(obj.order_item).data
        return {
            "id": obj.order_item.id,
            "sku": str(obj.order_item), # Assuming __str__ returns something useful
            # Add other order fields here (e.g., part name, due date)
        }

    def validate(self, data):
        """
        Check that the order item material matches the batch material if needed.
        """
        # Example validation logic:
        # if data['order_item'].material != data['batch'].material:
        #     raise serializers.ValidationError("Order Item material must match Batch material.")
        return data
    
class PrintBatchSerializer(serializers.ModelSerializer):
    # Helper fields for the frontend table view
    item_count = serializers.IntegerField(source='items.count', read_only=True)
    material_name = serializers.CharField(source='material.name', read_only=True)
    machine_name = serializers.CharField(source='machine_type.name', read_only=True)

    class Meta:
        model = PrintBatch
        fields = [
            'id', 
            'status', 
            'priority',
            'material',       # Input: ID
            'material_name',  # Output: String
            'layer_thickness_mm', 
            'machine_type',   # Input: ID
            'machine_name',   # Output: String
            'must_schedule_by',
            'scheduled_at',
            'created_at',
            'item_count'      # Useful for dashboards
        ]
        read_only_fields = ['id', 'created_at']

class PrintBatchDetailSerializer(serializers.ModelSerializer):
    # Nest the items here
    items = BatchItemSerializer(many=True, read_only=True)
    material = MaterialSerializer(read_only=True) 

    class Meta:
        model = PrintBatch
        fields = [
            'id', 
            'status', 
            'priority',
            'material', 
            'layer_thickness_mm', 
            'machine_type', 
            'must_schedule_by',
            'scheduled_at', 
            'created_at',
            'items' # <--- The nested list of items
        ]
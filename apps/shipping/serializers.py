from rest_framework import serializers
from .models import Shipment, ShipmentItem
from apps.orders.models import OrderItem # Import needed for validation

class ShipmentItemSerializer(serializers.ModelSerializer):
    # Read-only details for the UI (so the packer knows what item this is)
    sku = serializers.CharField(source='order_item.sku', read_only=True)
    product_name = serializers.CharField(source='order_item.product_name', read_only=True)
    
    class Meta:
        model = ShipmentItem
        fields = [
            'id', 
            'shipment', 
            'order_item', 
            'sku', 
            'product_name',
            'quantity'
        ]

    def validate(self, data):
        """
        Safety Check: Ensure the OrderItem belongs to the same Order 
        as the Shipment.
        """
        # Note: If this is an update, 'shipment' might not be in data, 
        # so we fetch it from the instance
        shipment = data.get('shipment')
        order_item = data.get('order_item')

        if order_item.order_id != shipment.order_id:
            raise serializers.ValidationError(
                "This item belongs to a different order and cannot be added to this shipment."
            )
        
        # Optional: Check if trying to ship more than ordered?
        # if data['quantity'] > order_item.quantity_remaining:
        #     raise serializers.ValidationError("Cannot ship more than ordered.")
            
        return data
    
class ShipmentSerializer(serializers.ModelSerializer):
    # Helper fields
    packer_name = serializers.CharField(source='packed_by.get_full_name', read_only=True)
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    item_count = serializers.IntegerField(source='items.count', read_only=True)

    class Meta:
        model = Shipment
        fields = [
            'id',
            'order',        # Writable (select order to ship)
            'order_number', # Read-only (display)
            'status',
            'carrier',
            'tracking_number',
            'weight_oz',
            'packed_by',    # Writable ID
            'packer_name',  # Read-only Name
            'packed_at',
            'shipped_at',
            'item_count',
        ]
        read_only_fields = ['id', 'shipped_at'] # Usually shipped_at is set automatically by backend logic

    def validate_tracking_number(self, value):
        # Optional: Clean up tracking number (remove spaces)
        return value.strip().upper() if value else value
    
class ShipmentDetailSerializer(serializers.ModelSerializer):
    # Reuse fields from parent, just add the nested items
    items = ShipmentItemSerializer(many=True, read_only=True)
    shipping_address = serializers.SerializerMethodField()

    class Meta:
        model = Shipment
        fields = ['id', 'order', 'status', 'carrier', 'tracking_number', 'weight_oz', 'packed_by', 'packed_at', 'shipped_at', 'items', 'shipping_address']

    def get_shipping_address(self, obj):
        # Assuming the Shipment model has a `shipping_address` field, or related address model
        # This could be a direct field or a ForeignKey to an Address model
        # For example, if there’s a `shipping_address` field in the `Order` model:

        return obj.order.shipping_address if obj.order else None
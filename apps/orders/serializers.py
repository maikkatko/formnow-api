# orders/serializers.py

from rest_framework import serializers
from .models import Order, OrderItem
from apps.core.serializers import MaterialSerializer


class OrderItemSerializer(serializers.ModelSerializer):
    material = MaterialSerializer(read_only=True)
    material_code = serializers.CharField(write_only=True)
    quantity_remaining = serializers.ReadOnlyField()
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'model_file_url', 'model_file_name', 'quantity',
            'material', 'material_code', 'layer_thickness_mm',
            'quantity_completed', 'quantity_remaining'
        ]


class OrderListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views"""
    item_count = serializers.IntegerField(source='items.count', read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'external_id', 'customer_name', 'status',
            'priority', 'due_date', 'received_at', 'item_count'
        ]


class OrderDetailSerializer(serializers.ModelSerializer):
    """Full serializer with nested items"""
    items = OrderItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'external_id', 'customer_email', 'customer_name',
            'shipping_address', 'status', 'priority', 'due_date',
            'received_at', 'shipped_at', 'items'
        ]


class OrderCreateSerializer(serializers.ModelSerializer):
    """For incoming orders from web app"""
    items = OrderItemSerializer(many=True)
    
    class Meta:
        model = Order
        fields = [
            'external_id', 'customer_email', 'customer_name',
            'shipping_address', 'priority', 'due_date', 'items', 'raw_payload'
        ]
    
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        order = Order.objects.create(**validated_data)
        
        for item_data in items_data:
            material_code = item_data.pop('material_code')
            OrderItem.objects.create(
                order=order,
                material_id=material_code,
                **item_data
            )
        
        return order
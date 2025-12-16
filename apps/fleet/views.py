from django.shortcuts import render

from rest_framework import viewsets, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Printer, CartridgeData, PrinterMaintenanceLog
from .serializers import (
    PrinterListSerializer, 
    PrinterDetailSerializer, 
    CartridgeDataSerializer
)

class PrinterViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing Printers.
    """
    # Optimized query to fetch foreign keys and reverse relationships in one go
    queryset = Printer.objects.all().select_related(
        'machine_type', 
        'tank_material'
    ).prefetch_related(
        'cartridges', 
        'cartridges__material' # Nested prefetch for cartridge material
    )

    def get_serializer_class(self):
        if self.action == 'list':
            return PrinterListSerializer
        if self.action == 'retrieve':
            return PrinterDetailSerializer
        # Use a flat serializer for creating/updating (allows setting IDs)
        return PrinterWriteSerializer

    @action(detail=True, methods=['post'])
    def ping(self, request, pk=None):
        """
        Optional: Custom action to manually trigger a status check
        """
        printer = self.get_object()
        # printer.check_connection() # Assuming you have a method like this on the model
        return Response({'status': 'ping sent', 'is_connected': printer.is_connected})


class CartridgeDataViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Cartridges. 
    Usually accessed via the Printer, but useful for independent inventory updates.
    """
    queryset = CartridgeData.objects.all().select_related('material')
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CartridgeWriteSerializer
        return CartridgeDataSerializer


# --- Helper Serializers for Writing ---

class PrinterWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Printer
        fields = [
            'id', 'name', 'machine_type', 'status', 'is_connected',
            'connection_type', 'ip_address', 'firmware_version',
            'tank_material'
        ]

class CartridgeWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartridgeData
        fields = ['id', 'printer', 'slot', 'material', 'volume_dispensed_ml', 'original_volume_ml']
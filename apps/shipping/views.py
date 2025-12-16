from typing import cast
from rest_framework import viewsets
from rest_framework import permissions
from .models import Shipment, ShipmentItem
from .serializers import ShipmentSerializer, ShipmentItemSerializer, ShipmentDetailSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.request import Request

class ShipmentViewSet(viewsets.ModelViewSet):
    queryset = Shipment.objects.all()
    serializer_class = ShipmentSerializer
    permission_classes = [permissions.IsAuthenticated]  # You can change this depending on your app's permissions
    
    def get_serializer_class(self):
        """
        Return the appropriate serializer class based on the action.
        """
        if self.action == 'retrieve':
            return ShipmentDetailSerializer
        return ShipmentSerializer

    def perform_create(self, serializer):
        """
        Override the default perform_create to add custom logic
        if needed before saving the Shipment instance.
        """
        # Example: Automatically set the user who created the shipment
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def pack(self, request, pk=None):
        """
        Custom action for packing a shipment.
        """
        shipment = self.get_object()
        # Add logic for packing the shipment
        shipment.status = 'Packed'
        shipment.packed_by = request.user
        shipment.save()

        return Response(ShipmentSerializer(shipment).data)


class ShipmentItemViewSet(viewsets.ModelViewSet):
    queryset = ShipmentItem.objects.all()
    serializer_class = ShipmentItemSerializer
    permission_classes = [permissions.IsAuthenticated]  # Adjust permissions as needed

    def perform_create(self, serializer):
        """
        Override the default perform_create to add custom logic
        before saving the ShipmentItem instance.
        """
        # Example: Automatically associate the user creating the ShipmentItem
        serializer.save(created_by=self.request.user)
        
    def get_queryset(self):
        """
        Optionally filter the queryset based on parameters
        like shipment ID, etc.
        """
        queryset = ShipmentItem.objects.all()
        request = cast(Request, self.request)
        shipment_id = request.query_params.get('shipment', None)
        if shipment_id:
            queryset = queryset.filter(shipment_id=shipment_id)
        return queryset

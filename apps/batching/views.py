from django.shortcuts import render

from rest_framework import viewsets
from .models import PrintBatch, BatchItem
from .serializers import BatchItemSerializer, PrintBatchDetailSerializer, PrintBatchSerializer

class PrintBatchViewSet(viewsets.ModelViewSet):
    queryset = PrintBatch.objects.all().select_related('material', 'machine_type')
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PrintBatchDetailSerializer
        return PrintBatchSerializer

class BatchItemViewSet(viewsets.ModelViewSet):
    queryset = BatchItem.objects.all()
    serializer_class = BatchItemSerializer  

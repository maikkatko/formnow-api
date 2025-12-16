from django.shortcuts import render
from rest_framework import viewsets

from .models import Employee
from .serializers import EmployeeCreateUpdateSerializer, EmployeeSerializer

class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all().select_related('user').prefetch_related('roles__permissions', 'extra_permissions')
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return EmployeeCreateUpdateSerializer
        return EmployeeSerializer
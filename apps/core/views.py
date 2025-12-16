# core/views.py

from rest_framework import viewsets, serializers
from .models import Material, PrintSetting, MachineType
from .serializers import MaterialSerializer, MachineTypeSerializer, PrintSettingSerializer

class MaterialViewSet(viewsets.ModelViewSet):
    queryset = Material.objects.all()
    serializer_class = MaterialSerializer


class MachineTypeViewSet(viewsets.ModelViewSet):
    queryset = MachineType.objects.all()
    serializer_class = MachineTypeSerializer


class PrintSettingViewSet(viewsets.ModelViewSet):
    # select_related prevents N+1 queries when fetching the nested material data
    queryset = PrintSetting.objects.all().select_related('material', 'machine_type')
    
    def get_serializer_class(self):
        """
        Use the nested serializer for reading (GET),
        but use a flat serializer for writing (POST/PUT).
        """
        if self.action in ['create', 'update', 'partial_update']:
            return PrintSettingWriteSerializer
        return PrintSettingSerializer


# --- Helper Serializer for Writing ---
# Since the 'PrintSettingSerializer' sets material to read_only=True,
# we need this helper to allow the API to accept a material ID during POST/PUT.

class PrintSettingWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrintSetting
        fields = ['id', 'machine_type', 'material', 'print_setting_name', 'layer_thickness_mm']

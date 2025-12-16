from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MaterialViewSet, MachineTypeViewSet, PrintSettingViewSet

router = DefaultRouter()
router.register(r'materials', MaterialViewSet)
router.register(r'machine-types', MachineTypeViewSet)
router.register(r'print-settings', PrintSettingViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
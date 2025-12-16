from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PrinterViewSet, CartridgeDataViewSet

router = DefaultRouter()
router.register(r'printers', PrinterViewSet)
router.register(r'cartridges', CartridgeDataViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
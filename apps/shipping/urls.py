from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ShipmentViewSet, ShipmentItemViewSet

router = DefaultRouter()
router.register(r'shipments', ShipmentViewSet)
router.register(r'shipment-items', ShipmentItemViewSet)

urlpatterns = [
    path('', include(router.urls))
]
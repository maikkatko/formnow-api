from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrderItemViewSet, OrderViewSet

router = DefaultRouter()
router.register(r'order-item', OrderItemViewSet)
router.register(r'order', OrderViewSet)

urlpatterns = [
    path('', include(router.urls))
]
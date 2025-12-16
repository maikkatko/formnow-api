from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PrintBatchViewSet, BatchItemViewSet

router = DefaultRouter()
router.register(r'print-batch', PrintBatchViewSet)
router.register(r'batch-item', BatchItemViewSet)

urlpatterns = [
    path('', include(router.urls))
]
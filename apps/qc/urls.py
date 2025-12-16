from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import QCInspectionViewSet, QCItemResultViewSet

router = DefaultRouter()
router.register(r'inspections', QCInspectionViewSet)
router.register(r'results', QCItemResultViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
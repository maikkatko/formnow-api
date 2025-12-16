from rest_framework.routers import DefaultRouter
from django.urls import path, include

from .views import DashboardStatsViewSet, ProductionMetricsViewSet, ProductionQueueViewSet 

router = DefaultRouter()
router.register(r'dashboard-stats', DashboardStatsViewSet)
router.register(r'production-queue', ProductionQueueViewSet)
router.register(r'production-metrics', ProductionMetricsViewSet)

urlpatterns = [
    path('', include(router.urls))
]


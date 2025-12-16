from rest_framework.routers import DefaultRouter
from django.urls import path, include

from .views import DashboardStatsViewSet, ProductionMetricsViewSet, ProductionQueueViewSet 

router = DefaultRouter()
router.register(r'dashboard-stats', DashboardStatsViewSet, basename='dashboard-stats')
router.register(r'production-queue', ProductionQueueViewSet, basename='production-queue')
router.register(r'production-metrics', ProductionMetricsViewSet, basename='production-metrics')

urlpatterns = [
    path('', include(router.urls))
]


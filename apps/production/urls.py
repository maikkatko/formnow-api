from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PrintJobViewSet, PrintJobItemViewSet

router = DefaultRouter()
router.register(r'print-jobs', PrintJobViewSet)
router.register(r'job-items', PrintJobItemViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
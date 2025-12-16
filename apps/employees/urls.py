from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import EmployeeViewSet

router = DefaultRouter()
router.register(r'employees', EmployeeViewSet)

url_patterns = [
    path('', include(router.urls))
]
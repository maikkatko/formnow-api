"""
URL configuration for formnow project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API endpoints - all apps
    path('api/', include([
        # Core configuration (materials, machine types, print settings)
        path('core/', include('apps.core.urls')),
        
        # Order management
        path('orders/', include('apps.orders.urls')),
        
        # Production (print jobs, scenes, queue)
        path('production/', include('apps.production.urls')),
        
        # Printer fleet management
        path('fleet/', include('apps.fleet.urls')),
        
        # Batching system
        path('batching/', include('apps.batching.urls')),
        
        # Quality control
        path('qc/', include('apps.qc.urls')),
        
        # Shipping
        path('shipping/', include('apps.shipping.urls')),
        
        # Employee management
        path('employees/', include('apps.employees.urls')),
    ])),
]
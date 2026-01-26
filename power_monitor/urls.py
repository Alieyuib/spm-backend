from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (PowerReadingViewSet, DailyConsumptionViewSet, 
                    AlertViewSet, BatteryReadingViewSet, DeviceViewSet,
                    EnergyTariffViewSet, ClientViewSet, EnergyReportViewSet,
                    WhatsAppMessageViewSet)

router = DefaultRouter()
router.register(r'readings', PowerReadingViewSet)
router.register(r'consumption', DailyConsumptionViewSet)
router.register(r'alerts', AlertViewSet)
router.register(r'battery', BatteryReadingViewSet)
router.register(r'devices', DeviceViewSet)
router.register(r'tariffs', EnergyTariffViewSet)
router.register(r'clients', ClientViewSet)
router.register(r'reports', EnergyReportViewSet)
router.register(r'whatsapp', WhatsAppMessageViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
]
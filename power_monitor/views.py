from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.utils import timezone
from django.db.models import Avg, Max, Min, Sum, Count
from datetime import timedelta, datetime
from .models import (PowerReading, DailyConsumption, Alert, BatteryReading, 
                    Device, EnergyTariff, Client, EnergyReport, WhatsAppMessage)
from .serializers import (PowerReadingSerializer, DailyConsumptionSerializer, 
                          AlertSerializer, BatteryReadingSerializer, DeviceSerializer,
                          EnergyTariffSerializer, ClientSerializer, EnergyReportSerializer,
                          WhatsAppMessageSerializer)

class DeviceViewSet(viewsets.ModelViewSet):
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get all active devices"""
        devices = Device.objects.filter(is_active=True)
        serializer = self.get_serializer(devices, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get statistics for a specific device"""
        device = self.get_object()
        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        
        readings = PowerReading.objects.filter(
            device=device, 
            timestamp__gte=last_24h
        )
        
        stats = readings.aggregate(
            avg_power=Avg('power'),
            peak_power=Max('power'),
            min_power=Min('power'),
            avg_voltage=Avg('voltage'),
            total_readings=Count('id')
        )
        
        return Response(stats)

class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    
    @action(detail=True, methods=['post'])
    def generate_report(self, request, pk=None):
        """Generate energy report for client"""
        from .services.report_service import ReportService
        
        client = self.get_object()
        report_type = request.data.get('report_type', 'WEEKLY')
        
        report_service = ReportService()
        report = report_service.generate_report(client, report_type)
        
        if report:
            serializer = EnergyReportSerializer(report)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(
            {"error": "Failed to generate report"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['get'])
    def reports(self, request, pk=None):
        """Get all reports for client"""
        client = self.get_object()
        reports = client.reports.all()
        serializer = EnergyReportSerializer(reports, many=True)
        return Response(serializer.data)
    

    @action(detail=False, methods=['get'])
    def by_device(self, request):
        """
        Get client(s) associated with a specific device_id
        """
        device_id = request.query_params.get('device_id', None)

        if not device_id:
            return Response(
                {"detail": "device_id query parameter is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        queryset = (
            Client.objects
            .filter(devices__device_id=device_id)
            .distinct()
        )

        if not queryset.exists():
            return Response(
                {"detail": "No client found for the given device_id."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class PowerReadingViewSet(viewsets.ModelViewSet):
    queryset = PowerReading.objects.all()
    serializer_class = PowerReadingSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'bulk_create']:
            return [AllowAny()]
        return super().get_permissions()
    
    def create(self, request, *args, **kwargs):
        # Get or create device
        device_id = request.data.get('device_id', 'default')
        device, created = Device.objects.get_or_create(
            device_id=device_id,
            defaults={
                'device_name': request.data.get('device_name', 'Unknown Device'),
                'device_type': 'inverter'
            }
        )
        
        # Create reading with device_identifier
        data = request.data.copy()
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save(device=device, device_identifier=device_id)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def latest(self, request):
        """Get the most recent power reading"""
        device_id = request.query_params.get('device_id', None)
        
        if device_id:
            reading = PowerReading.objects.filter(device_identifier=device_id).first()
        else:
            reading = PowerReading.objects.first()
            
        if reading:
            serializer = self.get_serializer(reading)
            return Response(serializer.data)
        return Response(
            {"error": "No readings available"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get readings from the last hour"""
        device_id = request.query_params.get('device_id', None)
        time_threshold = timezone.now() - timedelta(hours=1)
        
        if device_id:
            readings = PowerReading.objects.filter(
                device_identifier=device_id,
                timestamp__gte=time_threshold
            )
        else:
            readings = PowerReading.objects.filter(timestamp__gte=time_threshold)
            
        serializer = self.get_serializer(readings, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def bulk_create(self, request):
        """Create multiple readings at once"""
        if not isinstance(request.data, list):
            return Response(
                {"error": "Expected a list of readings"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def by_device(self, request):
        """Get readings grouped by device"""
        devices = Device.objects.filter(is_active=True)
        result = []
        
        for device in devices:
            latest = PowerReading.objects.filter(device=device).first()
            if latest:
                result.append({
                    'device_id': device.device_id,
                    'device_name': device.device_name,
                    'latest_reading': self.get_serializer(latest).data
                })
        
        return Response(result)

class DailyConsumptionViewSet(viewsets.ModelViewSet):
    queryset = DailyConsumption.objects.all()
    serializer_class = DailyConsumptionSerializer
    
    @action(detail=False, methods=['get'])
    def weekly(self, request):
        """Get consumption for the last 7 days"""
        device_id = request.query_params.get('device_id', None)
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=6)
        
        if device_id:
            consumption = DailyConsumption.objects.filter(
                device_identifier=device_id,
                date__range=[start_date, end_date]
            )
        else:
            consumption = DailyConsumption.objects.filter(
                date__range=[start_date, end_date]
            )
            
        serializer = self.get_serializer(consumption, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def monthly(self, request):
        """Get consumption for the last 30 days"""
        device_id = request.query_params.get('device_id', None)
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=29)
        
        if device_id:
            consumption = DailyConsumption.objects.filter(
                device_identifier=device_id,
                date__range=[start_date, end_date]
            )
        else:
            consumption = DailyConsumption.objects.filter(
                date__range=[start_date, end_date]
            )
            
        serializer = self.get_serializer(consumption, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def calculate_cost(self, request):
        """Calculate energy cost based on tariff"""
        consumption_kwh = request.data.get('consumption_kwh')
        tariff_id = request.data.get('tariff_id')
        
        try:
            tariff = EnergyTariff.objects.get(id=tariff_id, is_active=True)
            cost = consumption_kwh * tariff.rate_per_kwh
            
            return Response({
                'consumption_kwh': consumption_kwh,
                'rate_per_kwh': tariff.rate_per_kwh,
                'total_cost': cost,
                'currency': tariff.currency
            })
        except EnergyTariff.DoesNotExist:
            return Response(
                {"error": "Tariff not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )

class AlertViewSet(viewsets.ModelViewSet):
    queryset = Alert.objects.all()
    serializer_class = AlertSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        return super().get_permissions()
    
    def create(self, request, *args, **kwargs):
        device_id = request.data.get('device_id', 'default')
        device, _ = Device.objects.get_or_create(
            device_id=device_id,
            defaults={'device_name': request.data.get('device_name', 'Unknown Device')}
        )
        
        data = request.data.copy()
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        alert = serializer.save(device=device, device_identifier=device_id)
        
        # Send WhatsApp notification
        self._send_whatsapp_alert(alert)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def _send_whatsapp_alert(self, alert):
        """Send WhatsApp notification for alert"""
        # Only send for WARNING and CRITICAL alerts
        if alert.severity in ['WARNING', 'CRITICAL']:
            from .services.whatsapp_service import WhatsAppService
            wa_service = WhatsAppService()
            wa_service.send_alert_message(alert)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get all active alerts"""
        device_id = request.query_params.get('device_id', None)
        
        if device_id:
            alerts = Alert.objects.filter(device_identifier=device_id, status='ACTIVE')
        else:
            alerts = Alert.objects.filter(status='ACTIVE')
            
        serializer = self.get_serializer(alerts, many=True)
        return Response(serializer.data)
    
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get alerts from the last 24 hours"""
        time_threshold = timezone.now() - timedelta(hours=24)
        alerts = Alert.objects.filter(timestamp__gte=time_threshold)    
        serializer = self.get_serializer(alerts, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        """Acknowledge an alert"""
        alert = self.get_object()
        alert.status = 'ACKNOWLEDGED'
        alert.save()
        return Response({'status': 'Alert acknowledged'})
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Resolve an alert"""
        alert = self.get_object()
        alert.status = 'RESOLVED'
        alert.resolved_at = timezone.now()
        alert.save()
        return Response({'status': 'Alert resolved'})

class BatteryReadingViewSet(viewsets.ModelViewSet):
    queryset = BatteryReading.objects.all()
    serializer_class = BatteryReadingSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        return super().get_permissions()
    
    def create(self, request, *args, **kwargs):
        device_id = request.data.get('device_id', 'default')
        device, _ = Device.objects.get_or_create(
            device_id=device_id,
            defaults={'device_name': request.data.get('device_name', 'Unknown Device')}
        )
        
        data = request.data.copy()
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save(device=device, device_identifier=device_id)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def latest(self, request):
        """Get the most recent battery reading"""
        device_id = request.query_params.get('device_id', None)
        
        if device_id:
            reading = BatteryReading.objects.filter(device_identifier=device_id).first()
        else:
            reading = BatteryReading.objects.first()
            
        if reading:
            serializer = self.get_serializer(reading)
            return Response(serializer.data)
        return Response(
            {"error": "No battery readings available"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    @action(detail=False, methods=['get'])
    def history(self, request):
        """Get battery history for the last 24 hours"""
        device_id = request.query_params.get('device_id', None)
        time_threshold = timezone.now() - timedelta(hours=24)
        
        if device_id:
            readings = BatteryReading.objects.filter(
                device_identifier=device_id,
                timestamp__gte=time_threshold
            )
        else:
            readings = BatteryReading.objects.filter(timestamp__gte=time_threshold)
            
        serializer = self.get_serializer(readings, many=True)
        return Response(serializer.data)

class EnergyTariffViewSet(viewsets.ModelViewSet):
    queryset = EnergyTariff.objects.all()
    serializer_class = EnergyTariffSerializer
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get all active tariffs"""
        tariffs = EnergyTariff.objects.filter(is_active=True)
        serializer = self.get_serializer(tariffs, many=True)
        return Response(serializer.data)

class EnergyReportViewSet(viewsets.ModelViewSet):
    queryset = EnergyReport.objects.all()
    serializer_class = EnergyReportSerializer
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Generate energy report"""
        from .services.report_service import ReportService
        
        client_id = request.data.get('client_id')
        device_id = request.data.get('device_id')  # Optional - for device-specific reports
        report_type = request.data.get('report_type', 'WEEKLY')
        
        try:
            client = Client.objects.get(id=client_id)
        except Client.DoesNotExist:
            return Response(
                {"error": "Client not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get device if specified
        device = None
        if device_id:
            try:
                device = Device.objects.get(device_id=device_id)
                # Verify device belongs to client
                if device not in client.devices.all():
                    return Response(
                        {"error": "Device does not belong to this client"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except Device.DoesNotExist:
                return Response(
                    {"error": "Device not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        report_service = ReportService()
        report = report_service.generate_report(client, report_type, device=device)
        
        if report:
            # Send report if requested
            send_whatsapp = request.data.get('send_whatsapp', False)
            send_email = request.data.get('send_email', False)
            
            if send_whatsapp or send_email:
                report_service.send_report(report, via_email=send_email, via_whatsapp=send_whatsapp)
            
            serializer = self.get_serializer(report)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(
            {"error": "Failed to generate report"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['post'])
    def send(self, request, pk=None):
        """Send existing report"""
        from .services.report_service import ReportService
        
        report = self.get_object()
        send_whatsapp = request.data.get('send_whatsapp', True)
        send_email = request.data.get('send_email', True)
        
        report_service = ReportService()
        results = report_service.send_report(report, via_email=send_email, via_whatsapp=send_whatsapp)
        
        return Response(results)
    
    @action(detail=True, methods=['get'])
    def download_pdf(self, request, pk=None):
        """Download report as PDF"""
        from django.http import HttpResponse
        from .services.pdf_service import PDFReportService
        
        report = self.get_object()
        
        # Generate PDF
        pdf_service = PDFReportService()
        pdf_buffer = pdf_service.generate_report_pdf(report)
        
        if not pdf_buffer:
            return Response(
                {"error": "Failed to generate PDF"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Create response
        response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
        filename = f"energy_report_{report.client.name.replace(' ', '_')}_{report.start_date}_{report.end_date}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
    
    @action(detail=False, methods=['get'])
    def by_client(self, request):
        """Get reports for a specific client"""
        client_id = request.query_params.get('client_id')
        
        if not client_id:
            return Response(
                {"error": "client_id parameter required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reports = EnergyReport.objects.filter(client_id=client_id).order_by('-generated_at')
        serializer = self.get_serializer(reports, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_device(self, request):
        """
        Get energy reports for a specific device
        """
        device_id = request.query_params.get('device_id')

        if not device_id:
            return Response(
                {"detail": "device_id query parameter is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # device = get_object_or_404(Device, device_id=device_id)

        reports = (
            EnergyReport.objects
            .filter(device=device_id)
            .order_by('-generated_at')
        )

        serializer = self.get_serializer(reports, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class WhatsAppMessageViewSet(viewsets.ModelViewSet):
    queryset = WhatsAppMessage.objects.all()
    serializer_class = WhatsAppMessageSerializer
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent WhatsApp messages"""
        limit = int(request.query_params.get('limit', 50))
        messages = WhatsAppMessage.objects.all()[:limit]
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def failed(self, request):
        """Get failed WhatsApp messages"""
        messages = WhatsAppMessage.objects.filter(status='FAILED')
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)
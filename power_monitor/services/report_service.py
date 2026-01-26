# power_monitor/services/report_service.py
from django.db.models import Avg, Max, Min, Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from power_monitor.models import (
    EnergyReport, Client, Device, PowerReading, 
    DailyConsumption, Alert, EnergyTariff
)
import logging

logger = logging.getLogger(__name__)

class ReportService:
    """Service for generating energy usage reports"""
    
    def generate_report(self, client, report_type='WEEKLY', device=None, 
                       start_date=None, end_date=None):
        """Generate energy report for a client"""
        
        # Calculate date range
        if not start_date or not end_date:
            start_date, end_date = self._get_date_range(report_type)
        
        # Get devices
        devices = [device] if device else list(client.devices.all())
        
        if not devices:
            logger.warning(f"No devices found for client {client.name}")
            return None
        
        # Aggregate data from all client devices
        total_consumption = 0
        total_cost = 0
        peak_power = 0
        power_factors = []
        uptime_hours = 0
        total_alerts = 0
        critical_alerts = 0
        device_data = []
        
        for dev in devices:
            device_stats = self._get_device_statistics(dev, start_date, end_date)
            device_data.append(device_stats)
            
            total_consumption += device_stats['consumption']
            total_cost += device_stats['cost']
            peak_power = max(peak_power, device_stats['peak_power'])
            power_factors.extend(device_stats['power_factors'])
            uptime_hours += device_stats['uptime']
            total_alerts += device_stats['alerts']
            critical_alerts += device_stats['critical_alerts']
        
        # Calculate averages
        days_in_period = (end_date - start_date).days + 1
        avg_daily_consumption = total_consumption / days_in_period if days_in_period > 0 else 0
        avg_power_factor = sum(power_factors) / len(power_factors) if power_factors else 0
        
        # Create report
        report = EnergyReport.objects.create(
            client=client,
            device=device,
            report_type=report_type,
            start_date=start_date,
            end_date=end_date,
            total_consumption_kwh=total_consumption,
            total_cost=total_cost,
            avg_daily_consumption=avg_daily_consumption,
            peak_power=peak_power,
            avg_power_factor=avg_power_factor,
            uptime_hours=uptime_hours,
            total_alerts=total_alerts,
            critical_alerts=critical_alerts,
            report_data={
                'devices': device_data,
                'days_in_period': days_in_period,
                'generated_by': 'system'
            }
        )
        
        logger.info(f"Generated {report_type} report for {client.name}")
        return report
    
    def _get_date_range(self, report_type):
        """Get date range based on report type"""
        end_date = timezone.now().date()
        
        if report_type == 'DAILY':
            start_date = end_date
        elif report_type == 'WEEKLY':
            start_date = end_date - timedelta(days=6)
        elif report_type == 'MONTHLY':
            start_date = end_date - timedelta(days=29)
        else:
            start_date = end_date - timedelta(days=6)
        
        return start_date, end_date
    
    def _get_device_statistics(self, device, start_date, end_date):
        """Get statistics for a single device"""
        # Get consumption data
        consumption_records = DailyConsumption.objects.filter(
            device=device,
            date__range=[start_date, end_date]
        )
        
        consumption = consumption_records.aggregate(
            total=Sum('total_consumption'),
            cost=Sum('total_cost'),
            peak=Max('peak_power')
        )
        
        # Get power readings for power factor
        readings = PowerReading.objects.filter(
            device=device,
            timestamp__date__range=[start_date, end_date]
        )
        
        power_factors = list(readings.values_list('power_factor', flat=True))
        
        # Calculate uptime (hours with readings)
        uptime_hours = readings.count() * (5 / 60)  # 5 minutes per reading
        
        # Get alerts
        alerts = Alert.objects.filter(
            device=device,
            timestamp__date__range=[start_date, end_date]
        )
        
        return {
            'device_id': device.device_id,
            'device_name': device.device_name,
            'consumption': consumption['total'] or 0,
            'cost': consumption['cost'] or 0,
            'peak_power': consumption['peak'] or 0,
            'power_factors': power_factors,
            'uptime': uptime_hours,
            'alerts': alerts.count(),
            'critical_alerts': alerts.filter(severity='CRITICAL').count()
        }
    
    def send_report(self, report, via_email=True, via_whatsapp=True):
        """Send report to client"""
        results = {}
        
        # Send via Email
        if via_email and report.client.receive_email_reports:
            from .email_service import EmailService
            email_service = EmailService()
            email_result = email_service.send_report_email(report)
            
            if email_result:
                report.sent_via_email = True
                report.save()
                results['email'] = 'sent'
            else:
                results['email'] = 'failed'
        
        # Send via WhatsApp
        if via_whatsapp and report.client.receive_whatsapp_alerts:
            from .whatsapp_service import WhatsAppService
            wa_service = WhatsAppService()
            wa_result = wa_service.send_report_summary(report)
            
            if wa_result:
                report.sent_via_whatsapp = True
                report.save()
                results['whatsapp'] = 'sent'
            else:
                results['whatsapp'] = 'failed'
        
        return results
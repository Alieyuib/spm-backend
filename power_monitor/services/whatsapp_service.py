# power_monitor/services/whatsapp_service.py
import requests
from django.conf import settings
from django.utils import timezone
from power_monitor.models import WhatsAppMessage, Alert, Client
import logging

logger = logging.getLogger(__name__)

class WhatsAppService:
    """
    WhatsApp integration using Twilio or other WhatsApp Business API
    
    Setup:
    1. Sign up for Twilio (https://www.twilio.com/)
    2. Get WhatsApp-enabled number
    3. Add to settings.py:
       TWILIO_ACCOUNT_SID = 'your_account_sid'
       TWILIO_AUTH_TOKEN = 'your_auth_token'
       TWILIO_WHATSAPP_NUMBER = 'whatsapp:+14155238886'
    
    Alternative: Use WhatsApp Business API, WATI, or other providers
    """
    
    def __init__(self):
        self.account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
        self.auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
        self.from_number = getattr(settings, 'TWILIO_WHATSAPP_NUMBER', 'whatsapp:+14155238886')
        self.enabled = bool(self.account_sid and self.auth_token)
        
        if not self.enabled:
            logger.warning("WhatsApp service not configured. Set TWILIO credentials in settings.")
    
    def send_alert_message(self, alert, client=None):
        """Send alert notification via WhatsApp"""
        if not self.enabled:
            logger.info(f"WhatsApp disabled. Would send: {alert.message}")
            return self._create_mock_message(alert, client)
        
        # Get recipients
        recipients = self._get_alert_recipients(alert, client)
        
        if not recipients:
            logger.warning(f"No recipients found for alert {alert.id}")
            return None
        
        # Format message
        message = self._format_alert_message(alert)
        
        # Send to all recipients
        results = []
        for recipient in recipients:
            result = self._send_message(recipient['phone'], message, alert=alert, client=recipient.get('client'))
            results.append(result)
        
        return results
    
    def send_report_summary(self, report):
        """Send energy report summary via WhatsApp"""
        if not self.enabled:
            logger.info(f"WhatsApp disabled. Would send report for {report.client.name}")
            return None
        
        if not report.client.receive_whatsapp_alerts:
            logger.info(f"Client {report.client.name} has WhatsApp alerts disabled")
            return None
        
        message = self._format_report_message(report)
        return self._send_message(
            report.client.whatsapp_number, 
            message, 
            client=report.client,
            message_type='report'
        )
    
    def _get_alert_recipients(self, alert, client=None):
        """Get list of recipients for an alert"""
        recipients = []
        
        if client:
            if client.receive_whatsapp_alerts and client.whatsapp_number:
                recipients.append({
                    'phone': client.whatsapp_number,
                    'client': client
                })
        else:
            # Get all clients associated with the device
            if alert.device:
                clients = alert.device.clients.filter(
                    receive_whatsapp_alerts=True,
                    is_active=True
                )
                for c in clients:
                    if c.whatsapp_number:
                        recipients.append({
                            'phone': c.whatsapp_number,
                            'client': c
                        })
        
        return recipients
    
    def _format_alert_message(self, alert):
        """Format alert message for WhatsApp"""
        severity_emoji = {
            'INFO': 'ℹ️',
            'WARNING': '⚠️',
            'CRITICAL': '🚨'
        }
        
        emoji = severity_emoji.get(alert.severity, '📢')
        device_name = alert.device.device_name if alert.device else 'Unknown Device'
        
        message = f"""
{emoji} *{alert.severity} ALERT*

*Device:* {device_name}
*Type:* {alert.alert_type}

*Message:* {alert.message}
"""
        
        if alert.value:
            message += f"*Value:* {alert.value:.2f}\n"
        
        message += f"\n*Time:* {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
        message += "\n_Power Monitoring System_"
        
        return message.strip()
    
    def _format_report_message(self, report):
        """Format energy report for WhatsApp"""
        message = f"""
📊 *{report.report_type.title()} Energy Report*

*Period:* {report.start_date} to {report.end_date}

*Consumption Summary:*
• Total: {report.total_consumption_kwh:.2f} kWh
• Daily Average: {report.avg_daily_consumption:.2f} kWh
• Total Cost: ₦{report.total_cost:,.2f}

*Performance:*
• Peak Power: {report.peak_power:.0f} W
• Avg Power Factor: {report.avg_power_factor:.2f}
• Uptime: {report.uptime_hours:.1f} hours

*Alerts:*
• Total: {report.total_alerts}
• Critical: {report.critical_alerts}

_Full report available in dashboard_
_Power Monitoring System_
"""
        return message.strip()
    
    def _send_message(self, to_number, message, alert=None, client=None, message_type='alert'):
        """Send WhatsApp message using Twilio"""
        # Ensure number has whatsapp: prefix
        if not to_number.startswith('whatsapp:'):
            to_number = f'whatsapp:{to_number}'
        
        # Create WhatsApp message record
        wa_message = WhatsAppMessage.objects.create(
            recipient=to_number,
            message=message,
            message_type=message_type,
            alert=alert,
            client=client,
            status='PENDING'
        )
        
        try:
            # Using Twilio API
            from twilio.rest import Client as TwilioClient
            
            twilio_client = TwilioClient(self.account_sid, self.auth_token)
            
            message_obj = twilio_client.messages.create(
                body=message,
                from_=self.from_number,
                to=to_number
            )
            
            # Update message status
            wa_message.status = 'SENT'
            wa_message.sent_at = timezone.now()
            wa_message.response_data = {
                'sid': message_obj.sid,
                'status': message_obj.status
            }
            wa_message.save()
            
            # Update alert if provided
            if alert:
                alert.whatsapp_sent = True
                alert.whatsapp_sent_at = timezone.now()
                alert.save()
            
            logger.info(f"WhatsApp message sent to {to_number}")
            return wa_message
            
        except Exception as e:
            logger.error(f"Failed to send WhatsApp to {to_number}: {str(e)}")
            wa_message.status = 'FAILED'
            wa_message.response_data = {'error': str(e)}
            wa_message.save()
            return wa_message
    
    def _create_mock_message(self, alert, client):
        """Create mock message for testing without actual sending"""
        message = self._format_alert_message(alert)
        
        wa_message = WhatsAppMessage.objects.create(
            recipient=client.whatsapp_number if client else 'whatsapp:+1234567890',
            message=message,
            message_type='alert',
            alert=alert,
            client=client,
            status='SENT',  # Mock as sent
            sent_at=timezone.now()
        )
        
        logger.info(f"Mock WhatsApp message created for alert {alert.id}")
        return wa_message
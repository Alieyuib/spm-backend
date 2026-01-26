# power_monitor/services/email_service.py
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone
from power_monitor.models import EnergyReport
import logging

logger = logging.getLogger(__name__)

class EmailService:
    """
    Email service for sending energy reports to clients
    
    Setup:
    Add to settings.py:
        EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
        EMAIL_HOST = 'smtp.gmail.com'
        EMAIL_PORT = 587
        EMAIL_USE_TLS = True
        EMAIL_HOST_USER = 'your-email@gmail.com'
        EMAIL_HOST_PASSWORD = 'your-app-password'
        DEFAULT_FROM_EMAIL = 'Power Monitor <noreply@powermonitor.com>'
    """
    
    def __init__(self):
        self.from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@powermonitor.com')
        self.enabled = self._check_email_config()
        
        if not self.enabled:
            logger.warning("Email not configured. Set EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in settings.")
    
    def _check_email_config(self):
        """Check if email is properly configured"""
        host = getattr(settings, 'EMAIL_HOST', None)
        user = getattr(settings, 'EMAIL_HOST_USER', None)
        password = getattr(settings, 'EMAIL_HOST_PASSWORD', None)
        
        return bool(host and user and password)
    
    def send_report_email(self, report):
        """Send energy report via email"""
        if not self.enabled:
            logger.info(f"Email disabled. Would send report to {report.client.email}")
            return self._create_mock_email_log(report)
        
        if not report.client.email:
            logger.warning(f"Client {report.client.name} has no email address")
            return None
        
        if not report.client.receive_email_reports:
            logger.info(f"Client {report.client.name} has email reports disabled")
            return None
        
        try:
            # Generate email content
            subject = f"{report.report_type.title()} Energy Report - {report.start_date} to {report.end_date}"
            html_content = self._generate_html_report(report)
            text_content = self._generate_text_report(report)
            
            # Create email
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=self.from_email,
                to=[report.client.email],
                reply_to=[self.from_email]
            )
            
            # Attach HTML version
            email.attach_alternative(html_content, "text/html")
            
            # Send email
            email.send(fail_silently=False)
            
            # Update report status
            report.sent_via_email = True
            report.save()
            
            logger.info(f"Email report sent to {report.client.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {report.client.email}: {str(e)}")
            return False
    
    def send_alert_email(self, alert, recipients):
        """Send alert notification via email"""
        if not self.enabled:
            logger.info(f"Email disabled. Would send alert to {len(recipients)} recipients")
            return False
        
        if not recipients:
            return False
        
        try:
            subject = f"⚠️ {alert.severity} Alert - {alert.alert_type}"
            html_content = self._generate_html_alert(alert)
            text_content = self._generate_text_alert(alert)
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=self.from_email,
                to=recipients,
                reply_to=[self.from_email]
            )
            
            email.attach_alternative(html_content, "text/html")
            email.send(fail_silently=False)
            
            logger.info(f"Alert email sent to {len(recipients)} recipients")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send alert email: {str(e)}")
            return False
    
    def _generate_html_report(self, report):
        """Generate HTML email for report"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
            border-radius: 10px 10px 0 0;
        }}
        .header h1 {{
            margin: 0;
            font-size: 28px;
        }}
        .content {{
            background: #f8f9fa;
            padding: 30px;
            border-radius: 0 0 10px 10px;
        }}
        .summary-box {{
            background: white;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .stat {{
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #e9ecef;
        }}
        .stat:last-child {{
            border-bottom: none;
        }}
        .stat-label {{
            color: #6c757d;
            font-weight: 500;
        }}
        .stat-value {{
            color: #2d3748;
            font-weight: 700;
            font-size: 18px;
        }}
        .highlight {{
            background: #e7f3ff;
            padding: 15px;
            border-left: 4px solid #0066cc;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .alert-section {{
            background: #fff3cd;
            padding: 15px;
            border-left: 4px solid #ffc107;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .footer {{
            text-align: center;
            color: #6c757d;
            font-size: 12px;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #dee2e6;
        }}
        .button {{
            display: inline-block;
            padding: 12px 30px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>⚡ Energy Report</h1>
        <p style="margin: 10px 0 0 0; opacity: 0.9;">{report.report_type.title()} Report</p>
    </div>
    
    <div class="content">
        <p>Dear {report.client.name},</p>
        
        <p>Here is your {report.report_type.lower()} energy consumption report for the period 
        <strong>{report.start_date}</strong> to <strong>{report.end_date}</strong>.</p>
        
        <div class="summary-box">
            <h2 style="margin-top: 0; color: #2d3748;">📊 Consumption Summary</h2>
            
            <div class="stat">
                <span class="stat-label">Total Consumption</span>
                <span class="stat-value">{report.total_consumption_kwh:.2f} kWh</span>
            </div>
            
            <div class="stat">
                <span class="stat-label">Daily Average</span>
                <span class="stat-value">{report.avg_daily_consumption:.2f} kWh</span>
            </div>
            
            <div class="stat">
                <span class="stat-label">Total Cost</span>
                <span class="stat-value">₦{report.total_cost:,.2f}</span>
            </div>
        </div>
        
        <div class="summary-box">
            <h2 style="margin-top: 0; color: #2d3748;">⚡ Performance Metrics</h2>
            
            <div class="stat">
                <span class="stat-label">Peak Power</span>
                <span class="stat-value">{report.peak_power:.0f} W</span>
            </div>
            
            <div class="stat">
                <span class="stat-label">Average Power Factor</span>
                <span class="stat-value">{report.avg_power_factor:.2f}</span>
            </div>
            
            <div class="stat">
                <span class="stat-label">System Uptime</span>
                <span class="stat-value">{report.uptime_hours:.1f} hours</span>
            </div>
        </div>
        
        {self._generate_alert_section_html(report)}
        
        <div class="highlight">
            <strong>💡 Cost Analysis:</strong><br>
            Based on your consumption of <strong>{report.total_consumption_kwh:.2f} kWh</strong>, 
            your estimated monthly cost is approximately <strong>₦{report.total_cost * 4.3:,.2f}</strong>.
        </div>
        
        <center>
            <a href="http://localhost:8000/admin/power_monitor/energyreport/{report.id}/" class="button">
                View Detailed Report
            </a>
        </center>
        
        <p style="margin-top: 30px;">If you have any questions about this report, please don't hesitate to contact us.</p>
        
        <p>Best regards,<br>
        <strong>Power Monitoring System</strong></p>
    </div>
    
    <div class="footer">
        <p>This is an automated report from Power Monitoring System<br>
        Generated on {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p style="margin-top: 10px; font-size: 11px; color: #999;">
            To unsubscribe from these reports, please update your preferences in your account settings.
        </p>
    </div>
</body>
</html>
"""
        return html
    
    def _generate_alert_section_html(self, report):
        """Generate alert section for HTML email"""
        if report.total_alerts == 0:
            return """
        <div style="background: #d4edda; padding: 15px; border-left: 4px solid #28a745; margin: 20px 0; border-radius: 4px;">
            <strong>✅ System Status:</strong> No alerts during this period. All systems operating normally.
        </div>
"""
        
        severity_class = "alert-section" if report.critical_alerts == 0 else "background: #f8d7da; border-left-color: #dc3545;"
        
        return f"""
        <div style="{severity_class} padding: 15px; margin: 20px 0; border-radius: 4px;">
            <strong>⚠️ Alert Summary:</strong><br>
            Total Alerts: <strong>{report.total_alerts}</strong><br>
            Critical Alerts: <strong>{report.critical_alerts}</strong>
            {' ⚠️' if report.critical_alerts > 0 else ''}
            <br><br>
            <small>Please review the detailed report for specific alert information.</small>
        </div>
"""
    
    def _generate_text_report(self, report):
        """Generate plain text version of report"""
        text = f"""
ENERGY REPORT
{report.report_type.upper()} REPORT

Dear {report.client.name},

Here is your {report.report_type.lower()} energy consumption report.

REPORT PERIOD
From: {report.start_date}
To: {report.end_date}

CONSUMPTION SUMMARY
==================
Total Consumption: {report.total_consumption_kwh:.2f} kWh
Daily Average: {report.avg_daily_consumption:.2f} kWh
Total Cost: ₦{report.total_cost:,.2f}

PERFORMANCE METRICS
==================
Peak Power: {report.peak_power:.0f} W
Average Power Factor: {report.avg_power_factor:.2f}
System Uptime: {report.uptime_hours:.1f} hours

ALERT SUMMARY
==================
Total Alerts: {report.total_alerts}
Critical Alerts: {report.critical_alerts}

COST ANALYSIS
==================
Based on your consumption of {report.total_consumption_kwh:.2f} kWh, 
your estimated monthly cost is approximately ₦{report.total_cost * 4.3:,.2f}.

If you have any questions about this report, please contact us.

Best regards,
Power Monitoring System

---
This is an automated report generated on {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return text.strip()
    
    def _generate_html_alert(self, alert):
        """Generate HTML email for alert"""
        severity_colors = {
            'INFO': '#17a2b8',
            'WARNING': '#ffc107',
            'CRITICAL': '#dc3545'
        }
        
        color = severity_colors.get(alert.severity, '#6c757d')
        device_name = alert.device.device_name if alert.device else 'Unknown Device'
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .alert-box {{ background: {color}; color: white; padding: 20px; border-radius: 8px; }}
        .content {{ background: #f8f9fa; padding: 20px; margin-top: 20px; border-radius: 8px; }}
        .detail {{ padding: 10px 0; border-bottom: 1px solid #dee2e6; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="alert-box">
            <h1 style="margin: 0;">⚠️ {alert.severity} ALERT</h1>
            <p style="margin: 10px 0 0 0; opacity: 0.9;">{alert.alert_type}</p>
        </div>
        
        <div class="content">
            <div class="detail">
                <strong>Device:</strong> {device_name}
            </div>
            <div class="detail">
                <strong>Message:</strong> {alert.message}
            </div>
            {f'<div class="detail"><strong>Value:</strong> {alert.value:.2f}</div>' if alert.value else ''}
            <div class="detail">
                <strong>Time:</strong> {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
            </div>
            
            <p style="margin-top: 20px;">
                Please review this alert and take necessary action if required.
            </p>
        </div>
        
        <p style="text-align: center; color: #6c757d; font-size: 12px; margin-top: 20px;">
            Power Monitoring System - Automated Alert
        </p>
    </div>
</body>
</html>
"""
        return html
    
    def _generate_text_alert(self, alert):
        """Generate plain text alert"""
        device_name = alert.device.device_name if alert.device else 'Unknown Device'
        
        text = f"""
⚠️ {alert.severity} ALERT

Alert Type: {alert.alert_type}
Device: {device_name}

Message: {alert.message}
"""
        if alert.value:
            text += f"Value: {alert.value:.2f}\n"
        
        text += f"\nTime: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
        text += "\nPlease review this alert and take necessary action if required.\n"
        text += "\n---\nPower Monitoring System - Automated Alert"
        
        return text.strip()
    
    def _create_mock_email_log(self, report):
        """Log email that would be sent (for testing)"""
        logger.info(f"""
========================================
MOCK EMAIL - Would send to: {report.client.email}
Subject: {report.report_type.title()} Energy Report
Report ID: {report.id}
Period: {report.start_date} to {report.end_date}
Consumption: {report.total_consumption_kwh:.2f} kWh
Cost: ₦{report.total_cost:,.2f}
========================================
""")
        return True
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import json

class Device(models.Model):
    device_id = models.CharField(max_length=50, unique=True)
    device_name = models.CharField(max_length=100)
    device_type = models.CharField(max_length=50, default='inverter')
    location = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    last_seen = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.device_name} ({self.device_id})"

class Client(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20)
    whatsapp_number = models.CharField(max_length=20, help_text="Format: +234XXXXXXXXXX")
    address = models.TextField(blank=True)
    devices = models.ManyToManyField(Device, related_name='clients')
    is_active = models.BooleanField(default=True)
    receive_whatsapp_alerts = models.BooleanField(default=True)
    receive_email_reports = models.BooleanField(default=True)
    report_frequency = models.CharField(
        max_length=20,
        choices=[
            ('DAILY', 'Daily'),
            ('WEEKLY', 'Weekly'),
            ('MONTHLY', 'Monthly'),
        ],
        default='WEEKLY'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class PowerReading(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, null=True, blank=True, related_name='readings')
    device_identifier = models.CharField(max_length=50, default='default', db_column='power_device_id')
    voltage = models.FloatField(help_text="Voltage in Volts")
    current = models.FloatField(help_text="Current in Amperes")
    power = models.FloatField(help_text="Power in Watts")
    frequency = models.FloatField(help_text="Frequency in Hz")
    power_factor = models.FloatField(help_text="Power Factor (0-1)")
    battery_voltage = models.FloatField(null=True, blank=True, help_text="Battery voltage")
    battery_soc = models.FloatField(null=True, blank=True, help_text="Battery State of Charge %")
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['device_identifier', '-timestamp']),
        ]
    
    def __str__(self):
        return f"Reading at {self.timestamp}: {self.power}W"

class DailyConsumption(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, null=True, blank=True, related_name='daily_consumption')
    device_identifier = models.CharField(max_length=50, default='default', db_column='consumption_device_id')
    date = models.DateField(db_index=True)
    total_consumption = models.FloatField(help_text="Total consumption in kWh")
    avg_power = models.FloatField(help_text="Average power in Watts")
    peak_power = models.FloatField(help_text="Peak power in Watts")
    min_power = models.FloatField(help_text="Minimum power in Watts", default=0)
    total_cost = models.FloatField(help_text="Total cost in currency", default=0)
    
    class Meta:
        ordering = ['-date']
        unique_together = ['device_identifier', 'date']
    
    def __str__(self):
        return f"{self.date}: {self.total_consumption} kWh"

class Alert(models.Model):
    SEVERITY_CHOICES = [
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('CRITICAL', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('ACKNOWLEDGED', 'Acknowledged'),
        ('RESOLVED', 'Resolved'),
    ]
    
    device = models.ForeignKey(Device, on_delete=models.CASCADE, null=True, blank=True, related_name='alerts')
    device_identifier = models.CharField(max_length=50, default='default', db_column='alert_device_id')
    alert_type = models.CharField(max_length=50)
    message = models.TextField()
    value = models.FloatField(null=True, blank=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='INFO')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    whatsapp_sent = models.BooleanField(default=False)
    whatsapp_sent_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.severity}: {self.alert_type} - {self.message}"

class BatteryReading(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, null=True, blank=True, related_name='battery_readings')
    device_identifier = models.CharField(max_length=50, default='default', db_column='battery_device_id')
    voltage = models.FloatField(help_text="Battery voltage in Volts")
    soc = models.FloatField(help_text="State of Charge in %", 
                           validators=[MinValueValidator(0), MaxValueValidator(100)])
    is_charging = models.BooleanField(default=False)
    temperature = models.FloatField(null=True, blank=True, help_text="Battery temperature in °C")
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"Battery at {self.timestamp}: {self.soc}%"

class EnergyTariff(models.Model):
    name = models.CharField(max_length=100)
    rate_per_kwh = models.FloatField(help_text="Rate per kWh")
    currency = models.CharField(max_length=10, default='NGN')
    time_of_day_start = models.TimeField(null=True, blank=True)
    time_of_day_end = models.TimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name}: {self.rate_per_kwh} {self.currency}/kWh"

class EnergyReport(models.Model):
    REPORT_TYPE_CHOICES = [
        ('DAILY', 'Daily Report'),
        ('WEEKLY', 'Weekly Report'),
        ('MONTHLY', 'Monthly Report'),
        ('CUSTOM', 'Custom Report'),
    ]
    
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='reports')
    device = models.ForeignKey(Device, on_delete=models.CASCADE, null=True, blank=True)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    total_consumption_kwh = models.FloatField()
    total_cost = models.FloatField()
    avg_daily_consumption = models.FloatField()
    peak_power = models.FloatField()
    avg_power_factor = models.FloatField()
    uptime_hours = models.FloatField()
    total_alerts = models.IntegerField(default=0)
    critical_alerts = models.IntegerField(default=0)
    report_data = models.JSONField(default=dict)
    generated_at = models.DateTimeField(auto_now_add=True)
    sent_via_email = models.BooleanField(default=False)
    sent_via_whatsapp = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"{self.report_type} Report for {self.client.name} ({self.start_date} to {self.end_date})"

class WhatsAppMessage(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SENT', 'Sent'),
        ('FAILED', 'Failed'),
        ('DELIVERED', 'Delivered'),
    ]
    
    recipient = models.CharField(max_length=20)
    message = models.TextField()
    message_type = models.CharField(max_length=50, default='alert')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    alert = models.ForeignKey(Alert, on_delete=models.CASCADE, null=True, blank=True, related_name='whatsapp_messages')
    client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True, blank=True, related_name='whatsapp_messages')
    response_data = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"WhatsApp to {self.recipient} - {self.status}"
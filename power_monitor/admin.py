from django.contrib import admin
from .models import (PowerReading, DailyConsumption, Alert, BatteryReading, 
                     Device, EnergyTariff, Client, EnergyReport, WhatsAppMessage)

@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ['device_id', 'device_name', 'device_type', 'is_active', 'last_seen']
    list_filter = ['is_active', 'device_type']
    search_fields = ['device_id', 'device_name']

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'whatsapp_number', 'is_active', 'receive_whatsapp_alerts', 'report_frequency']
    list_filter = ['is_active', 'receive_whatsapp_alerts', 'report_frequency']
    search_fields = ['name', 'email', 'phone']
    filter_horizontal = ['devices']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'email', 'phone', 'whatsapp_number', 'address')
        }),
        ('Devices', {
            'fields': ('devices',)
        }),
        ('Preferences', {
            'fields': ('is_active', 'receive_whatsapp_alerts', 'receive_email_reports', 'report_frequency')
        }),
    )

@admin.register(PowerReading)
class PowerReadingAdmin(admin.ModelAdmin):
    list_display = ['device_identifier', 'timestamp', 'voltage', 'current', 'power', 'frequency']
    list_filter = ['device_identifier', 'timestamp']
    date_hierarchy = 'timestamp'
    readonly_fields = ['timestamp']

@admin.register(DailyConsumption)
class DailyConsumptionAdmin(admin.ModelAdmin):
    list_display = ['device_identifier', 'date', 'total_consumption', 'avg_power', 'peak_power', 'total_cost']
    list_filter = ['device_identifier', 'date']
    date_hierarchy = 'date'

@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ['device_identifier', 'alert_type', 'severity', 'status', 'timestamp', 'whatsapp_sent']
    list_filter = ['severity', 'status', 'alert_type', 'whatsapp_sent']
    date_hierarchy = 'timestamp'
    actions = ['mark_acknowledged', 'mark_resolved', 'resend_whatsapp']
    readonly_fields = ['whatsapp_sent_at']
    
    def mark_acknowledged(self, request, queryset):
        queryset.update(status='ACKNOWLEDGED')
    mark_acknowledged.short_description = "Mark selected alerts as acknowledged"
    
    def mark_resolved(self, request, queryset):
        from django.utils import timezone
        queryset.update(status='RESOLVED', resolved_at=timezone.now())
    mark_resolved.short_description = "Mark selected alerts as resolved"
    
    def resend_whatsapp(self, request, queryset):
        from .services.whatsapp_service import WhatsAppService
        wa_service = WhatsAppService()
        
        count = 0
        for alert in queryset:
            wa_service.send_alert_message(alert)
            count += 1
        
        self.message_user(request, f"Resent {count} WhatsApp alerts")
    resend_whatsapp.short_description = "Resend WhatsApp notifications"

@admin.register(BatteryReading)
class BatteryReadingAdmin(admin.ModelAdmin):
    list_display = ['device_identifier', 'timestamp', 'voltage', 'soc', 'is_charging']
    list_filter = ['device_identifier', 'is_charging']
    date_hierarchy = 'timestamp'

@admin.register(EnergyTariff)
class EnergyTariffAdmin(admin.ModelAdmin):
    list_display = ['name', 'rate_per_kwh', 'currency', 'is_active']
    list_filter = ['is_active', 'currency']

@admin.register(EnergyReport)
class EnergyReportAdmin(admin.ModelAdmin):
    list_display = ['client', 'report_type', 'start_date', 'end_date', 'total_consumption_kwh', 'total_cost', 'generated_at']
    list_filter = ['report_type', 'generated_at', 'sent_via_email', 'sent_via_whatsapp']
    date_hierarchy = 'generated_at'
    readonly_fields = ['generated_at', 'report_data']
    search_fields = ['client__name']
    actions = ['send_via_whatsapp', 'send_via_email']
    
    def send_via_whatsapp(self, request, queryset):
        from .services.report_service import ReportService
        report_service = ReportService()
        
        count = 0
        for report in queryset:
            report_service.send_report(report, via_email=False, via_whatsapp=True)
            count += 1
        
        self.message_user(request, f"Sent {count} reports via WhatsApp")
    send_via_whatsapp.short_description = "Send selected reports via WhatsApp"
    
    def send_via_email(self, request, queryset):
        self.message_user(request, "Email sending not yet implemented")
    send_via_email.short_description = "Send selected reports via Email"

@admin.register(WhatsAppMessage)
class WhatsAppMessageAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'message_type', 'status', 'created_at', 'sent_at']
    list_filter = ['status', 'message_type', 'created_at']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'sent_at', 'response_data']
    search_fields = ['recipient', 'message']
    
    fieldsets = (
        ('Message Details', {
            'fields': ('recipient', 'message', 'message_type')
        }),
        ('Related Objects', {
            'fields': ('alert', 'client')
        }),
        ('Status', {
            'fields': ('status', 'created_at', 'sent_at', 'response_data')
        }),
    )
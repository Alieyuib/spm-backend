from rest_framework import serializers
from .models import (PowerReading, DailyConsumption, Alert, BatteryReading, 
                     Device, EnergyTariff, Client, EnergyReport, WhatsAppMessage)

class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ['id', 'device_id', 'device_name', 'device_type', 'location', 
                  'is_active', 'last_seen', 'created_at']
        read_only_fields = ['id', 'last_seen', 'created_at']

class ClientSerializer(serializers.ModelSerializer):
    devices = DeviceSerializer(many=True, read_only=True)
    device_ids = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Client
        fields = ['id', 'name', 'email', 'phone', 'whatsapp_number', 'address',
                  'devices', 'device_ids', 'is_active', 'receive_whatsapp_alerts',
                  'receive_email_reports', 'report_frequency', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def create(self, validated_data):
        device_ids = validated_data.pop('device_ids', [])
        client = Client.objects.create(**validated_data)
        
        if device_ids:
            devices = Device.objects.filter(device_id__in=device_ids)
            client.devices.set(devices)
        
        return client

class PowerReadingSerializer(serializers.ModelSerializer):
    device_name = serializers.CharField(source='device.device_name', read_only=True)
    device_id = serializers.CharField(source='device_identifier', required=False)
    
    class Meta:
        model = PowerReading
        fields = ['id', 'device_id', 'device_name', 'voltage', 'current', 'power', 
                  'frequency', 'power_factor', 'battery_voltage', 'battery_soc', 'timestamp']
        read_only_fields = ['id', 'timestamp']
    
    def create(self, validated_data):
        # Handle device_id from device_identifier
        if 'device_identifier' in validated_data:
            device_id = validated_data.pop('device_identifier')
            validated_data['device_identifier'] = device_id
        return super().create(validated_data)

class DailyConsumptionSerializer(serializers.ModelSerializer):
    device_id = serializers.CharField(source='device_identifier', required=False)
    
    class Meta:
        model = DailyConsumption
        fields = ['id', 'device_id', 'date', 'total_consumption', 'avg_power', 
                  'peak_power', 'min_power', 'total_cost']
        read_only_fields = ['id']

class AlertSerializer(serializers.ModelSerializer):
    device_id = serializers.CharField(source='device_identifier', required=False)
    
    class Meta:
        model = Alert
        fields = ['id', 'device_id', 'alert_type', 'message', 'value', 'severity', 
                  'status', 'timestamp', 'resolved_at']
        read_only_fields = ['id', 'timestamp']

class BatteryReadingSerializer(serializers.ModelSerializer):
    device_id = serializers.CharField(source='device_identifier', required=False)
    
    class Meta:
        model = BatteryReading
        fields = ['id', 'device_id', 'voltage', 'soc', 'is_charging', 
                  'temperature', 'timestamp']
        read_only_fields = ['id', 'timestamp']

class EnergyTariffSerializer(serializers.ModelSerializer):
    class Meta:
        model = EnergyTariff
        fields = '__all__'

class EnergyReportSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.name', read_only=True)
    device_name = serializers.CharField(source='device.device_name', read_only=True)
    
    class Meta:
        model = EnergyReport
        fields = '__all__'
        read_only_fields = ['generated_at']

class WhatsAppMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = WhatsAppMessage
        fields = '__all__'
        read_only_fields = ['created_at', 'sent_at']

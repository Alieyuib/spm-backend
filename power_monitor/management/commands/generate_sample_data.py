# management/commands/generate_sample_data.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, datetime, time
import random
from power_monitor.models import (
    Device, PowerReading, DailyConsumption, 
    Alert, BatteryReading, EnergyTariff
)

class Command(BaseCommand):
    help = 'Generate comprehensive sample data for power monitoring system'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear all existing data before generating new data',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days of historical data to generate',
        )
    
    def handle(self, *args, **kwargs):
        clear_data = kwargs['clear']
        days = kwargs['days']
        
        if clear_data:
            self.stdout.write(self.style.WARNING('Clearing existing data...'))
            PowerReading.objects.all().delete()
            DailyConsumption.objects.all().delete()
            Alert.objects.all().delete()
            BatteryReading.objects.all().delete()
            Device.objects.all().delete()
            EnergyTariff.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('✓ Data cleared'))
        
        self.stdout.write(self.style.SUCCESS('Generating sample data...'))
        
        # Create devices
        devices = self.create_devices()
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(devices)} devices'))
        
        # Create tariffs
        tariffs = self.create_tariffs()
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(tariffs)} tariffs'))
        
        # Create clients
        clients = self.create_clients()
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(clients)} clients'))
        
        # Generate data for each device
        for device in devices:
            self.stdout.write(f'\nGenerating data for {device.device_name}...')
            
            # Generate power readings
            readings_count = self.generate_power_readings(device, days)
            self.stdout.write(self.style.SUCCESS(f'  ✓ {readings_count} power readings'))
            
            # Generate battery readings
            battery_count = self.generate_battery_readings(device, days)
            self.stdout.write(self.style.SUCCESS(f'  ✓ {battery_count} battery readings'))
            
            # Generate daily consumption
            consumption_count = self.generate_daily_consumption(device, days, tariffs[0])
            self.stdout.write(self.style.SUCCESS(f'  ✓ {consumption_count} daily consumption records'))
            
            # Generate alerts
            alerts_count = self.generate_alerts(device)
            self.stdout.write(self.style.SUCCESS(f'  ✓ {alerts_count} alerts'))
        
        # Generate reports for clients
        reports_count = self.generate_reports()
        self.stdout.write(self.style.SUCCESS(f'\n✓ Generated {reports_count} energy reports'))
        
        # Create WhatsApp message samples
        messages_count = self.generate_whatsapp_messages()
        self.stdout.write(self.style.SUCCESS(f'✓ Created {messages_count} WhatsApp message samples'))
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*50))
        self.stdout.write(self.style.SUCCESS('Sample data generation complete!'))
        self.stdout.write(self.style.SUCCESS('='*50))
        self.print_summary()
    
    def create_devices(self):
        devices_data = [
            {
                'device_id': 'INVERTER_01',
                'device_name': 'Main House Inverter',
                'device_type': 'inverter',
                'location': 'Main Building',
            },
            {
                'device_id': 'INVERTER_02',
                'device_name': 'Guest House Inverter',
                'device_type': 'inverter',
                'location': 'Guest House',
            },
            {
                'device_id': 'INVERTER_03',
                'device_name': 'Workshop Inverter',
                'device_type': 'inverter',
                'location': 'Workshop',
            },
        ]
        
        devices = []
        for data in devices_data:
            device, created = Device.objects.get_or_create(
                device_id=data['device_id'],
                defaults=data
            )
            devices.append(device)
        
        return devices
    
    def create_tariffs(self):
        tariffs_data = [
            {
                'name': 'Standard Rate',
                'rate_per_kwh': 65.0,
                'currency': 'NGN',
                'is_active': True,
            },
            {
                'name': 'Off-Peak Rate',
                'rate_per_kwh': 45.0,
                'currency': 'NGN',
                'time_of_day_start': time(22, 0),
                'time_of_day_end': time(6, 0),
                'is_active': True,
            },
            {
                'name': 'Peak Rate',
                'rate_per_kwh': 85.0,
                'currency': 'NGN',
                'time_of_day_start': time(17, 0),
                'time_of_day_end': time(22, 0),
                'is_active': True,
            },
        ]
        
        tariffs = []
        for data in tariffs_data:
            tariff, created = EnergyTariff.objects.get_or_create(
                name=data['name'],
                defaults=data
            )
            tariffs.append(tariff)
        
        return tariffs
    
    def create_clients(self):
        """Create sample clients"""
        from power_monitor.models import Client
        
        clients_data = [
            {
                'name': 'John Doe',
                'email': 'john.doe@example.com',
                'phone': '+234803456789 0',
                'whatsapp_number': '+2348034567890',
                'address': '123 Main Street, Lagos, Nigeria',
                'receive_whatsapp_alerts': True,
                'receive_email_reports': True,
                'report_frequency': 'WEEKLY',
            },
            {
                'name': 'Sarah Johnson',
                'email': 'sarah.j@example.com',
                'phone': '+2348098765432',
                'whatsapp_number': '+2348098765432',
                'address': '45 Victoria Island, Lagos, Nigeria',
                'receive_whatsapp_alerts': True,
                'receive_email_reports': False,
                'report_frequency': 'MONTHLY',
            },
            {
                'name': 'ABC Corporation',
                'email': 'admin@abc-corp.com',
                'phone': '+2347012345678',
                'whatsapp_number': '+2347012345678',
                'address': 'Plot 10, Industrial Estate, Abuja, Nigeria',
                'receive_whatsapp_alerts': True,
                'receive_email_reports': True,
                'report_frequency': 'DAILY',
            },
        ]
        
        clients = []
        devices = Device.objects.all()
        
        for i, data in enumerate(clients_data):
            client, created = Client.objects.get_or_create(
                name=data['name'],
                defaults=data
            )
            
            # Assign devices to clients
            if i == 0:
                # John gets INVERTER_01
                client.devices.set([devices[0]])
            elif i == 1:
                # Sarah gets INVERTER_02
                client.devices.set([devices[1]]) if len(devices) > 1 else None
            else:
                # ABC Corp gets INVERTER_03 and INVERTER_01
                client.devices.set([devices[2], devices[0]]) if len(devices) > 2 else None
            
            clients.append(client)
        
        return clients
    
    def generate_power_readings(self, device, days):
        """Generate realistic power readings with daily patterns"""
        now = timezone.now()
        count = 0
        
        # Generate readings for past days
        for day_offset in range(days, 0, -1):
            day_start = now - timedelta(days=day_offset)
            
            # Generate readings every 5 minutes for the day
            for hour in range(24):
                for minute in range(0, 60, 5):
                    timestamp = day_start.replace(
                        hour=hour, 
                        minute=minute, 
                        second=0, 
                        microsecond=0
                    )
                    
                    # Create realistic patterns based on time of day
                    base_power = self.get_base_power_for_time(hour)
                    
                    # Add device-specific variation
                    if device.device_id == 'INVERTER_01':
                        multiplier = 1.0
                    elif device.device_id == 'INVERTER_02':
                        multiplier = 0.6
                    else:
                        multiplier = 0.8
                    
                    power = base_power * multiplier + random.uniform(-100, 100)
                    voltage = 220 + random.uniform(-5, 5)
                    current = power / voltage if voltage > 0 else 0
                    frequency = 50 + random.uniform(-0.3, 0.3)
                    power_factor = 0.90 + random.uniform(-0.05, 0.08)
                    
                    # Battery data
                    battery_voltage = 12.5 + random.uniform(-1.0, 1.5)
                    battery_soc = ((battery_voltage - 10.5) / (14.5 - 10.5)) * 100
                    battery_soc = max(0, min(100, battery_soc))
                    
                    PowerReading.objects.create(
                        device=device,
                        device_identifier=device.device_id,
                        voltage=voltage,
                        current=current,
                        power=power,
                        frequency=frequency,
                        power_factor=power_factor,
                        battery_voltage=battery_voltage,
                        battery_soc=battery_soc,
                        timestamp=timestamp
                    )
                    count += 1
        
        # Generate recent readings (last hour with more frequent updates)
        for minutes_ago in range(60, 0, -1):
            timestamp = now - timedelta(minutes=minutes_ago)
            
            hour = timestamp.hour
            base_power = self.get_base_power_for_time(hour)
            
            if device.device_id == 'INVERTER_01':
                multiplier = 1.0
            elif device.device_id == 'INVERTER_02':
                multiplier = 0.6
            else:
                multiplier = 0.8
            
            power = base_power * multiplier + random.uniform(-100, 100)
            voltage = 220 + random.uniform(-5, 5)
            current = power / voltage if voltage > 0 else 0
            frequency = 50 + random.uniform(-0.3, 0.3)
            power_factor = 0.90 + random.uniform(-0.05, 0.08)
            
            battery_voltage = 12.5 + random.uniform(-1.0, 1.5)
            battery_soc = ((battery_voltage - 10.5) / (14.5 - 10.5)) * 100
            battery_soc = max(0, min(100, battery_soc))
            
            PowerReading.objects.create(
                device=device,
                device_identifier=device.device_id,
                voltage=voltage,
                current=current,
                power=power,
                frequency=frequency,
                power_factor=power_factor,
                battery_voltage=battery_voltage,
                battery_soc=battery_soc,
                timestamp=timestamp
            )
            count += 1
        
        return count
    
    def generate_reports(self):
        """Generate sample energy reports"""
        from power_monitor.models import Client, EnergyReport
        from power_monitor.services.report_service import ReportService
        
        report_service = ReportService()
        clients = Client.objects.all()
        count = 0
        
        for client in clients:
            # Generate weekly report
            try:
                report = report_service.generate_report(client, 'WEEKLY')
                if report:
                    count += 1
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Could not generate report for {client.name}: {str(e)}'))
            
            # Generate monthly report for some clients
            if client.report_frequency == 'MONTHLY':
                try:
                    report = report_service.generate_report(client, 'MONTHLY')
                    if report:
                        count += 1
                except Exception as e:
                    pass
        
        return count
    
    def generate_whatsapp_messages(self):
        """Generate sample WhatsApp messages"""
        from power_monitor.models import WhatsAppMessage, Alert, Client
        
        clients = Client.objects.filter(receive_whatsapp_alerts=True)
        alerts = Alert.objects.all()[:5]
        count = 0
        
        for i, alert in enumerate(alerts):
            if i < len(clients):
                client = list(clients)[i]
                
                message_text = f"""
🚨 *{alert.severity} ALERT*

*Device:* {alert.device.device_name if alert.device else 'Unknown'}
*Type:* {alert.alert_type}
*Message:* {alert.message}

*Time:* {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

_Power Monitoring System_
"""
                
                WhatsAppMessage.objects.create(
                    recipient=client.whatsapp_number,
                    message=message_text.strip(),
                    message_type='alert',
                    alert=alert,
                    client=client,
                    status='SENT' if i < 3 else 'FAILED',
                    sent_at=alert.timestamp if i < 3 else None
                )
                count += 1
        
        # Add some report messages
        for client in clients[:2]:
            message_text = f"""
📊 *Weekly Energy Report*

*Client:* {client.name}
*Period:* Last 7 days

*Consumption:* 45.2 kWh
*Cost:* ₦2,938.00

_Full report available in dashboard_
_Power Monitoring System_
"""
            
            WhatsAppMessage.objects.create(
                recipient=client.whatsapp_number,
                message=message_text.strip(),
                message_type='report',
                client=client,
                status='SENT',
                sent_at=timezone.now() - timedelta(hours=2)
            )
            count += 1
        
        return count
    
    def get_base_power_for_time(self, hour):
        """Return realistic base power consumption for time of day"""
        # Night (0-5): Low usage
        if 0 <= hour < 5:
            return random.uniform(300, 600)
        # Early morning (5-8): Medium usage
        elif 5 <= hour < 8:
            return random.uniform(800, 1200)
        # Morning (8-12): High usage
        elif 8 <= hour < 12:
            return random.uniform(1200, 1800)
        # Afternoon (12-17): Medium-high usage
        elif 12 <= hour < 17:
            return random.uniform(1000, 1500)
        # Evening (17-22): Peak usage
        elif 17 <= hour < 22:
            return random.uniform(1800, 2500)
        # Late night (22-24): Medium usage
        else:
            return random.uniform(600, 1000)
    
    def generate_battery_readings(self, device, days):
        """Generate battery readings"""
        now = timezone.now()
        count = 0
        
        # Generate readings every 15 minutes
        for day_offset in range(days, 0, -1):
            day_start = now - timedelta(days=day_offset)
            
            for hour in range(24):
                for minute in range(0, 60, 15):
                    timestamp = day_start.replace(
                        hour=hour, 
                        minute=minute, 
                        second=0, 
                        microsecond=0
                    )
                    
                    # Simulate battery charging/discharging cycle
                    # Charging during day (9-17), discharging at night
                    if 9 <= hour < 17:
                        base_voltage = 13.5 + random.uniform(-0.5, 0.5)
                        is_charging = True
                    else:
                        base_voltage = 12.0 + random.uniform(-0.5, 0.5)
                        is_charging = False
                    
                    voltage = base_voltage
                    soc = ((voltage - 10.5) / (14.5 - 10.5)) * 100
                    soc = max(0, min(100, soc))
                    temperature = 25 + random.uniform(-5, 10)
                    
                    BatteryReading.objects.create(
                        device=device,
                        device_identifier=device.device_id,
                        voltage=voltage,
                        soc=soc,
                        is_charging=is_charging,
                        temperature=temperature,
                        timestamp=timestamp
                    )
                    count += 1
        
        return count
    
    def generate_daily_consumption(self, device, days, tariff):
        """Generate daily consumption summaries"""
        now = timezone.now()
        count = 0
        
        for day_offset in range(days, 0, -1):
            date = (now - timedelta(days=day_offset)).date()
            
            # Calculate statistics from readings
            day_start = datetime.combine(date, time.min).replace(tzinfo=timezone.get_current_timezone())
            day_end = datetime.combine(date, time.max).replace(tzinfo=timezone.get_current_timezone())
            
            readings = PowerReading.objects.filter(
                device=device,
                timestamp__range=[day_start, day_end]
            )
            
            if readings.exists():
                avg_power = sum(r.power for r in readings) / len(readings)
                peak_power = max(r.power for r in readings)
                min_power = min(r.power for r in readings)
                
                # Calculate total consumption (kWh)
                # Power readings every 5 minutes = 288 readings per day
                # kWh = (sum of watts * hours) / 1000
                total_consumption = sum(r.power for r in readings) * (5/60) / 1000
                
                total_cost = total_consumption * tariff.rate_per_kwh
                
                DailyConsumption.objects.create(
                    device=device,
                    device_identifier=device.device_id,
                    date=date,
                    total_consumption=total_consumption,
                    avg_power=avg_power,
                    peak_power=peak_power,
                    min_power=min_power,
                    total_cost=total_cost
                )
                count += 1
        
        return count
    
    def generate_alerts(self, device):
        """Generate sample alerts"""
        now = timezone.now()
        count = 0
        
        alerts_data = [
            {
                'alert_type': 'VOLTAGE_HIGH',
                'message': 'Voltage exceeded maximum threshold of 250V',
                'value': 252.3,
                'severity': 'WARNING',
                'status': 'RESOLVED',
                'hours_ago': 48,
            },
            {
                'alert_type': 'CURRENT_HIGH',
                'message': 'Current exceeded maximum limit of 25A',
                'value': 26.8,
                'severity': 'WARNING',
                'status': 'ACKNOWLEDGED',
                'hours_ago': 24,
            },
            {
                'alert_type': 'BATTERY_LOW',
                'message': 'Battery level critically low',
                'value': 18.5,
                'severity': 'CRITICAL',
                'status': 'ACTIVE',
                'hours_ago': 2,
            },
            {
                'alert_type': 'FREQUENCY_ABNORMAL',
                'message': 'Frequency out of normal range',
                'value': 47.8,
                'severity': 'WARNING',
                'status': 'ACTIVE',
                'hours_ago': 1,
            },
            {
                'alert_type': 'POWER_FACTOR_LOW',
                'message': 'Low power factor detected',
                'value': 0.82,
                'severity': 'INFO',
                'status': 'ACTIVE',
                'hours_ago': 12,
            },
        ]
        
        for alert_data in alerts_data:
            timestamp = now - timedelta(hours=alert_data['hours_ago'])
            resolved_at = None
            
            if alert_data['status'] == 'RESOLVED':
                resolved_at = timestamp + timedelta(hours=random.randint(1, 6))
            
            Alert.objects.create(
                device=device,
                device_identifier=device.device_id,
                alert_type=alert_data['alert_type'],
                message=alert_data['message'],
                value=alert_data['value'],
                severity=alert_data['severity'],
                status=alert_data['status'],
                timestamp=timestamp,
                resolved_at=resolved_at
            )
            count += 1
        
        return count
    
    def print_summary(self):
        """Print summary of generated data"""
        from power_monitor.models import Client, EnergyReport, WhatsAppMessage
        
        self.stdout.write('\nData Summary:')
        self.stdout.write(f"  Devices: {Device.objects.count()}")
        self.stdout.write(f"  Clients: {Client.objects.count()}")
        self.stdout.write(f"  Power Readings: {PowerReading.objects.count()}")
        self.stdout.write(f"  Battery Readings: {BatteryReading.objects.count()}")
        self.stdout.write(f"  Daily Consumption: {DailyConsumption.objects.count()}")
        self.stdout.write(f"  Alerts: {Alert.objects.count()}")
        self.stdout.write(f"  Energy Reports: {EnergyReport.objects.count()}")
        self.stdout.write(f"  WhatsApp Messages: {WhatsAppMessage.objects.count()}")
        self.stdout.write(f"  Tariffs: {EnergyTariff.objects.count()}")
        
        # Alert breakdown
        active_alerts = Alert.objects.filter(status='ACTIVE').count()
        critical_alerts = Alert.objects.filter(severity='CRITICAL', status='ACTIVE').count()
        
        self.stdout.write('\nAlert Status:')
        self.stdout.write(f"  Active: {active_alerts}")
        self.stdout.write(f"  Critical: {critical_alerts}")
        
        # WhatsApp message breakdown
        sent_messages = WhatsAppMessage.objects.filter(status='SENT').count()
        failed_messages = WhatsAppMessage.objects.filter(status='FAILED').count()
        
        self.stdout.write('\nWhatsApp Messages:')
        self.stdout.write(f"  Sent: {sent_messages}")
        self.stdout.write(f"  Failed: {failed_messages}")
        
        # Latest readings
        latest_reading = PowerReading.objects.first()
        if latest_reading:
            self.stdout.write('\nLatest Reading:')
            self.stdout.write(f"  Device: {latest_reading.device.device_name}")
            self.stdout.write(f"  Power: {latest_reading.power:.2f} W")
            self.stdout.write(f"  Voltage: {latest_reading.voltage:.2f} V")
            self.stdout.write(f"  Battery SoC: {latest_reading.battery_soc:.1f}%")


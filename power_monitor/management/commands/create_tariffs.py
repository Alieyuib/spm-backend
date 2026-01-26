# Create a simple script to populate initial tariff data
# management/commands/create_tariffs.py
from django.core.management.base import BaseCommand
from power_monitor.models import EnergyTariff
from datetime import time

class Command(BaseCommand):
    help = 'Create default energy tariffs'
    
    def handle(self, *args, **kwargs):
        tariffs = [
            {
                'name': 'Standard Rate (Nigeria)',
                'rate_per_kwh': 65.0,
                'currency': 'NGN',
            },
            {
                'name': 'Off-Peak Rate',
                'rate_per_kwh': 45.0,
                'currency': 'NGN',
                'time_of_day_start': time(22, 0),
                'time_of_day_end': time(6, 0),
            },
            {
                'name': 'Peak Rate',
                'rate_per_kwh': 85.0,
                'currency': 'NGN',
                'time_of_day_start': time(17, 0),
                'time_of_day_end': time(22, 0),
            },
            {
                'name': 'USD Standard Rate',
                'rate_per_kwh': 0.12,
                'currency': 'USD',
            },
        ]
        
        created_count = 0
        for tariff_data in tariffs:
            tariff, created = EnergyTariff.objects.get_or_create(
                name=tariff_data['name'],
                defaults=tariff_data
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'✓ Created: {tariff.name}'))
            else:
                self.stdout.write(f'  Already exists: {tariff.name}')
        
        self.stdout.write(self.style.SUCCESS(f'\nCreated {created_count} new tariffs'))
        self.stdout.write(f'Total tariffs: {EnergyTariff.objects.count()}')
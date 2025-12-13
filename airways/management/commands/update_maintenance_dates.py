"""
Enhanced maintenance models for whiteboard calendar
Add these methods to your existing Component model or create management commands
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from maintenance.models import (
    AircraftMainComponent, AircraftSubComponent,
    AircraftSub2Component, AircraftSub3Component
)


class Command(BaseCommand):
    help = 'Update next maintenance dates for all components based on their calendar and hours'

    def handle(self, *args, **kwargs):
        """
        Calculate and update next_maintenance_date for all components
        This should run as a daily cron job
        """
        component_models = [
            AircraftMainComponent,
            AircraftSubComponent,
            AircraftSub2Component,
            AircraftSub3Component,
        ]
        
        total_updated = 0
        
        for Model in component_models:
            components = Model.objects.filter(
                component_status='Attached',
                maintenance_status='Operational'
            )
            
            for component in components:
                next_date = self.calculate_next_maintenance_date(component)
                if next_date and next_date != component.next_maintenance_date:
                    component.next_maintenance_date = next_date
                    component.save(update_fields=['next_maintenance_date'])
                    total_updated += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully updated {total_updated} component next maintenance dates')
        )
    
    def calculate_next_maintenance_date(self, component):
        """
        Calculate the next recommended maintenance date based on:
        1. Calendar maintenance (item_calender)
        2. Hours-based maintenance (min_maintenance_hours)
        3. Cycle-based maintenance (max_item_cycle)
        
        Returns the earliest date when maintenance is recommended
        """
        potential_dates = []
        
        # 1. Calendar-based maintenance
        if component.item_calender and component.item_calender_months:
            # If calendar maintenance is approaching (within 30 days), recommend it
            if component.item_calender:
                days_until_due = (component.item_calender - timezone.now()).days
                if 0 <= days_until_due <= 90:
                    # Recommend 30 days before due date
                    potential_dates.append(
                        component.item_calender - timedelta(days=30)
                    )
        
        # 2. Hours-based maintenance
        if component.min_maintenance_hours:
            # Estimate when hours will run out based on average usage
            current_hours = component.maintenance_hours
            min_hours = component.min_maintenance_hours
            
            if current_hours <= min_hours + 50:  # Within 50 hours of minimum
                # Estimate 2 weeks ahead (conservative estimate)
                potential_dates.append(
                    timezone.now() + timedelta(days=14)
                )
        
        # 3. Cycle-based maintenance
        if component.max_item_cycle and component.item_cycle:
            cycles_remaining = component.max_item_cycle - component.item_cycle
            if cycles_remaining <= 10:  # Within 10 cycles
                # Estimate based on average cycle rate
                potential_dates.append(
                    timezone.now() + timedelta(days=7)
                )
        
        # Return the earliest potential date
        if potential_dates:
            return min(potential_dates)
        
        return None


class UpdateComponentHoursCommand(BaseCommand):
    """
    Helper command to calculate maintenance hours remaining for components
    """
    help = 'Calculate maintenance hours status for all components'
    
    def handle(self, *args, **kwargs):
        component_models = [
            AircraftMainComponent,
            AircraftSubComponent,
            AircraftSub2Component,
            AircraftSub3Component,
        ]
        
        critical_components = 0
        warning_components = 0
        healthy_components = 0
        
        for Model in component_models:
            components = Model.objects.filter(component_status='Attached')
            
            for component in components:
                hours = component.maintenance_hours
                
                if hours < 10:
                    critical_components += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f'CRITICAL: {component.component_name} - {hours} hours remaining'
                        )
                    )
                elif hours < 50:
                    warning_components += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f'WARNING: {component.component_name} - {hours} hours remaining'
                        )
                    )
                else:
                    healthy_components += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSummary:\n'
                f'Critical: {critical_components}\n'
                f'Warning: {warning_components}\n'
                f'Healthy: {healthy_components}'
            )
        )
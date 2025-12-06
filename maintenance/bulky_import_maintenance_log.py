import csv
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "your_project.settings")
django.setup()

from maintenance.models import AircraftMaintenanceTechLog
from django.utils.dateparse import parse_datetime

# Database settings (not needed in the script, but ensure your Django settings are configured)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'eaw_erp_prd01',
        'USER': 'postgres',
        'PASSWORD': 'heaven2870',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

def parse_date(date_string):
    return parse_datetime(date_string) if date_string else None

def upload_csv(csv_file_path):
    with open(csv_file_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            tech_log = AircraftMaintenanceTechLog(
                # Assuming CSV column names match model field names
                aircraft_id=row.get('aircraft'),
                off_block=row.get('off_block'),
                flight_log_number=row.get('flight_log_number'),
                on_block=row.get('on_block'),
                # ... add all other fields similarly
                arrival_date=parse_date(row.get('arrival_date')),
                # Handle other fields, especially those needing type conversion
            )
            tech_log.save()

if __name__ == "__main__":
    csv_file_path = 'path_to_your_csv_file.csv'
    upload_csv(csv_file_path)

import os
import django

# Bootstrap Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'reservations.settings')
django.setup()

from django.core.management import call_command

if __name__ == "__main__":
    # Run the existing management command so there's a single source of truth
    call_command('create_test_lessons')

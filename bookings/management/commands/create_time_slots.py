from django.core.management.base import BaseCommand
from django.utils import timezone
from bookings.models import Lesson, TimeSlot
from datetime import datetime, time

class Command(BaseCommand):
    help = 'Vytvoří TimeSlot pro každou existující Lesson'

    def handle(self, *args, **kwargs):
        lessons = Lesson.objects.all()
        created_count = 0
        
        for lesson in lessons:
            # Zkombinujeme datum a čas z lekce
            start_datetime = datetime.combine(lesson.date, lesson.start_time)
            # Ujistíme se, že je to timezone-aware
            start_datetime = timezone.make_aware(start_datetime)
            
            # Vytvoříme TimeSlot pouze pokud ještě neexistuje
            time_slot, created = TimeSlot.objects.get_or_create(
                lesson=lesson,
                start_time=start_datetime,
                defaults={'is_available': True}
            )
            
            if created:
                created_count += 1
                self.stdout.write(f"Vytvořen TimeSlot pro {lesson.title} - {start_datetime}")
        
        self.stdout.write(self.style.SUCCESS(f'Celkem vytvořeno {created_count} nových TimeSlotů'))

from django.core.management.base import BaseCommand
from django.utils import timezone
from bookings.models import Lesson
from django.contrib.auth import get_user_model
from datetime import time, timedelta

class Command(BaseCommand):
    help = 'Vytvoří testovací lekce pro kalendář'

    def handle(self, *args, **kwargs):
        User = get_user_model()
        
        # Najít nebo vytvořit instruktora
        instructor, created = User.objects.get_or_create(
            username='testinstructor',
            defaults={
                'email': 'instructor@test.com',
                'first_name': 'Test',
                'last_name': 'Instructor',
                'user_type': 'instructor'
            }
        )
        
        # Aktuální datum pro tento měsíc
        current_date = timezone.now().date()
        
        # Seznam lekcí k vytvoření
        lessons_data = [
            {
                'title': 'Ranní jóga',
                'description': 'Začněte den s jógou',
                'price': '200.00',
                'duration': 60,
                'capacity': 10,
                'category': 'yoga',
                'location': 'Sál 1',
                'start_time': time(8, 0)  # 8:00
            },
            {
                'title': 'Kardio workout',
                'description': 'Intenzivní kardio trénink',
                'price': '250.00',
                'duration': 45,
                'capacity': 15,
                'category': 'cardio',
                'location': 'Sál 2',
                'start_time': time(17, 30)  # 17:30
            },
            {
                'title': 'Pilates pro začátečníky',
                'description': 'Základy pilates',
                'price': '200.00',
                'duration': 55,
                'capacity': 12,
                'category': 'pilates',
                'location': 'Sál 1',
                'start_time': time(10, 0)  # 10:00
            }
        ]
        
        # Vytvoření lekcí pro následujících 14 dní
        for i in range(14):
            lesson_date = current_date + timedelta(days=i)
            
            # Pro každý den vytvoříme všechny typy lekcí
            for lesson_data in lessons_data:
                Lesson.objects.create(
                    instructor=instructor,
                    date=lesson_date,
                    **lesson_data
                )
        
        self.stdout.write(self.style.SUCCESS('Úspěšně vytvořeny testovací lekce'))
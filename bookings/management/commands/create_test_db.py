from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from bookings.models import Category, Lesson, TimeSlot, Booking
from payments.models import TopUp, Payment
from datetime import time, timedelta, datetime
from decimal import Decimal

User = get_user_model()


class Command(BaseCommand):
    help = 'Vytvoří kompletní testovací data - uživatele, kategorie, lekce, rezervace'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Smaže všechna existující data před vytvořením nových',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Mažu existující data...'))
            Booking.objects.all().delete()
            TimeSlot.objects.all().delete()
            Lesson.objects.all().delete()
            Category.objects.all().delete()
            Payment.objects.all().delete()
            TopUp.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()
            self.stdout.write(self.style.SUCCESS('✓ Data smazána'))

        # 1. Vytvoření kategorií
        self.stdout.write('Vytvářím kategorie...')
        categories = [
            ('yoga', 'Jóga', 'Relaxační a protahovací cvičení zaměřené na tělo i mysl', 1),
            ('pilates', 'Pilates', 'Posilování hlubokých svalů a správné držení těla', 2),
            ('cardio', 'Cardio', 'Intenzivní kardiovaskulární trénink pro spalování kalorií', 3),
            ('strength', 'Silový trénink', 'Posilování svalové hmoty s váhami a činkami', 4),
            ('stretch', 'Protažení', 'Strečink a mobilita pro lepší pohyblivost', 5),
            ('dance', 'Taneční', 'Zumba, aerobik a další taneční lekce', 6),
            ('functional', 'Funkční trénink', 'Komplexní cvičení s vlastní vahou', 7),
        ]
        
        cat_objects = {}
        for slug, name, desc, order in categories:
            cat, created = Category.objects.get_or_create(
                slug=slug,
                defaults={'name': name, 'description': desc, 'order': order}
            )
            cat_objects[slug] = cat
            status = '✓ Vytvořeno' if created else '- Existuje'
            self.stdout.write(f'  {status}: {name}')

        # 2. Vytvoření uživatelů
        self.stdout.write('\nVytvářím uživatele...')
        
        # Instruktoři
        instructors = []
        instructor_data = [
            ('anna.novak', 'Anna', 'Nováková', 'anna@fitness.cz'),
            ('petr.svoboda', 'Petr', 'Svoboda', 'petr@fitness.cz'),
            ('marie.dvorak', 'Marie', 'Dvořáková', 'marie@fitness.cz'),
        ]
        
        for username, first, last, email in instructor_data:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': first,
                    'last_name': last,
                    'user_type': 'instructor',
                    'phone': '+420 777 888 999',
                    'bio': f'Profesionální trenér/ka s mnohaletými zkušenostmi.'
                }
            )
            if created:
                user.set_password('heslo123')
                user.save()
            instructors.append(user)
            status = '✓ Vytvořeno' if created else '- Existuje'
            self.stdout.write(f'  {status}: Instruktor {first} {last}')

        # Klienti
        clients = []
        client_data = [
            ('jan.novak', 'Jan', 'Novák', 'jan@email.cz', 500),
            ('eva.mala', 'Eva', 'Malá', 'eva@email.cz', 1000),
            ('tomas.velky', 'Tomáš', 'Velký', 'tomas@email.cz', 750),
            ('katerina.kral', 'Kateřina', 'Králová', 'katerina@email.cz', 300),
            ('lukas.hora', 'Lukáš', 'Hora', 'lukas@email.cz', 1500),
        ]
        
        for username, first, last, email, credits in client_data:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': first,
                    'last_name': last,
                    'user_type': 'client',
                    'credits': Decimal(credits),
                    'phone': '+420 606 123 456',
                }
            )
            if created:
                user.set_password('heslo123')
                user.save()
            clients.append(user)
            status = '✓ Vytvořeno' if created else '- Existuje'
            self.stdout.write(f'  {status}: Klient {first} {last} ({credits} Kč)')

        # 3. Vytvoření lekcí
        self.stdout.write('\nVytvářím lekce...')
        
        lessons_template = [
            # Anna - Jóga a Protažení
            ('Ranní jóga', cat_objects['yoga'], instructors[0], 200, 60, 12, 'Sál 1', time(7, 0), 'Začněte den s jógou'),
            ('Odpolední jóga', cat_objects['yoga'], instructors[0], 200, 60, 12, 'Sál 1', time(17, 0), 'Uvolnění po práci'),
            ('Večerní strečink', cat_objects['stretch'], instructors[0], 150, 45, 15, 'Sál 1', time(19, 30), 'Protažení celého těla'),
            
            # Petr - Cardio a Funkční
            ('HIIT workout', cat_objects['cardio'], instructors[1], 250, 45, 15, 'Sál 2', time(6, 30), 'Vysokointenzivní intervalový trénink'),
            ('Funkční trénink', cat_objects['functional'], instructors[1], 220, 60, 12, 'Sál 2', time(18, 0), 'Komplexní cvičení s vlastní vahou'),
            ('Spinning', cat_objects['cardio'], instructors[1], 200, 50, 20, 'Spinning sál', time(12, 0), 'Indoor cycling'),
            
            # Marie - Pilates a Silový
            ('Pilates začátečníci', cat_objects['pilates'], instructors[2], 200, 55, 10, 'Sál 3', time(9, 0), 'Úvod do pilates'),
            ('Pilates pokročilí', cat_objects['pilates'], instructors[2], 250, 60, 10, 'Sál 3', time(10, 30), 'Pokročilé techniky'),
            ('TRX trénink', cat_objects['strength'], instructors[2], 230, 50, 8, 'Sál 3', time(16, 0), 'Posilování na závěsném systému'),
            ('Kruhový trénink', cat_objects['strength'], instructors[2], 200, 60, 15, 'Sál 2', time(20, 0), 'Circuit training'),
        ]
        
        created_lessons = []
        current_date = timezone.now().date()
        
        # Vytvoříme lekce pro následujících 21 dní
        for i in range(21):
            lesson_date = current_date + timedelta(days=i)
            day_of_week = lesson_date.weekday()  # 0=Po, 6=Ne
            
            for title, category, instructor, price, duration, capacity, location, start, description in lessons_template:
                # Různé lekce v různé dny
                # HIIT jen Po, St, Pá
                if 'HIIT' in title and day_of_week not in [0, 2, 4]:
                    continue
                # Pilates jen Út, Čt
                if 'Pilates' in title and day_of_week not in [1, 3]:
                    continue
                # Spinning jen St, So
                if 'Spinning' in title and day_of_week not in [2, 5]:
                    continue
                # Jóga každý den kromě Ne
                if 'jóga' in title.lower() and day_of_week == 6:
                    continue
                    
                lesson = Lesson.objects.create(
                    instructor=instructor,
                    title=title,
                    description=description,
                    price=Decimal(price),
                    duration=duration,
                    capacity=capacity,
                    date=lesson_date,
                    start_time=start,
                    location=location,
                    category=category
                )
                created_lessons.append(lesson)
        
        self.stdout.write(f'  ✓ Vytvořeno {len(created_lessons)} lekcí')

        # 4. Vytvoření časových slotů
        self.stdout.write('\nVytvářím časové sloty...')
        time_slots_count = 0
        
        for lesson in created_lessons:
            # Spojíme datum a čas do datetime
            lesson_datetime = timezone.make_aware(
                datetime.combine(lesson.date, lesson.start_time)
            )
            
            time_slot = TimeSlot.objects.create(
                lesson=lesson,
                start_time=lesson_datetime,
                is_available=True
            )
            time_slots_count += 1
        
        self.stdout.write(f'  ✓ Vytvořeno {time_slots_count} časových slotů')

        # 5. Vytvoření rezervací (jen pro budoucí lekce)
        self.stdout.write('\nVytvářím rezervace...')
        future_slots = TimeSlot.objects.filter(start_time__gte=timezone.now()).order_by('start_time')[:30]
        bookings_count = 0
        
        import random
        for slot in future_slots:
            # Náhodně vytvoříme 1-3 rezervace pro každý slot
            num_bookings = random.randint(1, min(3, slot.lesson.capacity))
            available_clients = random.sample(clients, min(num_bookings, len(clients)))
            
            for client in available_clients:
                if client.credits >= slot.lesson.price:
                    booking = Booking.objects.create(
                        client=client,
                        time_slot=slot,
                        status='confirmed'
                    )
                    bookings_count += 1
        
        self.stdout.write(f'  ✓ Vytvořeno {bookings_count} rezervací')

        # 6. Vytvoření některých čekajících dobití
        self.stdout.write('\nVytvářím testovací dobití...')
        topup_count = 0
        for client in clients[:3]:
            topup = TopUp.objects.create(
                user=client,
                amount=Decimal('500.00'),
                variable_symbol=str(client.id),
                message=f'{client.get_full_name()}',
                status='pending'
            )
            topup_count += 1
        
        self.stdout.write(f'  ✓ Vytvořeno {topup_count} čekajících dobití')

        # 7. Vytvoření testovacích plateb mezi klientem a instruktorem
        self.stdout.write('\nVytvářím testovací platby...')
        payment_count = 0
        
        # Vytvoříme různé stavy plateb
        payment_scenarios = [
            # Čekající platby (pending) - ke schválení instruktorem
            (clients[0], instructors[0], Decimal('500.00'), 'pending'),
            (clients[1], instructors[1], Decimal('1000.00'), 'pending'),
            (clients[2], instructors[2], Decimal('750.00'), 'pending'),
            
            # Potvrzené platby (confirmed) - už připsané
            (clients[3], instructors[0], Decimal('300.00'), 'confirmed'),
            (clients[4], instructors[1], Decimal('1500.00'), 'confirmed'),
            (clients[0], instructors[2], Decimal('400.00'), 'confirmed'),
            
            # Zrušené platby (cancelled)
            (clients[1], instructors[0], Decimal('200.00'), 'cancelled'),
        ]
        
        for client, instructor, amount, status in payment_scenarios:
            payment = Payment.objects.create(
                client=client,
                instructor=instructor,
                amount=amount,
                status=status
            )
            payment_count += 1
            
            # Pro potvrzené platby se kredit připsává automaticky v save()
            # ale musíme to obejít, protože klient už má přednastavený kredit
            if status == 'confirmed':
                # Označíme, že platba už byla zpracována, aby se kredit nepřipsal znovu
                payment._payment_processed = True
                payment.save()
        
        self.stdout.write(f'  ✓ Vytvořeno {payment_count} plateb')
        self.stdout.write(f'    - Čekajících: {Payment.objects.filter(status="pending").count()}')
        self.stdout.write(f'    - Potvrzených: {Payment.objects.filter(status="confirmed").count()}')
        self.stdout.write(f'    - Zrušených: {Payment.objects.filter(status="cancelled").count()}')

        # Souhrn
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('✓ Testovací data úspěšně vytvořena!'))
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(f'\nPřihlašovací údaje:')
        self.stdout.write(f'  Instruktoři: anna.novak, petr.svoboda, marie.dvorak')
        self.stdout.write(f'  Klienti: jan.novak, eva.mala, tomas.velky, katerina.kral, lukas.hora')
        self.stdout.write(f'  Heslo pro všechny: heslo123')
        self.stdout.write(f'\nStatistiky:')
        self.stdout.write(f'  Kategorie: {Category.objects.count()}')
        self.stdout.write(f'  Uživatelé: {User.objects.filter(is_superuser=False).count()}')
        self.stdout.write(f'  Lekce: {Lesson.objects.count()}')
        self.stdout.write(f'  Časové sloty: {TimeSlot.objects.count()}')
        self.stdout.write(f'  Rezervace: {Booking.objects.count()}')
        self.stdout.write(f'  Platby (klient → instruktor): {Payment.objects.count()}')
        self.stdout.write(f'  Čekající dobití: {TopUp.objects.filter(status="pending").count()}')

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta, datetime, time as dtime
import random

from bookings.models import Lesson, TimeSlot, Booking
from payments.models import Payment

User = get_user_model()


class Command(BaseCommand):
    help = 'Vytvoří testovací data: uživatele, lekce, termíny, rezervace a platby.'

    def handle(self, *args, **options):
        now = timezone.now()

        # Vytvoříme 2 lektory
        instructors = []
        for i in range(1, 3):
            username = f'lektor{i}'
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@example.com',
                    'first_name': f'Lektor{i}',
                    'user_type': 'instructor'
                }
            )
            if created:
                user.set_password('password123')
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Vytvořen lektor: {username}'))
            else:
                self.stdout.write(f'Lektor {username} již existuje, přeskočeno')
            instructors.append(user)

        # Vytvoříme 3 klienty
        clients = []
        for i in range(1, 4):
            username = f'klient{i}'
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@example.com',
                    'first_name': f'Klient{i}',
                    'user_type': 'client',
                    'credits': 200.00,
                }
            )
            if created:
                user.set_password('password123')
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Vytvořen klient: {username}'))
            else:
                # zkontrolujeme, že mají aspoň 200 kreditů
                if user.credits < 50:
                    user.credits = 200
                    user.save()
                self.stdout.write(f'Klient {username} již existuje, přeskočeno')
            clients.append(user)

        # Pro každého lektora vytvoříme jednu lekci
        lessons = []
        for idx, instr in enumerate(instructors, start=1):
            title = f'Lekce #{idx} - Základní kurz'
            lesson, created = Lesson.objects.get_or_create(
                instructor=instr,
                title=title,
                defaults={
                    'description': 'Ukázková lekce pro testovací data.',
                    'price': 100 + idx * 50,
                    'duration': 60,
                    'capacity': 6,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Vytvořena lekce: {title}'))
            else:
                self.stdout.write(f'Lekce {title} již existuje, přeskočeno')
            lessons.append(lesson)

        # Vytvoříme timesloty pro následujících 10 dní (3 sloty/den)
        created_slots = 0
        for day_offset in range(1, 11):
            date = (now + timedelta(days=day_offset)).date()
            for hour in (10, 14, 18):
                for lesson in lessons:
                    start_dt = datetime.combine(date, dtime(hour, 0))
                    start_aware = timezone.make_aware(start_dt)
                    slot, created = TimeSlot.objects.get_or_create(
                        lesson=lesson,
                        start_time=start_aware,
                        defaults={'is_available': True}
                    )
                    if created:
                        created_slots += 1
        self.stdout.write(self.style.SUCCESS(f'Vytvořeno {created_slots} timeslotů'))

        # Vytvoříme několik potvrzených rezervací náhodně
        created_bookings = 0
        all_slots = list(TimeSlot.objects.filter(start_time__gte=now).order_by('start_time')[:50])
        random.shuffle(all_slots)
        for client in clients:
            # každý klient vytvoří 1-2 rezervace
            for _ in range(random.randint(1, 2)):
                if not all_slots:
                    break
                slot = all_slots.pop()
                # ujistíme se, že klient má dost kreditů
                if client.credits < slot.lesson.price:
                    client.credits += 200
                    client.save()
                booking, created = Booking.objects.get_or_create(
                    client=client,
                    time_slot=slot,
                    defaults={'status': 'confirmed'}
                )
                if created:
                    # save() u Bookingu odečte kredity a označí slot jako nedostupný
                    booking.status = 'confirmed'
                    booking.save()
                    created_bookings += 1
        self.stdout.write(self.style.SUCCESS(f'Vytvořeno {created_bookings} potvrzených rezervací'))

        # Vytvoříme několik plateb (pending) od klientů lektorům
        created_payments = 0
        for i, client in enumerate(clients, start=1):
            instr = random.choice(instructors)
            amount = random.choice([50, 100, 150])
            payment = Payment.objects.create(client=client, instructor=instr, amount=amount, status='pending')
            # uložíme a necháme QR vygenerovat
            payment.save()
            created_payments += 1
        self.stdout.write(self.style.SUCCESS(f'Vytvořeno {created_payments} plateb (pending)'))

        self.stdout.write(self.style.SUCCESS('Testovací data byla vytvořena.'))

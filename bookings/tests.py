"""
Testy pro aplikaci bookings - lekce, časové sloty, rezervace.
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import datetime, timedelta, time

from .models import Category, Lesson, TimeSlot, Booking

User = get_user_model()


class CategoryModelTests(TestCase):
    """Testy pro model Category."""

    def test_category_creation(self):
        """Test vytvoření kategorie."""
        category = Category.objects.create(
            name='Jóga',
            slug='joga',
            description='Relaxační lekce jógy',
            order=1
        )
        self.assertEqual(str(category), 'Jóga')
        self.assertEqual(category.slug, 'joga')


class LessonModelTests(TestCase):
    """Testy pro model Lesson."""

    def setUp(self):
        """Příprava testovacích dat."""
        self.instructor = User.objects.create_user(
            username='lektor@test.cz',
            email='lektor@test.cz',
            password='testpass123',
            user_type='instructor'
        )
        
        self.category = Category.objects.create(
            name='Jóga',
            slug='joga',
            order=1
        )
        
        self.tomorrow = timezone.now().date() + timedelta(days=1)

    def test_lesson_creation(self):
        """Test vytvoření lekce."""
        lesson = Lesson.objects.create(
            instructor=self.instructor,
            title='Ranní jóga',
            description='Relaxační lekce pro začátečníky',
            price=Decimal('200.00'),
            duration=60,
            capacity=10,
            date=self.tomorrow,
            start_time=time(9, 0),
            location='Studio A',
            category=self.category
        )
        
        self.assertEqual(lesson.title, 'Ranní jóga')
        self.assertEqual(lesson.instructor, self.instructor)
        self.assertEqual(lesson.price, Decimal('200.00'))
        self.assertIn('Ranní jóga', str(lesson))


class TimeSlotModelTests(TestCase):
    """Testy pro model TimeSlot."""

    def setUp(self):
        """Příprava testovacích dat."""
        self.instructor = User.objects.create_user(
            username='lektor@test.cz',
            email='lektor@test.cz',
            password='testpass123',
            user_type='instructor'
        )
        
        self.category = Category.objects.create(name='Jóga', slug='joga', order=1)
        
        self.tomorrow = timezone.now().date() + timedelta(days=1)
        
        self.lesson = Lesson.objects.create(
            instructor=self.instructor,
            title='Test lekce',
            price=Decimal('200.00'),
            duration=60,
            capacity=10,
            date=self.tomorrow,
            start_time=time(9, 0),
            category=self.category
        )

    def test_timeslot_creation(self):
        """Test vytvoření časového slotu."""
        future_time = timezone.now() + timedelta(days=1)
        
        slot = TimeSlot.objects.create(
            lesson=self.lesson,
            start_time=future_time,
            is_available=True
        )
        
        self.assertEqual(slot.lesson, self.lesson)
        self.assertTrue(slot.is_available)
        self.assertIn('Test lekce', str(slot))

    def test_timeslot_validation_past_time(self):
        """Test, že nelze vytvořit slot v minulosti."""
        past_time = timezone.now() - timedelta(days=1)
        
        slot = TimeSlot(
            lesson=self.lesson,
            start_time=past_time
        )
        
        with self.assertRaises(ValidationError):
            slot.clean()


class BookingModelTests(TestCase):
    """Testy pro model Booking."""

    def setUp(self):
        """Příprava testovacích dat."""
        self.client_user = User.objects.create_user(
            username='klient@test.cz',
            email='klient@test.cz',
            password='testpass123',
            user_type='client',
            credits=Decimal('500.00')
        )
        
        self.instructor = User.objects.create_user(
            username='lektor@test.cz',
            email='lektor@test.cz',
            password='testpass123',
            user_type='instructor'
        )
        
        self.category = Category.objects.create(name='Jóga', slug='joga', order=1)
        
        tomorrow = timezone.now().date() + timedelta(days=1)
        
        self.lesson = Lesson.objects.create(
            instructor=self.instructor,
            title='Test lekce',
            price=Decimal('200.00'),
            duration=60,
            capacity=10,
            date=tomorrow,
            start_time=time(9, 0),
            category=self.category
        )
        
        future_time = timezone.now() + timedelta(days=1)
        
        self.time_slot = TimeSlot.objects.create(
            lesson=self.lesson,
            start_time=future_time,
            is_available=True
        )

    def test_successful_booking_creation(self):
        """Test úspěšného vytvoření rezervace."""
        initial_credits = self.client_user.credits
        
        booking = Booking.objects.create(
            client=self.client_user,
            time_slot=self.time_slot,
            status='confirmed'
        )
        
        # Ověření, že rezervace byla vytvořena
        self.assertEqual(booking.client, self.client_user)
        self.assertEqual(booking.time_slot, self.time_slot)
        self.assertEqual(booking.status, 'confirmed')
        
        # Ověření, že kredity byly odečteny
        self.client_user.refresh_from_db()
        self.assertEqual(
            self.client_user.credits,
            initial_credits - self.lesson.price
        )
        
        # Ověření, že slot byl uzamčen
        self.time_slot.refresh_from_db()
        self.assertFalse(self.time_slot.is_available)

    def test_booking_with_insufficient_credits(self):
        """Test rezervace s nedostatečným kreditem."""
        # Nastavíme klientovi nízký kredit
        self.client_user.credits = Decimal('50.00')
        self.client_user.save()
        
        booking = Booking(
            client=self.client_user,
            time_slot=self.time_slot,
            status='pending'
        )
        
        with self.assertRaises(ValidationError):
            booking.clean()

    def test_booking_unavailable_slot(self):
        """Test rezervace již obsazeného slotu."""
        # Uzamkneme slot
        self.time_slot.is_available = False
        self.time_slot.save()
        
        booking = Booking(
            client=self.client_user,
            time_slot=self.time_slot,
            status='pending'
        )
        
        with self.assertRaises(ValidationError):
            booking.clean()

    def test_booking_cancellation_in_time(self):
        """Test zrušení rezervace včas (> 2 hodiny před začátkem)."""
        # Vytvoříme rezervaci na lekci za 3 hodiny
        future_time = timezone.now() + timedelta(hours=3)
        self.time_slot.start_time = future_time
        self.time_slot.save()
        
        booking = Booking.objects.create(
            client=self.client_user,
            time_slot=self.time_slot,
            status='confirmed'
        )
        
        initial_credits = self.client_user.credits
        
        # Zrušíme rezervaci
        self.assertTrue(booking.can_cancel())
        booking.cancel()
        
        # Ověření vrácení kreditu
        self.client_user.refresh_from_db()
        self.assertEqual(
            self.client_user.credits,
            initial_credits + self.lesson.price
        )
        
        # Ověření uvolnění slotu
        self.time_slot.refresh_from_db()
        self.assertTrue(self.time_slot.is_available)
        
        # Ověření statusu
        self.assertEqual(booking.status, 'cancelled')

    def test_booking_cancellation_too_late(self):
        """Test zrušení rezervace pozdě (< 2 hodiny před začátkem)."""
        # Vytvoříme rezervaci na lekci za 1 hodinu
        future_time = timezone.now() + timedelta(hours=1)
        self.time_slot.start_time = future_time
        self.time_slot.save()
        
        booking = Booking.objects.create(
            client=self.client_user,
            time_slot=self.time_slot,
            status='confirmed'
        )
        
        # Pokus o zrušení by měl selhat
        self.assertFalse(booking.can_cancel())
        
        with self.assertRaises(ValidationError):
            booking.cancel()


class LessonViewTests(TestCase):
    """Testy pro views související s lekcemi."""

    def setUp(self):
        """Příprava testovacích dat."""
        self.client = Client()
        
        self.instructor = User.objects.create_user(
            username='lektor@test.cz',
            email='lektor@test.cz',
            password='testpass123',
            user_type='instructor'
        )
        
        self.client_user = User.objects.create_user(
            username='klient@test.cz',
            email='klient@test.cz',
            password='testpass123',
            user_type='client',
            credits=Decimal('1000.00')
        )
        
        self.category = Category.objects.create(name='Jóga', slug='joga', order=1)

    def test_lessons_list_accessible(self):
        """Test, že seznam lekcí je veřejně přístupný."""
        response = self.client.get(reverse('lessons'))
        self.assertEqual(response.status_code, 200)

    def test_instructor_can_create_lesson(self):
        """Test, že lektor může vytvořit lekci."""
        self.client.login(username='lektor@test.cz', password='testpass123')
        
        tomorrow = timezone.now().date() + timedelta(days=1)
        
        data = {
            'title': 'Nová lekce',
            'description': 'Testovací popis',
            'category': self.category.id,
            'price': '200.00',
            'duration': 60,
            'capacity': 10,
            'date': tomorrow.strftime('%Y-%m-%d'),
            'start_time': '09:00',
            'location': 'Studio A'
        }
        
        response = self.client.post(reverse('bookings:lesson_create'), data)
        
        # Ověření přesměrování po úspěchu
        self.assertEqual(response.status_code, 302)
        
        # Ověření, že lekce byla vytvořena
        self.assertTrue(Lesson.objects.filter(title='Nová lekce').exists())

    def test_client_cannot_create_lesson(self):
        """Test, že klient NEMŮŽE vytvořit lekci."""
        self.client.login(username='klient@test.cz', password='testpass123')
        
        response = self.client.get(reverse('bookings:lesson_create'))
        
        # Očekáváme 403 nebo redirect
        self.assertIn(response.status_code, [302, 403])


class BookingViewTests(TestCase):
    """Testy pro views související s rezervacemi."""

    def setUp(self):
        """Příprava testovacích dat."""
        self.client = Client()
        
        self.client_user = User.objects.create_user(
            username='klient@test.cz',
            email='klient@test.cz',
            password='testpass123',
            user_type='client',
            credits=Decimal('1000.00')
        )
        
        self.instructor = User.objects.create_user(
            username='lektor@test.cz',
            email='lektor@test.cz',
            password='testpass123',
            user_type='instructor'
        )
        
        self.category = Category.objects.create(name='Jóga', slug='joga', order=1)
        
        tomorrow = timezone.now().date() + timedelta(days=1)
        
        self.lesson = Lesson.objects.create(
            instructor=self.instructor,
            title='Test lekce',
            price=Decimal('200.00'),
            duration=60,
            capacity=10,
            date=tomorrow,
            start_time=time(9, 0),
            category=self.category
        )
        
        future_time = timezone.now() + timedelta(days=1)
        
        self.time_slot = TimeSlot.objects.create(
            lesson=self.lesson,
            start_time=future_time,
            is_available=True
        )

    def test_authenticated_user_can_book_lesson(self):
        """Test, že přihlášený uživatel může rezervovat lekci."""
        self.client.login(username='klient@test.cz', password='testpass123')
        
        url = reverse('bookings:booking_create', kwargs={'time_slot_id': self.time_slot.id})
        response = self.client.post(url, {})
        
        # Ověření přesměrování
        self.assertEqual(response.status_code, 302)
        
        # Ověření, že rezervace byla vytvořena
        self.assertTrue(
            Booking.objects.filter(
                client=self.client_user,
                time_slot=self.time_slot
            ).exists()
        )

    def test_unauthenticated_user_cannot_book(self):
        """Test, že nepřihlášený uživatel nemůže rezervovat."""
        url = reverse('bookings:booking_create', kwargs={'time_slot_id': self.time_slot.id})
        response = self.client.post(url, {})
        
        # Očekáváme redirect na login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

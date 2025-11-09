"""
Pytest fixtures pro sdílená testovací data napříč všemi testy.

Použití v testech:
    def test_something(self, client_user, instructor_user):
        # client_user a instructor_user jsou připraveni k použití
"""
import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta, time

from bookings.models import Category, Lesson, TimeSlot, Booking
from payments.models import TopUp, Payment

User = get_user_model()


# ============= USER FIXTURES =============

@pytest.fixture
def client_user(db):
    """Fixture pro testovacího klienta s kreditem."""
    return User.objects.create_user(
        username='klient@test.cz',
        email='klient@test.cz',
        password='testpass123',
        first_name='Jan',
        last_name='Testovací',
        user_type='client',
        credits=Decimal('1000.00'),
        phone='123456789'
    )


@pytest.fixture
def client_user_no_credits(db):
    """Fixture pro klienta bez kreditů."""
    return User.objects.create_user(
        username='chudak@test.cz',
        email='chudak@test.cz',
        password='testpass123',
        first_name='Petr',
        last_name='Chudák',
        user_type='client',
        credits=Decimal('0.00')
    )


@pytest.fixture
def instructor_user(db):
    """Fixture pro testovacího lektora."""
    return User.objects.create_user(
        username='lektor@test.cz',
        email='lektor@test.cz',
        password='testpass123',
        first_name='Marie',
        last_name='Lektorová',
        user_type='instructor',
        credits=Decimal('0.00'),
        phone='987654321'
    )


# ============= CATEGORY FIXTURES =============

@pytest.fixture
def yoga_category(db):
    """Fixture pro kategorii Jóga."""
    return Category.objects.create(
        name='Jóga',
        slug='joga',
        description='Relaxační lekce jógy pro všechny úrovně',
        order=1
    )


@pytest.fixture
def pilates_category(db):
    """Fixture pro kategorii Pilates."""
    return Category.objects.create(
        name='Pilates',
        slug='pilates',
        description='Posilování hlubokých svalů',
        order=2
    )


# ============= LESSON FIXTURES =============

@pytest.fixture
def lesson_tomorrow(db, instructor_user, yoga_category):
    """Fixture pro lekci zítra."""
    tomorrow = timezone.now().date() + timedelta(days=1)
    
    return Lesson.objects.create(
        instructor=instructor_user,
        title='Ranní jóga',
        description='Relaxační lekce pro začátečníky',
        category=yoga_category,
        price=Decimal('200.00'),
        duration=60,
        capacity=10,
        date=tomorrow,
        start_time=time(9, 0),
        location='Studio A'
    )


@pytest.fixture
def lesson_next_week(db, instructor_user, pilates_category):
    """Fixture pro lekci za týden."""
    next_week = timezone.now().date() + timedelta(days=7)
    
    return Lesson.objects.create(
        instructor=instructor_user,
        title='Pilates pro pokročilé',
        description='Intenzivní trénink',
        category=pilates_category,
        price=Decimal('250.00'),
        duration=90,
        capacity=8,
        date=next_week,
        start_time=time(18, 0),
        location='Studio B'
    )


# ============= TIMESLOT FIXTURES =============

@pytest.fixture
def available_timeslot(db, lesson_tomorrow):
    """Fixture pro dostupný časový slot zítra."""
    future_time = timezone.now() + timedelta(days=1)
    
    return TimeSlot.objects.create(
        lesson=lesson_tomorrow,
        start_time=future_time,
        is_available=True
    )


@pytest.fixture
def occupied_timeslot(db, lesson_tomorrow):
    """Fixture pro obsazený časový slot."""
    future_time = timezone.now() + timedelta(days=1, hours=2)
    
    return TimeSlot.objects.create(
        lesson=lesson_tomorrow,
        start_time=future_time,
        is_available=False
    )


@pytest.fixture
def timeslot_in_3_hours(db, lesson_tomorrow):
    """Fixture pro slot za 3 hodiny (pro testování zrušení)."""
    future_time = timezone.now() + timedelta(hours=3)
    
    return TimeSlot.objects.create(
        lesson=lesson_tomorrow,
        start_time=future_time,
        is_available=True
    )


@pytest.fixture
def timeslot_in_1_hour(db, lesson_tomorrow):
    """Fixture pro slot za 1 hodinu (zrušení by mělo selhat)."""
    future_time = timezone.now() + timedelta(hours=1)
    
    return TimeSlot.objects.create(
        lesson=lesson_tomorrow,
        start_time=future_time,
        is_available=True
    )


# ============= BOOKING FIXTURES =============

@pytest.fixture
def confirmed_booking(db, client_user, available_timeslot):
    """Fixture pro potvrzenou rezervaci."""
    return Booking.objects.create(
        client=client_user,
        time_slot=available_timeslot,
        status='confirmed'
    )


@pytest.fixture
def pending_booking(db, client_user, available_timeslot):
    """Fixture pro čekající rezervaci."""
    return Booking.objects.create(
        client=client_user,
        time_slot=available_timeslot,
        status='pending'
    )


# ============= TOPUP FIXTURES =============

@pytest.fixture
def pending_topup(db, client_user):
    """Fixture pro čekající dobití."""
    return TopUp.objects.create(
        user=client_user,
        amount=Decimal('500.00'),
        status='pending'
    )


@pytest.fixture
def confirmed_topup(db, client_user):
    """Fixture pro potvrzené dobití."""
    topup = TopUp.objects.create(
        user=client_user,
        amount=Decimal('1000.00'),
        status='confirmed'
    )
    topup.credited_at = timezone.now()
    topup.save()
    return topup


# ============= PAYMENT FIXTURES =============

@pytest.fixture
def pending_payment(db, client_user, instructor_user):
    """Fixture pro čekající platbu."""
    return Payment.objects.create(
        client=client_user,
        instructor=instructor_user,
        amount=Decimal('200.00'),
        status='pending'
    )


@pytest.fixture
def completed_payment(db, client_user, instructor_user):
    """Fixture pro dokončenou platbu."""
    return Payment.objects.create(
        client=client_user,
        instructor=instructor_user,
        amount=Decimal('200.00'),
        status='completed'
    )


# ============= UTILITY FIXTURES =============

@pytest.fixture
def multiple_lessons(db, instructor_user, yoga_category):
    """Fixture pro více lekcí (pro testování seznamů)."""
    lessons = []
    
    for i in range(5):
        future_date = timezone.now().date() + timedelta(days=i+1)
        lesson = Lesson.objects.create(
            instructor=instructor_user,
            title=f'Lekce {i+1}',
            description=f'Testovací lekce číslo {i+1}',
            category=yoga_category,
            price=Decimal('200.00'),
            duration=60,
            capacity=10,
            date=future_date,
            start_time=time(9, 0),
            location='Studio A'
        )
        lessons.append(lesson)
    
    return lessons


@pytest.fixture
def authenticated_client(client, client_user):
    """Fixture pro přihlášeného klienta v Django test clientu."""
    from django.test import Client
    test_client = Client()
    test_client.force_login(client_user)
    return test_client


@pytest.fixture
def authenticated_instructor(client, instructor_user):
    """Fixture pro přihlášeného lektora v Django test clientu."""
    from django.test import Client
    test_client = Client()
    test_client.force_login(instructor_user)
    return test_client

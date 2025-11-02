from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal

from django.utils import timezone

class Lesson(models.Model):
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='instructor_lessons',
        limit_choices_to={'user_type': 'instructor'}
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration = models.IntegerField(help_text="Délka lekce v minutách")
    capacity = models.IntegerField(help_text="Maximální počet účastníků")
    date = models.DateField(help_text="Datum konání lekce", default=timezone.now)
    start_time = models.TimeField(help_text="Čas začátku lekce", default="09:00")
    location = models.CharField(max_length=200, help_text="Místo konání lekce", default="Fitness centrum")
    # Kategorie / typ lekce (ouška)
    LESSON_CATEGORIES = (
        ('yoga', 'Jóga'),
        ('cardio', 'Cardio'),
        ('strength', 'Silový trénink'),
        ('pilates', 'Pilates'),
        ('stretch', 'Stretch/rozcvička'),
        ('other', 'Jiné'),
    )
    category = models.CharField(max_length=20, choices=LESSON_CATEGORIES, default='other')
    
    def __str__(self):
        return f"{self.title} - {self.instructor.get_full_name()} ({self.get_category_display()})"

class TimeSlot(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    is_available = models.BooleanField(default=True)
    
    def clean(self):
        if self.start_time < timezone.now():
            raise ValidationError("Nelze vytvořit termín v minulosti")
    
    def __str__(self):
        return f"{self.lesson.title} - {self.start_time.strftime('%d.%m.%Y %H:%M')}"
    
    class Meta:
        ordering = ['start_time']

class Booking(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Čeká na potvrzení'),
        ('confirmed', 'Potvrzeno'),
        ('cancelled', 'Zrušeno'),
    )
    
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='client_bookings',
        limit_choices_to={'user_type': 'client'}
    )
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def clean(self):
        if not self.time_slot.is_available:
            raise ValidationError("Tento termín již není dostupný")
        
        if self.client.credits < self.time_slot.lesson.price:
            raise ValidationError("Nedostatek kreditů pro rezervaci")
    
    def save(self, *args, **kwargs):
        if self.status == 'confirmed' and not hasattr(self, '_booking_processed'):
            # ensure arithmetic uses Decimal to avoid float/Decimal type errors
            try:
                client_credits = Decimal(str(self.client.credits))
            except Exception:
                client_credits = Decimal(0)
            try:
                price = Decimal(str(self.time_slot.lesson.price))
            except Exception:
                price = Decimal(0)
            self.client.credits = client_credits - price
            self.client.save()
            self.time_slot.is_available = False
            self.time_slot.save()
            self._booking_processed = True
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.client.get_full_name()} - {self.time_slot}"
    
    class Meta:
        ordering = ['-created_at']

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.text import slugify
from decimal import Decimal
from datetime import timedelta


class Category(models.Model):
    """
    Kategorie lekcí (Jóga, Pilates, Cardio, ...) – spravovatelné přes admin.
    """
    name = models.CharField(max_length=100, unique=True, verbose_name='Název kategorie')
    slug = models.SlugField(max_length=100, unique=True, blank=True, verbose_name='Slug (URL)')
    description = models.TextField(blank=True, verbose_name='Popis')
    order = models.IntegerField(default=0, verbose_name='Pořadí', help_text='Nižší číslo = dříve v seznamu')

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Kategorie'
        verbose_name_plural = 'Kategorie'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

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
    
    # Kategorie / typ lekce – nyní FK na Category model
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lessons',
        verbose_name='Kategorie'
    )
    
    def __str__(self):
        category_name = self.category.name if self.category else 'Bez kategorie'
        return f"{self.title} - {self.instructor.get_full_name()} ({category_name})"
    
    @property
    def category_slug(self):
        """Helper property pro JS – vrací slug kategorie nebo 'other'."""
        return self.category.slug if self.category else 'other'

class TimeSlot(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    start_time = models.DateTimeField(db_index=True)  # Index pro rychlejší vyhledávání
    is_available = models.BooleanField(default=True)
    
    def clean(self):
        if self.start_time and self.start_time < timezone.now():
            raise ValidationError("Nelze vytvořit termín v minulosti")
    
    def __str__(self):
        return f"{self.lesson.title} - {self.start_time.strftime('%d.%m.%Y %H:%M')}"
    
    class Meta:
        ordering = ['start_time']
        indexes = [
            models.Index(fields=['start_time', 'is_available']),
        ]

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
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def clean(self):
        if not self.time_slot.is_available:
            raise ValidationError("Tento termín již není dostupný")
        
        if self.client.credits < self.time_slot.lesson.price:
            raise ValidationError("Nedostatek kreditů pro rezervaci")
    
    def save(self, *args, **kwargs):
        """
        Automaticky odečte kredity a uzamkne slot při potvrzení rezervace.
        """
        if self.status == 'confirmed' and not hasattr(self, '_booking_processed'):
            # Credits je již DecimalField, není potřeba konverze
            self.client.credits -= self.time_slot.lesson.price
            self.client.save()
            
            self.time_slot.is_available = False
            self.time_slot.save()
            
            self._booking_processed = True
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.client.get_full_name()} - {self.time_slot}"
    
    def can_cancel(self):
        """Kontrola, zda lze rezervaci zrušit (minimálně 2 hodiny před začátkem)"""
        if self.status == 'cancelled':
            return False
        now = timezone.now()
        time_before_lesson = self.time_slot.start_time - now
        return time_before_lesson >= timedelta(hours=2)
    
    def cancellation_deadline(self):
        """Vrací čas, do kdy je možné rezervaci zrušit (2 hodiny před začátkem lekce)"""
        return self.time_slot.start_time - timedelta(hours=2)
    
    def cancel(self):
        """Zruší rezervaci a vrátí kredit klientovi"""
        if not self.can_cancel():
            raise ValidationError("Rezervaci nelze zrušit méně než 2 hodiny před začátkem lekce")
        
        # Vrátit kredit klientovi (DecimalField, žádná konverze není potřeba)
        self.client.credits += self.time_slot.lesson.price
        self.client.save()
        
        # Uvolnit termín
        self.time_slot.is_available = True
        self.time_slot.save()
        
        # Změnit stav rezervace
        self.status = 'cancelled'
        self.save()
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
        ]

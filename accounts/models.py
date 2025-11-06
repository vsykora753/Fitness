from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.utils import timezone

class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('instructor', 'Lektor'),
        ('client', 'Klient'),
    )
    
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    email = models.EmailField(unique=True, blank=False)  # Email jako jedinečný identifikátor
    credits = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0)]
    )
    phone = models.CharField(max_length=20, blank=True)
    bio = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_user_type_display()})"

    def add_credits(self, amount):
        self.credits += amount
        self.save()

    @property
    def is_instructor(self) -> bool:
        return self.user_type == 'instructor'

    @property
    def is_client(self) -> bool:
        return self.user_type == 'client'


class AboutPage(models.Model):
    """
    Jednoduchá editovatelná stránka "O mě". Očekává se jedna instance.
    Spravovatelná přes admin rozhraní nebo vlastní edit formulář.
    """
    title = models.CharField(max_length=200, default='O mně')
    content = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Stránka O mně'
        verbose_name_plural = 'Stránky O mně'

    def __str__(self) -> str:
        return self.title or 'O mně'

    @classmethod
    def get_solo(cls):
        """Vrátí existující instanci nebo novou nevytvořenou (neuloženou) s defaulty."""
        obj = cls.objects.first()
        if obj:
            return obj
        return cls(title='O mně', content='')

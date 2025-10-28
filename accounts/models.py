from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator

class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('instructor', 'Lektor'),
        ('client', 'Klient'),
    )
    
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
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

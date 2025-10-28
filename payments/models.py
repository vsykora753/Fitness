from django.db import models
from django.conf import settings
import qrcode
from io import BytesIO
from django.core.files import File
from PIL import Image

class Payment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Čeká na potvrzení'),
        ('confirmed', 'Potvrzeno'),
        ('cancelled', 'Zrušeno'),
    )
    
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payments_made',
        limit_choices_to={'user_type': 'client'}
    )
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payments_received',
        limit_choices_to={'user_type': 'instructor'}
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True)
    
    def generate_qr_code(self):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        
        # Zde můžete přidat vlastní formát dat pro QR kód (např. bankovní údaje)
        qr_data = f"amount:{self.amount}|client:{self.client.username}|instructor:{self.instructor.username}"
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        
        self.qr_code.save(
            f'qr_payment_{self.id}.png',
            File(buffer),
            save=False
        )
    
    def save(self, *args, **kwargs):
        if not self.qr_code:
            self.generate_qr_code()
        if self.status == 'confirmed' and not hasattr(self, '_payment_processed'):
            self.client.add_credits(self.amount)
            self._payment_processed = True
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Platba {self.amount} Kč - {self.client.get_full_name()} -> {self.instructor.get_full_name()}"
    
    class Meta:
        ordering = ['-created_at']

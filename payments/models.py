from django.db import models
from django.conf import settings
from django.core.files import File
from io import BytesIO
from decimal import Decimal, ROUND_HALF_UP
import qrcode.main
import qrcode.constants
from PIL import Image
from django.utils import timezone

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
        qr = qrcode.main.QRCode(
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


class TopUp(models.Model):
    """
    Dobití kreditu uživatele bankovním převodem pomocí QR Platby.
    QR kód nese formát "SPD*1.0*ACC:<IBAN>*AM:<amount>*CC:CZK*X-VS:<varSymbol>*MSG:<message>"
    
    Poznámky:
    - Variabilní symbol je ID uživatele (lze upravit na jiné zákaznické číslo, pokud bude později přidáno).
    - Zpráva obsahuje celé jméno uživatele; je zkrácena na bezpečnou délku.
    - Cílové IBAN číslo účtu se bere ze settings.PAYMENT_BANK_IBAN.
    """

    STATUS_CHOICES = (
        ('pending', 'Čeká na platbu'),
        ('confirmed', 'Připsáno'),
        ('cancelled', 'Zrušeno'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='topups'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    variable_symbol = models.CharField(max_length=20, help_text='Variabilní symbol, typicky ID klienta.')
    message = models.CharField(max_length=70, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True)
    credited_at = models.DateTimeField(null=True, blank=True, help_text='Kdy byly připsány kredity (po potvrzení).')

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"Dobití {self.amount} Kč - {self.user.get_full_name()}"

    class Meta:
        ordering = ['-created_at']

    @staticmethod
    def _format_amount(amount: Decimal) -> str:
        # QR Platba očekává tečku jako desetinný oddělovač, 2 desetinná místa
        quantized = Decimal(amount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return f"{quantized:.2f}"

    def _qrplatba_payload(self) -> str:
        iban = getattr(settings, 'PAYMENT_BANK_IBAN', None)
        if not iban:
            # Bez IBANu nelze QR Platbu vytvořit; ponecháme alespoň libovolný qr obsah
            iban = 'CZ0000000000000000000000'
        amount_str = self._format_amount(self.amount)
        vs = str(self.variable_symbol)[:10]
        # Zkrátit zprávu na rozumnou délku
        msg = (self.message or '').strip()[:60]
        parts = [
            'SPD*1.0',
            f'ACC:{iban}',
            f'AM:{amount_str}',
            'CC:CZK',
        ]
        if vs:
            parts.append(f'X-VS:{vs}')
        if msg:
            parts.append(f'MSG:{msg}')
        return '*'.join(parts)

    def generate_qr_code(self):
        data = self._qrplatba_payload()
        qr = qrcode.main.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buffer = BytesIO()
        img.save(buffer, format='PNG')
        filename = f'topup_{self.pk}.png' if self.pk else 'topup.png'
        self.qr_code.save(filename, File(buffer), save=False)

    def save(self, *args, **kwargs):
        # Při prvním uložení nejdřív ulož, aby vzniklo PK, potom vygeneruj QR a ulož znovu
        creating = self.pk is None
        if creating:
            # Naplnit VS a zprávu při vytváření, pokud nejsou
            if not self.variable_symbol:
                self.variable_symbol = str(self.user_id or '')
            if not self.message:
                full_name = self.user.get_full_name() or self.user.username
                self.message = full_name
        # Nejprve ulož běžná data
        super().save(*args, **kwargs)
        # QR vygeneruj, pokud chybí
        if not self.qr_code:
            self.generate_qr_code()
            super().save(update_fields=['qr_code'])
        # Připsání kreditu pouze při přechodu do confirmed a pokud ještě nebylo připsáno
        if self.status == 'confirmed' and self.credited_at is None:
            self.user.add_credits(self.amount)
            self.credited_at = timezone.now()
            super().save(update_fields=['credited_at'])

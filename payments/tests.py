"""
Testy pro aplikaci payments - dobíjení kreditů, platby.
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta

from .models import TopUp, Payment

User = get_user_model()


class TopUpModelTests(TestCase):
    """Testy pro model TopUp (dobíjení kreditů)."""

    def setUp(self):
        """Příprava testovacích dat."""
        self.client_user = User.objects.create_user(
            username='klient@test.cz',
            email='klient@test.cz',
            password='testpass123',
            user_type='client',
            credits=Decimal('100.00')
        )
        
        self.instructor = User.objects.create_user(
            username='lektor@test.cz',
            email='lektor@test.cz',
            password='testpass123',
            user_type='instructor'
        )

    def test_topup_creation(self):
        """Test vytvoření žádosti o dobití."""
        topup = TopUp.objects.create(
            user=self.client_user,
            amount=Decimal('500.00'),
            status='pending'
        )
        
        self.assertEqual(topup.user, self.client_user)
        self.assertEqual(topup.amount, Decimal('500.00'))
        self.assertEqual(topup.status, 'pending')
        self.assertIsNotNone(topup.variable_symbol)  # VS by měl být vygenerován

    def test_topup_confirmation_adds_credits(self):
        """Test, že schválení dobití přidá kredity."""
        initial_credits = self.client_user.credits
        
        topup = TopUp.objects.create(
            user=self.client_user,
            amount=Decimal('500.00'),
            status='pending'
        )
        
        # Schválíme dobití změnou statusu
        topup.status = 'confirmed'
        topup.save()
        
        # Ověření, že kredity byly připsány
        self.client_user.refresh_from_db()
        self.assertEqual(
            self.client_user.credits,
            initial_credits + Decimal('500.00')
        )
        
        # Ověření, že credited_at bylo nastaveno
        self.assertIsNotNone(topup.credited_at)

    def test_topup_cancellation_does_not_add_credits(self):
        """Test, že zrušení dobití nepřidá kredity."""
        initial_credits = self.client_user.credits
        
        topup = TopUp.objects.create(
            user=self.client_user,
            amount=Decimal('500.00'),
            status='pending'
        )
        
        # Zrušíme dobití
        topup.status = 'cancelled'
        topup.save()
        
        # Ověření, že kredity nebyly změněny
        self.client_user.refresh_from_db()
        self.assertEqual(self.client_user.credits, initial_credits)

    def test_topup_string_representation(self):
        """Test __str__ metody TopUp."""
        topup = TopUp.objects.create(
            user=self.client_user,
            amount=Decimal('500.00'),
            status='pending'
        )
        
        self.assertIn('500.00', str(topup))
        self.assertIn('klient@test.cz', str(topup))


class PaymentModelTests(TestCase):
    """Testy pro model Payment (platby lektorovi)."""

    def setUp(self):
        """Příprava testovacích dat."""
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

    def test_payment_creation(self):
        """Test vytvoření platby."""
        payment = Payment.objects.create(
            client=self.client_user,
            instructor=self.instructor,
            amount=Decimal('200.00'),
            status='pending'
        )
        
        self.assertEqual(payment.client, self.client_user)
        self.assertEqual(payment.instructor, self.instructor)
        self.assertEqual(payment.amount, Decimal('200.00'))
        self.assertEqual(payment.status, 'pending')

    def test_payment_confirmation(self):
        """Test potvrzení platby."""
        payment = Payment.objects.create(
            client=self.client_user,
            instructor=self.instructor,
            amount=Decimal('200.00'),
            status='pending'
        )
        
        # Potvrdíme platbu
        payment.status = 'completed'
        payment.save()
        
        self.assertEqual(payment.status, 'completed')


class TopUpViewTests(TestCase):
    """Testy pro views související s dobíjením kreditů."""

    def setUp(self):
        """Příprava testovacích dat."""
        self.client = Client()
        
        self.client_user = User.objects.create_user(
            username='klient@test.cz',
            email='klient@test.cz',
            password='testpass123',
            user_type='client',
            credits=Decimal('100.00')
        )
        
        self.instructor = User.objects.create_user(
            username='lektor@test.cz',
            email='lektor@test.cz',
            password='testpass123',
            user_type='instructor'
        )

    def test_topup_create_page_loads_for_authenticated_user(self):
        """Test, že stránka pro dobití se načte pro přihlášeného uživatele."""
        self.client.login(username='klient@test.cz', password='testpass123')
        
        response = self.client.get(reverse('topup_create'))
        self.assertEqual(response.status_code, 200)

    def test_topup_create_redirects_for_anonymous(self):
        """Test, že nepřihlášený uživatel je přesměrován."""
        response = self.client.get(reverse('topup_create'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_client_can_create_topup_request(self):
        """Test, že klient může vytvořit žádost o dobití."""
        self.client.login(username='klient@test.cz', password='testpass123')
        
        data = {
            'amount': '500.00'
        }
        
        response = self.client.post(reverse('topup_create'), data)
        
        # Ověření přesměrování
        self.assertEqual(response.status_code, 302)
        
        # Ověření, že TopUp byl vytvořen
        self.assertTrue(
            TopUp.objects.filter(
                user=self.client_user,
                amount=Decimal('500.00')
            ).exists()
        )

    def test_topup_history_shows_user_topups(self):
        """Test, že historie dobití zobrazuje jen dobití daného uživatele."""
        # Vytvoříme TopUp pro testovacího klienta
        TopUp.objects.create(
            user=self.client_user,
            amount=Decimal('500.00'),
            status='confirmed'
        )
        
        # Vytvoříme jiného klienta s jiným TopUp
        other_client = User.objects.create_user(
            username='jiny@test.cz',
            email='jiny@test.cz',
            password='testpass123',
            user_type='client'
        )
        TopUp.objects.create(
            user=other_client,
            amount=Decimal('1000.00'),
            status='pending'
        )
        
        # Přihlásíme se jako původní klient
        self.client.login(username='klient@test.cz', password='testpass123')
        
        response = self.client.get(reverse('topup_history'))
        
        # Měli bychom vidět jen jeden TopUp (náš)
        self.assertEqual(len(response.context['topups']), 1)
        self.assertEqual(
            response.context['topups'][0].user,
            self.client_user
        )


class TopUpApprovalTests(TestCase):
    """Testy pro schvalování dobití lektorem."""

    def setUp(self):
        """Příprava testovacích dat."""
        self.client = Client()
        
        self.client_user = User.objects.create_user(
            username='klient@test.cz',
            email='klient@test.cz',
            password='testpass123',
            user_type='client',
            credits=Decimal('100.00')
        )
        
        self.instructor = User.objects.create_user(
            username='lektor@test.cz',
            email='lektor@test.cz',
            password='testpass123',
            user_type='instructor'
        )
        
        # Vytvoříme čekající TopUp
        self.pending_topup = TopUp.objects.create(
            user=self.client_user,
            amount=Decimal('500.00'),
            status='pending'
        )

    def test_instructor_can_access_approval_list(self):
        """Test, že lektor má přístup k seznamu čekajících dobití."""
        self.client.login(username='lektor@test.cz', password='testpass123')
        
        response = self.client.get(reverse('topup_approve_list'))
        self.assertEqual(response.status_code, 200)

    def test_client_cannot_access_approval_list(self):
        """Test, že klient NEMÁ přístup k seznamu čekajících dobití."""
        self.client.login(username='klient@test.cz', password='testpass123')
        
        response = self.client.get(reverse('topup_approve_list'))
        # Očekáváme 403 nebo redirect
        self.assertIn(response.status_code, [302, 403])

    def test_instructor_can_approve_topup(self):
        """Test, že lektor může schválit dobití."""
        self.client.login(username='lektor@test.cz', password='testpass123')
        
        initial_credits = self.client_user.credits
        
        # Schválíme TopUp
        url = reverse('topup_approve', kwargs={'pk': self.pending_topup.pk})
        data = {
            'status': 'confirmed'
        }
        response = self.client.post(url, data)
        
        # Ověření přesměrování
        self.assertEqual(response.status_code, 302)
        
        # Ověření, že status byl změněn
        self.pending_topup.refresh_from_db()
        self.assertEqual(self.pending_topup.status, 'confirmed')
        
        # Ověření, že kredity byly připsány
        self.client_user.refresh_from_db()
        self.assertEqual(
            self.client_user.credits,
            initial_credits + Decimal('500.00')
        )

    def test_instructor_can_cancel_topup(self):
        """Test, že lektor může zrušit dobití."""
        self.client.login(username='lektor@test.cz', password='testpass123')
        
        initial_credits = self.client_user.credits
        
        # Zrušíme TopUp
        url = reverse('topup_approve', kwargs={'pk': self.pending_topup.pk})
        data = {
            'status': 'cancelled'
        }
        response = self.client.post(url, data)
        
        # Ověření přesměrování
        self.assertEqual(response.status_code, 302)
        
        # Ověření, že status byl změněn
        self.pending_topup.refresh_from_db()
        self.assertEqual(self.pending_topup.status, 'cancelled')
        
        # Ověření, že kredity NEBYLY připsány
        self.client_user.refresh_from_db()
        self.assertEqual(self.client_user.credits, initial_credits)


class IntegrationPaymentFlowTests(TestCase):
    """Integrační testy celého platebního workflow."""

    def setUp(self):
        """Příprava testovacích dat."""
        self.client = Client()
        
        self.client_user = User.objects.create_user(
            username='klient@test.cz',
            email='klient@test.cz',
            password='testpass123',
            user_type='client',
            credits=Decimal('0.00')
        )
        
        self.instructor = User.objects.create_user(
            username='lektor@test.cz',
            email='lektor@test.cz',
            password='testpass123',
            user_type='instructor'
        )

    def test_complete_topup_workflow(self):
        """Test kompletního workflow dobití: vytvoření → schválení → připsání kreditu."""
        # 1. Klient vytvoří žádost o dobití
        self.client.login(username='klient@test.cz', password='testpass123')
        
        response = self.client.post(reverse('topup_create'), {'amount': '1000.00'})
        self.assertEqual(response.status_code, 302)
        
        # Ověření, že TopUp existuje se statusem pending
        topup = TopUp.objects.get(user=self.client_user)
        self.assertEqual(topup.status, 'pending')
        self.assertEqual(self.client_user.credits, Decimal('0.00'))  # Kredit ještě nepřipsán
        
        # 2. Odhlásíme klienta
        self.client.logout()
        
        # 3. Lektor se přihlásí a schválí dobití
        self.client.login(username='lektor@test.cz', password='testpass123')
        
        url = reverse('topup_approve', kwargs={'pk': topup.pk})
        response = self.client.post(url, {'status': 'confirmed'})
        self.assertEqual(response.status_code, 302)
        
        # 4. Ověření finálního stavu
        topup.refresh_from_db()
        self.assertEqual(topup.status, 'confirmed')
        
        self.client_user.refresh_from_db()
        self.assertEqual(self.client_user.credits, Decimal('1000.00'))  # Kredit připsán
        
        self.assertIsNotNone(topup.credited_at)  # Čas připsání nastaven

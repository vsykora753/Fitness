"""
Testy pro aplikaci accounts - uživatelské účty, registrace, autentizace.
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from decimal import Decimal

User = get_user_model()


class UserModelTests(TestCase):
    """Testy pro custom User model."""

    def setUp(self):
        """Příprava testovacích dat."""
        self.client_user = User.objects.create_user(
            username='klient@test.cz',
            email='klient@test.cz',
            password='testpass123',
            first_name='Jan',
            last_name='Novák',
            user_type='client',
            credits=Decimal('500.00')
        )
        
        self.instructor_user = User.objects.create_user(
            username='lektor@test.cz',
            email='lektor@test.cz',
            password='testpass123',
            first_name='Marie',
            last_name='Svobodová',
            user_type='instructor',
            credits=Decimal('0.00')
        )

    def test_user_creation(self):
        """Test vytvoření uživatele s požadovanými atributy."""
        self.assertEqual(self.client_user.email, 'klient@test.cz')
        self.assertEqual(self.client_user.user_type, 'client')
        self.assertEqual(self.client_user.credits, Decimal('500.00'))

    def test_user_string_representation(self):
        """Test __str__ metody uživatele."""
        expected = "Jan Novák (Klient)"
        self.assertEqual(str(self.client_user), expected)

    def test_is_instructor_property(self):
        """Test property is_instructor."""
        self.assertFalse(self.client_user.is_instructor)
        self.assertTrue(self.instructor_user.is_instructor)

    def test_is_client_property(self):
        """Test property is_client."""
        self.assertTrue(self.client_user.is_client)
        self.assertFalse(self.instructor_user.is_client)

    def test_add_credits_method(self):
        """Test metody add_credits()."""
        initial_credits = self.client_user.credits
        self.client_user.add_credits(Decimal('200.00'))
        
        self.client_user.refresh_from_db()
        self.assertEqual(self.client_user.credits, initial_credits + Decimal('200.00'))

    def test_email_uniqueness(self):
        """Test, že email musí být jedinečný."""
        with self.assertRaises(Exception):
            User.objects.create_user(
                username='duplicate@test.cz',
                email='klient@test.cz',  # duplicitní email
                password='testpass123'
            )


class UserRegistrationTests(TestCase):
    """Testy registrace nových uživatelů."""

    def setUp(self):
        self.client = Client()
        self.register_url = reverse('accounts:register')

    def test_registration_page_loads(self):
        """Test, že registrační stránka se načte."""
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/register.html')

    def test_successful_registration(self):
        """Test úspěšné registrace nového klienta."""
        data = {
            'email': 'novyuzivatel@test.cz',
            'first_name': 'Nový',
            'last_name': 'Uživatel',
            'phone': '123456789',
            'password1': 'silneheslo123',
            'password2': 'silneheslo123',
        }
        
        response = self.client.post(self.register_url, data)
        
        # Ověření přesměrování po úspěšné registraci
        self.assertEqual(response.status_code, 302)
        
        # Ověření, že uživatel byl vytvořen
        self.assertTrue(User.objects.filter(email='novyuzivatel@test.cz').exists())
        
        # Ověření, že má správný user_type
        user = User.objects.get(email='novyuzivatel@test.cz')
        self.assertEqual(user.user_type, 'client')
        self.assertEqual(user.username, 'novyuzivatel@test.cz')  # username = email

    def test_registration_with_duplicate_email(self):
        """Test registrace s již existujícím emailem."""
        # Vytvoříme existujícího uživatele
        User.objects.create_user(
            username='existing@test.cz',
            email='existing@test.cz',
            password='testpass123'
        )
        
        # Pokus o registraci s duplicitním emailem
        data = {
            'email': 'existing@test.cz',
            'first_name': 'Test',
            'last_name': 'User',
            'password1': 'testpass123',
            'password2': 'testpass123',
        }
        
        response = self.client.post(self.register_url, data)
        
        # Formulář by měl obsahovat chybu
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'email', 'Tento e-mail je již registrován.')

    def test_registration_with_weak_password(self):
        """Test registrace se slabým heslem."""
        data = {
            'email': 'test@test.cz',
            'first_name': 'Test',
            'last_name': 'User',
            'password1': '123',  # příliš krátké
            'password2': '123',
        }
        
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'password2', None)  # Django má vlastní validaci hesel

    def test_registration_with_mismatched_passwords(self):
        """Test registrace s neshodujícími se hesly."""
        data = {
            'email': 'test@test.cz',
            'first_name': 'Test',
            'last_name': 'User',
            'password1': 'silneheslo123',
            'password2': 'jineheslo456',
        }
        
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'password2', None)


class UserLoginTests(TestCase):
    """Testy přihlašování uživatelů."""

    def setUp(self):
        self.client = Client()
        self.login_url = reverse('accounts:login')
        
        # Vytvoříme testovací uživatele
        self.user = User.objects.create_user(
            username='testuser@test.cz',
            email='testuser@test.cz',
            password='testpass123',
            user_type='client'
        )

    def test_login_page_loads(self):
        """Test, že přihlašovací stránka se načte."""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/login.html')

    def test_successful_login(self):
        """Test úspěšného přihlášení."""
        data = {
            'username': 'testuser@test.cz',  # Django backend používá username (i když je to email)
            'password': 'testpass123',
        }
        
        response = self.client.post(self.login_url, data)
        
        # Ověření přesměrování
        self.assertEqual(response.status_code, 302)
        
        # Ověření, že uživatel je přihlášen
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_login_with_wrong_password(self):
        """Test přihlášení se špatným heslem."""
        data = {
            'username': 'testuser@test.cz',
            'password': 'špatnéheslo',
        }
        
        response = self.client.post(self.login_url, data)
        
        # Měla by se vrátit stejná stránka s chybou
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_login_with_nonexistent_user(self):
        """Test přihlášení s neexistujícím uživatelem."""
        data = {
            'username': 'neexistuje@test.cz',
            'password': 'jakékolivheslo',
        }
        
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_logout(self):
        """Test odhlášení."""
        # Nejprve se přihlásíme
        self.client.login(username='testuser@test.cz', password='testpass123')
        
        # Pak se odhlásíme
        logout_url = reverse('accounts:logout')
        response = self.client.post(logout_url)
        
        # Ověříme přesměrování a odhlášení
        self.assertEqual(response.status_code, 302)


class UserPermissionsTests(TestCase):
    """Testy oprávnění podle role (klient vs. lektor)."""

    def setUp(self):
        self.client = Client()
        
        self.client_user = User.objects.create_user(
            username='klient@test.cz',
            email='klient@test.cz',
            password='testpass123',
            user_type='client'
        )
        
        self.instructor_user = User.objects.create_user(
            username='lektor@test.cz',
            email='lektor@test.cz',
            password='testpass123',
            user_type='instructor'
        )

    def test_client_can_access_client_dashboard(self):
        """Test, že klient má přístup k client dashboardu."""
        self.client.login(username='klient@test.cz', password='testpass123')
        
        response = self.client.get(reverse('accounts:client_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_instructor_cannot_access_client_dashboard(self):
        """Test, že lektor NEMÁ přístup k client dashboardu."""
        self.client.login(username='lektor@test.cz', password='testpass123')
        
        response = self.client.get(reverse('accounts:client_dashboard'))
        # Očekáváme 403 (Forbidden) nebo redirect
        self.assertIn(response.status_code, [302, 403])

    def test_instructor_can_access_instructor_dashboard(self):
        """Test, že lektor má přístup k instructor dashboardu."""
        self.client.login(username='lektor@test.cz', password='testpass123')
        
        response = self.client.get(reverse('accounts:instructor_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_client_cannot_access_instructor_dashboard(self):
        """Test, že klient NEMÁ přístup k instructor dashboardu."""
        self.client.login(username='klient@test.cz', password='testpass123')
        
        response = self.client.get(reverse('accounts:instructor_dashboard'))
        self.assertIn(response.status_code, [302, 403])

    def test_unauthenticated_user_redirected_to_login(self):
        """Test, že nepřihlášený uživatel je přesměrován na login."""
        response = self.client.get(reverse('accounts:client_dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)


class UserProfileTests(TestCase):
    """Testy profilové stránky."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser@test.cz',
            email='testuser@test.cz',
            password='testpass123',
            first_name='Test',
            last_name='User',
            phone='123456789',
            bio='Testovací bio',
            user_type='client'
        )

    def test_profile_page_loads_for_authenticated_user(self):
        """Test, že profilová stránka se načte pro přihlášeného uživatele."""
        self.client.login(username='testuser@test.cz', password='testpass123')
        
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test User')

    def test_profile_page_redirects_for_anonymous(self):
        """Test, že nepřihlášený uživatel je přesměrován."""
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 302)

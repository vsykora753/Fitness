# 🧪 Testování - Fitness rezervační systém

**Kompletní průvodce automatizovaným testováním aplikace**

---

## 📖 Obsah

1. [Rychlý start](#rychlý-start)
2. [Struktura testů](#struktura-testů)
3. [Spuštění testů](#spuštění-testů)
4. [Pokrytí kódu](#pokrytí-kódu)
5. [Interpretace výsledků](#interpretace-výsledků)
6. [Přidání nových testů](#přidání-nových-testů)
7. [Troubleshooting](#troubleshooting)

---

## 🚀 Rychlý start

### 1. Spusťte všechny testy

```powershell
# Django TestCase (doporučeno)
python manage.py test

# Nebo s větším detailem
python manage.py test --verbosity=2
```

### 2. Spusťte testy konkrétní aplikace

```powershell
# Pouze accounts testy
python manage.py test accounts

# Pouze bookings testy
python manage.py test bookings

# Pouze payments testy
python manage.py test payments
```

### 3. Spusťte konkrétní testovací třídu

```powershell
python manage.py test accounts.tests.UserModelTests
```

### 4. Spusťte jeden konkrétní test

```powershell
python manage.py test accounts.tests.UserModelTests.test_user_creation
```

---

## 📁 Struktura testů

```
Fitness/
├── accounts/
│   └── tests.py          # Testy pro uživatele, registraci, autentizaci
├── bookings/
│   └── tests.py          # Testy pro lekce, rezervace, časové sloty
├── payments/
│   └── tests.py          # Testy pro platby a dobíjení kreditů
├── conftest.py           # Pytest fixtures (sdílená testovací data)
├── TESTING_MANUAL.md     # Manuální testovací checklist
└── TESTING_README.md     # Tento soubor
```

---

## 🏃 Spuštění testů

### Django TestCase (výchozí)

Django má vestavěný testovací framework založený na `unittest`:

```powershell
# Všechny testy
python manage.py test

# S podrobným výstupem
python manage.py test --verbosity=2

# Zachovat testovací databázi pro rychlejší opakované běhy
python manage.py test --keepdb

# Paralelní spuštění (rychlejší)
python manage.py test --parallel

# Failfast - zastaví se po první chybě
python manage.py test --failfast
```

### Pytest (volitelné)

Pokud preferujete pytest, nejprve ho nainstalujte:

```powershell
pip install pytest pytest-django
```

Vytvořte `pytest.ini` v root složce:

```ini
[pytest]
DJANGO_SETTINGS_MODULE = reservations.settings
python_files = tests.py test_*.py *_tests.py
```

Pak spusťte:

```powershell
pytest

# S větším detailem
pytest -v

# Specifický soubor
pytest accounts/tests.py

# Specifický test
pytest accounts/tests.py::UserModelTests::test_user_creation
```

---

## 📊 Pokrytí kódu (Coverage)

### Instalace

```powershell
pip install coverage
```

### Spuštění s měřením pokrytí

```powershell
# Spusťte testy s coverage
coverage run --source='.' manage.py test

# Zobrazte report v terminálu
coverage report

# Vygenerujte HTML report
coverage html

# Otevřete v prohlížeči
start htmlcov/index.html
```

### Interpretace výsledků

```
Name                                     Stmts   Miss  Cover
------------------------------------------------------------
accounts/models.py                          45      2    96%
accounts/views.py                           67      8    88%
bookings/models.py                          89      5    94%
payments/models.py                          54      3    94%
------------------------------------------------------------
TOTAL                                      512     28    95%
```

- **Stmts** = Celkový počet řádků kódu
- **Miss** = Počet netestovaných řádků
- **Cover** = Procento pokrytí (cíl: > 80%)

---

## 📈 Co jednotlivé testy ověřují

### **accounts/tests.py** (8 testovacích tříd, ~25 testů)

#### `UserModelTests`
- ✅ Vytvoření uživatele s kredity
- ✅ String reprezentace (__str__)
- ✅ Properties: is_instructor, is_client
- ✅ Metoda add_credits()
- ✅ Jedinečnost emailu

#### `UserRegistrationTests`
- ✅ Úspěšná registrace nového klienta
- ✅ Automatické nastavení user_type = 'client'
- ✅ Duplicitní email → chyba
- ✅ Slabé heslo → chyba
- ✅ Neshoda hesel → chyba

#### `UserLoginTests`
- ✅ Úspěšné přihlášení
- ✅ Špatné heslo → chyba
- ✅ Neexistující uživatel → chyba
- ✅ Odhlášení

#### `UserPermissionsTests`
- ✅ Klient má přístup k client dashboard
- ✅ Lektor NEMÁ přístup k client dashboard
- ✅ Lektor má přístup k instructor dashboard
- ✅ Klient NEMÁ přístup k instructor dashboard
- ✅ Nepřihlášený uživatel → redirect na login

---

### **bookings/tests.py** (6 testovacích tříd, ~35 testů)

#### `LessonModelTests`
- ✅ Vytvoření lekce s kategorií
- ✅ Validace ceny, kapacity, datumu

#### `TimeSlotModelTests`
- ✅ Vytvoření časového slotu
- ✅ Validace: nelze vytvořit slot v minulosti

#### `BookingModelTests`
- ✅ Úspěšná rezervace (odečtení kreditu, uzamčení slotu)
- ✅ Nedostatek kreditů → chyba
- ✅ Obsazený slot → chyba
- ✅ Včasné zrušení (> 2h) → vrácení kreditu
- ✅ Pozdní zrušení (< 2h) → chyba

#### `LessonViewTests`
- ✅ Lektor může vytvořit lekci
- ✅ Klient NEMŮŽE vytvořit lekci

#### `BookingViewTests`
- ✅ Přihlášený uživatel může rezervovat
- ✅ Nepřihlášený uživatel → redirect na login

---

### **payments/tests.py** (5 testovacích tříd, ~20 testů)

#### `TopUpModelTests`
- ✅ Vytvoření žádosti o dobití
- ✅ Schválení → připsání kreditu
- ✅ Zrušení → kredit se NEPŘIPÍŠE

#### `PaymentModelTests`
- ✅ Vytvoření platby lektorovi

#### `TopUpViewTests`
- ✅ Klient může vytvořit žádost o dobití
- ✅ Historie zobrazuje jen vlastní dobití

#### `TopUpApprovalTests`
- ✅ Lektor má přístup k schvalování
- ✅ Klient NEMÁ přístup
- ✅ Lektor schválí → kredit připsán
- ✅ Lektor zruší → kredit NEpřipsán

#### `IntegrationPaymentFlowTests`
- ✅ Kompletní workflow: vytvoření → schválení → připsání

---

## ✅ Interpretace výsledků

### Úspěšný běh

```
Ran 85 tests in 12.345s

OK
```

✅ Všechny testy prošly!

---

### Selhání testu

```
FAIL: test_registration_with_duplicate_email (accounts.tests.UserRegistrationTests)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "d:\WEB_APLIKACE\Fitness\accounts\tests.py", line 132, in test_registration_with_duplicate_email
    self.assertFormError(response, 'form', 'email', 'Tento e-mail je již registrován.')
AssertionError: ...
----------------------------------------------------------------------
Ran 85 tests in 12.345s

FAILED (failures=1)
```

❌ **Problém:** Test očekával chybovou hlášku, ale formulář ji nevyhodil.

**Jak opravit:**
1. Zkontrolujte validaci v `accounts/forms.py` (metoda `clean_email`)
2. Ověřte, že chybová hláška je přesně "Tento e-mail je již registrován."
3. Spusťte test znovu

---

### Chyba v kódu (Error)

```
ERROR: test_user_creation (accounts.tests.UserModelTests)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "d:\WEB_APLIKACE\Fitness\accounts\tests.py", line 25, in test_user_creation
    self.assertEqual(self.client_user.user_type, 'CLIENT')
AttributeError: 'User' object has no attribute 'CLIENT'
```

❌ **Problém:** Kód se pokouší přistoupit k neexistujícímu atributu.

**Jak opravit:**
1. V modelu jsou hodnoty `'client'` a `'instructor'` (malými písmeny), ne konstanty `CLIENT`
2. Opravte test: `self.assertEqual(self.client_user.user_type, 'client')`

---

## 🆕 Přidání nových testů

### Postup

1. **Otevřete příslušný `tests.py`** (např. `accounts/tests.py`)

2. **Vytvořte novou testovací třídu nebo přidejte metodu:**

```python
class MyNewTests(TestCase):
    """Popis skupiny testů."""

    def setUp(self):
        """Příprava dat pro každý test."""
        self.user = User.objects.create_user(
            username='test@test.cz',
            email='test@test.cz',
            password='testpass123'
        )

    def test_something_new(self):
        """Test nové funkcionality."""
        # Arrange (příprava)
        initial_value = self.user.credits

        # Act (akce)
        self.user.add_credits(Decimal('100.00'))

        # Assert (ověření)
        self.user.refresh_from_db()
        self.assertEqual(self.user.credits, initial_value + Decimal('100.00'))
```

3. **Spusťte test:**

```powershell
python manage.py test accounts.tests.MyNewTests.test_something_new
```

---

### Tipy pro psaní testů

#### ✅ Dobrý test

```python
def test_booking_with_sufficient_credits(self):
    """Test rezervace s dostatečným kreditem."""
    # Arrange
    self.client_user.credits = Decimal('500.00')
    self.client_user.save()

    # Act
    booking = Booking.objects.create(
        client=self.client_user,
        time_slot=self.time_slot,
        status='confirmed'
    )

    # Assert
    self.client_user.refresh_from_db()
    self.assertEqual(self.client_user.credits, Decimal('300.00'))
```

**Proč je dobrý?**
- Jasný název (víte, co testuje)
- Struktura Arrange-Act-Assert
- Testuje jednu věc
- Jasné očekávání

#### ❌ Špatný test

```python
def test_stuff(self):
    user = User.objects.create_user(username='x', email='x@x.cz')
    booking = Booking.objects.create(client=user, ...)
    self.assertTrue(True)  # Co vlastně testujeme?
```

**Proč je špatný?**
- Neinformativní název
- Nejasné, co se testuje
- `assertTrue(True)` nic netestuje

---

## 🐛 Troubleshooting

### Problém: "django.db.utils.OperationalError: no such table"

**Příčina:** Testovací databáze nebyla vytvořena nebo migrována.

**Řešení:**
```powershell
python manage.py migrate
python manage.py test
```

---

### Problém: "ModuleNotFoundError: No module named 'pytest'"

**Příčina:** Pytest není nainstalován.

**Řešení:**
```powershell
pip install pytest pytest-django
```

---

### Problém: Testy běží velmi pomalu

**Řešení 1:** Použijte `--keepdb` (zachová testovací DB mezi běhy)
```powershell
python manage.py test --keepdb
```

**Řešení 2:** Paralelní spuštění
```powershell
python manage.py test --parallel
```

**Řešení 3:** SQLite in-memory (rychlejší)
```python
# V settings.py pro testy
if 'test' in sys.argv:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }
```

---

### Problém: "AssertionError: 302 != 200"

**Příčina:** Stránka přesměrovala místo zobrazení.

**Řešení:** Zkontrolujte, zda je uživatel přihlášen (pokud view vyžaduje login):
```python
self.client.login(username='test@test.cz', password='testpass123')
response = self.client.get(reverse('my_view'))
```

---

## 📚 Další zdroje

- **Django Testing:** https://docs.djangoproject.com/en/5.1/topics/testing/
- **Pytest-Django:** https://pytest-django.readthedocs.io/
- **Coverage.py:** https://coverage.readthedocs.io/
- **Manuální testovací checklist:** `TESTING_MANUAL.md`

---

## 🎯 Checklist před commitováním

Před každým commitem spusťte:

```powershell
# 1. Všechny testy
python manage.py test

# 2. Coverage report
coverage run --source='.' manage.py test
coverage report

# 3. Zkontrolujte, že coverage je > 80%
```

---

**Připraveno! Nyní máte kompletní testovací infrastrukturu.** 🚀

Pro manuální testování viz `TESTING_MANUAL.md`.

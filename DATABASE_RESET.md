# Fitness aplikace - Reset databáze a vytvoření testovacích dat

## Jak kompletně resetovat databázi

### Varianta 1: Smazat DB a vytvořit novou
```powershell
# 1. Zastavte server (Ctrl+C)

# 2. Smažte databázový soubor
Remove-Item databaze.db

# 3. Vytvořte novou databázi s migrací
python manage.py migrate

# 4. Vytvořte superuživatele (admin)
python manage.py createsuperuser

# 5. Naplňte testovacími daty
python manage.py create_test_db
```

### Varianta 2: Jen vymazat data (zachovat strukturu)
```powershell
# Smaže všechna data a vytvoří nová (zachová migrace)
python manage.py create_test_db --clear
```

## Příkazy pro správu testovacích dat

### Vytvoření testovací databáze
```powershell
# Základní použití (přidá data k existujícím)
python manage.py create_test_db

# S vymazáním starých dat
python manage.py create_test_db --clear
```

### Co se vytvoří:
- **7 kategorií**: Jóga, Pilates, Cardio, Silový trénink, Protažení, Taneční, Funkční trénink
- **3 instruktoři**: Anna Nováková, Petr Svoboda, Marie Dvořáková
- **5 klientů**: Jan Novák (500 Kč), Eva Malá (1000 Kč), Tomáš Velký (750 Kč), Kateřina Králová (300 Kč), Lukáš Hora (1500 Kč)
- **Lekce**: Cca 150+ lekcí na následujících 21 dní
- **Časové sloty**: Pro každou lekci
- **Rezervace**: Náhodné rezervace klientů
- **Platby**: 7 plateb klient → instruktor (3 čekající, 3 potvrzené, 1 zrušená)
- **Dobití kreditu**: 3 čekající dobití ke schválení

### Přihlašovací údaje
**Instruktoři:**
- `anna.novak` / `heslo123`
- `petr.svoboda` / `heslo123`
- `marie.dvorak` / `heslo123`

**Klienti:**
- `jan.novak` / `heslo123` (500 Kč kreditu)
- `eva.mala` / `heslo123` (1000 Kč kreditu)
- `tomas.velky` / `heslo123` (750 Kč kreditu)
- `katerina.kral` / `heslo123` (300 Kč kreditu)
- `lukas.hora` / `heslo123` (1500 Kč kreditu)

## Kompletní reset workflow

```powershell
# 1. Smazat databázi
Remove-Item databaze.db

# 2. Aplikovat migrace
python manage.py migrate

# 3. Vytvořit admin účet
python manage.py createsuperuser
# Username: admin
# Email: admin@fitness.cz
# Password: (zadejte své heslo)

# 4. Naplnit testovacími daty
python manage.py create_test_db

# 5. Spustit server
python manage.py runserver
```

## Kontrola vytvořených dat

```powershell
# Spustit Django shell
python manage.py shell

# V shellu:
from bookings.models import *
from accounts.models import User

print(f'Kategorie: {Category.objects.count()}')
print(f'Lekce: {Lesson.objects.count()}')
print(f'Instruktoři: {User.objects.filter(user_type="instructor").count()}')
print(f'Klienti: {User.objects.filter(user_type="client").count()}')
print(f'Rezervace: {Booking.objects.count()}')

from payments.models import Payment, TopUp
print(f'Platby klient→instruktor: {Payment.objects.count()}')
print(f'  - Čekající ke schválení: {Payment.objects.filter(status="pending").count()}')
print(f'Dobití kreditu: {TopUp.objects.count()}')
print(f'  - Čekající ke schválení: {TopUp.objects.filter(status="pending").count()}')
```

## Poznámky

- Testovací data jsou vhodná pro **vývoj a testování**
- Pro **produkční** prostředí vždy vytvářejte data ručně
- Heslo `heslo123` je **jen pro testování** - v produkci použijte silná hesla
- Script automaticky rozděluje lekce do různých dnů podle typu (např. HIIT jen Po, St, Pá)

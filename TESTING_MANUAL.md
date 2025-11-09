# 📋 Manuální testovací checklist - Fitness rezervační systém

**Datum vytvoření:** 9. listopadu 2025  
**Verze:** 1.0

---

## 🎯 Před začátkem testování

### Příprava testovacího prostředí
```bash
# 1. Spusťte vývojový server
python manage.py runserver

# 2. Vytvořte testovací data (volitelné)
python manage.py create_test_db

# 3. Otevřete prohlížeč
# http://127.0.0.1:8000
```

### Testovací účty
Pokud jste spustili `create_test_db`, máte k dispozici:
- **Lektor:** lektor@fitness.cz / heslo123
- **Klient:** klient@fitness.cz / heslo123

---

## 1️⃣ ACCOUNTS - Uživatelské účty

### 1.1 Registrace nového klienta
- [ ] **TC-001:** Otevřete `/accounts/register/`
- [ ] **TC-002:** Vyplňte validní email (např. `novyklient@test.cz`)
- [ ] **TC-003:** Vyplňte jméno, příjmení, telefon
- [ ] **TC-004:** Zadejte heslo (min. 8 znaků)
- [ ] **TC-005:** Klikněte "Registrovat se"
- [ ] **Očekávaný výsledek:** Úspěšná registrace, přesměrování na dashboard
- [ ] **Ověření:** V databázi je nový uživatel s `user_type = 'client'`

**Edge cases:**
- [ ] **TC-006:** Zkuste registrovat stejný email znovu → **Chyba: "Tento e-mail je již registrován"**
- [ ] **TC-007:** Zadejte krátké heslo (< 8 znaků) → **Chyba validace**
- [ ] **TC-008:** Neshoda hesel → **Chyba: "Hesla se neshodují"**

---

### 1.2 Přihlášení a odhlášení
- [ ] **TC-010:** Otevřete `/accounts/login/`
- [ ] **TC-011:** Přihlaste se jako **klient@fitness.cz** / heslo123
- [ ] **TC-012:** Ověřte, že jste na `/accounts/client-dashboard/`
- [ ] **TC-013:** Odhlaste se pomocí tlačítka "Odhlásit se"
- [ ] **TC-014:** Ověřte redirect na homepage

**Negativní testy:**
- [ ] **TC-015:** Nesprávné heslo → **Chyba: "Nesprávný email nebo heslo"**
- [ ] **TC-016:** Neexistující email → **Chyba**

---

### 1.3 Role a oprávnění

#### Klient (client)
- [ ] **TC-020:** Přihlaste se jako klient
- [ ] **TC-021:** Máte přístup k "Moje rezervace"
- [ ] **TC-022:** NEMŮŽETE vytvořit lekci (odkaz není viditelný)
- [ ] **TC-023:** Přímý přístup `/bookings/instructor/create/` → **403 Forbidden**

#### Lektor (instructor)
- [ ] **TC-030:** Přihlaste se jako lektor
- [ ] **TC-031:** Máte přístup k "Můj rozvrh"
- [ ] **TC-032:** MŮŽETE vytvořit novou lekci
- [ ] **TC-033:** Vidíte "Schválit dobití" (TopUp approve list)

---

## 2️⃣ BOOKINGS - Lekce a rezervace

### 2.1 Vytvoření lekce (pouze lektor)
- [ ] **TC-040:** Přihlaste se jako **lektor@fitness.cz**
- [ ] **TC-041:** Klikněte "Můj rozvrh" → "Vytvořit lekci"
- [ ] **TC-042:** Vyplňte formulář:
  - Název: "Ranní jóga"
  - Kategorie: Jóga
  - Cena: 200 Kč
  - Kapacita: 10 osob
  - Datum: **zítřejší datum**
  - Čas: 09:00
  - Místo: "Studio A"
- [ ] **TC-043:** Odešlete formulář
- [ ] **Očekávaný výsledek:** Lekce vytvořena + automaticky jeden TimeSlot

**Validace:**
- [ ] **TC-044:** Zkuste vytvořit lekci se včerejším datem → **Chyba**
- [ ] **TC-045:** Záporná cena → **Chyba**
- [ ] **TC-046:** Kapacita 0 nebo záporná → **Chyba**

---

### 2.2 Přidání časových slotů
- [ ] **TC-050:** V detailu lekce klikněte "Přidat termín"
- [ ] **TC-051:** Zadejte budoucí datum a čas
- [ ] **TC-052:** Odešlete → nový slot se zobrazí v seznamu
- [ ] **TC-053:** Zkuste přidat slot v minulosti → **Chyba: "Nelze vytvořit termín v minulosti"**

---

### 2.3 Rezervace lekce (klient)

#### Úspěšná rezervace
- [ ] **TC-060:** Přihlaste se jako klient s dostatečným kreditem (min. 200 Kč)
- [ ] **TC-061:** Otevřete "Rozvrh lekcí"
- [ ] **TC-062:** Vyberte lekci s dostupným termínem
- [ ] **TC-063:** Klikněte "Rezervovat"
- [ ] **TC-064:** Potvrďte rezervaci
- [ ] **Očekávaný výsledek:**
  - ✅ Kredit odečten (kontrola v dashboardu)
  - ✅ Slot označen jako obsazený (`is_available = False`)
  - ✅ Rezervace ve stavu `confirmed`

#### Neúspěšná rezervace
- [ ] **TC-070:** Pokuste se rezervovat s **nedostatečným kreditem** → **Chyba: "Nemáte dostatek kreditů"**
- [ ] **TC-071:** Dva klienti rezervují stejný slot současně → **Druhý dostane chybu**

---

### 2.4 Zrušení rezervace

#### Včasné zrušení (> 2 hodiny před začátkem)
- [ ] **TC-080:** Přihlaste se jako klient s aktivní rezervací
- [ ] **TC-081:** V "Moje rezervace" klikněte "Zrušit"
- [ ] **TC-082:** Potvrďte zrušení
- [ ] **Očekávaný výsledek:**
  - ✅ Kredit vrácen klientovi
  - ✅ Slot uvolněn (`is_available = True`)
  - ✅ Status změněn na `cancelled`

#### Pozdní zrušení (< 2 hodiny před začátkem)
- [ ] **TC-090:** Vytvořte rezervaci na lekci, která začíná za 1 hodinu
- [ ] **TC-091:** Pokuste se ji zrušit → **Chyba: "Rezervaci nelze zrušit méně než 2 hodiny před začátkem"**

---

## 3️⃣ PAYMENTS - Platby a dobíjení

### 3.1 Dobíjení kreditů (TopUp)

#### Klient vytvoří žádost
- [ ] **TC-100:** Přihlaste se jako klient
- [ ] **TC-101:** Klikněte "Dobít kredit"
- [ ] **TC-102:** Zadejte částku: 500 Kč
- [ ] **TC-103:** Odešlete formulář
- [ ] **Očekávaný výsledek:**
  - ✅ Vytvořena žádost se statusem `pending`
  - ✅ Vygenerován QR kód
  - ✅ Přiřazen variabilní symbol

#### Lektor schválí dobití
- [ ] **TC-110:** Přihlaste se jako **lektor@fitness.cz**
- [ ] **TC-111:** Otevřete "Schválit dobití"
- [ ] **TC-112:** Najděte čekající žádost klienta
- [ ] **TC-113:** Klikněte "Schválit"
- [ ] **Očekávaný výsledek:**
  - ✅ Status změněn na `confirmed`
  - ✅ Kredit připsán na účet klienta
  - ✅ Pole `credited_at` vyplněno

**Ověření:**
- [ ] **TC-114:** Přihlaste se znovu jako klient → kredit se zvýšil

---

### 3.2 Edge cases pro platby
- [ ] **TC-120:** Zkuste dobít **zápornou částku** → **Chyba**
- [ ] **TC-121:** Zkuste dobít **0 Kč** → **Chyba**
- [ ] **TC-122:** Lektor zruší žádost → status `cancelled`, kredit NEpřipsán

---

## 4️⃣ INTEGRAČNÍ SCÉNÁŘE

### Scénář A: Kompletní cesta nového klienta
- [ ] **INT-001:** Registrujte se jako `kompletni@test.cz`
- [ ] **INT-002:** Dobijte 1000 Kč (čeká na schválení)
- [ ] **INT-003:** Přihlaste se jako lektor a schvalte dobití
- [ ] **INT-004:** Přihlaste se zpět jako klient → kredit 1000 Kč
- [ ] **INT-005:** Rezervujte lekci za 200 Kč → zůstatek 800 Kč
- [ ] **INT-006:** Zrušte rezervaci > 2h před začátkem → zůstatek 1000 Kč
- [ ] **INT-007:** Rezervujte dvě lekce (2× 200 Kč) → zůstatek 600 Kč

---

### Scénář B: Lektor spravuje rozvrh
- [ ] **INT-020:** Lektor vytvoří lekci "Pilates pro pokročilé"
- [ ] **INT-021:** Přidá 3 časové sloty (pondělí, středa, pátek 18:00)
- [ ] **INT-022:** Klient rezervuje středeční slot
- [ ] **INT-023:** Lektor zobrazí detail lekce → vidí 1 rezervaci
- [ ] **INT-024:** Lektor upraví čas na 19:00 → všechny sloty aktualizovány
- [ ] **INT-025:** Lektor smaže páteční slot (bez rezervace) → úspěch
- [ ] **INT-026:** Pokus o smazání středečního slotu (má rezervaci) → **nedovoleno**

---

### Scénář C: Race conditions a edge cases
- [ ] **INT-040:** Dva klienti současně rezervují poslední volné místo
  - Výsledek: Jeden úspěch, druhý chyba "již obsazeno"
- [ ] **INT-041:** Klient s 0 Kč se pokusí rezervovat → **Chyba**
- [ ] **INT-042:** Lektor smaže lekci s aktivními rezervacemi
  - Výsledek: Kaskádové smazání (nebo ochrana podle nastavení)

---

## 5️⃣ UI/UX kontroly

### Responsivita
- [ ] **UI-001:** Otevřete stránku na **mobilu** (nebo DevTools)
- [ ] **UI-002:** Navigace funguje (hamburger menu)
- [ ] **UI-003:** Formuláře jsou čitelné a použitelné
- [ ] **UI-004:** Fotografie na homepage se zobrazuje celá (bez ořezu)

### Zprávy a feedback
- [ ] **UI-010:** Úspěšná akce → zelená zpráva
- [ ] **UI-011:** Chyba → červená zpráva
- [ ] **UI-012:** Zprávy zmizí po několika sekundách (nebo manuálně zavíratelné)

---

## 📊 Checklist pro reportování chyb

Pokud najdete chybu, zaznamenejte:
1. **ID testu** (např. TC-070)
2. **Kroky k reprodukci**
3. **Očekávaný výsledek**
4. **Skutečný výsledek**
5. **Screenshot** (pokud relevantní)
6. **Chybová hláška** (traceback z Djanga)

---

## ✅ Kompletní test summary

| Oblast | Počet testů | Prošlo | Selhalo | Poznámky |
|--------|-------------|--------|---------|----------|
| Accounts | 16 | | | |
| Bookings | 32 | | | |
| Payments | 15 | | | |
| Integrace | 15 | | | |
| UI/UX | 7 | | | |
| **CELKEM** | **85** | | | |

---

**💡 TIP:** Tento checklist použijte před každým releaseм nebo po větších změnách v kódu.

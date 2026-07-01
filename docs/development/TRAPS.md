# TRAPS.md — Fouten Die Je Niet Mag Maken

Dit bestand beschrijft de kritische valkuilen voor dit project. Lees dit bij elke sessie. Controleer actief of je in een van deze traps valt voordat je code commit.

---

## Trap 1 — Peildatum tijdzone fout

**Het probleem:** 1 januari 00:00 CET is NIET 1 januari 00:00 UTC. In UTC is dat 31 december 23:00 (winter, UTC+1). Als je de snapshot op UTC doet, pak je de verkeerde waarde.

**De oplossing:**
```python
from django.utils import timezone
import pytz

cet = pytz.timezone('Europe/Amsterdam')
peildatum = cet.localize(datetime(year, 1, 1, 0, 0, 0))
```

**Test dit altijd** met een unit test die beide tijdzones verifieert.

---

## Trap 2 — Peildatum snapshot: herbereken vs vastzetten

**Het probleem:** Box 3 vereist de waarde op 1 januari op basis van alle transacties t/m die peildatum. Gebruikers voegen vaak **later** historische transacties toe (CSV, jaaropgave). Die moeten de snapshot **wel** bijwerken — tot de aangifte-deadline. Na 1 mei van het volgende jaar moet de snapshot **niet** meer wijzigen (FSD §21.2.2).

**De oplossing:**
- `unique_together = ['user', 'year']` — geen tweede snapshot per jaar
- **Herbereken** ontgrendelde snapshots bij transacties met `occurred_at` op/vóór 1 januari van dat jaar (`maybe_recalculate_peildatum_snapshots`)
- **Lock** vanaf 1 mei jaar+1 (`is_peildatum_snapshot_locked`) — geen `save()` op bestaande snapshot meer
- **Nooit** `delete()` op snapshots
- Bij transactie na lock: wel opslaan, waarschuwing in API-response (geen stille overschrijving)

```python
# Fout: altijd immutable
if self.pk:
    raise ValueError("immutable")

# Goed: alleen locked snapshots blokkeren
if self.pk and is_peildatum_snapshot_locked(self.year):
    raise ValueError("vastgezet na 1 mei")
```

---

## Trap 3 — API keys plaintext opslaan

**Het probleem:** Bitvavo API keys in de database opslaan zonder encryptie is een kritische security fout. Bij een database leak heeft een aanvaller direct toegang tot alle brokeraccounts.

**De oplossing:** AES-256-GCM encryptie via Python `cryptography` library. De encryption key staat uitsluitend in environment variables.

```python
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os, base64

def encrypt_api_key(plaintext: str) -> str:
    key = base64.b64decode(os.environ['ENCRYPTION_KEY'])
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
    return base64.b64encode(nonce + ciphertext).decode()

def decrypt_api_key(encrypted: str) -> str:
    key = base64.b64decode(os.environ['ENCRYPTION_KEY'])
    data = base64.b64decode(encrypted)
    nonce, ciphertext = data[:12], data[12:]
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, None).decode()
```

---

## Trap 4 — Box 3 berekening zonder categorie splitsing

**Het probleem:** Box 3 heeft drie categorieën met elk een eigen forfaitair rendement: banktegoeden, beleggingen, en schulden. Ze door elkaar halen geeft een verkeerde belastingberekening.

**De oplossing:** Elke asset heeft een expliciete vermogenscategorie. De calculator splitst voor de berekening.

```python
class VermogensCategorie(models.TextChoices):
    BANKTEGOED = 'banktegoed'
    BELEGGING = 'belegging'
    EDELMETAAL = 'edelmetaal'
    SCHULD = 'schuld'
    OVERIG = 'overig'
```

Forfaitaire rendementen zijn jaarlijks en staan in de database, niet hardcoded.

---

## Trap 5 — Synchrone broker API calls in request handler

**Het probleem:** Bitvavo API ophalen duurt 2-5 seconden. Als dit in een Django view gebeurt, time-out de request.

**De oplossing:** Alle externe API calls via Celery background tasks. De view start de task en geeft een `task_id` terug. De frontend pollt de status.

```python
# FOUT
def sync_portfolio(request):
    data = bitvavo_client.get_portfolio()  # Blokkeert 3 seconden
    return JsonResponse(data)

# GOED
def sync_portfolio(request):
    task = sync_bitvavo_portfolio.delay(request.user.id)
    return JsonResponse({'task_id': task.id})
```

---

## Trap 6 — DEGIRO CSV deduplicatie vergeten

**Het probleem:** Als een gebruiker twee keer dezelfde CSV upload, worden transacties dubbel geteld. Dit geeft een volledig verkeerd portfoliooverzicht.

**De oplossing:** Elke transactie heeft een unieke identifier op basis van datum + ISIN + aantal + prijs. Bij import wordt dit gecheckt.

```python
transaction_hash = hashlib.sha256(
    f"{date}{isin}{quantity}{price}".encode()
).hexdigest()

Transaction.objects.get_or_create(
    hash=transaction_hash,
    defaults={...}
)
```

---

## Trap 7 — CSV-regels stilletjes overslaan

**Het probleem:** Onbekende `Description`-waarden of nul-bedragen weglaten zonder melding. De gebruiker denkt dat alles geïmporteerd is; Box 3 en rendement kloppen niet.

**De oplossing:**

- Parser retourneert `CsvParseResult` met `rows` + `skipped` (reden per regel).
- Import-API: `has_import_gaps`, `skipped_rows`, `trust_summary` altijd teruggeven.
- Header-fingerprint vóór parse (`validate_csv_for_platform`) — geen verkeerde broker-parser.
- Nieuwe platformen registreren in `apps/integrations/csv/registry.py`.

Zie [PLATFORM-FIXTURES.md](./PLATFORM-FIXTURES.md). Kolom-aliases staan in `column_schema.py` per platform — nooit stil een nieuwe header als bestaande canonical mappen zonder productcheck. Drift: `report_csv_drift` + `CsvImportDiagnostic` in admin.

---

## Trap 8 — Mollie webhook niet verifiëren

**Het probleem:** Iedereen kan een POST sturen naar je webhook endpoint en beweren dat een betaling geslaagd is.

**De oplossing:** Verifieer altijd bij Mollie of een betaling echt geslaagd is door de payment ID op te halen via de Mollie API, nooit alleen vertrouwen op de webhook body.

```python
def mollie_webhook(request):
    payment_id = request.POST.get('id')
    # ALTIJD zelf ophalen bij Mollie, nooit vertrouwen op webhook data
    payment = mollie_client.payments.get(payment_id)
    if payment.is_paid():
        activate_premium(payment.metadata['user_id'])
```

---

## Trap 9 — Koersprijzen niet cachen

**Het probleem:** Elke portfoliopagina ophalen van koersprijzen via externe API kost geld en is traag. Bij 1000 gebruikers is dit onhoudbaar.

**De oplossing:** Koersprijzen cachen in Redis met TTL van 15 minuten voor real-time koersen, 24 uur voor historische data.

---

## Trap 10 — User data niet isoleren

**Het probleem:** Een bug waarbij user A de portfoliodata van user B kan zien is een catastrofale privacy schending.

**De oplossing:** Elke queryset filtert ALTIJD op de ingelogde user. Gebruik een base QuerySet class die dit afdwingt.

```python
class UserOwnedQuerySet(models.QuerySet):
    def for_user(self, user):
        return self.filter(user=user)

# In elke view:
portfolios = Portfolio.objects.for_user(request.user)
# Nooit:
portfolios = Portfolio.objects.all()
```

---

## Trap 11 — 2FA bypass via password reset

**Het probleem:** Als de password reset flow direct inlogt zonder 2FA te vereisen, omzeilt dit de volledige 2FA beveiliging.

**De oplossing:** Na een password reset moet de gebruiker alsnog 2FA voltooien voor toegang. De reset flow zet alleen het wachtwoord, het geeft geen auth token terug.

---

## Trap 12 — Secrets in git history

**Het probleem:** Eén keer een API key gecommit, ook al delete je hem daarna, staat hij voor altijd in de git history.

**De oplossing:**
- `.env` staat in `.gitignore` — nooit aanpassen
- Gebruik `git-secrets` of GitHub secret scanning
- Als het toch gebeurt: roteer de key direct en gebruik `git filter-branch` of BFG

---

## Checklist voor elke commit

- [ ] Geen hardcoded secrets of API keys
- [ ] Geen plaintext API key opslag
- [ ] Alle queries gefilterd op `user`
- [ ] Externe API calls via Celery, niet in views
- [ ] Tijdzone correctie voor peildatum
- [ ] Unit tests toegevoegd voor nieuwe logica
- [ ] docs/development/PROGRESS.md bijgewerkt

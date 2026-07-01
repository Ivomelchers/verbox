# Vermogenspeil · Berekeningen Fase 1

**Doel:** dit document beschrijft in gewone taal én met de exacte formules alle berekeningen die nodig zijn voor fase 1 van Vermogenspeil. Bedoeld zodat een developer het kan lezen, begrijpen en direct kan implementeren. De technische bijlagen (database, edge cases) staan onderaan.

**Scope:** belastingjaar 2026 en later. Cijfers voor 2024 en 2025 zijn niet opgenomen — Vermogenspeil start vanaf 2026\.

**Bronnen:**

- Vermogenspeil FSD v1.0 \+ prototypes (gratis \+ premium)  
- Belastingdienst — "Hoe is het box 3-inkomen op mijn voorlopige aanslag 2026 berekend?"  
- Belastingdienst — "Wat is mijn werkelijk rendement?" (gewijzigd 6 mei 2026\)

---

## Inhoudsopgave

1. [Het grote plaatje](#1-het-grote-plaatje)  
2. [Fiscale parameters per jaar](#2-fiscale-parameters-per-jaar)  
3. [Cost basis per positie](#3-cost-basis-per-positie)  
4. [Wat is een positie waard en hoeveel winst maakt iemand erop](#4-wat-is-een-positie-waard)  
5. [Het totale portfolio doorrekenen](#5-het-totale-portfolio-doorrekenen)  
6. [De peildatum-snapshot maken](#6-de-peildatum-snapshot-maken)  
7. [Welk vermogen valt onder welke categorie](#7-welk-vermogen-onder-welke-categorie)  
8. [Schulden meerekenen](#8-schulden-meerekenen)  
9. [Vastgoed: complete behandeling](#9-vastgoed-complete-behandeling)  
10. [De forfaitaire belasting berekenen](#10-de-forfaitaire-belasting-berekenen)  
11. [Welk belastingjaar moet ik tonen](#11-welk-belastingjaar-moet-ik-tonen)  
12. [Het werkelijke rendement berekenen](#12-het-werkelijke-rendement-berekenen)  
13. [Forfait vs. werkelijk vergelijken](#13-forfait-vs-werkelijk-vergelijken)  
14. [Omgaan met vreemde valuta](#14-omgaan-met-vreemde-valuta)  
15. [Edge cases (technische bijlage)](#15-edge-cases)  
16. [Database-schets (technische bijlage)](#16-database-schets)  
17. [Wat valt buiten fase 1](#17-wat-valt-buiten-fase-1)

---

## 1\. Het grote plaatje

Vermogenspeil rekent in fase 1 twee dingen uit die naast elkaar lopen:

**De forfaitaire belasting (verplicht).** Dit is de standaardberekening die de Belastingdienst altijd doet. Hij kijkt naar je vermogen op 1 januari, deelt het op in drie categorieën (banktegoeden, beleggingen, schulden) en doet alsof je een vast percentage rendement hebt gehad op elk daarvan. Over dat fictieve rendement betaal je 36% belasting.

**Het werkelijke rendement (Premium, optioneel).** Sinds 2025 mag je aantonen dat je echte rendement lager was dan het fictieve. Als dat zo is, wordt belasting geheven over het lagere bedrag. Je telt dan al je werkelijke inkomsten en waardestijgingen over het hele jaar bij elkaar op. Belangrijk: kosten mag je hierbij **niet** aftrekken (één uitzondering: rente op box 3-schulden). Ook geldt het heffingsvrij vermogen niet — die vrijstelling vervalt.

Om die twee berekeningen te kunnen doen, moet het platform een hoop ondersteunende dingen kunnen: bijhouden hoeveel iemand voor zijn beleggingen heeft betaald, de waarde op een specifieke datum reconstrueren, vreemde valuta omrekenen, en op het juiste moment van belastingjaar wisselen.

---

## 2\. Fiscale parameters per jaar

Sla alle fiscale getallen op in een aparte tabel of configuratiebestand per belastingjaar. **Hardcode ze niet** — ze veranderen jaarlijks.

| Parameter | 2026 | 2027 |
| :---- | :---- | :---- |
| Heffingsvrij vermogen | € 59.357 | nog niet bekend |
| Rendement banktegoeden | 1,28% (voorlopig) | n.t.b. |
| Rendement overige bezittingen | 6,00% (definitief) | n.t.b. |
| Rendement schulden | 2,70% (voorlopig) | n.t.b. |
| Drempel schulden per persoon | € 3.800 | n.t.b. |
| Tarief box 3 | 36% | n.t.b. |
| Vrijstelling groene beleggingen | € 26.715 | € 200 (aangekondigd) |
| Vrijstelling contant geld | € 672 | n.t.b. |
| Bijtelling-percentage eigen gebruik 2e woning (WOZ-methode) | 5,06% | n.t.b. |

**Belangrijke regels rond deze tabel:**

De percentages voor banktegoeden en schulden zijn pas **definitief** na afloop van het kalenderjaar (op basis van werkelijke gemiddelde rentes). Tot die tijd gelden voorlopige cijfers. Sla per parameter op of hij definitief is of niet, plus wanneer en waar je hem hebt opgehaald.

Voor **fiscale partners** geldt: het heffingsvrij vermogen en de schuldendrempel worden verdubbeld.

Voor **belastingjaar 2027** zijn nog geen cijfers gepubliceerd (status mei 2026). De Belastingdienst stelt die meestal vast bij het Belastingplan in het najaar van het voorgaande jaar. Tot die tijd: toon in de UI een melding dat de tarieven nog niet bekend zijn, en bereken niet met geschatte cijfers (of doe het alleen met duidelijke "indicatief"-labels).

### Formele notatie

Door het hele document gebruik ik deze variabele-namen, gevuld vanuit de tabel hierboven:

PB   \= rendement banktegoeden (2026: 0,0128)

PO   \= rendement overige bezittingen (2026: 0,0600)

PS   \= rendement schulden (2026: 0,0270)

T    \= tarief box 3 (2026: 0,36)

HF   \= heffingsvrij vermogen (2026: 59.357)

SD   \= schuldendrempel (2026: 3.800)

Bij fiscale partner: `HF = 2 × HF` en `SD = 2 × SD`.

---

## 3\. Cost basis per positie

### Wat het is en waarom

De cost basis is de gemiddelde aankoopprijs van wat iemand nu nog bezit. Die heb je nodig om winst of verlies te kunnen tonen per positie, en als basis voor het werkelijke rendement.

Bijna geen enkele broker of exchange levert dit getal aan. Vermogenspeil rekent het zelf uit, met de **gewogen gemiddelde methode**.

### Hoe het werkt (gewone taal)

Stel je voor dat iemand een potje bewaart met twee dingen erin: het totaal aantal stuks dat hij bezit, en het totale bedrag dat hij ervoor heeft betaald.

**Bij elke aankoop:** voeg de hoeveelheid toe aan het potje, en voeg de aankoopprijs plus de transactiekosten toe aan het bedrag.

**Bij elke verkoop:** bereken eerst wat één stuk gemiddeld heeft gekost. Haal vervolgens de verkochte hoeveelheid uit het potje, en haal het naar-rato bedrag eruit. De gemiddelde aankoopprijs per stuk verandert hierdoor niet — alleen het totaal wordt evenredig kleiner.

### Bijzondere events: drie verschillende behandelingen

Drie events lijken op aan- of verkopen maar moeten elk anders worden behandeld. Door ze door elkaar te halen ontstaan grote fouten (dubbeltelling van rendement, of fictieve winst bij verplaatsing). Volg deze regels strikt.

**Staking-reward en airdrop:** behandel als aankoop tegen marktprijs op moment van ontvangst — hoeveelheid stijgt, totaal betaald bedrag stijgt met `aantal × marktprijs`. Geen transactiekosten erbij. Reden: dit is direct rendement. De marktwaarde wordt tegelijk geboekt als inkomst (staking\_reward) voor het werkelijke-rendement-spoor. Door de cost basis óók te verhogen voorkom je dat hetzelfde bedrag later nóg een keer als koerswinst wordt geteld bij verkoop.

**Stock-dividend (bonusaandelen, geen cash):** alleen het aantal stuks verhogen. De cost basis blijft gelijk. Reden: dit is geen rendement — het bedrijf splitst alleen meer aandelen onder dezelfde eigenaren. De marktprijs daalt evenredig. Door alleen het aantal te verhogen daalt de cost basis per stuk automatisch en blijft de boekhouding correct.

**Transfer tussen platforms (van wallet naar broker, of tussen twee brokers):** geen wijziging in de cost basis. Het is geen aankoop, geen verkoop, geen rendement — alleen een verplaatsing. Cost basis wordt **per gebruiker per asset** bijgehouden, niet per platform. Een transfer is daardoor administratief: het beïnvloedt waar het asset getoond wordt in de UI, maar niet de cost basis of P\&L.

**Waarschuwing tegen veelvoorkomende fout:** als je een transfer-in zou behandelen als aankoop tegen marktprijs, ontstaat fictieve winst bij de transfer-out (verschil tussen oorspronkelijke aankoopprijs en huidige marktprijs). Iemand die in 2023 1 BTC voor € 30.000 kocht op Bitvavo en die in 2026 naar Ledger transfert (bij koers € 60.000) zou dan € 30.000 "verdienen" bij de transfer — terwijl er feitelijk niets is gebeurd behalve een verplaatsing.

### Architectuur-implicatie: cost basis per user per asset

Bereken cost basis op **gebruikersniveau per asset**, niet per platform. Dus: één BTC-positie voor de gebruiker, niet aparte BTC-posities per broker. In de UI kun je nog steeds tonen waar het asset op een bepaald moment ligt (Bitvavo, Ledger, etc.), maar de cost basis-administratie is unified.

Dit maakt transfers tussen platforms triviaal (no-op voor cost basis) en is fiscaal correct: de Belastingdienst kijkt naar de totale positie van de belastingplichtige in een asset, niet per bewaaradres.

### Formules

Definities:

Q     \= totaal aantal stuks dat de gebruiker nu bezit

C     \= totaal bedrag dat de gebruiker tot nu toe voor die stuks betaald heeft

CB    \= cost basis per stuk \= C / Q  (alleen als Q \> 0\)

RPL   \= gerealiseerd winst/verlies (Realized Profit/Loss), cumulatief

**Bij een aankoop van q stuks voor prijs p per stuk, met kosten f:**

C  ← C \+ (q × p) \+ f

Q  ← Q \+ q

**Bij een verkoop van q stuks voor prijs p per stuk, met kosten f:**

CB           \= C / Q

afgeboekt    \= q × CB

opbrengst    \= (q × p) − f

RPL          ← RPL \+ (opbrengst − afgeboekt)

C            ← C − afgeboekt

Q            ← Q − q

**Bij een staking-reward of airdrop van q stuks, marktprijs p op moment van ontvangst:**

C  ← C \+ (q × p)

Q  ← Q \+ q

(Geen kosten erbij, want het is geen aankoop. Tegelijk: registreer `q × p` als direct rendement voor het werkelijke-rendement-spoor — zie hoofdstuk 12.)

**Bij een stock-dividend van q stuks:**

Q  ← Q \+ q

C  blijft ongewijzigd

(Alleen aantal verhogen. De cost basis per stuk daalt automatisch — dit is geen rendement.)

**Bij een transfer tussen platforms (in of uit):**

Geen wijziging in C of Q.

(Cost basis is op user-niveau per asset. Wel registreren in de transactietabel met type `transfer_in` of `transfer_out` voor audit-trail en UI-display van waar het asset zich bevindt.)

### Voorbeeld

Iemand koopt:

- 10 ETH voor € 2.000 per stuk, met € 10 kosten → `C = 20.010`, `Q = 10`  
- Daarna 5 ETH voor € 3.000 per stuk, met € 10 kosten → `C = 35.020`, `Q = 15`  
- Cost basis per stuk: `35.020 / 15 = € 2.334,67`

Daarna verkoopt hij 8 ETH voor € 3.500 per stuk, met € 20 kosten:

- Afgeboekt: `8 × 2.334,67 = € 18.677,36`  
- Opbrengst: `8 × 3.500 − 20 = € 27.980`  
- Gerealiseerd: `27.980 − 18.677,36 = € 9.302,64`  
- Nieuw: `C = 16.342,64`, `Q = 7`

### Architectonische eis

Sla **elke aankoop apart op** in de database (niet alleen de aggregaten). Dit is nodig om later naar FIFO of LIFO uit te kunnen breiden in fase 3 zonder dat alles herbouwd moet worden. De gewogen gemiddelde berekening wordt daar in elk verzoek uit afgeleid.

### Transfers tussen platforms: matching uit CSV-imports

De vorige paragrafen zeggen dat een transfer tussen platforms een no-op is voor de cost basis. In theorie klopt dat — maar in de praktijk is het complexer, omdat de gebruiker meestal CSV-bestanden van meerdere platforms uploadt en elk platform de transfer anders labelt (of zelfs helemaal niet als transfer herkent).

#### Het probleem in vier scenario's

**Scenario 1: Beide CSV's geüpload, transfers correct gelabeld.** Ledger exporteert `transfer_out 1 BTC` op 15 maart 14:00. Bitvavo exporteert `transfer_in 1 BTC` op 15 maart 14:08. Vermogenspeil moet deze twee events koppelen en als één no-op behandelen — niet als twee aparte events.

**Scenario 2: Bitvavo labelt het als deposit, niet als transfer.** Veel platforms zien een binnenkomende crypto-transfer als een gewone `deposit`, omdat ze niet weten waar het vandaan komt. Als Vermogenspeil dit naïef behandelt als aankoop tegen marktprijs, ontstaat fictieve winst — precies wat we wilden voorkomen.

**Scenario 3: Alleen Bitvavo CSV geüpload.** Er verschijnt 1 BTC op Bitvavo zonder dat er een corresponderende `transfer_out` ergens anders is. Vermogenspeil kan niet weten of dit een eigen transfer is (cost basis bestaat al ergens, alleen niet in de geïmporteerde data) of een echte ontvangst (schenking, salaris in crypto, P2P-aankoop).

**Scenario 4: Alleen Ledger CSV geüpload.** Er verdwijnt 1 BTC van Ledger zonder corresponderende `transfer_in`. Vermogenspeil kan niet weten of dit een transfer naar een eigen account elders is (geen rendement) of een verkoop / schenking / verlies.

In de eerste twee scenario's moet de software automatisch herkennen wat er gebeurt; in de laatste twee moet de gebruiker classificeren.

#### Aanpak: automatische matching plus review-flow

Vermogenspeil doet bij elke CSV-import drie dingen:

1. **Normaliseer** binnenkomende events naar één van de erkende transactietypes. Een `deposit` van crypto-asset wordt initieel als `transfer_in` gelabeld (status: `unmatched`). Een `withdrawal` van crypto-asset als `transfer_out` (status: `unmatched`).  
     
2. **Match-engine zoekt paren.** Voor elke ongematchte `transfer_out`: zoek een ongematchte `transfer_in` van dezelfde gebruiker, voor hetzelfde asset, met ongeveer dezelfde hoeveelheid, binnen een tijdsvenster. Als gevonden: koppel ze met een gemeenschappelijke `transfer_pair_id` en zet beide statussen op `matched`.  
     
3. **Review-flow voor ongematchte events.** Wat overblijft krijgt een review-status en wordt aan de gebruiker getoond met de vraag: "wat was dit?". Pas na bevestiging van de gebruiker telt het event mee in cost basis en rendement.

#### Matching-criteria in gewone taal

Twee events vormen een paar als ze aan alle van deze voorwaarden voldoen:

- **Zelfde gebruiker** (vanzelfsprekend, want één account)  
- **Zelfde asset** (zelfde symbool, of geconfigureerde alias zoals BTC ↔ XBT, of WETH ↔ ETH bij wrapping)  
- **Hoeveelheden komen overeen binnen een marge.** Crypto-netwerken rekenen transactiekosten — de gebruiker stuurt 1 BTC, maar er komt 0,99985 BTC aan. Standaard marge: hoeveelheid bij ontvangst tussen 99% en 100% van uitgaande hoeveelheid.  
- **Tijdsverschil binnen tolerantie.** Bitcoin-bevestiging kan tot een uur duren, Ethereum minuten. Standaard tolerantie: ontvangst is na uitgaand en binnen 48 uur. Voor sommige assets (XRP, snelle L2's) is een kleinere window strakker.  
- **Verschillende platforms.** Een uitgaande transfer op Bitvavo en een binnenkomende op Bitvavo van dezelfde gebruiker zou geen pair moeten zijn (dat is een interne move).

Als meerdere mogelijke matches bestaan: pak de match met het kleinste tijdsverschil. Als geen match: laat het event op `unmatched` staan voor review.

#### Matching-algoritme in pseudocode

function matchTransfers(userId):

    open\_out \= SELECT \* FROM transactions

               WHERE user\_id \= userId

                 AND type \= 'transfer\_out'

                 AND status \= 'unmatched'

               ORDER BY transaction\_date ASC

    for tx\_out in open\_out:

        candidates \= SELECT \* FROM transactions

                     WHERE user\_id \= userId

                       AND type \= 'transfer\_in'

                       AND status \= 'unmatched'

                       AND asset\_symbol\_or\_alias \= tx\_out.asset\_symbol

                       AND platform \!= tx\_out.platform

                       AND transaction\_date BETWEEN tx\_out.transaction\_date

                                                AND tx\_out.transaction\_date \+ 48 hours

                       AND quantity BETWEEN 0.99 × tx\_out.quantity

                                        AND 1.00 × tx\_out.quantity

                     ORDER BY ABS(transaction\_date \- tx\_out.transaction\_date) ASC

        if candidates is not empty:

            tx\_in \= candidates\[0\]   \# kleinste tijdsverschil

            pair\_id \= generate\_uuid()

            UPDATE transactions

                SET status \= 'matched', transfer\_pair\_id \= pair\_id

                WHERE id IN (tx\_out.id, tx\_in.id)

Draai dit algoritme:

- Na elke CSV-import (zoekt over alle huidige ongematchte events)  
- Bij handmatige toevoeging van een transfer-event  
- Optioneel via een nightly cron-job voor systeem-wide check

#### Review-flow voor ongematchte events

Een ongematchte `transfer_out` toont in de UI als reviewable. De gebruiker krijgt drie keuzes:

1. **"Dit was een transfer naar een eigen account dat ik nog niet heb verbonden."** Het event wordt gemarkeerd als `confirmed_transfer` zonder pair. Het asset verdwijnt uit de portfolio voor de cost-basis-berekening (zoals bij elke transfer-out), maar er is geen overeenkomstige `transfer_in`. Vermogenspeil onthoudt: deze gebruiker heeft een externe wallet/broker die hij later wellicht koppelt. Geen P\&L-event.  
     
2. **"Dit was een verkoop (verkoop buiten platform, P2P, OTC)."** Het event wordt geherclassificeerd naar `sell` en de gebruiker vult de opbrengst in. Cost basis wordt afgeboekt, gerealiseerde winst berekend.  
     
3. **"Dit was een schenking, betaling of verlies."** Het event wordt geherclassificeerd naar `gift_out` of `loss`. Cost basis wordt afgeboekt zonder gerealiseerde winst. Voor box 3: hoeveelheid verdwijnt uit de positie, einde verhaal.

Een ongematchte `transfer_in` of `deposit` toont vergelijkbaar. De gebruiker krijgt vier keuzes:

1. **"Dit was een transfer vanuit een eigen account dat ik niet heb verbonden."** Vraag de gebruiker om de oorspronkelijke aankoopdatum en \-prijs (zo goed als hij weet) zodat de cost basis correct kan worden gereconstrueerd. Markeer als `confirmed_transfer_with_manual_basis`. Status van het event blijft `unmatched_pair` maar P\&L-impact wordt correct berekend.  
     
2. **"Dit was een aankoop buiten platform (P2P, OTC, geschenkkaart-conversie)."** Geherclassificeer naar `buy` en laat de gebruiker prijs en kosten invullen. Voegt toe aan cost basis.  
     
3. **"Dit was een ontvangen schenking of betaling."** Geherclassificeer naar `gift_in`. Cost basis op marktprijs van moment ontvangst, hoeveelheid toegevoegd. (Voor box 3 maakt dit geen verschil; voor fase 2/3 kan schenking-belasting relevant worden.)  
     
4. **"Weet ik niet / sla over."** Event wordt als `pending_review` opgeslagen, telt nergens in mee tot review. Vermogenspeil toont een waarschuwing in de UI: "X events wachten op review; je belastingberekening kan onvolledig zijn."

#### Handmatige koppeling en ontkoppeling

Soms gaat het automatisch fout. Een transactie met meerdere kleine fragmenten (DeFi-bridges, splitsing van transfers), een grote tijdsvertraging door netwerk-congestie, een hoeveelheid die door bridge-fees ver onder 99% zakt. De UI moet altijd toestaan:

- **Handmatig koppelen:** gebruiker selecteert twee events en bevestigt dat ze één pair zijn (override van automatische logica).  
- **Handmatig ontkoppelen:** een verkeerd gematchte pair losmaken; beide events terug op `unmatched`.  
- **Marges aanpassen:** in geavanceerde instellingen kan de gebruiker tijdvenster en hoeveelheid-marge bijstellen (default 48u / 99%, sommige use-cases vragen 7 dagen / 95% voor bridges).

#### Snapshot-implicatie

Voor de peildatum-snapshot (hoofdstuk 6\) telt alleen wat op 1 januari aanwezig was. Gematchte transfers hebben geen effect — de hoeveelheid is netto onveranderd. Maar `pending_review`\-events hebben wel effect: ze worden tijdelijk genegeerd in de snapshot, met disclaimer in de UI. Dat is een goede prikkel voor de gebruiker om de review af te ronden vóór aangiftedatum.

#### Database-uitbreidingen voor transfer-matching

Twee velden moeten worden toegevoegd aan de `transactions`\-tabel:

status VARCHAR(30),              \-- 'confirmed' | 'unmatched' | 'matched' |

                                 \-- 'pending\_review' | 'confirmed\_transfer' |

                                 \-- 'confirmed\_transfer\_with\_manual\_basis'

transfer\_pair\_id UUID NULL,      \-- gemeenschappelijke ID voor gematchte transfer-pairs

Plus optioneel een aparte `transfer_matches`\-tabel voor audit:

transfer\_matches (

    pair\_id UUID PRIMARY KEY,

    user\_id UUID,

    out\_transaction\_id UUID,

    in\_transaction\_id UUID,

    matched\_at TIMESTAMP,

    matched\_by VARCHAR(10),       \-- 'auto' | 'manual'

    time\_delta\_seconds INT,

    quantity\_delta DECIMAL(20,8)

)

Dit laatste is geen vereiste maar maakt latere debugging veel makkelijker.

### Hoe kosten worden behandeld (kritisch — lees voor implementatie)

Kosten zijn het meest verwarrende onderdeel van fase 1, omdat ze in vier verschillende berekeningen op vier verschillende manieren worden behandeld. Eén bedrag aan transactiekosten kan dus tegelijk wel én niet meetellen, afhankelijk van welke vraag je beantwoordt.

#### Twee werelden: boekhoudkundig vs. fiscaal

Het verschil zit in welke vraag je stelt:

**Boekhoudkundig (cost basis, gerealiseerde winst, "totale winst" in UI):** kosten horen erbij. Als iemand € 10.000 aan ETH koopt met € 30 transactiekosten, dan heeft die positie hem € 10.030 gekost. Dat is geen fiscale stelling — het is gewoon administratie. Verkoopt hij later voor € 12.000 met € 30 kosten, dan is zijn nettowinst € 12.000 − € 30 − € 10.030 \= € 1.940.

**Fiscaal (werkelijke rendement voor box 3, fase 1):** kosten zijn níet aftrekbaar — met twee specifieke uitzonderingen die hieronder beschreven staan. Dit is een **bewuste keuze van de Nederlandse wetgever** voor het overgangsstelsel onder de tegenbewijsregeling. De Hoge Raad heeft dit bevestigd: bij werkelijk rendement geldt het bruto-bedrag, omdat het forfaitaire stelsel al rekening houdt met kosten in de bepaling van de percentages. Onder het toekomstige stelsel vanaf 2028 (Wet werkelijk rendement box 3\) wordt dit fundamenteel anders.

#### Volledige kostenmatrix voor fase 1

Welke kosten waar wel en niet meetellen. Deze tabel is **autoritair**: bij twijfel altijd hier kijken, niet improviseren.

| Soort kosten | Database | Cost basis | Gerealiseerde winst | Werkelijk rendement | UI "totale winst" |
| :---- | :---- | :---- | :---- | :---- | :---- |
| Transactie-fee bij aankoop (broker, exchange) | `transactions.fees_eur` | \+ verhoogt C | n.v.t. | **niet aftrekbaar** | − verlaagt winst |
| Transactie-fee bij verkoop | `transactions.fees_eur` | n.v.t. | − verlaagt opbrengst | **niet aftrekbaar** | − verlaagt winst |
| Spread (impliciet in prijs) | `transactions.implicit_spread_eur` | \+ verhoogt C (via prijs) | − via prijs | **niet aftrekbaar** | − verlaagt winst |
| Currency-conversie-fee | `transactions.fees_eur` of `transactions.fx_fee_eur` | \+ verhoogt C | n.v.t. | **niet aftrekbaar** | − verlaagt winst |
| Netwerk-fee crypto-transfer | aparte `fee` transactie | n.v.t. | n.v.t. | **niet aftrekbaar** | − verlaagt winst |
| Bridge-fee (DeFi) | aparte `fee` transactie | n.v.t. | n.v.t. | **niet aftrekbaar** | − verlaagt winst |
| Swap-fee op DEX | aparte `fee` transactie | n.v.t. | n.v.t. | **niet aftrekbaar** | − verlaagt winst |
| Custody-fee / vermogensbeheer-fee | `periodic_costs` | n.v.t. | n.v.t. | **niet aftrekbaar** | − verlaagt winst |
| Platform-abonnement (broker premium) | `periodic_costs` | n.v.t. | n.v.t. | **niet aftrekbaar** | − verlaagt winst |
| ETF management fee (TER, in NAV) | `holdings.implicit_ter_pct` (info) | impliciet via prijs | impliciet via prijs | **niet aftrekbaar** | impliciet via waarde |
| Inactiviteits-fee | `periodic_costs` | n.v.t. | n.v.t. | **niet aftrekbaar** | − verlaagt winst |
| **Dividendbelasting** (15% NL, soms hoger buitenland) | `transactions.tax_withheld_eur` | n.v.t. | n.v.t. | **niet in mindering** (bruto telt) | optioneel netto tonen |
| Onderhoudskosten 2e woning (klein onderhoud) | `real_estate_costs` | n.v.t. | n.v.t. | **niet aftrekbaar** | n.v.t. (informatief) |
| Verzekering 2e woning | `real_estate_costs` | n.v.t. | n.v.t. | **niet aftrekbaar** | informatief |
| VvE-bijdragen 2e woning | `real_estate_costs` | n.v.t. | n.v.t. | **niet aftrekbaar** | informatief |
| OZB en andere gemeentelijke heffingen | `real_estate_costs` | n.v.t. | n.v.t. | **niet aftrekbaar** | informatief |
| Beheerkosten verhuurde woning | `real_estate_costs` | n.v.t. | n.v.t. | **niet aftrekbaar** | informatief |
| Afsluitkosten lening | `debts.afsluitkosten` | n.v.t. | n.v.t. | **niet aftrekbaar** | informatief |
| Boeterente vervroegd aflossen | `debts.boeterente` | n.v.t. | n.v.t. | **niet aftrekbaar** | informatief |
| **Rente op box 3-schulden** | `debts.rente_betaald_ytd` | n.v.t. | n.v.t. | **WEL aftrekbaar** | apart tonen |
| **WOZ-verhogende investering 2e woning (gemeld bij gemeente)** | `real_estate.woz_verhogende_investering_ytd` | verhoogt instapwaarde | n.v.t. | **WEL aftrekbaar** | apart tonen |

#### De twee aftrekbare categorieën — onderbouwing

**Rente op box 3-schulden** is aftrekbaar omdat het de keerzijde is van het forfaitaire rendement op schulden (stap 1 in de forfaitaire berekening trekt al een fictief schulden-rendement af). De Hoge Raad heeft expliciet bevestigd dat rente bij werkelijk rendement ook moet kunnen worden afgetrokken — anders zou de tegenbewijsregeling oneerlijk uitpakken voor mensen met schulden.

**WOZ-verhogende investeringen** zijn aftrekbaar in het jaar van investering omdat ze anders dubbel zouden worden belast: eerst nu via de verhoogde WOZ-waarde (hogere waardemutatie), en later nog eens. De meldplicht bij de gemeente is voorwaarde: zonder melding gaat de Belastingdienst ervan uit dat de verhoging marktwerking is, niet een investering. Klein onderhoud en regulier onderhoud tellen niet — alleen investeringen die de WOZ aantoonbaar verhogen (aanbouw, gebouwgebonden verbouwingen, energielabel-upgrades indien WOZ-relevant).

#### Specifieke kostentypes — behandeling in detail

**Transactiekosten (per trade).** Sla op in `transactions.fees_eur` op de aankoop- of verkooprij zelf. Deze fee verhoogt de cost basis bij aankoop, verlaagt de opbrengst bij verkoop. In de cost basis-formule (hoofdstuk 3): `C ← C + (q × p) + f` bij aankoop, en `opbrengst = (q × p) − f` bij verkoop. Voor werkelijk rendement: negeren.

**Spread (impliciete kosten in prijs).** Bij crypto-aankopen op exchanges zoals Bitvavo is de spread vaak niet zichtbaar — de prijs die je betaalt is al inclusief broker-marge. Voor transparantie wel apart tracken waar bekend (Bitvavo toont bijvoorbeeld in CSV soms zowel midprijs als afgerekende prijs). Sla het verschil op in `transactions.implicit_spread_eur`. Het zit al verwerkt in `price_eur` dus telt automatisch mee in de cost basis. Het `implicit_spread_eur`\-veld is puur voor weergave en analyse ("je betaalde € X aan impliciete kosten dit jaar"). Niet apart aftrekken — anders dubbeltelling.

**Currency-conversie-fee.** Veel brokers rekenen een opslag bovenop de wisselkoers (vaak 0,15-0,5%). Sla op als aparte fee bij de transactie, of verwerk in de fx\_rate. Beste praktijk: sla zowel de "officiële" ECB-koers (`fx_rate`) als de werkelijk gebruikte koers (`fx_rate_actual`) op. Het verschil maal bedrag is de impliciete fee — informatief voor de gebruiker.

**Netwerk-fees bij crypto-transfers tussen eigen platforms.** Boekhoudkundige behandeling: maak een **aparte transactie** met type `fee`, en houd Q van het asset onveranderd (de hoeveelheid die binnenkomt bij ontvanger is wel minder). Concreet: gebruiker verstuurt 1 BTC van Ledger naar Bitvavo, ontvangt 0,9998 BTC. Boekhouding:

- Transfer-out: 1 BTC (Ledger) — no-op voor cost basis  
- Fee: 0,0002 BTC (waarde in EUR op transferdatum) — type `fee`, registreer in `transactions.fees_eur`  
- Transfer-in: 0,9998 BTC (Bitvavo) — no-op voor cost basis

Resultaat: totaal aantal BTC op user-niveau daalt met 0,0002 (de fee verlaat de portfolio echt — naar de miners). Cost basis blijft op user-niveau intact maar geldt nu voor minder stuks, dus de cost basis per stuk stijgt iets. Voor werkelijk rendement: niet aftrekbaar. Voor de UI: tel de fee mee bij "totale kosten dit jaar".

**Bridge-fees en swap-fees op DEX.** Behandel hetzelfde als netwerk-fees: aparte `fee`\-transactie, Q van overgangs-asset constant, cost basis daalt impliciet door minder beschikbare stuks.

**Custody-fee, vermogensbeheer-fee, platform-abonnement, inactiviteits-fee.** Niet gekoppeld aan een specifieke transactie. Sla op in een aparte `periodic_costs`\-tabel met datum, bedrag, type en platform. Voor de UI-berekening "totale winst": som van alle `periodic_costs` van het jaar wordt afgetrokken. Voor werkelijk rendement: niet meegenomen.

**ETF management fee (TER, Total Expense Ratio).** Wordt **niet** als aparte fee gefactureerd — het zit al in de NAV (Net Asset Value) van het ETF. Een ETF met 0,20% TER en 5% bruto rendement levert 4,80% op voor de belegger. Sla TER op als metadata bij het asset (`holdings.implicit_ter_pct`) voor informatieve weergave, maar voer geen aparte aftrek door — dat zou dubbeltelling zijn want het is al in de prijs verwerkt.

**Dividendbelasting.** Belangrijk: voor werkelijk rendement geldt het **bruto-dividend** (Belastingdienst, bevestigd door rechtbank). De ingehouden dividendbelasting wordt verrekend met de gewone IB-aanslag, niet met het rendement.

Concreet: een aandeel keert € 100 dividend uit. Bedrijf houdt € 15 dividendbelasting in, broker rekent € 1 inningskosten. Gebruiker krijgt € 84 op zijn rekening.

Voor werkelijk rendement tel je: **€ 100 (bruto)**. Voor netto-display in UI tel je: € 84\. De € 15 dividendbelasting wordt **apart geregistreerd** in `transactions.tax_withheld_eur` en verschijnt in het OWR-rapport als "ingehouden dividendbelasting (verrekenbaar)".

Maak per dividend-transactie deze velden:

- `transactions.amount_gross_eur` \= € 100 (bruto, voor werkelijk rendement)  
- `transactions.tax_withheld_eur` \= € 15 (dividendbelasting, voor verrekening IB)  
- `transactions.fees_eur` \= € 1 (broker-inningskosten, niet aftrekbaar)  
- `transactions.amount_net_eur` \= € 84 (wat gebruiker netto ontving, voor UI)

**Let op — dubbeltelling-valkuil bij herbeleggen.** Als de gebruiker netto-dividend automatisch laat herbeleggen ("DRIP"), zit het bedrag straks in zijn portfoliowaarde op 31 december. Bij waardemutatie-berekening (`WM = (W_eind − W_start) − NI`) moet je dat bedrag als storting (`NI`) opnemen, anders wordt het twee keer geteld (één keer als direct rendement via DIV, één keer als waardestijging via WM). Bron: Van Lanschot Kempen-richtlijn werkelijk rendement.

**Onderhoudskosten 2e woning, verzekering, VvE, OZB.** Sla op in `real_estate_costs`\-tabel voor weergave aan gebruiker. Niet aftrekbaar voor werkelijk rendement in fase 1\. Wordt vanaf 2028 wel aftrekbaar — sla daarom de data nu al netjes per categorie op.

**Rente op box 3-schulden.** Sla op in `debts.rente_betaald_ytd`. Eén van de twee aftrekbare posten. In de werkelijk-rendement-formule: `WR = Reg + WM + BIJT − RNT_s − INV_woz`, waarbij `RNT_s` de som is over alle schulden.

**WOZ-verhogende investering.** Aftrekbaar **alleen als gemeld bij gemeente**. Vereist twee velden in `real_estate`: `woz_verhogende_investering_ytd` en `investering_gemeld_bij_gemeente` (boolean). In de UI: vraag de gebruiker expliciet of de melding is gedaan voordat het bedrag wordt meegenomen.

#### Implementatie-implicaties

**Voor de database:** sla álle kosten op, ook de niet-aftrekbare. Drie redenen: (1) de UI heeft ze nodig voor "totale winst", (2) vanaf 2028 worden de meeste alsnog fiscaal relevant, (3) audit-trail voor controle.

Belangrijke design-keuze: kosten worden in drie verschillende structuren opgeslagen, afhankelijk van type:

- **Per-transactie**: trade-fees, currency-fees, dividendbelasting → veld op `transactions`  
- **Periodieke**: custody, beheer, abonnement → eigen `periodic_costs`\-tabel  
- **Asset-gebonden**: ETF TER → metadata op `holdings`  
- **Vastgoed-gebonden**: onderhoud, VvE, OZB → eigen `real_estate_costs`\-tabel  
- **Schuld-gebonden**: rente, afsluitkosten → velden op `debts`

**Voor de forfait-berekening (hoofdstuk 10):** kosten spelen geen enkele rol. De forfaitaire berekening kijkt alleen naar het vermogen op peildatum. Negeer alle kosten-velden hierin.

**Voor de werkelijk-rendement-berekening (hoofdstuk 12):** gebruik alleen de twee aftrekbare categorieën (rente op schulden, WOZ-verhogende investering). De formule bevat geen ander kostenbedrag. Specifiek: de waardemutatie `WM` gebruikt aankoopprijzen en eindwaardes **zonder** transactiekosten te verrekenen — anders zou je impliciet kosten aftrekken.

**Voor het UI-rapport "totale winst":** wél alle kosten verrekenen, want de gebruiker wil zien wat zijn beleggingen hem netto hebben opgeleverd. Dit cijfer is informatief, niet fiscaal.

**Voor het OWR-rapport / aangifte-export:** geen kosten opnemen behalve de twee aftrekbare categorieën. Wel apart vermelden: ingehouden dividendbelasting (verrekenbaar met IB-aanslag).

#### Voorbeeld dat alle behandelingen laat zien

Iemand koopt 10 ETH voor € 30.000 met € 50 transactiekosten en € 30 impliciete spread. Hij betaalt dat jaar:

- € 100 beheerfees voor zijn broker  
- € 540 rente op een schuld van € 20.000  
- € 8 netwerk-fees voor een transfer naar zijn hardware wallet

Hij ontvangt € 200 bruto dividend op een ander aandeel (€ 30 dividendbelasting, € 2 broker-inningskosten, dus € 168 netto op rekening).

Aan het einde van het jaar staat zijn ETH op € 32.000.

**Cost basis ETH (boekhoudkundig):**

C \= 30.000 \+ 50 \= 30.050   (transactiekosten erbij; spread zit al in prijs)

Q \= 10

Cost basis per stuk: € 3.005.

**Werkelijk rendement (fase 1):**

Reguliere voordelen (DIV):

  bruto dividend \= € 200          (let op: bruto, niet netto € 168\)

Waardemutatie (WM):

  W\_eind ETH \= 32.000

  W\_start ETH \= 30.000           (let op: zonder transactiekosten; gebruik ruwe aankoopprijs)

  NI \= 0 (geen bijkoop/verkoop)

  WM \= 32.000 − 30.000 − 0 \= 2.000

Rente schuld (RNT\_s) \= 540

Beheerfees, netwerk-fees, spread, broker-inningskosten op dividend: niet aftrekbaar (= 0 in formule)

WR \= 200 \+ 2.000 \+ 0 − 540 − 0 \= € 1.660

**UI "totale winst":**

Waardestijging ETH: 32.000 − 30.050 \= 1.950

Bruto dividend: \+ 200

Min dividendbelasting: − 30

Min broker-inningskosten dividend: − 2

Min beheerfees: − 100

Min netwerk-fees: − 8

Min impliciete spread (al in prijs verwerkt — niet dubbel aftrekken): 0

Totaal: € 2.010 netto resultaat voor gebruiker

**OWR-export:**

Dividend bruto: € 200

Ingehouden dividendbelasting (verrekenbaar): € 30

Waardemutatie ETH: € 2.000

Rente schuld: € 540 (aftrek)

Werkelijk rendement totaal: € 1.660

Drie verschillende getallen voor dezelfde portfolio, allemaal correct binnen hun eigen context.

#### Vooruitblik: wat verandert in 2028 (informatief)

Vanaf belastingjaar 2028 (mogelijk uitgesteld naar 2029\) treedt de Wet werkelijk rendement box 3 in werking. Daarin wordt **algemene kostenaftrek wél toegestaan**: transactiekosten, beheerfees, custody-kosten en onderhoudskosten van vastgoed worden aftrekbaar voor het werkelijke rendement. Uitzonderingen die níét aftrekbaar zijn: dividendbelasting (blijft verrekenbaar met IB), kosten voor congressen, vervoer, werkruimte, telefoonabonnementen.

Voor fase 1 (t/m 2027): blijf strikt bij de regels en de matrix hierboven. Niet anticiperen op fase 2 in de berekeningen — wel anticiperen in de database-architectuur door alle kostendata netjes per categorie op te slaan, zodat fase 2 een berekenings-update wordt, geen data-migratie.

---

## 4\. Wat is een positie waard

Per positie wil je op elk moment de volgende cijfers kunnen tonen.

### In gewone taal

- **Aantal nu bezit:** komt uit de cost basis-berekening hierboven.  
- **Huidige marktwaarde:** aantal × actuele koers in euro's.  
- **Ongerealiseerde winst:** marktwaarde min cost basis.  
- **Totale winst:** ongerealiseerde winst plus alle eerder gerealiseerde winsten op deze positie.  
- **Aandeel in portfolio:** waarde van deze positie gedeeld door totale portfoliowaarde.

### Formules

Definities:

Q       \= aantal nu bezit (zie hoofdstuk 3\)

C       \= totaal betaald (zie hoofdstuk 3\)

Pnu     \= actuele koers in EUR

RPL     \= gerealiseerd winst/verlies op deze positie (cumulatief)

Wtotaal \= totale portfoliowaarde

Mw   \= Q × Pnu                       (marktwaarde nu)

UPL  \= Mw − C                        (ongerealiseerde winst, in EUR)

UPL% \= UPL / C                       (als C \> 0\)

TPL  \= UPL \+ RPL                     (totale winst, in EUR)

Aandeel% \= Mw / Wtotaal

### Rendement over een periode (1W, 1M, 1Y) — Premium

Voor een positie over een specifieke periode:

Qstart   \= aantal op begindatum van de periode

Pstart   \= koers op begindatum

Vstart   \= Qstart × Pstart           (waarde op begin)

Vnu      \= Q × Pnu                   (waarde nu)

NIp      \= netto inleg deze positie in deze periode (aankopen − verkopen, exclusief koerswijziging)

Dp       \= ontvangen dividend deze positie in deze periode

R\_eur   \= Vnu − Vstart − NIp \+ Dp

R\_pct   \= R\_eur / Vstart             (als Vstart \> 0\)

---

## 5\. Het totale portfolio doorrekenen

### Insight-cards (in gewone taal)

- **Totaal ingelegd:** de som van de cost basis van alle huidige posities.  
- **Huidige waarde:** de som van de marktwaardes van alle posities.  
- **Totale winst in EUR:** huidige waarde min totaal ingelegd, plus alle gerealiseerde winsten uit het verleden, plus alle ontvangen dividenden en andere inkomsten, min kosten die buiten de aankopen vielen (bijvoorbeeld jaarlijkse beheerfees).  
- **Totale winst in %:** totale winst gedeeld door totaal ingelegd.  
- **Geannualiseerd rendement (CAGR):** zie hieronder.

### Formules portfolio-totalen

Definities:

Ci    \= cost basis (C) per positie i

Mwi   \= marktwaarde nu per positie i

RPLi  \= gerealiseerd winst/verlies per positie i

Dtot  \= som van alle ontvangen dividenden, staking-rewards, rente (cumulatief)

Fout  \= som van kosten buiten aankoop/verkoop (beheerfees, custody-kosten)

Ingelegd\_totaal \= Σ Ci  voor alle huidige posities

Waarde\_nu       \= Σ Mwi voor alle huidige posities

Winst\_eur       \= Waarde\_nu − Ingelegd\_totaal \+ Σ RPLi \+ Dtot − Fout

Winst\_pct       \= Winst\_eur / Ingelegd\_totaal

### Geannualiseerd rendement (CAGR)

Dit cijfer is lastiger. De UI noemt het "gewogen naar inleg-tijd", wat betekent dat je niet zomaar de simpele CAGR-formule kunt gebruiken — die werkt slecht als iemand op verschillende momenten heeft ingelegd.

**Wat je moet doen:** bereken de Money-Weighted Return, ook bekend als XIRR (Extended Internal Rate of Return). Dit is een rentevoet `r` die je vindt door alle cashflows zo te verdisconteren dat hun som nul is.

**Cashflow-conventie:**

- Stortingen: negatief (geld stroomt het portfolio in)  
- Onttrekkingen: positief (geld stroomt eruit)  
- Eindwaarde portfolio op de peildatum: positief (alsof je het hele portfolio zou liquideren)

**Formule:**

Voor elke cashflow CFi op datum di, met d0 \= datum van de eerste cashflow:

Σ ( CFi / (1 \+ r)^((di − d0) / 365.25) ) \= 0

Los op naar r met een numerieke solver.

**Praktische implementatie:**

- Node.js: het `xirr` package  
- Python: `pyxirr`, of `scipy.optimize.brentq` als je het zelf wil schrijven

Cache het resultaat per gebruiker. Hercaculeer alleen als er nieuwe transacties zijn toegevoegd.

### Grafiek 'waarde vs. inleg' (12 maanden)

Voor elke datum t op de tijdas heb je twee getallen nodig:

**In gewone taal:** de totale portfoliowaarde op datum t, en de cumulatieve netto inleg tot en met datum t.

**Formules:**

Voor elke positie i, op datum t:

  Qi(t) \= aantal bezit op datum t

  Pi(t) \= koers op datum t

Waarde\_t  \= Σ ( Qi(t) × Pi(t) )  over alle posities die op t bestonden

Inleg\_t   \= Σ stortingen tot en met t − Σ onttrekkingen tot en met t

Cashflows uit verkopen blijven als cash in de portfolio meegerekend zolang ze niet onttrokken zijn. Voor een consistent beeld: tel cash-saldi van brokers mee in `Waarde_t` als de gebruiker die bijhoudt.

---

## 6\. De peildatum-snapshot maken

### Wat het is

Voor de box 3-belasting telt alleen het vermogen op **1 januari 00:00**. Het platform moet dus precies kunnen zeggen wat iemand op die exacte datum bezat. Geen exchange-API levert die snapshot kant-en-klaar; je rekent hem uit op basis van transactie-historie.

### Hoe je de snapshot bouwt

**Stap 1\.** Verzamel alle transacties van de gebruiker tot en met de peildatum.

**Stap 2\.** Loop door die transacties chronologisch, en bouw per asset (combinatie van platform en symbool) op wat hij op die peildatum nog bezit. Gebruik dezelfde logica als bij de cost basis (hoofdstuk 3).

**Stap 3\.** Waardeer elk asset op de peildatum-koers. Voor beursgenoteerde effecten: de slotkoers van de laatste handelsdag voor 1 januari (meestal 31 december). Voor crypto (24/7): de prijs om 00:00 op 1 januari, of de slotprijs van 31 december. Als geen koers beschikbaar: gebruik de laatst bekende koers vóór de peildatum en markeer in de UI als "indicatieve waardering".

**Stap 4\.** Tel daar het overige vermogen bij op — handmatig ingevoerde gegevens: spaarrekeningen, betaalrekeningen, deposito's, vastgoed (op WOZ-waarde), schulden.

**Stap 5\.** Bereken de drie categorie-totalen voor de belastingberekening: totaal banktegoeden, totaal overige bezittingen, totaal schulden. Sla die op samen met de hele snapshot.

### Wanneer je de snapshot maakt en wanneer hij vastligt

**Aanmaken:** automatisch elke 1 januari om 00:01 Nederlandse tijd voor alle gebruikers. Plus on-demand: als een gebruiker een nieuwe transactie toevoegt met een datum vóór de peildatum, herbereken je de snapshot (mits hij nog niet vastligt).

**Vastleggen ('locken'):** op 1 mei van het opvolgende jaar — dat is de aangifte-deadline. Vanaf dat moment mag de snapshot niet meer wijzigen. Latere transacties worden wel opgeslagen voor toekomstige perioden, maar de snapshot blijft staan. Toon banner: "Deze transactie wordt niet meer meegenomen in aangifte 2026."

### Omgang met ongematchte transfers en pending review

Events met status `unmatched` of `pending_review` (zie hoofdstuk 3\) worden in de snapshot **tijdelijk genegeerd**. De cost basis en hoeveelheden gaan uit van wat wel bevestigd is.

Toon in de UI een waarschuwing: "Er zijn X events die op review wachten. Je snapshot voor 1-1-{jaar} kan onvolledig zijn." Dit motiveert de gebruiker om vóór de aangifte-deadline alle openstaande events af te handelen.

Zodra een gebruiker een event bevestigt en het wordt verplaatst van `pending_review` naar `confirmed`: herbereken de snapshot (mits nog niet gelockt).

### WOZ-waarde voor vastgoed

Voor belastingjaar 2026 gebruik je de **WOZ-waarde 2026**: de waarde die de gemeente begin 2026 vaststelt op basis van waardepeildatum 1 januari 2025\. Niet de waarde op het moment van de peildatum 1-1-2026 zelf (die kent de gemeente nog niet).

---

## 7\. Welk vermogen onder welke categorie

De Belastingdienst kent drie categorieën met elk een eigen rendementspercentage.

### Wat valt onder banktegoeden (lage categorie)

- Bank- en spaartegoeden in Nederland en in het buitenland  
- Contant geld boven de vrijstelling (2026: € 672 per persoon)  
- Premiedepots  
- Het niet-vrijgestelde deel van groene spaartegoeden  
- Aandeel in vermogen van een Vereniging van Eigenaars  
- Geld op derdenrekening van notaris of gerechtsdeurwaarder

### Wat valt onder overige bezittingen (hoge categorie)

- Aandelen, obligaties, effecten en andere beleggingen  
- Het niet-vrijgestelde deel van groene beleggingen  
- Overige vorderingen  
- Een 2e woning in Nederland (op WOZ-waarde)  
- Een 2e woning in het buitenland (waarde in het economisch verkeer)  
- Een verhuurde woning  
- Overige onroerende zaken  
- **Cryptovaluta** — door de Belastingdienst expliciet hier genoemd. Stablecoins (USDC, USDT, EURC) horen er dus ook bij; ze tellen niet als banktegoed.  
- Een lot waarop een prijs is gevallen

### Wat valt onder schulden

- Schulden voor consumptie (auto, vakantie)  
- Negatief saldo op een bankrekening  
- Schulden voor financiering van beleggingen  
- Schulden voor een 2e woning  
- Hypotheekschulden die niet in box 1 aftrekbaar zijn  
- Terug te betalen levenlanglerenkrediet  
- Erfbelasting  
- Schuld door schenking op papier

**Niet in box 3:** de eigen woning en de bijbehorende hypotheek — die staan in box 1\.

### Formules sommatie op peildatum

B  \= Σ waarde-op-peildatum  waar category \== 'banktegoeden'

O  \= Σ waarde-op-peildatum  waar category \== 'overige bezittingen'

S  \= Σ openstaand-op-peildatum  over alle box 3-schulden

---

## 8\. Schulden meerekenen

Schulden verlagen je belasting, maar pas vanaf een drempel. Voor 2026: € 3.800 per persoon, € 7.600 met fiscaal partner.

De drempel werkt op het **totaal** van alle schulden, niet per schuld apart.

### Formule

Saf \= max(0, S − SD)

Waarbij `Saf` de aftrekbare schuld is, `S` het totaal van alle box 3-schulden, en `SD` de drempel.

### Voorbeeld

Iemand met drie schulden van € 1.500 (totaal € 4.500) en zonder partner:

Saf \= max(0, 4.500 − 3.800) \= € 700

---

## 9\. Vastgoed: complete behandeling

Vastgoed is het meest complexe onderdeel van box 3 en vraagt om uitvoerige handmatige invoer. Geen broker of API levert vastgoeddata — alles wordt door de gebruiker zelf ingevoerd. Dit hoofdstuk behandelt **alle** vastgoed dat in box 3 valt, met alle bijbehorende velden, waarderingen, kosten en berekeningen.

### Welk vastgoed valt in box 3

De volgende vastgoed-types horen in box 3 (de eigen woning hoort in box 1 en valt buiten dit hoofdstuk):

- 2e woning in Nederland (vakantiewoning, pied-à-terre)  
- 2e woning in het buitenland (vakantiewoning Spanje, ski-appartement Oostenrijk, etc.)  
- Verhuurde woning in Nederland  
- Verhuurde woning in het buitenland  
- Garage of parkeerplaats die los van eigen woning is gekocht  
- Grond (bouwgrond, landbouwgrond, natuurgrond)  
- Recreatiewoning op recreatiepark  
- Bedrijfspand dat privé wordt gehouden (niet zakelijk in eigen onderneming)  
- Aandeel in onverdeelde eigendom (bijv. erfenis nog niet verdeeld)  
- Recht van vruchtgebruik of erfpacht op vastgoed  
- Overige onroerende zaken

### Waardering per type

Welke waarde gebruik je voor box 3? Dit verschilt per type vastgoed.

**Nederlandse 2e woning (niet-verhuurd):** WOZ-waarde van het belastingjaar zelf. Voor belastingjaar 2026 dus de WOZ-waarde 2026, die gebaseerd is op waardepeildatum 1 januari 2025\. De gemeente verstuurt deze WOZ-beschikking begin van het jaar.

**Nederlandse verhuurde woning:** WOZ-waarde × leegwaarderatio. De leegwaarderatio is een percentage dat de Belastingdienst publiceert op basis van de jaarhuur ten opzichte van de WOZ-waarde. Door deze ratio wordt de waarde van een verhuurde woning lager gewaardeerd, omdat een verhuurde woning in de markt minder waard is dan een leeg pand.

Waarde\_verhuurd \= WOZ × leegwaarderatio

De leegwaarderatio staat in een door de Belastingdienst gepubliceerde tabel. Voorbeeld waardes (controleer voor productie de actuele tabel):

| Jaarhuur / WOZ-waarde | Leegwaarderatio (verhuurd op peildatum) |
| :---- | :---- |
| ≤ 1,0% | 73% |
| 1,0% – 2,0% | 79% |
| 2,0% – 3,0% | 84% |
| 3,0% – 4,0% | 90% |
| 4,0% – 5,0% | 95% |
| \> 5,0% | 100% |

Voor tijdelijke verhuur (korte termijn, Airbnb-achtig) gelden andere regels — meestal wordt de WOZ volledig gehanteerd. Sla daarom de `verhuur_type` op (`permanent`, `tijdelijk`, `geen`).

**Buitenlands vastgoed:** **WEV (Waarde in het Economisch Verkeer)**. Dit is de marktwaarde — wat de woning zou opleveren bij verkoop onder normale omstandigheden. Geen Nederlandse WOZ-beschikking beschikbaar. De gebruiker moet zelf de waarde inschatten op basis van:

- Vergelijkbare woningen in de regio (Spaanse Idealista, Franse SeLoger, etc.)  
- Officiële taxatierapporten (verplicht bij financiering, soms beschikbaar)  
- Buitenlandse vastgoedbelasting-waardes (zoals Spaanse "valor catastral", al is die meestal lager dan WEV)

Sla op: `waardering_methode` en `waardering_bron` zodat bij een latere controle duidelijk is hoe de waarde is bepaald.

**Grond en parkeerplaats:** in Nederland WOZ-waarde (als die wordt afgegeven), anders WEV. Bij landbouwgrond geldt soms een lagere "agrarische waarde" — dat is een specialistische berekening die voor Vermogenspeil te ver gaat; verwijs naar fiscalist.

**Recht van vruchtgebruik of erfpacht:** complex. De vruchtgebruiker waardeert het recht (waarde gebruik gedurende levensverwachting), de blote eigenaar waardeert de blote eigendom. De Belastingdienst publiceert tabellen voor de berekening. Voor Vermogenspeil fase 1: behandel als handmatige WEV-invoer met disclaimer ("verwijs naar fiscalist voor exacte waardering").

### Buitenlands vastgoed: voorkoming dubbele belasting

Buitenlands vastgoed hoort wél in box 3 — het wereldwijde vermogen telt mee — maar Nederland heeft belastingverdragen waarin staat dat onroerend goed wordt belast in het land waar het ligt. Het effect:

1. De waarde wordt **wel** opgenomen in de rendementsgrondslag (`O` in de forfait-berekening).  
2. Het draagt **wel** bij aan de berekening van het aandeel-percentage (stap 4 hoofdstuk 10).  
3. Maar er wordt een **aftrek voorkoming dubbele belasting** verleend zodat de gebruiker over het buitenlandse deel netto geen Nederlandse box 3-belasting betaalt.

De aftrek wordt berekend als:

Aftrek\_dubbele\_belasting \= (Waarde\_buitenlands\_vastgoed / Rendementsgrondslag) × Belasting\_forfaitair

Concreet voorbeeld:

- Iemand heeft € 100.000 spaargeld, € 200.000 NL 2e woning, € 150.000 Spaanse vakantiewoning.  
- Forfaitaire belasting volgens hoofdstuk 10: € 4.000.  
- Rendementsgrondslag: € 450.000.  
- Aftrek: (150.000 / 450.000) × 4.000 \= **€ 1.333**.  
- Netto verschuldigd: 4.000 − 1.333 \= **€ 2.667**.

**Belangrijk:** de gebruiker moet ook in het buitenland aangifte doen en daar mogelijk vastgoedbelasting betalen (Spaanse IBI, Franse taxe foncière, etc.). Vermogenspeil rekent dat niet door — het toont alleen de Nederlandse positie. Voeg een UI-disclaimer toe: *"Voor de belasting in {land} wordt verwezen naar een lokale fiscalist."*

### Hypotheken en schulden op vastgoed

Een hypotheek op een 2e woning of verhuurde woning hoort in box 3 (niet in box 1, want daar hoort alleen de eigen-woning-hypotheek). De schuld wordt meegeteld in `S` (zie hoofdstuk 8).

Belangrijk: de hypotheek en het vastgoed worden **apart** opgegeven. Niet als nettowaarde. Reden: vastgoed valt onder de hoge categorie (6,00%), schuld onder een lagere categorie (2,70%). Salderen zou de berekening verkeerd maken.

Sla in de `debts`\-tabel het veld `linked_real_estate_id` (UUID, nullable) op, zodat de UI kan tonen welke hypotheek bij welk pand hoort. Dit is alleen voor weergave; de berekening trekt de schuld niet specifiek af van het pand.

### Huurinkomsten

Alleen relevant bij verhuurde woningen. Sla per pand op: `huurinkomsten_ytd` (cumulatief over het jaar) en optioneel een tabel `rental_periods` met details (huurder, periode, bedrag) voor audit-trail.

**Voor forfait (hoofdstuk 10):** huurinkomsten spelen geen rol. Het forfaitaire stelsel kijkt alleen naar de waarde van het pand, niet naar de feitelijke inkomsten.

**Voor werkelijk rendement (hoofdstuk 12):** huurinkomsten tellen als regulier voordeel (`HUUR` in de formule). Bruto-bedragen, dus voor aftrek van eventuele buitenlandse bronbelasting.

### Bijtelling eigen gebruik (vanaf 2026\)

Sinds belastingjaar 2026 geldt een bijtelling voor eigen gebruik van onroerende zaken in box 3\. Dit is alleen relevant voor de **werkelijke-rendement-berekening**, niet voor forfait. Volledige formule en methodes staan in hoofdstuk 12 (werkelijk rendement). Hier wat per-pand wordt opgeslagen voor die berekening:

- `eigen_gebruik_methode`: `huurwaarde` (Methode A) of `woz_vast` (Methode B)  
- `economische_huurwaarde_per_jaar`: voor Methode A, in EUR  
- `woz_vorig_jaar`: voor Methode B (WOZ met waardepeildatum 1-1 van vorig jaar)  
- `verhuur_dagen_ytd`: aantal dagen verhuurd dit jaar  
- `verbouw_dagen_ytd`: aantal dagen in verbouwing (onbruikbaar voor eigen gebruik)  
- `eigen_gebruik_dagen = 365 − verhuur_dagen − verbouw_dagen` (afgeleid, niet apart opslaan)

**Buitenlands vastgoed en bijtelling:** ook hierop is de bijtelling van toepassing. Maar omdat de aftrek voorkoming dubbele belasting (zie hierboven) het netto-effect neutraliseert, is het in de praktijk een nul-som operatie. Wel correct meenemen in de berekening voor consistentie en transparantie.

### WOZ-verhogende investeringen

Investeringen die de WOZ-waarde aantoonbaar verhogen (aanbouw, gebouwgebonden verbouwing, energielabel-upgrade voor zover WOZ-relevant) zijn aftrekbaar voor werkelijk rendement — **maar alleen als ze bij de gemeente zijn gemeld**. Zonder melding gaat de Belastingdienst ervan uit dat de WOZ-stijging marktwerking is.

Sla op in de `real_estate_costs`\-tabel:

- `cost_type = 'woz_verhogend'`  
- `woz_increasing = true`  
- `gemeente_gemeld = true | false` (cruciaal voor aftrekbaarheid)  
- `factuur_referentie` (voor audit)

Voor de werkelijk-rendement-formule: alleen meenemen als `gemeente_gemeld = true`. Anders 0\. In de UI: vraag de gebruiker expliciet of de melding is gedaan.

### Overige vastgoedkosten (niet aftrekbaar in fase 1\)

De volgende kosten worden opgeslagen voor weergave en toekomstige fase 2-berekening, maar zijn **niet aftrekbaar** in fase 1:

- Klein onderhoud (schilderwerk, reparaties)  
- Groot onderhoud niet WOZ-verhogend (dakvervanging zonder uitbreiding)  
- Verzekering opstal  
- VvE-bijdragen (voor zover niet WOZ-verhogend)  
- OZB en andere gemeentelijke heffingen (riool, waterschap)  
- Beheerkosten verhuurde woning (vastgoedbeheerder)  
- Afsluitkosten hypotheek

Allemaal in `real_estate_costs` met passende `cost_type`. Vermogenspeil toont ze in de UI bij "totale kosten 2e woning dit jaar" voor transparantie, maar verrekent ze niet in werkelijk rendement.

### Verkoop van vastgoed

Onder huidige fase 1-regels (forfaitair \+ tegenbewijsregeling) heeft een verkoop geen directe fiscale gevolgen voor box 3 — er is geen vermogenswinstbelasting. Wel:

- Op de peildatum 1-1 van het volgende jaar staat het pand niet meer op de balans (de waarde komt nu als cash op een bankrekening of als nieuwe aankoop).  
- Voor werkelijk rendement van het jaar van verkoop: waardestijging \= verkoopopbrengst − WOZ\_1jan (of beginwaarde), geen aftrek transactiekosten.

**Vooruitblik fase 2 (vanaf 2028):** vastgoed valt straks onder vermogenswinstbelasting (niet vermogensaanwas zoals beleggingen). Waardestijging wordt pas belast bij verkoop. Sla daarom in fase 1 al netjes aankoopdatum, aankoopprijs en alle WOZ-verhogende investeringen op — die vormen straks de "kostprijs" voor vermogenswinstberekening.

### Aankoopdatum, aankoopprijs en metadata

Voor compleetheid (audit, fase 2-voorbereiding) sla per pand op:

- `aankoopdatum`: wanneer gekocht  
- `aankoopprijs`: koopsom (excl. kosten koper)  
- `aankoopkosten`: notaris, overdrachtsbelasting, makelaar, taxatie (voor fase 2-kostprijs)  
- `verkoopdatum`, `verkoopprijs`, `verkoopkosten`: bij verkoop later

Plus identificatie:

- `adres_straat`, `adres_huisnummer`, `adres_postcode`, `adres_plaats`, `adres_land`  
- `kadaster_referentie` (voor NL-vastgoed)  
- `oppervlakte_m2`  
- `gebruiksvorm`: `2e_woning_eigen_gebruik`, `verhuur_permanent`, `verhuur_tijdelijk`, `gemengd`, `grond`, `garage`, `recreatie`, `bedrijfspand_prive`, `overig`  
- `eigendomsdeel_pct`: aandeel in eigendom (100% als alleenzelfheid, 50% bij gezamenlijke aanschaf met niet-fiscaal-partner, etc.)

Bij `eigendomsdeel_pct < 100`: het pand wordt naar rato meegenomen in de berekening. Een woning van € 400.000 waar de gebruiker 50% eigenaar van is, telt voor € 200.000 in `O`. Voor fiscaal partners is dit niet relevant (samen 100%); voor anderen wel.

### Validatie en UI-volgorde

De gebruiker moet bij toevoeging van een pand een minimaal aantal velden invoeren. Verplicht:

1. Type en gebruiksvorm  
2. Adres (in elk geval land en stad)  
3. WOZ-waarde of WEV per peildatum  
4. Aankoopdatum en aankoopprijs (voor fase 2-voorbereiding; bij oud bezit mag een schatting met disclaimer)  
5. Eigendomsdeel %

Optioneel maar sterk aanbevolen:

- Hypotheek-koppeling  
- Huurinkomsten (alleen bij verhuurde panden)  
- Bijtelling-methode (alleen bij eigen gebruik vanaf 2026\)  
- Kosten-administratie

Voor buitenlands vastgoed extra:

- Waarderingsmethode en bron  
- Buitenlandse vastgoedbelasting betaald (informatief, voor UI-overzicht)

### Database-velden voor vastgoed

De volledige `real_estate`\-tabel ziet er als volgt uit (uitbreiding van wat in hoofdstuk 16 staat):

real\_estate (

    id UUID PRIMARY KEY,

    user\_id UUID,

    \-- type en gebruik

    type VARCHAR(30),                       \-- 2e\_woning/verhuurde\_woning/grond/garage/recreatie/bedrijfspand/vruchtgebruik/erfpacht/overig

    gebruiksvorm VARCHAR(30),               \-- eigen\_gebruik/verhuur\_permanent/verhuur\_tijdelijk/gemengd/leegstand

    verhuur\_type VARCHAR(20),               \-- permanent/tijdelijk/geen

    eigendomsdeel\_pct DECIMAL(5,2) DEFAULT 100,

    \-- adres en identificatie

    adres\_straat VARCHAR(100),

    adres\_huisnummer VARCHAR(20),

    adres\_postcode VARCHAR(10),

    adres\_plaats VARCHAR(50),

    adres\_land VARCHAR(50),

    kadaster\_referentie VARCHAR(50),        \-- alleen NL

    oppervlakte\_m2 INT,

    beschrijving TEXT,

    \-- waardering

    woz\_peildatum DECIMAL(14,2),            \-- WOZ-waarde voor huidig belastingjaar (NL)

    peildatum DATE,

    woz\_vorig\_jaar DECIMAL(14,2),           \-- voor bijtelling Methode B

    wev\_peildatum DECIMAL(14,2),            \-- voor buitenlands vastgoed: Waarde Economisch Verkeer

    waardering\_methode VARCHAR(30),         \-- WOZ/WEV/leegwaarderatio/taxatie

    waardering\_bron VARCHAR(200),           \-- toelichting hoe waarde is bepaald

    leegwaarderatio\_pct DECIMAL(5,2),       \-- voor verhuurde NL-woningen

    \-- aankoop (voor fase 2-voorbereiding en audit)

    aankoopdatum DATE,

    aankoopprijs DECIMAL(14,2),

    aankoopkosten DECIMAL(12,2),            \-- notaris/overdracht/makelaar/taxatie

    verkoopdatum DATE,

    verkoopprijs DECIMAL(14,2),

    verkoopkosten DECIMAL(12,2),

    \-- inkomsten

    huurinkomsten\_ytd DECIMAL(12,2),

    \-- bijtelling eigen gebruik (vanaf 2026\)

    eigen\_gebruik\_methode VARCHAR(10),      \-- huurwaarde/woz\_vast

    economische\_huurwaarde\_per\_jaar DECIMAL(12,2),

    verhuur\_dagen\_ytd INT DEFAULT 0,

    verbouw\_dagen\_ytd INT DEFAULT 0,

    \-- WOZ-verhogende investeringen

    woz\_verhogende\_investering\_ytd DECIMAL(12,2) DEFAULT 0,

    investering\_gemeld\_bij\_gemeente BOOLEAN DEFAULT false,

    \-- buitenland

    buitenlandse\_vastgoedbelasting\_ytd DECIMAL(12,2) DEFAULT 0,   \-- informatief

    voorkoming\_dubbele\_belasting\_van\_toepassing BOOLEAN DEFAULT false,

    created\_at TIMESTAMP,

    updated\_at TIMESTAMP

)

rental\_periods (

    id UUID PRIMARY KEY,

    real\_estate\_id UUID REFERENCES real\_estate(id),

    tenant\_name VARCHAR(100),

    period\_start DATE,

    period\_end DATE,

    rent\_per\_month DECIMAL(10,2),

    total\_received\_eur DECIMAL(12,2),

    currency CHAR(3),

    note TEXT

)

### Volledig voorbeeld

Iemand bezit:

- 100% eigenaar 2e woning in Drenthe, WOZ 2026 € 280.000, hypotheek € 120.000, eigen gebruik 200 dagen/jaar  
- 50% eigenaar verhuurde woning in Amsterdam met fiscaal partner. WOZ 2026 € 450.000. Jaarhuur € 14.400 (3,2% van WOZ → leegwaarderatio 90%)  
- 100% eigenaar vakantiewoning in Spanje, WEV € 200.000 (op basis van Idealista-vergelijking), geen hypotheek

Voor de berekening:

**Drenthe (NL 2e woning, eigen gebruik):**

- Waarde in `O`: € 280.000  
- Hypotheek in `S`: € 120.000  
- Bijtelling werkelijk rendement (vanaf 2026):  
  - Methode B: 0,0506 × 280.000 × (200/365) \= € 7.760  
- WOZ-verhogende investeringen 2026: € 0

**Amsterdam (verhuurde woning, fiscaal partner-deel):**

- Volledige waarde: 450.000 × 90% \= € 405.000  
- Eigen deel (50%): € 202.500 in `O`  
- Hypotheek niet in scenario  
- Huurinkomsten eigen deel: € 7.200 in `HUUR` (helft van € 14.400)  
- Geen bijtelling (verhuurd permanent)

**Spanje (buitenland 2e woning, eigen gebruik):**

- Waarde in `O`: € 200.000  
- Bijtelling werkelijk rendement: pro-rata zoals NL, maar voor het rendement  
- Voorkoming dubbele belasting van toepassing op € 200.000

**Forfaitaire berekening:**

- B \= 0 (geen spaargeld in dit voorbeeld)  
- O \= 280.000 \+ 202.500 \+ 200.000 \= € 682.500  
- S \= 120.000

Doorrekening via stappen hoofdstuk 10\. Daarna toepassen aftrek voorkoming dubbele belasting voor het Spaanse deel.

---

## 10\. De forfaitaire belasting berekenen

Dit is het hart van fase 1\. De Belastingdienst gebruikt een specifieke methode in zes stappen. Het is **niet** een kwestie van "vermogen min heffingsvrij maal tarief". Het is rendement-eerst, daarna een breuk-correctie.

Pak deze methode letterlijk over, ook al lijkt het omslachtig. Hij is zo opgebouwd zodat de tussenwaarden in de UI overeenkomen met wat de Belastingdienst in zijn eigen rekenvoorbeelden toont.

### De zes stappen — in gewone taal

**Stap 1 — Rendement per categorie.** Vermenigvuldig:

- De banktegoeden met het bank-percentage (2026: 1,28%)  
- De overige bezittingen met het overige-percentage (2026: 6,00%)  
- De aftrekbare schulden met het schulden-percentage (2026: 2,70%)

Tel die op: bank-rendement plus overige-rendement, **min** schulden-rendement. Resultaat: het belastbare rendement.

**Stap 2 — Rendementsgrondslag.** Tel banktegoeden en overige bezittingen op, en trek de aftrekbare schulden eraf.

**Stap 3 — Grondslag sparen en beleggen.** Trek het heffingsvrij vermogen van de rendementsgrondslag af (2026: € 59.357 per persoon, dubbel met partner). Resultaat: GSB. Als negatief: zet op nul, geen belasting.

**Stap 4 — Het aandeel.** Deel GSB door rendementsgrondslag, maal 100, rond af op 2 decimalen.

**Stap 5 — Voordeel uit sparen en beleggen.** Belastbaar rendement uit stap 1 maal het aandeel-percentage uit stap 4, gedeeld door 100\.

**Stap 6 — Belasting.** Voordeel maal 36%, afgerond op hele euro's.

**Stap 7 — Aftrek voorkoming dubbele belasting (alleen bij buitenlands vastgoed).** Als de gebruiker buitenlands vastgoed bezit (zie hoofdstuk 9), wordt een aftrek toegepast zodat het buitenlandse deel feitelijk geen Nederlandse box 3-belasting kost. De aftrek wordt berekend door het aandeel van het buitenlandse vastgoed in de rendementsgrondslag te vermenigvuldigen met de berekende belasting. Resultaat: netto te betalen Nederlandse box 3-belasting.

### De zes stappen — formules

Inputs:

B   \= totaal banktegoeden op peildatum (uit hoofdstuk 7\)

O   \= totaal overige bezittingen op peildatum

S   \= totaal box 3-schulden op peildatum

PB, PO, PS, T, HF, SD \= parameters voor het belastingjaar (zie hoofdstuk 2\)

Voorbereiding bij fiscaal partner:

als heeft\_partner:

    HF ← 2 × HF

    SD ← 2 × SD

**Stap 1: Belastbaar rendement (R)**

Saf  \= max(0, S − SD)

Rb   \= B × PB

Ro   \= O × PO

Rs   \= Saf × PS

R    \= Rb \+ Ro − Rs

**Stap 2: Rendementsgrondslag (RG)**

RG \= B \+ O − Saf

**Stap 3: Grondslag sparen en beleggen (GSB)**

GSB \= max(0, RG − HF)

als GSB \== 0:

    Belasting \= 0  → stop

**Stap 4: Aandeel-percentage (A)**

A \= round((GSB / RG) × 100, 2\)     (in procenten, 2 decimalen)

**Stap 5: Voordeel uit sparen en beleggen (V)**

V \= R × A / 100

**Stap 6: Verschuldigde belasting**

Belasting \= round(V × T, 0\)        (afronden op hele euro's)

**Stap 7: Aftrek voorkoming dubbele belasting (alleen bij buitenlands vastgoed)**

O\_buitenland   \= som waarde van vastgoed in buitenland (per pand)

Aftrek\_dub\_bel \= round((O\_buitenland / RG) × Belasting, 0\)

Belasting\_netto \= max(0, Belasting − Aftrek\_dub\_bel)

Bij geen buitenlands vastgoed: `Aftrek_dub_bel = 0` en `Belasting_netto = Belasting`. De UI moet zowel het bruto-bedrag (vóór aftrek) als netto-bedrag tonen, met toelichting.

### Volledig uitgewerkt voorbeeld (zonder partner, 2026\)

Iemand heeft:

- € 150.000 op een spaarrekening (B)  
- € 75.000 aan beleggingen (deel van O)  
- € 200.000 aan een 2e woning op WOZ-waarde (deel van O)  
- € 100.000 hypotheekschuld op die 2e woning (S)

Dus: `B = 150.000`, `O = 275.000`, `S = 100.000`.

| Stap | Berekening | Resultaat |
| :---- | :---- | :---- |
| Stap 1a | `Saf = max(0, 100.000 − 3.800)` | € 96.200 |
| Stap 1b | `Rb = 150.000 × 0,0128` | € 1.920 |
| Stap 1c | `Ro = 275.000 × 0,0600` | € 16.500 |
| Stap 1d | `Rs = 96.200 × 0,0270` | € 2.597 |
| Stap 1e | `R = 1.920 + 16.500 − 2.597` | **€ 15.823** |
| Stap 2 | `RG = 150.000 + 275.000 − 96.200` | **€ 328.800** |
| Stap 3 | `GSB = max(0, 328.800 − 59.357)` | **€ 269.443** |
| Stap 4 | `A = round(269.443 / 328.800 × 100, 2)` | **81,94%** |
| Stap 5 | `V = 15.823 × 81,94 / 100` | **€ 12.965** |
| Stap 6 | `Belasting = round(12.965 × 0,36, 0)` | **€ 4.667** |

Dit getal — € 4.667 — is identiek aan het officiële Belastingdienst-rekenvoorbeeld voor dit scenario. **Gebruik deze case als unit-test in je codebase**: als je implementatie hier niet exact € 4.667 uitspuugt, klopt er iets niet.

### Voorbeeld met fiscale partner

Zelfde bezittingen en schulden, maar nu met fiscale partner:

HF ← 2 × 59.357 \= 118.714

SD ← 2 × 3.800 \= 7.600

| Stap | Berekening | Resultaat |
| :---- | :---- | :---- |
| Stap 1a | `Saf = max(0, 100.000 − 7.600)` | € 92.400 |
| Stap 1b | `Rb = 150.000 × 0,0128` | € 1.920 |
| Stap 1c | `Ro = 275.000 × 0,0600` | € 16.500 |
| Stap 1d | `Rs = 92.400 × 0,0270` | € 2.495 |
| Stap 1e | `R = 1.920 + 16.500 − 2.495` | **€ 15.925** |
| Stap 2 | `RG = 150.000 + 275.000 − 92.400` | **€ 332.600** |
| Stap 3 | `GSB = max(0, 332.600 − 118.714)` | **€ 213.886** |

In de aangifte mogen partners de GSB onderling verdelen — vrije keuze mits totaal 100%. Bij 50/50:

GSB\_per\_partner \= 213.886 / 2 \= 106.943

A\_per\_partner   \= round(106.943 / 332.600 × 100, 2\) \= 32,15%

V\_per\_partner   \= 15.925 × 32,15 / 100 \= 5.119

Belasting\_per   \= round(5.119 × 0,36, 0\) \= € 1.842

Totaal huishouden \= 2 × 1.842 \= € 3.684

Dit komt overeen met het Belastingdienst-voorbeeld. Tweede unit-test.

### Verdeling tussen partners — design-keuze

De Belastingdienst staat elke verdeling toe (50/50, 100/0, 30/70, wat dan ook), zolang totaal 100%. Voor MVP: ga uit van 50/50. Voor Premium-uitbreiding: laat de gebruiker zelf kiezen, of optimaliseer automatisch op basis van bijvoorbeeld heffingskortingen.

### Wat de berekening moet teruggeven

Voor de UI heb je een complete uitsplitsing nodig. Bewaar in elk geval:

- De inputs (B, O, S)  
- Alle tussenwaarden van de zes stappen (Saf, Rb, Ro, Rs, R, RG, GSB, A, V)  
- Het eindresultaat (Belasting)  
- Welke parameters gebruikt zijn (PB, PO, PS, T, HF, SD)  
- Het effectieve tarief: `Belasting / (B + O)` — als informatie voor de gebruiker

---

## 11\. Welk belastingjaar moet ik tonen

### Regel in gewone taal

Vóór 1 mei toon je het vorige belastingjaar (waarover nog aangifte gedaan kan worden). Vanaf 1 mei wissel je naar het lopende belastingjaar.

### Formule

Voor huidige datum d (in timezone Europe/Amsterdam):

deadline \= 1 mei van het jaar waarin d valt

als d \< deadline:

    relevant\_belastingjaar \= jaar(d) − 1

anders:

    relevant\_belastingjaar \= jaar(d)

peildatum \= 1 januari van relevant\_belastingjaar

### Voorbeelden

| Datum (Europe/Amsterdam) | Relevant belastingjaar | Peildatum |
| :---- | :---- | :---- |
| 21 april 2026 | 2025 | 1-1-2025 |
| 30 april 2026 | 2025 | 1-1-2025 |
| 1 mei 2026 23:59 | 2025 | 1-1-2025 |
| 2 mei 2026 00:00 | 2026 | 1-1-2026 |
| 15 oktober 2026 | 2026 | 1-1-2026 |
| 2 mei 2027 | 2027 | 1-1-2027 |
| 2 mei 2028 | 2028 | 1-1-2028 (nieuwe wetgeving activeert) |

### Drie implementatie-eisen

**Timezone.** Doe deze vergelijking altijd in `Europe/Amsterdam`, niet in UTC. Anders wisselt het in de nacht van 30 april op 1 mei verkeerd.

**Caching.** Cache-sleutel moet het belastingjaar bevatten. Anders blijft een verouderd bedrag staan op 2 mei.

**Test-modus.** Bouw een config-flag (bijvoorbeeld `VIRTUAL_DATE`) waarmee de developer in staging een fictieve datum kan instellen. In productie staat die altijd uit.

---

## 12\. Het werkelijke rendement berekenen

Dit is een Premium-feature. Sinds 19 juli 2025 mag iemand via de Wet tegenbewijsregeling box 3 aantonen dat zijn werkelijke rendement lager was dan het forfait — als dat zo is, gebruikt de Belastingdienst automatisch het lagere bedrag.

### Zes kernregels

**Regel 1: Kosten zijn NIET aftrekbaar.** Aan- en verkoopkosten van beleggingen, beheerfees, custody-kosten, onderhoudskosten van een 2e woning — geen daarvan tel je af. Bron: Belastingdienst, "Wat is mijn werkelijk rendement?".

**Regel 2: Twee uitzonderingen op regel 1:**

- Rente betaald op box 3-schulden.  
- WOZ-verhogende investeringen in 2e woning, mits gemeld bij gemeente.

**Regel 3: Geen heffingsvrij vermogen.** Bij werkelijk rendement vervalt de vrijstelling van € 59.357 volledig.

**Regel 4: Heel jaar, niet alleen 1 januari.** Werkelijk rendement gaat over alle vermogen tijdens het jaar — beleggingen aangekocht in maart tellen mee vanaf de aankoop.

**Regel 5: Nominaal.** Geen inflatie-correctie.

**Regel 6: Negatief totaal wordt nul.** Verliezen verrekenen met winsten binnen het jaar; als totaal negatief, zet op nul. Geen verrekening met andere jaren.

### Formule werkelijk rendement (over heel jaar)

Definities:

DIV    \= som ontvangen dividenden (bruto, vóór dividendbelasting) over heel jaar

RNT\_b  \= som ontvangen rente op banktegoeden over heel jaar

HUUR   \= som huurinkomsten 2e woning over heel jaar

STK    \= som staking-rewards, gewaardeerd tegen marktprijs op moment ontvangst

INK    \= som overige periodieke inkomsten

W\_eind \= portfoliowaarde op 31 december

W\_start \= portfoliowaarde op 1 januari (uit snapshot)

NI     \= netto inleg tijdens jaar \= som stortingen − som onttrekkingen

BIJT   \= bijtelling eigen gebruik 2e woning (zie 11.2)  \-- alleen vanaf 2026

RNT\_s  \= som betaalde rente op box 3-schulden over heel jaar

INV\_woz \= WOZ-verhogende investering 2e woning (alleen als gemeld bij gemeente)

**Reguliere voordelen:**

Reg \= DIV \+ RNT\_b \+ HUUR \+ STK \+ INK

**Waardemutatie:**

WM \= (W\_eind − W\_start) − NI

**Belangrijk:** `W_start` en `W_eind` zijn de ruwe marktwaardes (hoeveelheid × koers), níet de cost basis. De cost basis bevat transactiekosten, en die mogen niet meetellen in de waardemutatie — anders trek je impliciet kosten af terwijl dat fiscaal niet mag. Zie hoofdstuk 3.5 voor de volledige kostenbehandeling.

**Dividend dat in het portfolio blijft (DRIP) telt mee als storting `NI`** om dubbeltelling te voorkomen. Het bedrag staat al in `Reg` als direct rendement; in `W_eind` zit het ook (want het is herbelegd); daarom moet het ook in `NI` om de waardemutatie correct te maken.

**Werkelijk rendement:**

WR \= Reg \+ WM \+ BIJT − RNT\_s − INV\_woz

**Negatief totaal wordt nul:**

WR\_belastbaar \= max(0, WR)

### Bijtelling eigen gebruik 2e woning (vanaf 2026\)

De gebruiker kiest een van twee methodes per onroerende zaak.

**Methode A — economische huurwaarde:**

BIJT\_A \= HW\_jaar × (D\_eigen / 365\)

Waarbij:

- `HW_jaar` \= jaarlijkse economische huurwaarde (via huurcommissie.nl Huurprijscheck of vergelijking)  
- `D_eigen` \= aantal dagen dat de woning beschikbaar was voor eigen gebruik

**Methode B — vast percentage WOZ:**

BIJT\_B \= 0,0506 × WOZ\_vorig × (D\_eigen / 365\)

Waarbij:

- `WOZ_vorig` \= WOZ-waarde met waardepeildatum 1-1 van vorig jaar (voor 2026: WOZ-waarde 1-1-2025)  
- `D_eigen` \= aantal dagen dat de woning beschikbaar was voor eigen gebruik

**Eigen-gebruik-dagen:**

D\_eigen \= 365 − D\_verhuur − D\_verbouw

Het gaat om dagen dat de gebruiker de woning **kan** gebruiken. Dagen dat verhuurd of in verbouwing (en daardoor onbruikbaar) tellen niet mee.

### YTD-berekening (tussentijds, indicatief)

Voor de tussentijdse display in de UI: vervang `W_eind` door huidige portfoliowaarde, en alle `_over heel jaar`\-sommen door YTD-sommen vanaf 1-1 t/m vandaag. Bijtelling pro-rata berekenen voor het deel van het jaar dat al voorbij is.

**Markeer altijd als "Voorlopige berekening, definitief op 31-12-{jaar}"** in de UI.

### Voorbeeld

Iemand begint 2026 met (en eindigt op):

- € 50.000 spaargeld → € 50.000 (rente staat apart, geen waardemutatie op spaargeld)  
- € 30.000 aandelen → € 28.000, kreeg € 600 dividend  
- € 10.000 crypto → € 14.000  
- Kocht in mei € 5.000 bij in andere aandeel → eindigt op € 5.300

Heeft € 20.000 schuld, betaalde € 540 rente. Ontvangen rente spaargeld: € 500\.

W\_start \= 50.000 \+ 30.000 \+ 10.000 \= € 90.000

W\_eind  \= 50.000 \+ 28.000 \+ 14.000 \+ 5.300 \= € 97.300

NI      \= 5.000 (bijgekocht aandeel in mei)

WM      \= (97.300 − 90.000) − 5.000 \= € 2.300

DIV     \= 600

RNT\_b   \= 500

Reg     \= 600 \+ 500 \= 1.100

RNT\_s   \= 540

BIJT    \= 0 (geen 2e woning)

INV\_woz \= 0

WR \= Reg \+ WM \+ BIJT − RNT\_s − INV\_woz

WR \= 1.100 \+ 2.300 \+ 0 − 540 − 0 \= € 2.860

WR\_belastbaar \= max(0, 2.860) \= € 2.860

### Werkelijk rendement als percentage (voor UI)

Voor de vergelijkingskaart wil je ook een percentage tonen.

**MVP-formule (simpele middeling):**

W\_gem \= (W\_start \+ W\_eind) / 2

WR\_pct \= WR / W\_gem

Label de UI met "indicatieve berekening" — dit middelt geen tussentijdse cashflows.

**Volledige formule (latere uitbreiding, tijdgewogen):** Verdeel het jaar in subperiodes op datums waar de portfoliowaarde significant verandert door een cashflow (storting/onttrekking \> 5% van waarde op dat moment). Bereken de gemiddelde waarde per subperiode `((Vs + Ve) / 2)` en weeg met de duur in dagen. De volledige formule:

Voor subperiodes 1...n, met start-waarde Vs\_i, eindwaarde Ve\_i, duur d\_i:

W\_gem \= Σ ( ((Vs\_i \+ Ve\_i) / 2\) × (d\_i / d\_totaal) )

### Architectonisch: de fees blijven nodig

Het feit dat kosten **niet** aftrekbaar zijn voor werkelijk rendement, betekent niet dat je het veld `fees_eur` op transacties mag weggooien. Je hebt het nodig voor:

- De cost-basis berekening (waar aankoopkosten meetellen).  
- De gerealiseerde-winst berekening (waar verkoopkosten van de opbrengst afgaan).  
- Toekomstige fase 2 en 3, waar deze kosten waarschijnlijk wél aftrekbaar worden.

In de werkelijk-rendement-formule gebruik je het veld dus niet — sla het wel op.

---

## 13\. Forfait vs. werkelijk vergelijken

### In gewone taal

De Belastingdienst gebruikt automatisch het laagste bedrag tussen forfaitaire en werkelijke belasting. In Vermogenspeil moet je beide kunnen tonen en het verschil markeren.

Een belangrijk inzicht: de vergelijking is niet zomaar "appels met appels". Bij forfait wordt het heffingsvrij vermogen verwerkt; bij werkelijk rendement vervalt het. Voor mensen met klein vermogen is werkelijk rendement bijna nooit voordelig. Pas bij groter vermogen of beleggingsverliezen wordt het aantrekkelijk. Toon altijd beide bedragen.

### Formules

Belasting\_forfait    \= uitkomst hoofdstuk 10 (Belasting)

Belasting\_werkelijk  \= round(WR\_belastbaar × T, 0\)

Besparing \= Belasting\_forfait − Belasting\_werkelijk

Voordelig \= Besparing \> 0

### UI-gedrag

- Als `Voordelig`: groene melding, "Werkelijk rendement opgeven kan € {Besparing} besparen."  
- Als niet: neutrale melding, "Forfait blijft het voordeligst voor jou dit jaar."  
- Vóór 31 december altijd: "Voorlopige berekening, definitief op 31-12-{jaar}."  
- Bij negatief werkelijk rendement: communiceer duidelijk dat de belasting nul wordt, geen teruggave.

### Wat het rapport moet bevatten

Als iemand werkelijk rendement wil opgeven (in aangifte of OWR-formulier voor oudere jaren), heeft hij onderbouwing nodig. Export:

- Beginwaarde portfolio per asset, op 1-1.  
- Eindwaarde portfolio per asset, op 31-12.  
- Alle stortingen en onttrekkingen met datum en bedrag.  
- Alle reguliere voordelen (dividend bruto, rente, huur, staking) met datum en bron.  
- Betaalde rente op box 3-schulden per schuld.  
- Bijtelling eigen gebruik 2e woning (vanaf 2026), met methode en eigen-gebruik-dagen.  
- WOZ-verhogende investeringen (alleen als gemeld bij gemeente).  
- Bronnen van waarderingen (broker-statements, koers-databronnen).

**Niet opnemen:** transactiekosten, beheerfees, custody-kosten, onderhoudskosten 2e woning.

---

## 14\. Omgaan met vreemde valuta

### Regels in gewone taal

- **Historische transactie:** wisselkoers op transactiedatum (broker-koers als beschikbaar, anders ECB).  
- **Huidige waardering:** dagkoers uit prijsdatabase.  
- **Peildatum-snapshot:** ECB-slotkoers van laatste handelsdag van voorgaand jaar (meestal 31 december).

### Formule omrekening

Voor elke bedrag X in valuta C op datum d:

  fx\_rate \= getEcbRate(C, d)

  X\_eur \= X / fx\_rate            (als ECB-koers uitgedrukt is als 1 EUR \= X C, bijv. EUR/USD \= 1,08)

**Let op de richting van de ECB-koers.** ECB publiceert wisselkoersen als "hoeveel vreemde valuta krijg je voor 1 EUR". USD \= 1,08 betekent: 1 EUR \= 1,08 USD. Om USD naar EUR om te rekenen, deel je dus door 1,08.

### ECB-koersen ophalen

ECB publiceert dagkoersen elke werkdag rond 16:00 Nederlandse tijd. Bouw een scheduled job die ze dagelijks ophaalt en in de `ecb_rates`\-tabel zet. Voor weekends/feestdagen: koers van de laatste werkdag ervoor.

Bron: ECB Statistical Data Warehouse, vrij toegankelijk via website of API.

function getEcbRate(currency, date):

    rate \= query ecb\_rates waar currency \= ? en rate\_date \= ?

    als rate is null:

        rate \= query ecb\_rates waar currency \= ? en rate\_date \< ?

                sorteer rate\_date DESC, limit 1

    return rate

---

## 15\. Edge cases

| \# | Situatie | Wat te doen |
| :---- | :---- | :---- |
| E1 | Gebruiker registreert in maart 2026 zonder historie | Snapshot 1-1-2026 reconstrueren uit ingevoerde transacties \+ historische koersen. Toon disclaimer "snapshot gebaseerd op X% van geïmporteerde data". |
| E2 | Gebruiker voegt later vergeten transactie van vóór peildatum toe | Snapshot herberekenen (mits niet gelockt). Oudere locked snapshots niet wijzigen. |
| E3 | Negatief portfolio (verlies \> inleg) | Belastbaar rendement kan negatief zijn, verschuldigde belasting heeft ondergrens van € 0\. |
| E4 | Werkelijk rendement hoger dan forfait | Forfait blijft voordeligst, niet aanbevelen werkelijk rendement op te geven. |
| E5 | Asset zonder koers op peildatum (illiquide, gedelist) | Gebruik laatst bekende koers vóór peildatum. Markeer als "indicatieve waardering". |
| E6 | Stortingsdatum is precies de peildatum | Conventie: storting per 1 januari telt mee in snapshot van 1 januari. Documenteer en test. |
| E7 | Fiscaal partner halverwege jaar gestart | Verdubbeling HF \+ SD geldt alleen als partnerschap op peildatum (1-1) bestond. |
| E8 | Verkoop voordat enige aankoop is geregistreerd | Hard error. Symptoom van ontbrekende CSV-historie. |
| E9 | Crypto airdrop / hard fork / staking-reward | Behandel als aankoop tegen marktprijs op moment ontvangst (verhoog C én Q). Registreer tegelijk als direct rendement voor werkelijk-rendement-spoor. Voor box 3-snapshot alleen relevant als positie op 1-1 nog gehouden. |
| E10 | Onttrekking groter dan bezitting | Hard error: wijst op ontbrekende aankoop-transactie. |
| E11 | Snapshot gelockt, transactie van vóór peildatum komt binnen | Transactie opslaan, snapshot ongewijzigd. Banner: "Niet meer meegenomen in aangifte {jaar}." |
| E12 | Banktegoed-saldo op peildatum onbekend | Snapshot toont waarschuwing. Belasting berekend met disclaimer "exclusief X banktegoeden". |
| E13 | Tarieven voor toekomstig belastingjaar nog niet vastgesteld | Geen berekening tonen, of duidelijk "indicatief"-label. |
| E14 | Groene beleggingen onder vrijstelling | Bedrag tot vrijstelling telt niet mee in `O`. Premium-feature, aparte invoer. |
| E15 | 2e woning met eigen gebruik (vanaf 2026\) | Bijtelling toepassen bij werkelijk rendement, zie 11.2. |
| E16 | Stock-dividend (bonusaandelen) | Alleen Q verhogen, C blijft gelijk. Geen rendement, geen direct rendement-registratie. De marktprijs daalt evenredig waardoor de cost basis per stuk klopt. |
| E17 | Transfer tussen platforms (zelfde gebruiker) | No-op voor cost basis (C en Q ongewijzigd). Wel registreren in transactietabel voor audit-trail. Niet als aankoop of verkoop behandelen — dat zou fictieve winst genereren. |
| E18 | Aandelensplitsing (stock split, bijv. 2-voor-1) | Net als stock-dividend: alleen Q verhogen volgens splitsing-ratio, C blijft gelijk. Bij omgekeerde splitsing: Q evenredig verlagen. |
| E19 | Ongematchte transfer-out (bijv. naar onbekend/onverbonden account) | Event krijgt status `unmatched`. Toon in review-flow. Gebruiker classificeert als: transfer naar eigen extern account, verkoop (P2P/OTC), of schenking/verlies. Tot bevestiging telt het event niet mee in cost basis. |
| E20 | Ongematchte transfer-in / onbekende deposit | Event krijgt status `unmatched`. Toon in review-flow. Gebruiker classificeert als: transfer vanuit eigen extern account (vraag aankoopdatum \+ prijs voor cost basis-reconstructie), aankoop buiten platform, of ontvangen schenking. |
| E21 | Bridge-transfer met grote fee (bijv. ETH → Polygon, ontvangen 0,98 ETH bij 1 ETH verstuurd) | Standaard matching-marge van 99% mist dit. Gebruiker handmatig koppelen via UI, of marge verruimen tot bijv. 95%. Verschil registreren als `bridge_fee`\-kosten (niet aftrekbaar voor werkelijk rendement). |
| E22 | Wrapped tokens (WETH ↔ ETH, WBTC ↔ BTC) | Standaard behandelen als één asset via asset-alias-configuratie. Wrap/unwrap-events zijn dan transfers tussen platforms, geen koop/verkoop. |
| E23 | Platform-naamswijziging in CSV-export tussen imports | Asset-symbool moet stabiel zijn ongeacht platform. Gebruik genormaliseerde symbolen (CoinGecko ID, ISIN voor effecten). Per platform een mapping-tabel die ruwe CSV-namen normaliseert. |

---

## 16\. Database-schets

tax\_parameters (

    tax\_year INT PRIMARY KEY,

    heffingsvrij\_bedrag DECIMAL(12,2),

    banktegoed\_pct DECIMAL(6,4),

    overige\_pct DECIMAL(6,4),

    schuld\_pct DECIMAL(6,4),

    schuld\_drempel DECIMAL(12,2),

    tarief\_pct DECIMAL(6,4),

    groene\_belegging\_vrijstelling DECIMAL(12,2),

    contant\_geld\_vrijstelling DECIMAL(12,2),

    bijtelling\_woz\_pct DECIMAL(6,4),

    banktegoed\_pct\_definitief BOOLEAN,

    schuld\_pct\_definitief BOOLEAN,

    bron\_url VARCHAR(255),

    geraadpleegd\_op DATE

)

transactions (

    id UUID PRIMARY KEY,

    user\_id UUID,

    platform VARCHAR(50),

    asset\_symbol VARCHAR(20),

    asset\_category VARCHAR(20),    \-- crypto/stock/etf/fund/metal/cash

    transaction\_date TIMESTAMP WITH TIME ZONE,

    type VARCHAR(30),               \-- buy/sell/dividend/staking\_reward/airdrop/stock\_dividend/stock\_split/transfer\_in/transfer\_out/gift\_in/gift\_out/loss/deposit/withdrawal/fee

    quantity DECIMAL(20,8),

    price\_original DECIMAL(20,8),

    currency CHAR(3),

    fx\_rate DECIMAL(14,6),           \-- ECB-koers (officieel)

    fx\_rate\_actual DECIMAL(14,6),    \-- werkelijk gebruikte koers door broker (incl. opslag)

    price\_eur DECIMAL(20,8),

    fees\_eur DECIMAL(12,2),          \-- expliciete transactiekosten

    implicit\_spread\_eur DECIMAL(12,2), \-- impliciete spread waar bekend (info, niet apart aftrekken)

    fx\_fee\_eur DECIMAL(12,2),        \-- impliciete currency-conversie-fee

    amount\_gross\_eur DECIMAL(14,2),  \-- voor dividend: bruto bedrag (voor werkelijk rendement)

    tax\_withheld\_eur DECIMAL(12,2),  \-- voor dividend: ingehouden dividendbelasting (verrekenbaar met IB)

    amount\_net\_eur DECIMAL(14,2),    \-- voor dividend: netto ontvangen bedrag (voor UI)

    related\_asset\_symbol VARCHAR(20),-- voor fee-transacties: aan welk asset/transfer gerelateerd

    status VARCHAR(40),              \-- confirmed/unmatched/matched/pending\_review/confirmed\_transfer/confirmed\_transfer\_with\_manual\_basis

    transfer\_pair\_id UUID NULL,      \-- gemeenschappelijke ID voor gekoppelde transfer-pairs

    note TEXT,

    source VARCHAR(20),              \-- api/csv/pdf/manual

    created\_at TIMESTAMP

)

transfer\_matches (

    pair\_id UUID PRIMARY KEY,

    user\_id UUID,

    out\_transaction\_id UUID REFERENCES transactions(id),

    in\_transaction\_id UUID REFERENCES transactions(id),

    network\_fee\_transaction\_id UUID NULL REFERENCES transactions(id),   \-- gekoppelde fee

    matched\_at TIMESTAMP,

    matched\_by VARCHAR(10),         \-- auto/manual

    time\_delta\_seconds INT,

    quantity\_delta DECIMAL(20,8)    \-- verschil tussen uitgaande en binnenkomende hoeveelheid (= netwerk-fee)

)

periodic\_costs (

    id UUID PRIMARY KEY,

    user\_id UUID,

    platform VARCHAR(50),

    cost\_type VARCHAR(40),           \-- custody/beheer/abonnement/inactiviteit/overig

    description VARCHAR(200),

    period\_start DATE,

    period\_end DATE,

    charged\_date DATE,

    amount\_eur DECIMAL(12,2),

    currency CHAR(3),

    fx\_rate DECIMAL(14,6),

    amount\_original DECIMAL(12,2),

    source VARCHAR(20),              \-- api/csv/pdf/manual

    note TEXT,

    created\_at TIMESTAMP

)

real\_estate\_costs (

    id UUID PRIMARY KEY,

    user\_id UUID,

    real\_estate\_id UUID REFERENCES real\_estate(id),

    cost\_type VARCHAR(40),           \-- onderhoud\_klein/onderhoud\_groot/woz\_verhogend/verzekering/vve/ozb/beheer\_verhuur/overig

    description VARCHAR(200),

    cost\_date DATE,

    amount\_eur DECIMAL(12,2),

    woz\_increasing BOOLEAN DEFAULT false,

    gemeente\_gemeld BOOLEAN DEFAULT false,

    factuur\_referentie VARCHAR(100),

    note TEXT,

    created\_at TIMESTAMP

)

holdings (

    \-- bestaande velden ...

    implicit\_ter\_pct DECIMAL(6,4),   \-- ETF management fee in NAV verwerkt (info, niet apart aftrekken)

    isin VARCHAR(12),                \-- voor effecten

    coingecko\_id VARCHAR(50)         \-- voor crypto, voor stabiele naamgeving

)

portfolio\_snapshots (

    id UUID PRIMARY KEY,

    user\_id UUID,

    snapshot\_date DATE,             \-- altijd 1 januari

    holdings\_json JSONB,

    bank\_deposits\_json JSONB,

    real\_estate\_json JSONB,

    debts\_json JSONB,

    total\_banktegoeden\_eur DECIMAL(14,2),

    total\_overige\_eur DECIMAL(14,2),

    total\_schulden\_eur DECIMAL(14,2),

    locked BOOLEAN DEFAULT false,

    generated\_at TIMESTAMP,

    UNIQUE (user\_id, snapshot\_date)

)

koers\_data (

    asset\_symbol VARCHAR(20),

    asset\_category VARCHAR(20),

    price\_date DATE,

    price\_eur DECIMAL(14,6),

    source VARCHAR(50),

    fetched\_at TIMESTAMP,

    PRIMARY KEY (asset\_symbol, price\_date)

)

ecb\_rates (

    currency CHAR(3),

    rate\_date DATE,

    rate DECIMAL(14,6),

    PRIMARY KEY (currency, rate\_date)

)

bank\_deposits (

    id UUID PRIMARY KEY,

    user\_id UUID,

    bank\_name VARCHAR(50),

    type VARCHAR(20),

    saldo\_peildatum DECIMAL(14,2),

    peildatum DATE,

    rente\_pct DECIMAL(6,4),

    received\_interest\_ytd DECIMAL(12,2),

    note TEXT

)

debts (

    id UUID PRIMARY KEY,

    user\_id UUID,

    type VARCHAR(50),

    openstaand\_peildatum DECIMAL(14,2),

    peildatum DATE,

    rente\_pct DECIMAL(6,4),

    rente\_betaald\_ytd DECIMAL(12,2),

    eerste\_schulddatum DATE,

    schuldeiser VARCHAR(100),

    linked\_real\_estate\_id UUID NULL,

    note TEXT

)

real\_estate (

    id UUID PRIMARY KEY,

    user\_id UUID,

    type VARCHAR(30),

    woz\_peildatum DECIMAL(14,2),

    peildatum DATE,

    woz\_vorig\_jaar DECIMAL(14,2),    \-- voor bijtelling methode B

    aankoopdatum DATE,

    aankoopprijs DECIMAL(14,2),

    adres\_straat VARCHAR(100),

    adres\_huisnummer VARCHAR(20),

    adres\_postcode VARCHAR(10),

    adres\_plaats VARCHAR(50),

    adres\_land VARCHAR(50),

    oppervlakte\_m2 INT,

    gebruiksvorm VARCHAR(30),

    huurinkomsten\_ytd DECIMAL(12,2),

    eigen\_gebruik\_methode VARCHAR(10),    \-- huurwaarde/woz\_vast

    economische\_huurwaarde\_per\_jaar DECIMAL(12,2),

    verhuur\_dagen\_ytd INT DEFAULT 0,

    verbouw\_dagen\_ytd INT DEFAULT 0,

    woz\_verhogende\_investering\_ytd DECIMAL(12,2) DEFAULT 0,

    investering\_gemeld\_bij\_gemeente BOOLEAN DEFAULT false,

    beschrijving TEXT

)

### Volgorde van berekeningen bij een verzoek

Als een gebruiker de Belastingpositie-pagina opent, doet het backend dit:

1. **Bepaal relevant belastingjaar** op basis van huidige datum (vóór/na 1 mei, zie hoofdstuk 11).  
2. **Haal snapshot op of genereer hem** voor peildatum van dat jaar.  
3. **Laad fiscale parameters** voor dat belastingjaar. Als ze nog niet bestaan: toon melding "tarieven nog niet vastgesteld".  
4. **Bereken forfaitaire belasting** volgens zes stappen van hoofdstuk 10\.  
5. **Voor Premium:** bereken werkelijk rendement volgens hoofdstuk 12\.  
6. **Vergelijk** forfait met werkelijk, bereken besparing.  
7. **Cache resultaat** met sleutel die belastingjaar én snapshot-tijdstempel bevat.

---

## 17\. Wat valt buiten fase 1

- **FIFO of LIFO toewijzing bij verkopen.** Pas relevant in fase 3\. Lot-niveau opslag wel een fase 1-architectuureis.  
- **Vermogensaanwasbelasting (hoofdregel vanaf 2028).** De Wet werkelijk rendement box 3 is op 12 februari 2026 aangenomen in de Tweede Kamer. Eerste Kamer-behandeling is uitgesteld tot mei 2026, waardoor de beoogde ingangsdatum 1 januari 2028 mogelijk doorschuift naar 1 januari 2029\. Hoofdregel: jaarlijkse belasting over werkelijk rendement (rente, dividend, huur, waardestijging incl. ongerealiseerd) tegen 36%, met een heffingsvrij rendement van € 1.800 per persoon. Voor banktegoeden, beleggingen en crypto wordt vermogensaanwas gehanteerd. Architectuur fase 1 moet hierop voorbereid zijn (lot-niveau opslag, kostenvelden, dividend-tracking).  
- **Vermogenswinstbelasting (uitzondering vanaf 2028).** Voor onroerende zaken en aandelen in innovatieve start-ups/scale-ups geldt vermogenswinst in plaats van vermogensaanwas: waardestijging pas belast bij verkoop. Architectuur moet onderscheid kunnen maken tussen vermogensaanwas-assets en vermogenswinst-assets.  
- **Algemene kostenaftrek (zeker vanaf fase 2).** Vanaf 2028 worden transactiekosten, beheerfees, custody-kosten en onderhoudskosten vastgoed wél aftrekbaar voor het werkelijke rendement. Uitzonderingen die níét aftrekbaar zijn: dividendbelasting, kosten voor congressen, vervoer, werkruimte, telefoonabonnementen. Belangrijke verandering t.o.v. fase 1: bewaar daarom in fase 1 al alle kostendata netjes per categorie (transactiekosten, beheerfees, onderhoud), ook al worden ze fiscaal nu nog niet gebruikt.  
- **Verliesverrekening (vanaf fase 2).** Carry-forward van verliezen wordt mogelijk vanaf 2028\. Architectuur moet historische winst/verlies per belastingjaar bewaren.  
- **Vastgoedbijtelling 3,35% (vanaf 2028).** Voor eigen gebruik vastgoed gaat de bijtelling van 5,06% naar 3,35%. Parameter in `tax_parameters`\-tabel houdt deze wijziging vanzelf bij.  
- **Aangifte-rapport voor lopend jaar.** Pas vanaf 1 januari volgend jaar te genereren.  
- **Heffingskorting groene beleggingen** (0,1% in 2026/2027). Kleine optimalisatie, kan in fase 1.5.

---

*Dit document is bedoeld als specificatie voor de developer en is gebaseerd op de officiële Belastingdienst-rekenmethode zoals gepubliceerd voor de voorlopige aanslag 2026\. De voorlopige percentages voor banktegoeden en schulden 2026 (1,28% en 2,70%) worden begin 2027 definitief. Parameters voor 2027 zijn op moment van schrijven (mei 2026\) nog niet bekend.*  

# FSD.md — MijnVermogen Functioneel Platformoverzicht

> **Bron:** MijnVermogen_FSD_v1.0 (1) (1).docx (versie 1.0, april 2026)  
> **Status:** Geëxtraheerd naar Markdown voor ontwikkeling en AI-sessies.  
> **Visuele referentie:** MijnVermogen-Gratis-v4.html en MijnVermogen-Premium-v4.html (repo root)  
> **Design implementatie:** [DESIGN.md](../architecture/DESIGN.md) + `frontend/src/theme.ts`

---

MijnVermogen

Functioneel platformoverzicht

Vermogensinzicht voor de Nederlandse belegger

Functies en technische vereisten voor ontwikkeling

Versie 1.0  ·  April 2026

Inhoudsopgave

1. Inleiding

2. Account aanmaken en aanmelden

3. Abonnementstiers — Gratis versus Premium

4. Algemene navigatie en layout

5. Module — Dashboard

6. Module — Portefeuille (gratis versus premium)

7. Module — Transacties

8. Module — Belastingpositie (Premium)

9. Module — Werkelijk rendement (Premium)

10. Module — Overig vermogen (Premium)

11. Module — Mijn platformen

12. Module — Platform toevoegen

13. Module — Transactie handmatig toevoegen

14. Module — Platform-vergelijker

15. Module — Profiel en accountbeheer

16. Module — Abonnement en upgrade

17. Tijd-gebonden fiscale logica (KRITIEK)

18. Platform-integraties — technische details per platform

19. Koersdata en prijs-APIs

20. CSV- en PDF-verwerking

21. Drie kritieke technische bouwblokken

22. Algemene technische vereisten

23. Beveiliging en privacy

24. Data-model (overzicht)

25. Out-of-scope voor fase 1

1. Inleiding

1.1 Doel van dit document

Dit document beschrijft welke functies het MijnVermogen platform moet bevatten, hoe gratis en premium van elkaar verschillen, en welke technische vereisten er zijn voor de implementatie. Het document is bedoeld voor ontwikkelaars die op basis hiervan hun eigen technische beslissingen maken, kosten inschatten en planning maken.

De werkende HTML-prototypes (fase-1-forfaitair-gratis.html en fase-1-forfaitair-premium.html) vormen de visuele referentie voor look-and-feel. Dit document is niet bindend op het niveau van pixels of styling-details — het beschrijft welke functionaliteit het platform moet bieden en welke technische randvoorwaarden ontwikkelaars moeten respecteren (met name rond externe API's, fiscale logica en peildatum-snapshots).

1.2 Productomschrijving

MijnVermogen is een Nederlands SaaS-platform waarop beleggers al hun investeringen centraal kunnen bijhouden — aandelen, ETF's, indexfondsen, crypto, edelmetalen — verspreid over meerdere brokers, exchanges en banken. Het platform aggregeert data via verschillende koppelingstypen (API, CSV-upload, jaaroverzicht-PDF, handmatige invoer) en toont deze in één dashboard.

Voor Premium-gebruikers biedt het platform daarnaast Nederlandse box 3-belastingberekening die doorlopend actueel is, inclusief de tegenbewijsregeling voor werkelijk rendement waarmee gebruikers mogelijk minder belasting kunnen betalen dan het forfaitair rendement voorschrijft.

1.3 Scope

Dit document beschrijft Fase 1 van het platform: het forfaitaire box 3-stelsel zoals dat geldt tot en met belastingjaar 2027. De architectuur moet uitbreidbaar zijn naar:

Fase 2: vermogensaanwasbelasting (vanaf 2028) — jaarlijkse belasting over daadwerkelijke waardestijgingen en directe inkomsten

Fase 3: eventuele vermogenswinstbelasting (toekomst) — belasting bij realisatie

Het wetsvoorstel voor fase 2 is op 12 februari 2026 aangenomen door de Tweede Kamer. Goedkeuring door de Eerste Kamer staat nog uit. De data-modellen moeten zo gebouwd worden dat fase 2-features later toegevoegd kunnen worden zonder fundamentele herbouw.

1.4 Juridische positionering

Fiscaal inzicht, geen fiscaal advies

MijnVermogen biedt fiscaal inzicht op basis van door de gebruiker aangeleverde data. Het platform geeft geen persoonlijk fiscaal advies en neemt geen aangifte-besluiten. Deze positionering moet consequent worden doorgevoerd in alle UI-copy, onboarding-schermen, help-teksten, marketing en export-PDFs. Disclaimers worden opgenomen in: profiel-view onderaan, elke fiscale berekeningsview onderaan, aangifte-rapport PDF voorblad, algemene voorwaarden. Gebruik overal de term 'fiscaal inzicht', nooit 'fiscaal advies'.

2. Account aanmaken en aanmelden

Het platform vereist een account voordat een gebruiker zijn portfolio kan opbouwen. Dit hoofdstuk beschrijft het registratie-, login- en wachtwoordherstel-proces.

2.1 Account aanmaken (registratie)

Nieuwe gebruikers registreren zich met e-mailadres en wachtwoord. De flow is laagdrempelig: minimum velden bij registratie, aanvullende profielgegevens ( fiscaal partner bijv.) worden later in het profiel ingevuld zodra de gebruiker een abonnement afsluit en dus toegang krijgt tot fiscaal inzicht.

2.1.1 Verplichte velden bij registratie

E-mailadres (uniek, gevalideerd op formaat)

Wachtwoord (minimaal 12 karakters, sterke wachtwoord-eisen, sterkte-indicator zichtbaar tijdens invoer)

Voornaam (voor personalisatie van het dashboard, bv. 'Hallo Sarah')

Akkoord op algemene voorwaarden en privacyverklaring (verplichte checkbox)

2.1.2 E-mailbevestiging

Na registratie ontvangt de gebruiker direct een bevestigingsmail met een unieke verificatie-link (token, geldig 24 uur). Het account is in afwachting tot de e-mail is bevestigd:

Vóór bevestiging: gebruiker kan inloggen maar krijgt overal in de UI een banner 'Bevestig je e-mailadres' met knop 'Stuur bevestigingsmail opnieuw'

Sommige acties zijn geblokkeerd tot na bevestiging: platform-koppelingen toevoegen, betalingen, exports

Bevestigde e-mail = volledige toegang

Bij geen bevestiging binnen 30 dagen: automatische verwijdering account

2.1.3 Welkom-onboarding na bevestiging

Bij eerste login na e-mailbevestiging start een korte onboarding-tour:

Korte uitleg wat MijnVermogen voor je doet (3 schermen, swipen of skipen)

CTA voor premium

Eerste platform koppelen — directe link naar Platform toevoegen

2.2 Aanmelden (login)

2.2.1 Login-flow

Inloggen met e-mailadres + wachtwoord

Optie 'Onthoud mij' verlengt sessie tot 30 dagen (anders 7 dagen)

Bij geactiveerde 2FA (TOTP): tweede stap met 6-cijferige code uit authenticator-app

Bij login op nieuwe locatie/device: e-mail-notificatie naar gebruiker met optie om verdachte sessies direct uit te loggen

2.2.2 Brute-force bescherming

Maximaal 5 mislukte pogingen per e-mailadres per 15 minuten

Tijdelijke account-lock van 30 minuten na overschrijding

Bij 3 lockouts in 24 uur: e-mail naar gebruiker met waarschuwing en wachtwoord-reset link

CAPTCHA na 3 mislukte pogingen (bv. hCaptcha of Cloudflare Turnstile)

2.3 Wachtwoord vergeten

'Wachtwoord vergeten?' link op login-pagina

Gebruiker voert e-mailadres in

Reset-mail wordt verstuurd met unieke token (geldig 1 uur)

Token-link leidt naar pagina waar nieuw wachtwoord ingesteld kan worden (twee keer invoeren ter bevestiging)

Na succesvolle reset: alle bestaande sessies worden automatisch ongeldig gemaakt

Notificatie-mail naar gebruiker met datum/tijd/IP van de wachtwoord-wijziging

2.4 Tweefactor-authenticatie (2FA)

2FA is optioneel voor gratis-gebruikers maar verplicht voor premium-gebruikers vanwege de fiscaal-gevoelige data

Methode: TOTP (compatible met Google Authenticator, Authy, 1Password, Microsoft Authenticator)

Activatie via Profiel → Veiligheid: QR-code scannen + verificatie-code invoeren

Backup-codes: 10 codes worden eenmalig gegenereerd voor noodtoegang

Bij upgrade naar Premium: gebruiker moet 2FA activeren als nog niet actief

Deactivering vereist huidig wachtwoord + huidige 2FA-code

2.5 Account verwijderen

Knop 'Verwijder account' in Profiel onder Veiligheid

Vereist wachtwoord + 2FA-bevestiging (als actief)

Soft-delete met 30 dagen herstel-periode (gebruiker kan terugkeren via login)

Na 30 dagen: GDPR-compliant volledig wissen, inclusief uit backups bij volgende rotatie

Uitzondering: financiële logs voor wettelijke bewaarplicht 7 jaar (geanonimiseerd)

3. Abonnementstiers — Gratis versus Premium

Het platform kent twee abonnementsvormen. Beide zijn volledige interfaces met eigen navigatie en dashboard. De gratis versie is geen beperkte proefversie maar een zelfstandig waardevolle portfolio-tracker. Premium voegt fiscale berekeningen, diepere portfolio-inzichten en uitgebreide vermogens-invoer toe.

3.1 Gratis tier — volledige feature-lijst

Prijs: € 0, voor altijd gratis.

3.1.1 Portfolio-tracking

Onbeperkt aantal platformen koppelen

Onbeperkt aantal posities en transacties

Totaal vermogen en vermogensontwikkeling over tijd

Verdeling per asset-categorie (aandelen, ETF's, indexfondsen, crypto, edelmetalen, cash)

Winnaars en verliezers per periode (vandaag, week, maand, year-to-date)

Waarde-vs-inleg grafiek over de afgelopen 12 maanden

Winst en verlies per positie (eenvoudige tabel)

Insights: totaal ingelegd, huidige waarde, totale winst, geannualiseerd rendement (CAGR)

Alle posities tabel met basiskolommen (asset, aantal, koers, waarde, % portfolio, platform)

3.1.2 Platform-koppelingen

API-koppelingen voor exchanges en brokers die dit ondersteunen (Bitvavo, Coinbase, IBKR, Bybit EU, Kraken, Bitpanda, OKX)

CSV-uploads voor brokers en exchanges zonder API (DEGIRO, Trading 212, BUX Zero, eToro, etc.)

Jaaroverzicht PDF-import (banken: ING, ABN AMRO, Rabobank; indexfondsen: Meesman, Brand New Day)

Handmatige invoer voor edelmetalen en wallets zonder integratie

3.1.3 Transacties en handmatige invoer

Transactie-overzicht van alle bewegingen aggregaat over alle platformen

Filter op type (aankoop, verkoop, dividend, storting, etc.) en periode

Handmatig transacties toevoegen, ook met terugkerende-aankoop instelling (herinneringsmail-flow, niet automatische boeking)

3.1.4 Platform-tools

Mijn platformen: overzicht van alle gekoppelde databronnen

Platform toevoegen: stap-voor-stap wizard

Handmatig transacties toevoegen

Platform-vergelijker: helpt kiezen welk platform past bij gebruikersprofiel (met affiliate links een mogelijke inkomstenbron)

3.1.5 Account en personalisatie

Profiel-beheer: persoonsgegevens, e-mailadres, wachtwoord wijzigen

Optionele 2FA-activatie

Voorkeuren: dark/light theme, notificatie-instellingen

Permanente sidebar-promo voor Premium upgrade

Compacte premium-hint bovenin Portefeuille-view

3.2 Premium tier — volledige feature-lijst

Prijs: € 49,99 per jaar. Prijs-vast bij upgrade vóór invoering vermogensaanwasbelasting (2028); standaardprijs daarna € 69,99. Fiscaal partner toevoegen kost €10,00 extra.

3.2.1 Alles van Gratis

Volledige portfolio-tracker, alle platform-koppelingen en account-opties blijven beschikbaar.

3.2.2 Fiscaal inzicht — mogelijk geld besparen

Minder belasting betalen als je werkelijke rendement lager is dan het forfait (tegenbewijsregeling)

Automatisch OWR-rapport (Opgaaf Werkelijk Rendement) voor de Belastingdienst

Belastingpositie doorlopend zichtbaar — geen verrassingen bij aangifte

Stapsgewijze berekening box 3 (per jaar configureerbaar voor wijzigingen tarieven en grenzen)

Heffingsvrije grens-tracker met vooruitblik naar volgende peildatum

Werkelijk rendement uitgesplitst per asset

Automatische vergelijking forfaitair tarief versus daadwerkelijk rendement

Fiscaal partner ondersteund: verdubbelde heffingsvrije grens en twee API-verbindingen mogelijk per platform

3.2.3 Diepere portfolio-inzichten

Portefeuille-samenstelling als donut-grafiek met alle individuele posities (kleurgroepen per assetklasse)

Gemiddelde aankoopprijs per positie (cost basis)

Rendement per positie over verschillende periodes: 1 week, 1 maand, 1 jaar

Ontvangen dividend en staking rewards per positie en per platform

Betaalde fees per platform (transactiekosten, custody/beheer)

Waarde van iedere positie op peildatum 1 januari (uitgebreide holdings-tabel)

Inleg per positie inzichtelijk naast huidige waarde

3.2.4 Overig vermogen en schulden

Vastgoed (tweede woning, vakantiehuis, beleggingspand) met uitgebreide checklist per object

WOZ-waardeverloop, huurinkomsten en aftrekbare kosten registreren

Schulden registreren met automatische drempelberekening (€ 3.800 per persoon, niet aftrekbaar gedeelte)

Leegwaarderatio en verbeteringskosten bijhouden voor verhuurde panden

Banktegoeden per peildatum (uitsluitend peildatum-waarde, niet huidig saldo — fiscaal correct)

3.2.5 Service en support

Signaal na afloop boekjaar als werkelijk rendement voordeliger blijkt dan forfait

3.3 Visueel onderscheid tussen tiers

Het platform gebruikt een slotje-icoon als consistente visuele markering voor premium-content. Het slotje suggereert 'achter slot' wat de daadwerkelijke UX beschrijft.

3.3.1 In de gratis versie

Slotjes naast nav-items van premium-secties (Belastingpositie, Werkelijk rendement, Overig vermogen)

Permanente Premium-promo kaart linksonder in sidebar

Compacte premium-hint bovenaan de Portefeuille-view

Klik op een premium-nav-item leidt naar een upgrade-banner in plaats van de feature

Abonnement-view toegankelijk via promo-knoppen (verborgen nav-item)

3.3.2 In de premium versie

Slotjes blijven zichtbaar (maar dan open) op fiscale views als consistente markering dat dit Premium-features zijn (niet als slot — de features zijn volledig toegankelijk)

Geen Premium-promo kaart in sidebar

Geen Abonnement-view in zichtbare navigatie (toegankelijk via Profiel)

3.4 Abonnement-overgangen

3.4.1 Upgrade gratis → premium

Via Abonnement-view: betalen via Mollie of Stripe (iDEAL, creditcard, SEPA-incasso)

Direct na succesvolle betaling: account upgraded, premium features ontgrendeld

Welkom-mail + onboarding-modal in de app voor nieuwe features

Prijs-lock geactiveerd: bij upgrade vóór 2028 blijft prijs € 49,99 ook na invoering vermogensaanwasbelasting

3.4.2 Downgrade premium → gratis

Opzeggen via Profiel onder Abonnement

Toegang tot premium-features blijft tot einde betaalde periode

Daarna automatisch terug naar Gratis — geen dataverlies

Portfolio-data, transacties en peildatum-snapshots blijven volledig behouden

Fiscale berekeningen, OWR-rapport-toegang, overig vermogen en uitgebreide portfolio-inzichten worden afgesloten

Bij latere upgrade: alles direct weer beschikbaar

4. Algemene navigatie en layout 

4.1 Globale structuur

De applicatie heeft een vaste two-column layout op desktop: een sidebar links voor navigatie en branding, een main content area rechts met dynamische views. Op mobile transformeert de sidebar naar een hamburger-menu.

4.2 Sidebar-inhoud

Branding bovenaan: logo (vier oplopende staafjes) + wordmark MijnVermogen

Navigatie gegroepeerd in drie groepen: Overzicht, Fiscaal, Platformen

Premium-promo kaart (alleen in gratis versie) onder de navigatie

User-pill onderaan: initialen, naam, account-type ('Gratis' of 'Premium'). Klikbaar → Profiel

4.3 Navigatie-items

Groep — Overzicht

Dashboard

Portefeuille (gratis: met slotje voor premium-secties)

Transacties

Groep — Fiscaal (alle drie met slotje)

Belastingpositie

Werkelijk rendement

Overig vermogen

Groep — Platformen

Mijn platformen

Platform toevoegen

Transactie handmatig toevoegen

Vergelijker

4.4 Topbar

Theme-toggle: dark/light mode wisselen, voorkeur opgeslagen in localStorage

Breadcrumbs onder topbar tonen huidige locatie (bv. 'Fiscaal / Belastingpositie')

4.5 Routing-systeem

Single page application met client-side routing. Elke view heeft een unieke route. Programmatische navigatie via data-goto attributen op buttons en hint-balken (bv. tip-balk op Belastingpositie verwijst naar Werkelijk rendement).

5. Module — Dashboard

Landingspagina na inloggen. Doel: in één oogopslag totaalvermogen, samenstelling en recente beweging laten zien. Layout is identiek tussen gratis en premium.

5.1 Functionele onderdelen

Persoonlijke begroeting met voornaam (uit account)

Hero-kaart met totaalvermogen en delta over de afgelopen 30 dagen (in euro's en procenten)

Vermogensontwikkeling over tijd: line chart over 12 maanden met portfolio-waarde versus cost basis

Winnaars en verliezers: top 3 stijgers en dalers met periode-toggle (vandaag, week, maand, year-to-date)

Platform-overzicht strook: alle gekoppelde platformen met logo, totaalwaarde en sync-status

5.2 Verschillen Gratis versus Premium

Het dashboard is functioneel identiek tussen beide tiers. Gebruikers van beide tiers zien dezelfde data en visualisaties. De heffingsvrije grens-tracker hoort thematisch bij Belastingpositie en is daar opgenomen, niet hier.

Het enige zichtbare verschil: gratis-gebruikers zien de Premium-promo kaart in de sidebar, premium-gebruikers niet.

6. Module — Portefeuille (gratis versus premium)

De Portefeuille-view is het hart van het portfolio-overzicht. Hier komen alle individuele posities en analyses bij elkaar. Dit is ook waar het verschil tussen gratis en premium het duidelijkst voelbaar is — premium voegt veel meer analyse-diepte toe.

6.1 Onderdelen die in BEIDE tiers zitten

De volgende onderdelen zijn identiek beschikbaar in gratis en premium:

Page header en kicker. Titel 'Portefeuille — alle posities' met meta-regel 'Alle posities · X platformen'.

Portefeuille inzichten. Insight-grid met totaal ingelegd, huidige waarde, totale winst (€ en %), en geannualiseerd rendement (CAGR).

Waarde versus inleg grafiek. Line chart over 12 maanden met huidige portfolio-waarde tegen cost basis.

Winst en verlies per positie (eenvoudig). Tabel met asset, inleg, huidige waarde, winst/verlies in euro's en percentage. Gesorteerd op absolute P&L.

Alle posities tabel (basis-kolommen). Tabel met filters per asset-categorie en platform. Basis-kolommen: asset, aantal, koers, waarde, % portfolio, platform.

6.2 Onderdelen die ALLEEN in Premium zitten

6.2.1 Portefeuille-samenstelling — donut-grafiek

Visuele weergave van de hele portefeuille als donut-grafiek met alle individuele posities. Posities binnen dezelfde assetklasse delen een basiskleur met variaties voor onderscheid:

ETF's: oker tinten

Aandelen: taupe tinten

Indexfondsen: magenta tinten

Crypto: mossgroen tinten

Edelmetalen: warm goud tinten

Banktegoeden: grijs

Hover-interactie toont per segment de details (symbool, naam, waarde, percentage, platform). De legenda rechts groepeert posities per categorie met subtotalen. Dit overzicht ontbreekt volledig in gratis.

6.2.2 Verrijkte 'Alle posities' tabel

In premium krijgt de Alle-posities tabel zes extra kolommen vergeleken met gratis:

Kolom

Gratis

Premium

Asset (symbool + naam)

✓

✓

Aantal

✓

✓

Koers

✓

✓

Gem. aankoop (cost basis per stuk)

—

✓

Waarde

✓

✓

Inleg per positie

—

✓

Rendement % (totaal)

—

✓

Rendement 1 week / 1 maand / 1 jaar

—

✓

Dividend / fees per positie

—

✓

Waarde op peildatum 1 januari

—

✓

% portfolio

✓

(in donut)

Platform

✓

✓

De premium-tabel is daarmee een volwaardig analyse-instrument: gebruikers zien per positie hun rendement over verschillende periodes, hun gemiddelde aankoopprijs voor cost-basis-analyse, hun ontvangen dividend en betaalde fees, en de waarde op de peildatum (essentieel voor box 3-aangifte).

6.2.3 Betaalde fees per platform

Tabel met per platform de totaal betaalde transactiekosten en custody/beheer-fees year-to-date. Helpt gebruikers de werkelijke kosten van hun beleggingen te zien, en is relevant voor de tegenbewijsregeling (kosten zijn aftrekbaar van werkelijk rendement).

6.2.4 Ontvangen dividend per platform

Tabel met per platform het totaal ontvangen dividend en staking rewards year-to-date. Voor Belastingdienst-aangifte zijn deze bedragen relevant voor de werkelijk-rendementsberekening.

6.3 Premium-hint in gratis versie

Bovenaan de Portefeuille-view in de gratis versie staat een compacte klikbare hint-balk. De inhoud verwijst naar wat premium toevoegt: "Met Premium zie je ook rendement per positie, dividend, fees en een taartgrafiek met alle assets." Klik leidt naar de Abonnement-view.

6.4 Functioneel verschil — samenvatting

De kern van het verschil

Gratis = portfolio-overzicht (wat heb ik en hoeveel is het waard). Premium = portfolio-analyse (hoe presteert elke positie, wat kost het me, wat is fiscaal relevant). Een gratis-gebruiker ziet zijn vermogen, een premium-gebruiker begrijpt zijn vermogen tot in detail.

7. Module — Transacties

Chronologisch overzicht van elke transactie samengevoegd uit alle databronnen (API's, CSV-imports, PDF-parsers en handmatige invoer). Identieke functionaliteit in beide tiers.

7.1 Functionele onderdelen

Filter op type: aankoop, verkoop, dividend, storting, onttrekking, kosten, staking reward

Filter op periode: year-to-date, kwartaal, maand, vorig boekjaar, aangepast bereik

Filter op platform

Zoekveld op asset-symbool of naam

Tabel met datum, type, asset, aantal, bedrag, platform, kosten, notitie

Type wordt kleur-gecodeerd weergegeven (winst-positief, neutraal, kosten-rood)

Sorteren op datum (default aflopend) of bedrag

Paginering met lazy-loading bij scroll voor grote datasets

7.2 Export-functionaliteit

CSV-export: alle transacties met alle kolommen inclusief notities (beide tiers)

8. Module — Belastingpositie (Premium)

De kern van Premium. Toont exact wat verschuldigd is aan box 3-belasting, stap voor stap berekend op basis van de relevante peildatum. In gratis vervangt een upgrade-banner deze hele view.

8.1 Gratis versie — upgrade-banner

Gratis-gebruikers die naar Belastingpositie navigeren krijgen een upgrade-banner met uitleg wat Premium toevoegt: automatische berekening op basis van portfolio, peildatum-waarde automatisch vastgelegd, stap-voor-stap uitleg, heffingsvrije grens-tracker. Een primary CTA-knop leidt naar de Abonnement-view.

8.2 Premium — functionele onderdelen

8.2.1 Tip-balk naar Werkelijk rendement

Klikbare balk bovenaan de view die uitlegt dat de gebruiker mogelijk minder belasting kan betalen via de tegenbewijsregeling. Klik leidt direct naar de Werkelijk rendement-view.

8.2.2 Hero — verschuldigde belasting

Groot bedrag dat aangeeft wat verschuldigd is aan box 3-belasting voor het relevante belastingjaar. Onder het bedrag een toelichting: 'Berekend over je vermogen van € X op peildatum 1 januari JJJJ. Aanslag ontvang je in JJJJ+1.' Het bedrag wordt automatisch herberekend bij wijzigingen in portfolio of overig vermogen.

Relevante peildatum-logica (cruciaal)

Het bedrag past zich automatisch aan op basis van de huidige datum. Vóór 1 mei van een belastingjaar (bv. 1 mei 2027) toont het bedrag nog de belasting over het vorige boekjaar (2026, peildatum 1-1-2026). Vanaf 2 mei schakelt het automatisch naar het nieuwe belastingjaar (2027, peildatum 1-1-2027). Volledige uitwerking in hoofdstuk 17.

8.2.3 Heffingsvrije grens — vooruitblik

Sectie ná de hero die de gebruiker toont waar hij staat ten opzichte van de heffingsvrije grens van het volgende belastingjaar. Bevat:

Een visuele tracker met huidige vermogen versus heffingsvrije grens

Stat-kaarten met heffingsvrij deel, belastbaar deel en totaal vermogen

Disclaimer-blok dat duidelijk maakt dat dit een vooruitblik is voor de volgende peildatum, niet de huidige berekening

8.2.4 Stap-voor-stap berekening

Genummerde stappen die de berekening van forfaitair tarief uitleggen:

Vermogen op peildatum

Min: heffingsvrij vermogen (verdubbeld bij fiscaal partner)

= Belastbaar vermogen

Banktegoeden × tarief banktegoeden (2026: 1,44%)

Overige bezittingen × tarief overige (2026: 6,04%)

= Fictief rendement totaal

× Tarief box 3 (2026: 36%) = verschuldigde belasting

Tarieven en grenzen — configureerbaar per jaar

De fiscale parameters MOGEN NIET hardcoded zijn. Ze moeten in een config of database-tabel per belastingjaar staan (heffingsvrij_bedrag, banktegoed_pct, overige_pct, tarief_pct, schuld_drempel). Tarieven wijzigen jaarlijks bij het Belastingplan en het platform moet snel kunnen updaten zonder code-release.

8.2.5 Werkelijk rendement YTD-summary

Korte samenvatting onderaan de view met werkelijk rendement year-to-date in euro's, inleg year-to-date en gerealiseerde winst. Klikbare link naar volledige Werkelijk rendement-view.

8.3 Fiscaal partner-effect

Als de gebruiker een fiscaal partner heeft (ingesteld in Profiel), wordt het heffingsvrij vermogen automatisch verdubbeld. Berekening hanteert die verdubbelde grens.

9. Module — Werkelijk rendement (Premium)

Wet werkelijke rendement: als het werkelijke rendement over het jaar lager was dan het forfait, mag de belegger dat opgeven en minder belasting betalen. Deze view berekent dat rendement year-to-date en toont de vergelijking.

9.1 Gratis versie — upgrade-banner met educatieve uitleg

Naast de standaard upgrade-banner toont de gratis versie ook een educatief uitleg-blok over de wet werkelijke rendement. Doel: de waarde van Premium inzichtelijk maken en SEO-waarde creëren rond zoekopdrachten als 'werkelijk rendement berekenen'.

9.2 Premium — functionele onderdelen

9.2.1 Vergelijkingskaart

Centrale kaart die forfaitair rendement (per Belastingdienst-formule) vergelijkt met werkelijk rendement (year-to-date berekend uit portfolio-data). Toont het verschil in percentpunten en geeft een geschatte besparing als werkelijk lager is. Kleur-coderend: moss-groen als werkelijk lager (voordelig), rust-rood als hoger.

9.2.2 Direct rendement uitgesplitst

Sectie met per inkomstenbron het ontvangen bedrag year-to-date:

Dividend ontvangen

Staking rewards

Ontvangen rente op banktegoeden

Totaal direct rendement

9.2.3 Indirect rendement per positie

Tabel met per positie de waardeverandering tussen begin en huidige datum:

Asset, beginwaarde (1 januari), eindwaarde (huidige), mutatie in euro's en percentage

Gesorteerd op euro-mutatie aflopend

Totaal indirect rendement onderaan

9.2.4 Aangifte-rapport (PDF)

Generator die een professioneel rapport produceert dat klaar is voor de Belastingdienst of een fiscaal adviseur:

Voorblad met BSN opengelaten, belastingjaar, datum

Samenvatting: peildatum-vermogen, forfaitaire berekening, werkelijke berekening, verschil

Detail per positie met transactie-bewijzen

Bronvermelding: welke platformen en welke koppeltypen

Disclaimer: 'Dit rapport is fiscaal inzicht, geen advies'

Beschikbaar vanaf 1 januari van het volgende jaar (niet voor lopend jaar)

9.3 Berekening van werkelijk rendement

Formule

werkelijk_rendement_euro = (eindwaarde_portfolio − beginwaarde_portfolio − netto_inleg) + dividend + staking_rewards + ontvangen_rente − betaalde_kosten. Met netto_inleg = stortingen − onttrekkingen. Het percentage = werkelijk_rendement / gemiddelde_waarde over de periode (tijdgewogen, met herijking bij cashflow-mutaties > 5%).

10. Module — Overig vermogen (Premium)

Plek om niet-beleggingsvermogen in te voeren: vastgoed, schulden en banktegoeden die niet via platform-koppeling binnenkomen. Essentieel voor accurate belastingberekening want deze bestanddelen tellen mee voor box 3.

10.1 Gratis versie

Upgrade-banner zonder invoervelden. Standaard uitleg wat Premium toevoegt.

10.2 Premium — drie tabs

10.2.1 Tab Vastgoed

Voor tweede woningen, vakantiehuizen, beleggingspanden en garages/parkeerplekken. De eigen woning hoort in box 1 en is uitgesloten — expliciete tekst in de UI.

Invoervelden per object

Type: tweede woning, vakantiehuis, beleggingspand, garage/parkeerplek, overig

WOZ-waarde op peildatum

Aankoopdatum en aankoopprijs

Adres (straat, huisnummer, postcode, plaats, land)

Oppervlakte in m²

Gebruiksvorm: verhuurd / zelfbewoond / leegstaand

Beschrijving (vrije tekst)

Checklist per object

Opklapbare checklist om te zorgen dat alle relevante fiscale gegevens compleet zijn:

Waardeverloop: WOZ-waarde per jaar, taxaties

Gebruik: huurinkomsten, verhuurperiode, leegwaarderatio bij verhuur

Kosten: aftrekbare kosten (relevant onder vermogensaanwasbelasting)

Bij verkoop: voor toekomstige vermogenswinstbelasting

10.2.2 Tab Schulden

Voor studieschulden (DUO), hypotheken op tweede woning, persoonlijke leningen, creditcardschulden. Hypotheken op de eigen woning horen in box 1 en zijn uitgesloten.

Summary-kaart bovenaan

Totale box 3-schulden (excl. hypotheek eigen woning)

Drempel per belastingjaar (2027: € 3.800 per persoon, configureerbaar)

Bedrag dat box 3-vermogen verlaagt (schulden boven drempel)

Invoervelden per schuld

Type: persoonlijke lening, studieschuld DUO, creditcard, hypotheek tweede woning, rekening-courant familie/vrienden

Openstaand bedrag op peildatum

Rente-percentage en betaalde rente year-to-date (relevant voor fase 2 als aftrekpost)

Eerste schuld-datum en schuldeiser

Optionele koppeling aan vastgoed (voor hypotheken)

Opmerking-veld

10.2.3 Tab Banktegoeden

Voor spaarrekeningen, betaalrekeningen en deposito's die niet via platform-koppeling binnenkomen.

KRITIEK — alleen peildatum-waarde

Banktegoeden worden uitsluitend opgegeven als peildatum-waarde, NIET als huidig saldo. Voor box 3 telt alleen wat er op 1 januari stond. Het huidige saldo is fiscaal niet relevant en zou verwarring veroorzaken. In de UI staat daarom alleen 'Saldo peildatum' als invoerveld. Er is GEEN veld voor 'huidig saldo'.

Invoervelden per banktegoed

Saldo op peildatum (jaar dynamisch op basis van actuele peildatum)

Type: spaarrekening, betaalrekening, deposito

Bank-naam

Rente-percentage

Ontvangen rente year-to-date

Notitie (spaardoel of rekeningnaam)

11. Module — Mijn platformen

Overzichtspagina van alle gekoppelde databronnen. Toont API-koppelingen, CSV-uploads, jaaroverzicht-imports en handmatige bronnen — gegroepeerd per koppeltype.

11.1 Gegroepeerde weergave

Platform-kaarten zijn gegroepeerd in vier secties:

API-koppelingen (realtime sync)

CSV-uploads (periodiek bijwerken)

Jaaroverzichten (jaarlijks)

Handmatige invoer

Elke sectie heeft een 'Toevoegen' knop die naar Platform toevoegen leidt met voorgeselecteerd koppeltype.

11.2 Per platform-kaart

Platform-logo en naam

Categorie-label (Crypto, Broker, Indexfonds, Edelmetaal, Bank)

Totaalwaarde van posities op dit platform

Aantal posities

Sync-status: Live / laatste sync / waarschuwing bij API-key verloop

Acties: instellingen, pauzeren, verwijderen

11.3 Acties per koppeltype

Bij API-koppelingen

API-key roteren

Sync pauzeren of handmatig synchroniseren

Sync-frequentie aanpassen

Waarschuwing bij naderende API-key vervaldatum (< 30 dagen)

Bij CSV-uploads

Knop 'Nieuwe CSV uploaden' om laatste periode aan te vullen

Datum laatste upload zichtbaar

Waarschuwing als data > 45 dagen oud is

Bij jaaroverzichten

Knop 'Upload nieuw jaaroverzicht'

Overzicht van geüploade jaren

Bij handmatige invoer

Knop 'Voeg transactie toe' (navigeert naar handmatig toevoegen)

12. Module — Platform toevoegen

Wizard voor het toevoegen van een nieuwe broker, exchange, bank of indexfonds. Volgorde: eerst platform kiezen, daarna koppelmethode.

12.1 Stap 1 — Kies een platform

Zoekbalk met live filter

Grid met de meest gebruikte platformen (Bitvavo, DEGIRO, IBKR, OKX, Trading 212, BUX Zero, Meesman, Bybit EU)

Knop 'Toon alle 30+ platformen' voor volledige lijst

Filter op categorie (Crypto, Broker, Indexfonds, Edelmetaal, Bank)

12.2 Stap 2 — Hoe wil je koppelen?

Drie methode-kaarten waarbij beschikbaarheid afhangt van het gekozen platform:

API-koppeling (realtime sync) — beste optie als beschikbaar

CSV-upload (periodiek bijwerken) — voor brokers zonder API

Jaaroverzicht PDF — voor banken en indexfondsen

Handmatige invoer staat NIET als vierde optie hier; daarvoor is de aparte tab 'Transactie handmatig toevoegen'. Een info-blok onder de methode-kaarten verwijst naar die tab.

12.3 Onboarding-flow per methode

API-koppeling

Platform-specifieke instructies hoe een API-key aan te maken (met screenshots)

Waarschuwing: alleen View-only key, geen trade- of withdrawal-rechten

Invoer van API-key en API-secret (gemaskeerd, beide encrypted opgeslagen)

Optionele startdatum voor historische sync

Testverbinding-knop, daarna eerste sync op achtergrond

CSV-upload

Platform-specifieke export-instructies (vooral belangrijk om te benoemen dat het dus regelmatig geüpload dient te worden

Drag-and-drop of bestandskiezer

Server parst het bestand, toont preview met aantal transacties en duplicaten

Confirm-knop voor definitieve import

Jaaroverzicht PDF

Upload het officiële jaaroverzicht-PDF

Server parst met platform-specifieke parser

Preview met beginsaldo, eindsaldo, totaal dividend

Bevestiging of correctie door gebruiker

13. Module — Transactie handmatig toevoegen

Voor transacties die niet automatisch via een gekoppeld platform binnenkomen — bijvoorbeeld aankopen bij edelmetaal-handelaren, overboekingen tussen wallets, of periodieke aankopen die de gebruiker zelf wil bevestigen.

13.1 Formuliervelden

Type transactie: aankoop, verkoop, dividend, storting, onttrekking, kosten, staking reward

Datum (datepicker)

Platform (dropdown van gekoppelde platformen of 'Nieuw platform')

Asset (tekstveld met autocomplete uit eerder ingevoerde assets)

Aantal (5 decimalen voor crypto-precisie)

Prijs per stuk in euro's

Transactiekosten (optioneel)

Valuta (EUR, USD, GBP — bij niet-EUR ook wisselkoers)

Opmerking (optioneel, voor context)

13.2 Terugkerende aankoop — toggle

Optionele instelling waarbij de gebruiker kan aangeven dat dit een terugkerende aankoop is. Bij activatie verschijnen extra velden:

Frequentie: maandelijks, elke 2 weken, wekelijks, per kwartaal, jaarlijks

Dag van de maand (bij maandelijks)

Einddatum (optioneel, leeg = oneindig)

BELANGRIJK — geen automatische boeking

Terugkerende aankopen worden NIET automatisch aan het portfolio toegevoegd. Je weet immers niet tegen welke prijs er aangekocht wordt. Op de ingestelde datum ontvangt de gebruiker een herinneringsmail met een directe link om de transactie te bevestigen of aan te passen.

14. Module — Platform-vergelijker

Hulpmiddel voor gebruikers die twijfelen welk platform bij hen past. Bevat een quiz-gebaseerde aanbeveling plus directe platform-vergelijking op kostenstructuur en features. Tegelijk fungeert deze module als een belangrijk inkomstenkanaal voor MijnVermogen via affiliate-partnerships met de getoonde platformen.

Verdienmodel — affiliate links

Naast het Premium-abonnement is de Vergelijker een primair inkomstenkanaal. MijnVermogen heeft (of bouwt) affiliate-partnerships met de getoonde brokers, exchanges en edelmetaalhandelaren. Wanneer een gebruiker via een MijnVermogen-link doorklikt naar een platform en daar een account opent (en eventueel een eerste storting doet), ontvangt MijnVermogen een vergoeding van dat platform. Dit moet daarom een prominente, herkenbare functionaliteit zijn — geen verstopte feature.

14.1 Platform-secties

Drie gegroepeerde secties met platform-kaarten:

Cryptobeurzen: Bitvavo, OKX, Bybit, Bitpanda

Brokers (aandelen/ETF): DEGIRO, Interactive Brokers, Trading 212, BUX Zero

Edelmetaalhandelaren: GoldRepublic, Holland Gold

De lijst groeit op termijn met meer platformen naarmate er affiliate-partnerships worden gesloten.

14.2 Per platform-kaart

Elke kaart toont:

Platform-logo en naam

Toezichthouder (AFM, BaFin, FMA, etc.)

Tarief-informatie: belangrijkste kostenposten (bv. transactiekosten, custody-fee)

Hoofdkenmerk in één zin (bv. 'Nederlandse marktleider crypto', 'Lage kosten, veel opties')

Beschikbare koppeltypes met MijnVermogen (API / CSV / Jaaroverzicht / Handmatig)

Primaire CTA-knop: 'Account aanmaken bij [platform-naam]' — opent het registratie-proces van het platform via een affiliate-link in een nieuw tabblad. Voor sommige platformen kan dit een welkomstbonus of korting voor de gebruiker bevatten als de affiliate-deal dat toelaat.

14.3 Affiliate-link implementatie

14.3.1 Per platform een unieke partner-URL

Elk platform levert een eigen affiliate-URL met daarin een tracking-parameter (referral code, partner ID of UTM-tags). Het platform zelf herkent dat de bezoeker via MijnVermogen kwam en koppelt eventuele aanmeldingen aan de affiliate-account.

Voorbeelden: ?ref=mijnvermogen, ?utm_source=mijnvermogen, /signup?partner=12345

De URLs worden centraal beheerd in een config-tabel of CMS zodat ze aangepast kunnen worden zonder code-release

Per platform configureerbaar: actief/inactief (om platformen waarvan de affiliate-deal verlopen is tijdelijk uit te schakelen)

14.3.2 Klik-tracking aan MijnVermogen-zijde

Naast de tracking bij het externe platform houdt MijnVermogen zelf ook bij welke gebruiker op welke partner-link heeft geklikt:

Bij klik op CTA: log-event opslaan met user_id, platform_slug, timestamp, source-page (vergelijker, platform-toevoegen, etc.)

Dit maakt het mogelijk om conversie-statistieken te koppelen (X gebruikers klikten naar Bitvavo, Y daarvan zijn nu via API gekoppeld — wat conversie suggereert)

Bruikbaar voor heronderhandeling van affiliate-tarieven met platformen op basis van bewezen conversie

14.3.3 Transparantie en wettelijke verplichtingen

Verplicht — affiliate disclosure

Onder Nederlandse en EU-regelgeving (AFM, EU-richtlijn oneerlijke handelspraktijken) moet duidelijk zichtbaar zijn dat MijnVermogen vergoedingen ontvangt voor doorverwijzingen. Op de Vergelijker-pagina staat daarom een prominente disclosure: 'MijnVermogen kan een vergoeding ontvangen wanneer je via een van deze links een account opent. Dit beïnvloedt niet onze beoordeling — we kiezen platformen op basis van geschiktheid voor de Nederlandse belegger.' Zelfde tekst opnemen op elke pagina waar affiliate-links staan.

14.4 Affiliate-CTA op andere plekken in het platform

De affiliate-CTA is niet alleen op de Vergelijker zichtbaar. Op alle plekken waar een gebruiker een nieuw platform overweegt of nog geen account heeft, biedt MijnVermogen de mogelijkheid om direct een account aan te maken via de affiliate-link:

Bij Platform toevoegen (hoofdstuk 12): Op de platform-keuze-pagina krijgt elk platform-kaart naast de 'Selecteer'-knop ook een secundaire link 'Heb je nog geen account? Maak er hier een aan →' die naar de affiliate-URL leidt.

Bij Mijn platformen — Toevoegen-knop per categorie: Idem, gebruikers worden uitgenodigd om bij een nieuw platform direct een account aan te maken via de affiliate-link.

Bij quiz-resultaten in de Vergelijker: De top 3 aanbevolen platformen krijgen elk hun eigen 'Account aanmaken'-knop met affiliate-link.

14.5 Quiz

Vijf vragen die het profiel van de gebruiker bepalen:

Wat wil je vooral doen? (beleggen, sparen-met-rente, crypto, edelmetaal)

Hoe actief ben je? (passief indexfonds, maandelijkse inleg, actief traden)

Hoeveel ervaring heb je? (beginner, gevorderd, expert)

Wat is belangrijker? (lage kosten, veel opties, beide)

Voorkeur voor Nederlands platform? (ja, maakt niet uit)

Een scoring-algoritme matched antwoorden aan platform-profielen en presenteert top 3 aanbevelingen met uitleg waarom. Elke aanbeveling heeft een 'Account aanmaken'-knop (affiliate-link) en een 'Toevoegen aan MijnVermogen'-knop voor gebruikers die er al een account hebben.

14.6 Eerlijkheid in aanbevelingen

Hoewel de Vergelijker een commercieel doel dient, mag de scoring NIET worden vertekend door affiliate-tarieven. Het algoritme beveelt aan op basis van geschiktheid voor de gebruiker, niet op basis van wat MijnVermogen het meest oplevert. Voor het lange-termijn vertrouwen van gebruikers is dit cruciaal — een vergelijker die naar de hoogste commissie stuurt verliest snel zijn geloofwaardigheid.

Scoring-gewichten zijn publiekelijk uitlegbaar via 'Hoe komen we tot deze aanbeveling?'-link

Platformen zonder affiliate-deal worden ook getoond in vergelijking en quiz-resultaten (zonder CTA, met label 'geen affiliate-link beschikbaar')

Bij gelijke score-uitkomst geen voorkeur voor platform met hogere affiliate-vergoeding

15. Module — Profiel en accountbeheer

User-account management. Beide tiers hebben dezelfde Profiel-view met dezelfde secties. Premium toont 'Premium lid sinds X' header, gratis toont 'Gratis account'.

15.1 Persoonlijke gegevens

Voornaam en achternaam

E-mailadres (gevalideerd, wijzigbaar via wachtwoord-bevestiging)

Geboortedatum

Premium-gebruikers: fiscale partner ja/nee (bij ‘ja’ moet het heffingsvrije vermogen verdubbeld worden)

15.2 Veiligheid

2FA activeren of beheren (TOTP)

Wachtwoord wijzigen (vereist huidig wachtwoord)

Lijst van actieve sessies met device, locatie en laatste activiteit; logout-knop per sessie

Account verwijderen (zie hoofdstuk 2.6)

15.3 Voorkeuren

Thema: dark, light, of systeem

Taal (Nederlands voor MVP, Engels in latere fase)

Valuta (EUR voor MVP 1)

Notificatie-voorkeuren: herinneringen aangifte-deadline (Premium), terugkerende-aankoop herinneringen, API-key vervaldatum-waarschuwingen

15.4 Premium-specifieke secties

Gedownloade documenten: lijst van eerder gegenereerde aangifte-rapporten per belastingjaar, met download-knop

Abonnement-info: Premium lid sinds-datum, huidige prijs, volgende facturatie-datum, opzeg-link, factuur-historie

15.5 Footer-disclaimer

Onderaan elke Profiel-view een disclaimer: 'MijnVermogen biedt fiscaal inzicht, geen fiscaal advies. Raadpleeg een erkend belastingadviseur voor persoonlijke fiscale beslissingen.' Plus links naar algemene voorwaarden, privacyverklaring, cookie-beleid, contact.

16. Module — Abonnement en upgrade

Upgrade-landingspagina, alleen toegankelijk in de gratis versie. Niet zichtbaar in de hoofdnavigatie van premium (premium-gebruikers beheren hun abonnement via Profiel).

16.1 Onderdelen op de Abonnement-pagina

Hero met titel 'Kies je abonnement'

Twee kolommen naast elkaar: Gratis (huidige tier) en Premium (upgrade-doel)

Per kolom: prijs, tagline, volledige feature-lijst per groep

Premium-kolom heeft een 'Bespaart geld bij vermogen > € 60.000' lint bovenaan

Prijs-lock notice in Premium: € 49,99 blijft van toepassing zelfs als de standaardprijs naar € 69,99 stijgt na 2028

Primary CTA bij Premium: 'Upgrade naar Premium'

Secundaire link: '30 dagen geld-terug-garantie'

16.2 Feature-vergelijking per groep

Premium-kolom toont features gegroepeerd:

Alles van Gratis (uitleg dat alle gratis-features behouden blijven)

Fiscaal inzicht — mogelijk geld besparen

Diepere portfolio-inzichten

Overig vermogen en schulden

Service en support

16.3 FAQ-sectie

Onder de prijs-vergelijking een FAQ met de meest voorkomende vragen:

Kan ik altijd opzeggen?

Wat gebeurt er met mijn data als ik van Premium naar Gratis ga?

Hoe zit het met fiscaal partnerschap?

16.4 Betalingsflow

16.4.1 Betalingsproviders

Mollie (primair, NL): iDEAL, creditcard, SEPA-incasso

Stripe (fallback, internationaal): creditcard, debitcard

Default: iDEAL (hoogste conversie in NL)

16.4.2 Flow

Klik 'Upgrade naar Premium'

Betalingsscherm: betaalmethode kiezen

Bij iDEAL: redirect naar bank, bevestig, redirect terug

Server ontvangt webhook van betaalprovider

Account upgraden in database (tier=premium, price_lock geactiveerd indien vóór 2028)

Welkom-mail versturen

Onboarding-modal in app voor nieuwe premium-features

16.4.3 Jaarlijkse verlenging

30 dagen voor verloop: herinneringsmail

14 dagen voor verloop: tweede herinnering met opzeg-link

Dag voor verloop: automatische incasso (SEPA of creditcard)

Bij mislukte betaling: 3 retry-pogingen over 7 dagen, dan downgrade naar gratis

16.4.4 BTW en factuur

Voor consumenten in NL: € 49,99 incl. 21% BTW

Factuur per mail (PDF) na elke betaling

Voor zakelijk: optie om BTW-nummer toe te voegen voor zakelijke factuur

17. Tijd-gebonden fiscale logica (KRITIEK)

Het platform moet automatisch omgaan met het verstrijken van fiscale mijlpalen. Dit is een van de belangrijkste onderdelen van de applicatie omdat fouten hier direct leiden tot foutieve belastingberekeningen en verwarring bij gebruikers.

17.1 Kalender van fiscale gebeurtenissen

Datum

Gebeurtenis

Systeem-actie

1 januari 2026

Peildatum belastingjaar 2026

Portfolio-snapshot vastleggen voor elke user

31 december 2026

Einde boekjaar 2026

Werkelijk rendement finaliseerbaar in Premium

1 januari 2027

Peildatum belastingjaar 2027

Nieuwe portfolio-snapshot vastleggen

1 maart 2027

Aangifte 2026 opent bij Belastingdienst

E-mail notificatie Premium: 'Aangifte-rapport beschikbaar'

1 mei 2027

Aangifte-deadline 2026 verstrijkt

KRITIEK: systeem schakelt verschuldigde-bedrag naar jaar 2027

1 mei 2028

Aangifte-deadline 2027 verstrijkt

Schakel naar 2028 + fase 2-logica activeert

17.2 Automatische peildatum-switch

KERNVEREISTE — het bedrag bovenaan Belastingpositie

Het bedrag bij 'Je verschuldigde belasting over JAAR' op de Belastingpositie-pagina moet automatisch updaten zodra de aangifte-deadline van 1 mei is verstreken. Na 1 mei 2027 mag het bedrag NIET meer gebaseerd zijn op peildatum 1 januari 2026 (belastingjaar 2026), maar op peildatum 1 januari 2027 (belastingjaar 2027). Vóór 1 mei 2027 blijft het 2026-jaar staan omdat de gebruiker dan nog kan aangeven. Dezelfde logica herhaalt zich jaarlijks.

17.2.1 Pseudocode van de logica

De backend moet bij elke request voor de Belastingpositie-data deze beslissing nemen:

Pseudocode

currentDate = today()relevantTaxYear = currentDate.yearif (currentDate < Date(currentDate.year, 5, 1)) {    relevantTaxYear = currentDate.year - 1}peildatum = Date(relevantTaxYear, 1, 1)vermogenOpPeildatum = fetchSnapshot(user, peildatum)verschuldigdeBelasting = calculateTax(vermogenOpPeildatum, relevantTaxYear)

17.2.2 Praktijkvoorbeelden

Zo valt de logica uit op verschillende momenten:

Huidige datum

Relevant belastingjaar

Relevante peildatum

Bedrag gebaseerd op

21 april 2026

2026

1 januari 2026

Vermogen op 1-1-2026 = € 64.820

30 april 2027

2026

1 januari 2026

Nog steeds 1-1-2026 (deadline niet verstreken)

1 mei 2027

2026

1 januari 2026

Nog steeds 1-1-2026 (deadline is vandaag)

2 mei 2027

2027

1 januari 2027

Nieuw: vermogen op 1-1-2027

15 oktober 2027

2027

1 januari 2027

Idem 1-1-2027

2 mei 2028

2028

1 januari 2028

Fase 2-logica activeert (vermogensaanwasbelasting)

17.3 UI-gedrag bij peildatum-switch

Wanneer de switch plaatsvindt (2 mei om 00:00 CET), moeten de volgende UI-elementen automatisch herberekenen en herladen zodra de pagina wordt opgevraagd:

Kicker boven page-header: "Belastingjaar 2026" → "Belastingjaar 2027"

Peildatum-tekst: "peildatum 1 januari 2026" → "peildatum 1 januari 2027"

Subtitle van de hero: "Berekend over je vermogen van € X op peildatum 1 januari 2026. Aanslag ontvang je in 2027." → "Berekend over € Y op peildatum 1 januari 2027. Aanslag ontvang je in 2028."

Hero-bedrag: grote euro-waarde updatet (bijv. € 174 → € 412)

Stap-voor-stap berekening: alle 7 stappen herberekenen met de nieuwe peildatum-waarde en de tarieven van het nieuwe jaar

Heffingsvrije grens-tracker: verschuift naar vooruitblik peildatum 1 januari 2028 (de volgende peildatum)

Disclaimer-blok boven tracker: "Let op: deze vooruitblik geldt voor de volgende peildatum (1 januari 2028)..."

In Werkelijk rendement view: YTD-data reset naar 1 januari 2027 als startdatum

17.4 E-mail notificaties rond de switch

Premium-gebruikers ontvangen automatische e-mails:

Datum

Onderwerp

Inhoud (samenvatting)

1 maart

Je aangifte-rapport 2026 is beschikbaar

Link naar Aangifte-rapport PDF + werkelijk rendement-check

15 april

Over 2 weken: aangifte-deadline 1 mei

Herinnering + check tegenbewijsregeling

30 april

Morgen deadline aangifte 2026

Laatste oproep + link naar rapport

2 mei

Je platform toont nu belastingjaar 2027

Uitleg over de switch + link naar nieuwe Belastingpositie

17.5 Historische data blijft toegankelijk

Ook na de switch moet de gebruiker historische aangifte-data kunnen raadplegen:

Dropdown boven de Belastingpositie-view met keuze: "Belastingjaar 2027 (huidig) / 2026 / 2025 / ..."

Bij selectie van historisch jaar: toont alle berekeningen voor dat jaar (read-only)

Aangifte-rapporten blijven eeuwig bewaard in Profiel → Documenten

Portfolio-snapshots op elke 1 januari blijven onbeperkt bewaard

Transactie-historie: onbeperkt, geen archivering

17.6 Implementatie-overwegingen

17.6.1 Timezone

Alle datum-vergelijkingen MOETEN in Europe/Amsterdam (CET/CEST) gebeuren. Server UTC is verkeerd — dan zou 1 mei 02:00 Nederlandse tijd al na 1 mei UTC zijn. Best practice: alle datum-logica via moment-timezone of native Intl met expliciete timezone-parameter.

17.6.2 Caching

De berekende verschuldigde belasting mag gecached worden voor performance, maar cache-key moet het relevantTaxYear bevatten. Simpelweg 'verschuldigde_belasting_user_X' is fout — na de switch zou dezelfde cache-key gebruikt worden maar met verouderde data.

17.6.3 Testen van de switch

Maak een config-vlag VIRTUAL_DATE die developers kunnen overschrijven voor testing. In staging kunnen ze dan handmatig de datum op 30 april 2027 of 2 mei 2027 zetten en zien dat de UI goed switcht. In productie is VIRTUAL_DATE altijd null → real date wordt gebruikt.

17.7 Fase 2 — vermogensaanwasbelasting

Hoewel buiten de scope van de MVP-release, moet de architectuur klaar zijn voor:

Vanaf belastingjaar 2028: forfaitair stelsel wordt vervangen door vermogensaanwasbelasting

Berekening wordt fundamenteel anders: waardestijging + directe ontvangsten worden belast, niet meer een fictief rendement

Rente-aftrek wordt mogelijk op schulden

Tarief en heffingsvrije grens moeten configureerbaar zijn per belastingjaar (config-tabel)

UI-kicker verandert: "Belastingjaar 2028 · vermogensaanwasbelasting"

Nieuwe datamodel-velden: realized_gains, unrealized_gains, deductible_interest, tax_liability_per_asset

18. Platform-integraties — technische details per platform

Per platform een gedetailleerde specificatie van hoe de integratie technisch werkt, wat opgehaald kan worden, waar de beperkingen zitten, en welke prioriteit het heeft. De 30+ platformen zijn gegroepeerd in vier categorieën.

Samenvatting prioriteit

MVP (eerste release): Bitvavo API + DEGIRO CSV + handmatige invoer voor overige platformen. Groeifase (eerste 6 maanden): IBKR/Lynx/MEXEM Flex, Coinbase, Bybit, Bitstamp API's + Kraken, Bitpanda, OKX API's + ABN AMRO/ING/Rabobank jaaropgave-parser + eToro/Crypto.com/Coinmerce CSV-parsers. Uitbreiding: Trading 212 (bij API-beta einde), Finst, Amdax, BUX Zero, Scalable, Flatex, Meesman/BND/Peaks jaaropgave, edelmetalen handmatig + prijs-API, Saxo Bank (bij partnership).

18.1 Aandelen/ETF-brokers

18.1.1 DEGIRO (BaFin, EER-paspoort)

Geschat NL-gebruikers: ~1.000.000 (dominant in NL)

Integratie: alleen CSV — geen officiële API beschikbaar

Waarschuwing — geen onofficiële API

Community-library 'degiro-connector' bestaat maar vereist credential-sharing (username + password van gebruiker), schendt DEGIRO's ToS en breekt regelmatig bij frontend-updates. Niet gebruiken voor consumer SaaS. Alleen CSV-import is verantwoord.

CSV-import mogelijkheden

Transactieoverzicht (CSV of XLSX): alle aan- en verkopen met datum, asset, hoeveelheid, prijs, koers, fees

Account Statement (CSV): stortingen, onttrekkingen, dividenden met aparte Dividendbelasting/bronbelasting regels, kosten

Jaarrapport (PDF): overzicht voor belastingaangifte

Wat is afleidbaar uit deze data

Volledige transactiehistorie reconstrueren

Cost basis berekenen (niet in CSV maar afleidbaar uit transactiehistorie)

Dividenden en bronbelasting per positie

Waarde op peildata via transacties + externe koers-API (yfinance, EODHD)

Beperkingen en implementatie

Gebruiker moet periodiek handmatig CSV exporteren en uploaden — geen real-time sync mogelijk

Koersdata niet in CSV — externe koers-API noodzakelijk voor doorlopende waardering

CSV-formaat: Nederlandse datumnotatie (dd-mm-yyyy), komma als decimaalteken, semicolon als scheidingsteken (mogelijk)

Prioriteit: ZEER HOOG — dominante broker in Nederland, goede CSV-parser is essentieel voor MVP

18.1.2 Interactive Brokers / Lynx / MEXEM (Ierland/Hongarije)

Geschat NL-gebruikers: ~50.000-150.000 (IBKR) + ~25.000-50.000 (Lynx) + ~25.000-75.000 (MEXEM)

Integratie: Flex Web Service (tweestaps: SendRequest → GetStatement) — retourneert XML-rapporten

Lynx en MEXEM zijn Nederlandse IBKR-resellers en gebruiken dezelfde Flex Web Service

Authenticatie

Flex Query token — geen credential-sharing, geen sessie-management nodig

Gebruiker genereert token in IBKR Client Portal → Reports → Flex Queries

Beschikbare data

Volledige transactiehistorie met per-trade fees

Dividenden met bronbelasting per land apart uitgesplitst (cruciaal voor Nederlandse bronbelasting-administratie)

Broker-rente ontvangen/betaald, corporate actions

Cost basis en cost basis price — native beschikbaar

FX-koersen naar basisvaluta, NAV-samenvattingen

Lookback: volledige accounthistorie

Beperkingen en implementatie

Geen real-time API — scheduled reports (gebruiker moet Flex Query configureren, ~dagelijks auto-run)

De TWS API en Client Portal Web API zijn ongeschikt voor consumer SaaS (vereisen actieve TWS-sessie)

CSV-fallback: Flex Queries leveren XML óf CSV

Prioriteit: Tier 1 — beste broker-integratie, bestaand parsing-patroon (Portfolio Performance, ibflex library als referentie)

18.1.3 Saxo Bank (Denemarken, EER-paspoort)

Geschat NL-gebruikers: ~200.000-400.000

API: technisch de beste broker-API van alle opties — OAuth2, native AverageOpenPrice (cost basis direct beschikbaar)

API-mogelijkheden

Historische accountwaardes via hist/v3/accountValues (direct bruikbaar voor peildatum)

Corporate actions met dividend/rente/bronbelasting-types netjes uitgesplitst

OAuth2-authenticatie (user-friendly)

Probleem

Commercieel gebruik vereist formeel partnerschap met Saxo Bank

Juridisch en compliance-traject van meerdere maanden

Implementatie-advies

CSV-fallback: SAXO biedt uitgebreide rapportages en exports. CSV-import is de pragmatische route totdat een partnerschap is gesloten

Prioriteit: partnership — alleen nastreven als de vraag het rechtvaardigt

18.1.4 Trading 212 (EER-paspoort)

Geschat NL-gebruikers: ~100.000-250.000

Status API: beta

API-beperkingen

FX-conversiekosten niet apart per trade in JSON (wel in CSV)

Type-veld op contante transacties ontbreekt in JSON maar staat wél in CSV

CSV-import mogelijkheden

Transactiehistorie als CSV — trades, dividenden (bruto en netto), stortingen, onttrekkingen

averagePrice (cost basis) wél beschikbaar via API maar niet in CSV

Implementatie-advies

CSV-import nu, heroverweeg API-koppeling wanneer Trading 212's 'major upgrade' uit beta komt

Prioriteit: afwachten

18.1.5 eToro (Cyprus, EER-paspoort)

Geschat NL-gebruikers: ~100.000-200.000

Status API: gelanceerd oktober 2025, nog in gated early-access met wachtlijst (april 2026). Retourneert alleen trade-level data — geen stortingen, onttrekkingen, dividenden, bronbelasting of kosten

CSV-import mogelijkheden

eToro Account Statement als XLSX — bevat alle trades, dividenden, fees, stortingen, onttrekkingen

eToro Tax Report PDF als aanvulling voor fiscale details

Beperkingen

Spreads verwerkt in open/close rates (niet apart weergegeven)

Overnight/rollover fees niet apart gerapporteerd

Prioriteit: CSV prio 2

18.1.6 BUX Zero (AFM, Nederland)

Geschat NL-gebruikers: ~50.000-100.000

Integratie: geen API beschikbaar. CSV-export via het platform

CSV-import: transactiehistorie als CSV — aan/verkopen, dividenden

Beperkingen: geen API, gebruiker moet handmatig exporteren, externe koers-API nodig voor doorlopende waardering

Prioriteit: CSV

18.1.7 Scalable Capital (BaFin, EER-paspoort)

Geschat NL-gebruikers: ~50.000-100.000

Integratie: geen API beschikbaar. CSV/rapport-export via het platform

Beperkingen: geen API, externe koers-API nodig

Prioriteit: CSV

18.1.8 Flatex (BaFin, EER-paspoort)

Geschat NL-gebruikers: ~25.000-75.000

Integratie: geen officiële API. Native export-mogelijkheden zeer beperkt — volledige export alleen via extern tool (Portfolio Performance o.i.d.)

CSV moet uit Flatex Classic geëxporteerd worden, niet uit Flatex Next

CSV-import: depotumsätze als CSV (beperkt), transacties en portfolio via extern tool exporteerbaar

Beperkingen: geen API, native export zeer beperkt, vereist mogelijk extern tool voor volledige data

Prioriteit: CSV

18.1.9 ABN AMRO / ING / Rabobank (Zelfbeleggen)

Geschat NL-gebruikers: ~500.000-800.000 (ABN) + ~400.000-700.000 (ING) + ~300.000-500.000 (Rabo)

Integratie: geen API voor beleggingsdata. PSD2/Open Banking dekt alleen betaalrekeningen, niet beleggingsrekeningen

Beschikbaar

Jaaropgave als PDF — bevat vermogensstand per 1 januari, ontvangen dividend, totale waarde beleggingen

Wordt ook automatisch gerenseigneerd aan de Belastingdienst

Implementatie-aanpak

Generieke jaaropgave-parser (PDF) bouwen die voor alle drie de banken werkt

Of handmatige invoer als snelle fallback

Beperkingen

Geen transactie-level data, alleen jaarlijkse snapshots

Geen real-time sync

Prioriteit: jaaropgave — belangrijk vanwege groot gebruikersaantal

18.2 Crypto-exchanges

18.2.1 Bitvavo (AFM, Nederland)

Geschat NL-gebruikers: ~1.000.000 (Nederlandse marktleider)

API: officiële REST API + WebSocket op https://api.bitvavo.com/v2/

Authenticatie: HMAC-SHA256, View-only key geeft alles wat nodig is

Rate limit: 1.000 gewichtspunten per minuut (ruim)

SDK's: officieel in Python, Node, Go, PHP, Java

Lookback: volledige accounthistorie

Beschikbare data

Volledige transactiehistorie via GET /account/history — getypeerd: trade, deposit, withdrawal, staking, distribution, affiliate, internal/external transfer

Stortingen/onttrekkingen apart via GET /depositHistory en GET /withdrawalHistory, met fee per item

Huidige posities via GET /balance

Historische koersen via GET /{market}/candles

Orderhistorie met filledAmount, feePaid, feeCurrency

Beperkingen

Geen peildatum-snapshot via API (Balance Statement PDF alleen via web-UI)

Geen cost basis — moet afgeleid worden uit transactiehistorie

CSV-fallback: CSV-export via website beschikbaar als back-up

Prioriteit: Tier 1 — eerste API-integratie, schoonste API van alle exchanges

18.2.2 OKX (Malta, gepassporteerd)

Geschat NL-gebruikers: ~50.000-150.000

API: REST API v5, HMAC-authenticatie, read-only instelbaar

MiCA: eerste globale MiCA-licentie (Malta, januari 2025)

Rate limit: per endpoint, typisch 5-20 req per 2-seconden window

Lookback: maximaal 3 maanden op bills-archive

Beschikbare data via API

Account-ledger via GET /api/v5/account/bills-archive — alle bewegingen inclusief simpele buy/convert (type CONVERT)

Spot trades via GET /api/v5/trade/fills-history — alleen orderboek-trades, GEEN simpele buys

Convert-historie via aparte endpoints (Get convert history, Get buy/sell trade history)

Aparte deposit/withdrawal/staking endpoints

CSV-export

Wél beschikbaar inclusief simpele aan- en verkopen, maar alleen per periode van maximaal 3 maanden per bestand

Voor een volledig jaar zijn minimaal 4 uploads nodig

Twee aparte exports nodig: Trading History + Funding History

Account Statements downloadbaar via Statement Center (afgelopen 12 maanden)

Beperkingen en kritieke architectuur-implicatie

API lookback max 3 maanden — MOET continu pollen (minimaal wekelijks) en data server-side archiveren

Zonder server-side archivering gaat data na 3 maanden verloren

Voor data vóór API-koppeling: CSV-upload (per 3 maanden, meerdere bestanden nodig voor volledige historie)

Geen cost basis

Prioriteit: Tier 2 — API-koppeling bouwen + CSV als fallback voor historische data

18.2.3 Bybit EU (Oostenrijk)

Geschat NL-gebruikers: ~50.000-150.000

API: REST API v5, HMAC-SHA256, Read-only permissies

MiCA: licentie via Oostenrijkse FMA (mei 2025), bedient Nederland via bybit.eu

Lookback: maximaal 2 jaar

Beschikbare data

Transactielogboek via GET /v5/account/transaction-log — types: TRADE, DEPOSIT, WITHDRAWAL, INTEREST, BONUS, AIRDROP, CONVERT, SETTLEMENT, FUNDING, FEE_REFUND

Lopend cashBalance veld per entry — point-in-time balansreconstructie mogelijk (handig voor peildatum-snapshots)

Aparte deposit/withdrawal endpoints met fees

Historische koersen via GET /v5/market/kline

Beperkingen

Lookback max 2 jaar — data voor die periode via CSV

Geen cost basis

CSV-fallback: beschikbaar

Prioriteit: Tier 1

18.2.4 Kraken (Ierland)

Geschat NL-gebruikers: ~50.000-100.000

API: REST API, HMAC-SHA512

Lookback: volledige accounthistorie

Beschikbare data

Ledger via POST /0/private/Ledgers — 11 typen: deposit, withdrawal, trade, staking, sale, transfer, rollover, credit, etc.

Trade history met fees per trade

Huidige posities

Historische koersen via OHLC endpoint (max 720 punten per call)

Beperkingen

Extreem lage rate limits — initiële sync ~20 minuten voor actieve gebruiker

Geen cost basis

CSV-fallback: uitgebreide CSV-exports via dashboard (Trades, Ledgers)

Prioriteit: Tier 2 — uitstekende data maar trage sync, CSV kan sneller zijn bij initiële import

18.2.5 Coinbase (Luxemburg)

Geschat NL-gebruikers: ~100.000-200.000

API: REST v2 + v3 Advanced Trade, OAuth2 beschikbaar

Lookback: volledige accounthistorie

Beschikbare data

Transacties via GET /v2/accounts/:id/transactions — 15+ typen inclusief staking_reward, interest, earn_payout

Trade fills met commissies via v3

Historische spotprijs op willekeurige datum via GET /v2/prices/{pair}/spot?date=YYYY-MM-DD — direct bruikbaar voor peildatum

Beperkingen

Twee API's nodig (v2 + v3 combineren)

Complexere JWT-authenticatie

Geen cost basis

CSV-fallback: beschikbaar

Prioriteit: Tier 1 — OAuth2 ideaal voor SaaS, beste historische-prijs endpoint van alle exchanges

18.2.6 Crypto.com (Malta)

Geschat NL-gebruikers: ~25.000-75.000

Belangrijk onderscheid

De Crypto.com App (retail, meeste NL-gebruikers) heeft geen publieke API. De Crypto.com Exchange (apart product, minderheid van gebruikers) heeft wél een uitstekende API met dagelijkse balanssnapshots. Implementatie-prioriteit: eerst CSV-import voor de App, optioneel API voor Exchange-gebruikers.

App (retail)

Alleen CSV-export via de app (buys, sells, staking rewards, deposits, withdrawals)

Exchange (API)

journal_type enum met TRADING, TRADE_FEE, DEPOSIT, WITHDRAWAL, STAKE_REWARD, INTEREST

Uniek: private/user-balance-history endpoint met dagelijkse balanssnapshots (ideaal voor peildatum)

Prioriteit: CSV prio 3 (App), optionele API voor Exchange-gebruikers

18.2.7 Bitpanda (Malta)

Geschat NL-gebruikers: ~25.000-75.000

API: REST API op https://api.bitpanda.com/v1/, API key authenticatie

MiCA: CASP + MiFID II (Oostenrijk)

Lookback: volledige accounthistorie

Beschikbare data

Crypto, fiat, edelmetalen én fractionele aandelen/ETF's via aparte endpoints per assetklasse

Trades, fiat-transacties, commodity-transacties, security-transacties

Uniek

Enige platform dat crypto + edelmetalen + aandelen/ETF's in één API combineert

Beperkingen

Dividend-typing fragiel (afhankelijk van purpose_text veld)

Geen datumfilter op transactielijsten

Rate limits niet gedocumenteerd

Geen cost basis voor crypto

CSV-fallback: CSV-export per assetklasse

Prioriteit: Tier 2 — unieke multi-asset waarde

18.2.8 Finst (AFM, Nederland)

Geschat NL-gebruikers: ~10.000-50.000

Integratie: geen publieke retail-API. Institutionele API beschikbaar voor partners.

CSV-export: transactiehistorie exporteerbaar — trades, deposits, withdrawals, staking rewards, fees. Filteren en sorteren mogelijk vóór export

Beperkingen: geen API-koppeling voor automatische sync, gebruiker moet periodiek exporteren

Prioriteit: CSV

18.2.9 Amdax (AFM, Nederland)

Geschat NL-gebruikers: ~10.000-25.000 (vermogende klanten, min. € 25.000 inleg)

Integratie: geen publieke retail-API. Gericht op persoonlijke dienstverlening

MiCA: licentie ontvangen

Beschikbaar: klanten ontvangen automatisch financieel overzicht met waarde van alle crypto-assets op 1 januari om 00:00 — direct bruikbaar voor peildatum

Beperkingen: kleine doelgroep, mogelijk alleen PDF-upload van jaaroverzicht

Prioriteit: CSV/PDF — relevant voor premium-gebruikers

18.2.10 Coinmerce / Blox

Geschat NL-gebruikers: ~850.000+ (Blox) + Coinmerce gebruikers (Blox overgenomen door Coinmerce in 2024)

Integratie: geen publieke API

CSV-export: via Orders → Exports kun je CSV downloaden van afgeronde orders

Jaaroverzicht beschikbaar via de app (waarde begin en einde jaar — bruikbaar voor peildatum)

Beperkingen: fees worden niet meegenomen in de CSV-export (let op!); Blox-data mogelijk alleen via Coinmerce-omgeving na overname

Prioriteit: CSV — groot gebruikersaantal door Blox

18.2.11 Binance

Geschat NL-gebruikers: ~50.000-100.000 (legacy)

Status: niet beschikbaar voor Nederlandse inwoners sinds juni/juli 2023 (DNB-exit). Geen MiCA CASP-registratie. Check huidig register voor updates

CSV-import: gebruikers die nog toegang hebben kunnen transactiehistorie als CSV exporteren. accountSnapshot API heeft slechts 30 dagen lookback

Prioriteit: legacy — alleen voor historische data-import

18.3 Edelmetaalplatformen

Geen enkel edelmetaalplatform biedt een API. De aanpak is voor allemaal hetzelfde: de gebruiker voert eenmalig in welk type metaal, hoeveel gram en de aankoopprijs. Het platform haalt via een externe prijs-API (GoldAPI.io, MetalpriceAPI) de koers op voor elke gewenste datum — peildatum, huidige waarde, of historisch. De gebruiker hoeft alleen bij te werken bij aan- of verkoop.

18.3.1 GoldRepublic (AFM-vergund)

Geschat NL-gebruikers: ~50.000-100.000

Integratie: handmatige invoer. Jaaropgave beschikbaar als verificatie

Prioriteit: handmatig + externe prijs-API

18.3.2 Holland Gold (webwinkel, geen AFM-vergunning nodig)

Geschat NL-gebruikers: ~25.000-50.000

Integratie: handmatige invoer. Geen CSV, geen jaaropgave

Prioriteit: handmatig + externe prijs-API

18.3.3 Goudzaken

Geschat NL-gebruikers: ~10.000-25.000

Integratie: handmatige invoer. Geen CSV, geen jaaropgave

Prioriteit: handmatig + externe prijs-API

18.3.4 Silver Mountain

Geschat NL-gebruikers: ~10.000-25.000

Integratie: handmatige invoer. Geen CSV, geen jaaropgave

Prioriteit: handmatig + externe prijs-API

18.4 Indexfondsen en vermogensbeheer

Geen van deze platformen biedt een API. Het zijn typisch simpele portefeuilles (1-3 fondsen, weinig transacties). De aanpak is jaaropgave-import of handmatige invoer.

18.4.1 Meesman (AFM)

Geschat NL-gebruikers: ~50.000-100.000

Integratie: jaaropgave PDF. Geen API, geen CSV

Wat je krijgt: waarde per 1 januari, ontvangen dividend

Prioriteit: jaaropgave

18.4.2 Brand New Day

Geschat NL-gebruikers: ~25.000-50.000

Integratie: jaaropgave PDF. Geen API, geen CSV

Prioriteit: jaaropgave

18.4.3 Peaks (onderdeel Rabobank)

Geschat NL-gebruikers: ~100.000-250.000

Integratie: geen API, geen CSV-export. App toont transacties maar biedt geen export

Peaks rapporteert de waarde van beleggingen aan de Belastingdienst (BSN vereist bij registratie)

Aanpak: handmatige invoer van vermogenswaarde, of gebruik de vooringevulde gegevens van de Belastingdienst als verificatie

Prioriteit: jaaropgave/handmatig

18.4.4 Bux (fondsen, AFM)

Geschat NL-gebruikers: ~50.000-100.000

Integratie: CSV-export beschikbaar. Geen API

Prioriteit: CSV

18.5 Overzichtstabel — alle 30 platformen

Platform

Primair

Rol CSV

Lookback

Cost basis

Peildatum

Prioriteit

Bitvavo

API

Fallback

Volledig

❌

❌ Reconstructie

Tier 1

Coinbase

API

Fallback

Volledig

❌

✅ Spotprijs/datum

Tier 1

Bybit EU

API

Voor data >2 jaar

2 jaar

❌

⚠️ via cashBalance

Tier 1

IBKR/Lynx/MEXEM

API (Flex)

Fallback

Volledig

✅ Native

✅ via NAV

Tier 1

Kraken

API

Sneller dan API

Volledig

❌

❌ Reconstructie

Tier 2

Bitpanda

API

Fallback

Volledig

❌

❌ Reconstructie

Tier 2

OKX

API (3mnd) + CSV

CRUCIAAL voor historie

3 maanden

❌

❌ Reconstructie

Tier 2

DEGIRO

CSV

Enige optie

Volledig

⚠️

❌ Ext. koers-API

CSV prio 1

eToro

CSV/XLSX

Enige optie

Volledig

✅ OpenRate

❌

CSV prio 2

Crypto.com App

CSV

Enige optie (App)

Volledig

❌

❌

CSV prio 3

Coinmerce/Blox

CSV

Enige optie

Volledig

❌

✅ Jaaroverzicht

CSV

Finst

CSV

Enige optie

Volledig

❌

❌

CSV

Amdax

CSV/PDF

Enige optie

Volledig

❌

✅ Jaaroverzicht 1 jan

CSV

Trading 212

CSV (API beta)

Primair nu

Volledig

✅ averagePrice

❌

Afwachten

BUX Zero

CSV

Enige optie

Volledig

❌

❌

CSV

Scalable Capital

CSV

Enige optie

Volledig

❌

❌

CSV

Flatex

CSV

Enige optie (beperkt)

Volledig

❌

❌

CSV

Bux (fondsen)

CSV

Enige optie

Volledig

❌

❌

CSV

Saxo Bank

Partnership

Pragmatische route

Volledig

✅ Native

✅ Native

Partnership

ABN AMRO

Jaaropgave PDF

Enige optie

Jaarlijks

❌

✅ Jaaropgave

Jaaropgave

ING

Jaaropgave PDF

Enige optie

Jaarlijks

❌

✅ Jaaropgave

Jaaropgave

Rabobank

Jaaropgave PDF

Enige optie

Jaarlijks

❌

✅ Jaaropgave

Jaaropgave

Meesman

Jaaropgave PDF

Enige optie

Jaarlijks

❌

✅ Jaaropgave

Jaaropgave

Brand New Day

Jaaropgave PDF

Enige optie

Jaarlijks

❌

✅ Jaaropgave

Jaaropgave

Peaks

Handmatig

Geen export

Jaarlijks

❌

✅ via Belastingdienst

Jaaropgave

GoldRepublic

Handmatig + API

Jaaropgave

n.v.t.

❌

❌ Ext. prijs-API

Handmatig

Holland Gold

Handmatig + API

Geen export

n.v.t.

❌

❌ Ext. prijs-API

Handmatig

Goudzaken

Handmatig + API

Geen export

n.v.t.

❌

❌ Ext. prijs-API

Handmatig

Silver Mountain

Handmatig + API

Geen export

n.v.t.

❌

❌ Ext. prijs-API

Handmatig

Binance

CSV (legacy)

Enige optie (NL gesloten)

Beperkt

❌

⚠️ 30 dagen

Legacy

19. Koersdata en prijs-APIs

MijnVermogen heeft koersdata nodig om de waarde van posities op peildata (1 januari, 31 december) en doorlopend te berekenen. Het platform bouwt hiervoor ÉÉN centrale koersdatabase — niet per gebruiker, maar voor het hele platform. De koers van Bitcoin of ASML is overal hetzelfde, dus één dagelijkse opvraging volstaat voor alle gebruikers.

19.1 Crypto — exchange API's als universele koersbron

Voor crypto hoeft het platform geen externe koers-API in te kopen. De grote crypto-exchanges (Bitvavo, Coinbase, Kraken, OKX, Bybit, Bitstamp, Bitpanda) hebben naast hun privé-API (waar gebruikers met een API-key hun eigen accountdata ophalen) ook een publiek deel van diezelfde API. Dat publieke deel bevat marktdata: actuele en historische koersen van alle verhandelde assets. Het is gratis te gebruiken, vereist geen API-key, geen account en geen authenticatie — een simpele HTTP-aanroep volstaat. Concreet voorbeeld: de BTC/EUR-koers op een willekeurige datum is op te halen via Bitvavo's GET /{market}/candles endpoint, zonder dat het platform of de eindgebruiker daarvoor hoeft in te loggen. 

19.2 Aandelen & ETF's — altijd een externe koers-API nodig

Geen enkele broker-API die MijnVermogen integreert biedt een bruikbare universele koersbron voor aandelen en ETF's:

Interactive Brokers (Flex Web Service): de Flex Queries leveren alleen rapportages over de posities van die specifieke gebruiker — geen publiek koers-endpoint. De IBKR TWS/Web API biedt wél historische koersdata, maar vereist een gefinancierd IBKR-account (minimaal $500) plus betaalde marktdata-abonnementen per exchange. Die abonnementen zijn per gebruiker — je kunt niet één IBKR-account gebruiken als koersbron voor het hele platform.

Saxo Bank: heeft publieke marktdata-endpoints, maar commercieel gebruik vereist het partnerschap dat je toch al nodig hebt voor de transactie-integratie.

Trading 212, eToro, DEGIRO: geen publieke koers-endpoints beschikbaar.

MijnVermogen heeft daarom een externe koers-API nodig voor aandelen en ETF's:

Provider

Dekking

Gratis tier

Betaald

yfinance (Python library)

Aandelen, ETF's, fondsen, indices wereldwijd incl. Euronext Amsterdam

Volledig gratis

—

EODHD

150.000+ tickers wereldwijd incl. Euronext Amsterdam

Beperkt gratis

Vanaf ~$20/mnd

Twelve Data

Aandelen, ETF's, forex, crypto, real-time + historisch

Beperkt gratis

Vanaf ~$29/mnd

Aanbeveling

Start met yfinance voor de MVP (gratis, dekt Euronext Amsterdam). Het is een onofficiële library die Yahoo Finance scrapet en kan breken, dus bouw op termijn een fallback naar EODHD of Twelve Data als betrouwbare betaalde bron.

19.3 Edelmetalen — altijd een externe prijs-API nodig

Geen enkel edelmetaalplatform biedt een API. Gebruik GoldAPI.io, MetalpriceAPI of Metals.Dev (~€10-15/mnd) voor goud, zilver, platina en palladium. Dagelijkse prijs-update om 17:00 UTC volstaat voor peildatum-doeleinden.

19.4 Samenvatting koersbronnen

Asset-categorie

Koersbron

Extern nodig?

Crypto (exchange én eigen wallet)

Exchange API's (Bitvavo, Coinbase etc.) — publiek, gratis

❌ Nee

Aandelen & ETF's

Externe API: yfinance (gratis) → EODHD/Twelve Data (betaald)

✅ Altijd

Indexfondsen

Zelfde externe API als aandelen/ETF's

✅ Altijd

Edelmetalen

Externe prijs-API: GoldAPI.io, MetalpriceAPI

✅ Altijd

20. CSV-verwerking en databeheer

20.1 Per-platform CSV-parsers

Elke broker/exchange heeft een eigen CSV-formaat. Het platform heeft een PlatformAdapter-architectuur waarbij elk platform zijn eigen parser krijgt. De parsers leven in een aparte module en worden via een factory geladen op basis van het platform-slug.

20.2 Generieke CSV-verwerkings-flow

Gebruiker upload bestand via drag-and-drop of file-picker

Server detecteert encoding (UTF-8, Windows-1252, ISO-8859-1) en delimiter (komma, semicolon, tab)

Server roept platform-specifieke parser aan op basis van platform_slug

Parser retourneert genormaliseerde Transaction-objecten met source='csv'

Duplicate-detectie op basis van external_id (platform-specifieke transactie-ID) of fingerprint (datum + asset + aantal + prijs hash)

Preview tonen aan gebruiker: X gedetecteerd / Y duplicaten / Z fouten

Bij confirm: bulk-insert in database, refresh holdings, herbereken cost basis

20.3 Belangrijke CSV-quirks per platform

DEGIRO: Nederlandse datumformaat (dd-mm-yyyy), komma als decimaalteken, mogelijk semicolon-separated. Aparte exports voor Transacties en Account Statement.

Trading 212: FX-conversiekosten apart per trade in CSV (niet in API). Eén export voor alles.

OKX: Maximaal 3 maanden per export-bestand. Voor één jaar: minimaal 4 uploads. Twee aparte exports nodig (Trading History + Funding History).

Coinmerce/Blox: Fees worden NIET meegenomen in CSV-export. Apart parsen of negeren.

Bitvavo CSV-fallback: Comma-separated, UTF-8, Engelse datumformaat. Fees in fee_paid kolom.

Kraken: Twee aparte exports nodig: Trades.csv en Ledgers.csv. Combineren voor volledige historie.

Bybit (CSV-fallback voor data ouder dan 2 jaar API-lookback): Export via Assets → Funding Account → History → Data Export (of via Account → Data Export). Levert een ZIP-bestand dat eerst uitgepakt moet worden — daarin zitten meerdere CSV's gesplitst per data-type (Asset Change voor stortingen/onttrekkingen, Unified Account voor Spot/Derivatives). Maximaal 12 maanden per export, dus voor langere periodes meerdere exports combineren. Het platform moet ZIP-uitpakken server-side ondersteunen en de losse CSV's mergen naar één geïntegreerde transactiehistorie. 

eToro: Account Statement als XLSX (niet CSV). Tax Report PDF voor fiscale details. averagePrice (cost basis) is wel in CSV beschikbaar via OpenRate kolom.

20.4 PDF-jaaroverzicht parsers

Voor banken (ABN, ING, Rabobank) en indexfondsen (Meesman, Brand New Day) is de jaaropgave de enige bron. Parsing-aanpak:

Library: pdfplumber (Python) of pdf-parse (Node)

Per platform een aparte parser met eigen regex en kolomdetectie

Validatie: minimum-fields check (beginsaldo, eindsaldo, totaal dividend) — bij missende velden om handmatige aanvulling vragen

Robuust tegen jaarlijkse layout-wijzigingen: parser-version per jaar (Meesman 2024, Meesman 2025, etc.)

20.5 Data-validatie en deduplicatie

20.5.1 Duplicate-detectie strategieën

Niveau 1: external_id (zoals trade-ID van Bitvavo, order-ID van DEGIRO). Indien aanwezig: deduplicatie hierop

Niveau 2: fingerprint hash van (transaction_date + asset_symbol + quantity + price_per_unit + platform_id). Bij identieke fingerprint: duplicate

Niveau 3: handmatige conflictresolutie als beide niveaus mismatchen — UI toont 'mogelijke duplicate, verschil in fees' met merge/keep-both keuzes

20.5.2 Validatie-regels

transaction_date moet in het verleden liggen (geen toekomstige transacties toegestaan, behalve recurring)

quantity > 0 voor buy/sell/dividend

price_per_unit > 0 voor buy/sell

currency moet bestaan in valid currencies-list (EUR, USD, GBP, CHF, etc.)

Bij niet-EUR currency: exchange_rate verplicht

21. Drie kritieke technische bouwblokken

Het marktonderzoek identificeert drie technische problemen die los van platform-integratie opgelost moeten worden voor een werkend platform.

21.1 Cost basis berekening

De aankoopwaarde van een positie is fundamenteel voor winstberekening en om tot het werkelijke rendement te komen.

21.1.1 Het probleem

Bijna geen enkele platform-integratie levert cost basis direct mee:

✅ Heeft cost basis: IBKR (native), Saxo (AverageOpenPrice), eToro (OpenRate), Trading 212 API (averagePrice)

❌ Geen cost basis: Bitvavo, Coinbase, Kraken, OKX, Bybit, Bitpanda, Crypto.com, Binance, DEGIRO (niet in CSV), Trading 212 CSV

21.1.2 De oplossing

Het platform berekent doorlopend de cost basis per positie — de gemiddelde aankoopprijs van wat de gebruiker bezit. Daarvoor wordt vanaf fase 1 de gewogen gemiddelde methode gehanteerd: bij elke aankoop wordt total_cost en total_quantity opgehoogd, bij elke verkoop wordt naar rato verlaagd. Cost basis per stuk = total_cost / total_quantity.

Deze methode is voldoende voor:

Het tonen van rendement per positie aan de gebruiker (gerealiseerde winst bij verkoop én ongerealiseerde winst op nog gehouden posities)

De wet werkelijke rendement in fase 1 (forfaitair stelsel) — die werkt op portfolio-niveau via eindwaarde − beginwaarde − netto inleg + dividend + staking + rente − kosten. Welke specifieke aankoop verkocht is doet er niet toe

Vermogensaanwasbelasting in fase 2 — ook al valt gerealiseerde winst hieronder, de berekening kijkt naar de totale waardeverandering van de portefeuille tussen 1 januari en 31 december. Een verkoop in juli zit automatisch al in de eindwaarde verwerkt (als cash of nieuwe positie). Een aparte lot-toewijzing is niet nodig

FIFO (First In, First Out) en LIFO (Last In, First Out) zijn alternatieve methodes waarbij verkopen specifiek aan de oudste of nieuwste aankoop worden toegerekend. Dit wordt pas fiscaal relevant bij een eventuele vermogenswinstbelasting (fase 3, toekomst), omdat je dan belasting betaalt op het moment van verkoop en de keuze van toewijzing direct invloed heeft op het belastingbedrag.

Voor fase 1 hoeven FIFO en LIFO dus niet als optie aan de gebruiker te worden aangeboden. Wel moet de architectuur deze methodes kunnen ondersteunen voor latere uitbreiding — concreet betekent dit dat elke aankoop apart wordt opgeslagen met datum, aantal en prijs (in plaats van alleen aggregaten te bewaren). De gewogen gemiddelde berekening leidt het platform daaruit af, maar de onderliggende lot-data blijven beschikbaar voor toekomstige fases.

21.2 Peildatum-snapshots

Voor box 3 is de waarde op 1 januari 00:00 fundamenteel. Geen enkele exchange-API levert deze snapshot direct (behalve Bitvavo's PDF en Crypto.com Exchange's user-balance-history endpoint).

21.2.1 De snapshot-berekening

MijnVermogen genereert peildatum-snapshots door alle transacties met datum ≤ peildatum te aggregeren tot de positiestand op die datum, en die te waarderen tegen de koers op de peildatum:

Per gebruiker: alle transacties (uit API-sync, CSV-uploads, PDF-imports en handmatige invoer) met transaction_date op of vóór de peildatum verzamelen

Per asset het totaal aantal berekenen op basis van die transacties (aankopen − verkopen + stortingen − onttrekkingen)

Per asset de koers op de peildatum ophalen uit de centrale koers-database (zie hoofdstuk 19)

PortfolioSnapshot-record aanmaken met snapshot_date = jjjj-01-01, holdings_snapshot_json met volledige detail per positie

Een eerste snapshot wordt automatisch gegenereerd door een cron-job op 1 januari 00:00 CET

De snapshot wordt locked = true vanaf 1 mei van het volgende jaar (na aangifte-deadline)

21.2.2 Snapshot-herberekening bij latere data-aanvulling

Een snapshot is niet alleen een momentopname op 1 januari — het is een berekening op basis van álle bekende transacties tot en met de peildatum. Gebruikers voegen vaak pas later data toe die wél historisch is:

Een gebruiker registreert in maart 2027 en uploadt zijn DEGIRO-CSV met transacties tot eind december 2026 — die transacties moeten meetellen in de snapshot van 1 januari 2027

Een gebruiker koppelt in juli 2027 zijn Meesman-jaaroverzicht 2026 — de eindwaarde 2026 moet de snapshot van 1 januari 2027 vullen of corrigeren

Een gebruiker voegt in oktober 2027 handmatig een vergeten goud-aankoop van november 2026 toe — de snapshot moet bijgewerkt worden

Het platform moet daarom:

Bij elke nieuwe transactie controleren of de transaction_date vóór een bestaande peildatum valt

Als dat zo is en de bijbehorende snapshot is niet locked: de snapshot automatisch herberekenen en het bijgewerkte resultaat opslaan

Als dat zo is en de snapshot is wel locked (na 1 mei van het opvolgende jaar): de transactie wel registreren maar de snapshot ongewijzigd laten, met een waarschuwing aan de gebruiker dat deze toevoeging niet meer in het rapport van dat jaar verwerkt kan worden

21.2.3 Herinneringsmails vóór de aangifte-deadlines

Omdat snapshots alleen automatisch herberekenen zolang ze niet locked zijn, moet de gebruiker actief gewezen worden op het belang van complete data vóór 1 mei. Het platform stuurt daarom proactief herinneringsmails in de weken voor de deadline:

Begin maart: eerste herinnering — "De aangifte voor belastingjaar [JJJJ-1] is geopend. Controleer of al je transacties van vorig jaar in MijnVermogen staan, zodat je peildatum-snapshot van 1 januari klopt."

Begin april: tweede herinnering — overzicht van platformen die mogelijk niet up-to-date zijn (CSV ouder dan 60 dagen, jaaroverzichten die nog niet zijn geüpload, gekoppelde API's met sync-fouten). Per platform een directe link om de data aan te vullen

Twee weken vóór 1 mei: laatste herinnering — "Nog 2 weken tot de aangifte-deadline. Hierna wordt je peildatum-snapshot definitief vastgezet en kunnen latere wijzigingen niet meer verwerkt worden in dit aangiftejaar."

Op 1 mei: bevestiging dat de snapshot definitief is vastgezet, met overzicht van wat is meegenomen

Deze herinneringen zijn alleen van toepassing voor Premium-gebruikers, omdat alleen zij de Belastingpositie- en Werkelijk rendement-views gebruiken. Notificatie-voorkeuren in het profiel laten gebruikers de e-mails uitzetten als ze die niet wensen.

21.2.4 Edge cases

Gebruiker registreert in maart 2027 zonder eerdere data: snapshot 1-1-2027 reconstructie via transactiehistorie zoals die binnenkomt + historische koersen uit de centrale koers-database

Gebruiker koppelt nieuwe broker in juli 2027: vraag om CSV met historie tot 1-1-2027, herbereken de snapshot

Gebruiker corrigeert een bestaande transactie (bv. fout aantal): snapshot herberekenen tenzij locked

Gebruiker verwijdert een transactie: idem

Bij correctie ná locking: melding tonen en transactie wel registreren voor toekomstige berekeningen, maar snapshot niet wijzigen

21.3 Centrale koersdatabase

Eén tabel KoersData in de database, gevuld door scheduled jobs:

Veld

Type

Beschrijving

asset_symbol

VARCHAR(20)

BTC / ASML / IWDA / AU

asset_category

ENUM

crypto / stock / etf / fund / metal

price_date

DATE

Datum van de koers

price_eur

DECIMAL(14,6)

Slotkoers in EUR

source

VARCHAR(50)

bitvavo_api / yfinance / goldapi

fetched_at

TIMESTAMP

Wanneer opgehaald

Indexen op (asset_symbol, price_date) voor snelle lookups. Eén centrale opslag voorkomt dat dezelfde koers voor 1.000 gebruikers 1.000 keer wordt opgehaald.

22. Algemene technische randvoorwaarden

22.1 Stack-suggesties (niet bindend)

De ontwikkelpartij is vrij in stack-keuze. Onderstaand zijn referenties die past bij de prototype-implementatie:

22.1.1 Frontend

Framework: React 18+ of Vue 3+ (de prototypes zijn vanilla HTML/CSS/JS, framework-keuze is open)

Styling: CSS custom properties (gebruikt in prototypes) + utility framework als gewenst

Fonts: Fraunces (serif, voor display), JetBrains Mono (monospace, voor numerieke waarden), Inter (sans, voor body)

Charts: custom SVG (zoals in prototypes) of een library — maar custom geeft meeste controle over branding

State management: Context API + SWR / TanStack Query voor server-state

Theme: dark/light toggle via class op html-element + CSS custom properties

22.1.2 Backend

Runtime: Node.js LTS, Python 3.11+, of Go (alle drie geschikt)

Framework: NestJS / Express / FastAPI / Gin

API stijl: REST (eenvoudigst) of GraphQL (flexibel)

Database ORM: Prisma, TypeORM, SQLAlchemy

Authentication: JWT + refresh tokens, 2FA via TOTP

Queue-systeem voor sync-jobs en mail: BullMQ (Node), Celery (Python), of native job-runner

22.1.3 Database en infrastructuur

Database: PostgreSQL 15+ (uitstekende JSONB support voor snapshots)

Cache: Redis voor sessies en koers-cache

Object storage: S3-compatible (AWS S3, Wasabi, MinIO) voor PDF's

Hosting: AWS Frankfurt (eu-central-1) of Hetzner Cloud (NL/Helsinki) — beide GDPR-compliant

Container-orchestratie: Docker Compose (klein) of Kubernetes (groot)

CI/CD: GitHub Actions / GitLab CI

Monitoring: Sentry (errors), Grafana + Prometheus (metrics)

22.1.4 Third-party services

Betalingen: Mollie (NL voorkeur, iDEAL native) of Stripe (internationaal)

Transactionele e-mail: Postmark, SendGrid, of AWS SES

Edelmetaal-prijzen: GoldAPI.io, MetalpriceAPI

Aandelen-koersen: yfinance (gratis fallback) of EODHD (betaald, robuuster)

Crypto-koersen: gekoppelde exchange-API's (zie hoofdstuk 19) + CoinGecko als fallback

Encryption keys: AWS KMS, HashiCorp Vault, of Hetzner Vault

22.2 Architectuur — PlatformAdapter pattern

Elke platform-integratie wordt geabstraheerd achter een gemeenschappelijke interface zodat nieuwe platformen eenvoudig toegevoegd kunnen worden zonder de core-logica aan te passen:

PlatformAdapter interface (TypeScript-style)

interface PlatformAdapter {  authenticate(credentials: Credentials): Promise<AuthResult>;  fetchBalances(): Promise<Holding[]>;  fetchTransactions(since: Date): Promise<Transaction[]>;  validateConnection(): Promise<boolean>;  parseImport?(file: Buffer, type: 'csv' | 'pdf'): Promise<Transaction[]>;}

Concrete implementaties: BitvavoApiAdapter, DEGIROCsvAdapter, MeesmanPdfAdapter, IBKRFlexAdapter, etc. Een SyncWorker job pickt platformen op uit de queue en synct via de adapter.

22.3 Sync-strategie

22.3.1 API-sync frequentie

Balances (portfolio-waarde): elke 5 minuten tijdens kantooruren, elke 30 min 's nachts

Transacties: elke 15 minuten

Rate-limit aware: bij approach van limit, throttle en retry met exponential backoff

OKX speciaal: dagelijkse sync verplicht (3-maanden lookback) + server-side archivering

Foutenafhandeling: 3 retries, dan status='error' + e-mail naar gebruiker

22.3.2 CSV/PDF upload sync

Handmatig geïnitieerd door gebruiker

Bij upload: parse direct, toon preview, wacht op confirm, importeer

Audit-log: wat is wanneer door wie geüpload (user_id, timestamp, file_hash)

22.3.3 Koersdata-sync (centraal)

Crypto: dagelijks op een vast tijdstip via exchange API's voor alle assets in database

Aandelen/ETF/indexfondsen: dagelijks via yfinance/EODHD

Edelmetalen: dagelijks via GoldAPI

Bij elke nieuwe holding: backfill historische koersen vanaf transactie-datum

22.4 Schaalbaarheid

Stateless application servers, load-balanced

Database: read-replicas voor dashboard queries, master voor writes

Caching: prijs-data 5 min TTL in Redis, user-profile 1 uur TTL

Sync-jobs: horizontaal schaalbaar via job-queue workers

23. Beveiliging en privacy

23.1 Gevoelige datacategorieën

Het platform verwerkt fiscaal en financieel gevoelige data. De volgende vereisten zijn niet-onderhandelbaar, ongeacht de gekozen technische stack.

23.1.1 API-keys van gekoppelde platforms

API-keys geven toegang tot de financiële accounts van de gebruiker bij externe partijen. Behandeling moet daarom aan deze eisen voldoen:

Encrypted at rest met een industriestandaard sterke symmetrische encryptie

Encryptie-keys beheerd via een dedicated key management oplossing — nooit als plaintext in code, config of database

Aparte encryptie-keys per environment (development, staging, productie)

Alleen read-only API-keys geaccepteerd waar het externe platform dit ondersteunt — bij platformen zonder dit onderscheid duidelijke waarschuwing aan gebruiker

Gebruiker kan op elk moment een API-key revoken vanuit Mijn platformen

Bij langdurige inactiviteit (richtlijn: 90 dagen): automatische revoke met e-mail notificatie

23.1.2 Portfolio-data, transactiehistorie en overig vermogen

Database encryption at rest verplicht

Strikte data-isolatie tussen gebruikers, afgedwongen op database-niveau (niet alleen op application-niveau)

Audit-log voor write-acties: welke gebruiker heeft wanneer welke wijziging gedaan

Gevoelige velden niet in logs, niet in error-messages, niet in URL-parameters

23.2 Authenticatie en autorisatie

Wachtwoord-opslag: moderne hashing (geen MD5/SHA1, geen plaintext)

Sterke wachtwoord-eisen bij registratie en wijziging

2FA via TOTP — optioneel voor gratis, verplicht voor Premium

Korte-lifespan sessies met refresh-mechanisme

Rate-limiting op login-endpoint met tijdelijke account-lock bij overschrijding

Detectie van login vanaf nieuwe locatie of device, met e-mail-notificatie naar gebruiker

CAPTCHA-bescherming bij verdacht patroon

23.3 GDPR/AVG compliance

23.3.1 Recht op inzage (Art. 15)

Gebruiker kan via Profiel een volledige data-export downloaden van alle persoonlijke data. Levering binnen de wettelijke termijn van 30 dagen — meestal direct beschikbaar, eventueel asynchroon voor grote datasets.

23.3.2 Recht op verwijdering (Art. 17)

Account-verwijder optie in Profiel

Soft-delete met herstelperiode (richtlijn: 30 dagen) waarin gebruiker kan terugkeren

Na de herstelperiode: volledige verwijdering, ook uit backups bij volgende rotatie

Uitzondering: financiële logs voor wettelijke bewaartermijn (geanonimiseerd)

23.3.3 Data-processor agreements

Met elke externe dienstverlener die persoonsgegevens verwerkt (hosting, betalingen, e-mail, koersdata, monitoring) moet een geldige verwerkersovereenkomst (DPA) worden afgesloten. Alle processors moeten binnen de EU gevestigd zijn óf onder een geldig adequacy-besluit van de Europese Commissie vallen.

23.3.4 Privacyverklaring en cookies

Privacyverklaring permanent toegankelijk vanuit footer

Cookie-consent vóór niet-essentiële cookies — analytische cookies opt-in, niet opt-out

Geen tracking-cookies van derden, geen analytics zonder consent

Affiliate-links naar externe platformen (zie hoofdstuk 14) duidelijk gemarkeerd in privacyverklaring

23.4 Beveiligings-audits

Externe penetratietest vóór publieke launch

Periodieke herhaalde pen-tests (richtlijn: jaarlijks)

Continu geautomatiseerd security-scanning in de CI/CD-pipeline

Bekende kwetsbaarheden in dependencies actief monitoren en patchen

23.5 Disaster recovery en backups

Geautomatiseerde backups met meerdere herstel-punten per dag

Backups encrypted at rest en geografisch gescheiden van productie

RPO (Recovery Point Objective) en RTO (Recovery Time Objective) vooraf vastleggen in SLA — afhankelijk van hosting-keuze van de ontwikkelpartij

Periodieke restore-drills om aan te tonen dat backups daadwerkelijk werkbaar zijn

Einde document

Dit FSD versie 1.0 beschrijft fase 1 van het MijnVermogen platform op basis van de werkende HTML-prototypes (fase-1-forfaitair-gratis.html en fase-1-forfaitair-premium.html) en het marktonderzoek-document.

Wijzigingen op dit document worden vastgelegd in een versiebeheer-log. Elke aanpassing die de scope van fase 1 wijzigt, vereist expliciete goedkeuring van opdrachtgever.
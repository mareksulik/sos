# Share of Search Tool - Lead Magnet

Toto je zjednodušená verzia Share of Search Tool, ktorá slúži ako lead magnet na webe. Aplikácia umožňuje návštevníkom získať analýzu podielu vyhľadávania pre zadané kľúčové slová, krajinu a jazyk výmenou za ich email.

## Funkcie

- Jednoduchý formulár pre zadanie kľúčových slov, krajiny, jazyka a emailu
- Zobrazenie 5 grafov analýzy jednej krajiny:
  1. Ročný podiel vyhľadávania
  2. Priemerný mesačný objem segmentu
  3. Priemerný mesačný objem konkurentov
  4. Priemerný mesačný objem konkurentov (Skladaný stĺpcový)
  5. Tempo rastu
- Ukladanie informácií o leadoch do súboru leads.csv
- Prispôsobený dizajn s nastavenou farebnou schémou (#202028, #F1F0EB, #DAEC34)
- Limit použitia emailovej adresy (maximálne 3x)
- GDPR súhlas na spracovanie osobných údajov
- Validácia emailovej adresy

## Spustenie aplikácie

```bash
streamlit run lead_magnet_app.py
```

## Prispôsobenie

1. **Logo**: Nahraďte súbor `snag.png` vaším vlastným logom.
2. **Farby**: Upravte CSS farby v konštante `CUSTOM_CSS` podľa vašej firemnej identity.
3. **Ukladanie leadov**: Upravte funkciu `save_lead_info()` pre integráciu s vaším CRM systémom.
4. **Predvolené hodnoty**: Aktualizujte predvolené kľúčové slová, krajinu a jazyk v hlavnej funkcii `main()`.

## Porovnanie s plnou verziou

Táto zjednodušená verzia neobsahuje:
- Postranný panel (sidebar)
- Autentifikáciu pomocou PIN kódu
- Analýzu viacerých krajín
- Nastavenie granularity (je fixne nastavená na ročnú)
- Históriu vyhľadávaní
- Loading hlásky API
- Možnosť sťahovania grafov

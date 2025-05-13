# Share of Search Tool 📊📈

Jednoduchá [Streamlit](https://streamlit.io/) aplikácia na vizualizáciu a analýzu "Share of Search" (podielu vyhľadávania) pre zadané kľúčové slová pomocou dát z [DataForSEO API](https://dataforseo.com/). Aplikácia bola vytvorená s pomocou Google Gemini.

## Funkcie

Aplikácia ponúka dva hlavné režimy analýzy:

**1. Analýza jednej krajiny:**
* **Získavanie dát:** Načíta historické mesačné objemy vyhľadávania pre zadané kľúčové slová, vybranú krajinu a jazyk z DataForSEO Google Ads Search Volume API.
* **Vizualizácia podielu (SoS):** Zobrazí vývoj podielu jednotlivých kľúčových slov na celkovom objeme vyhľadávania v čase (ročná, štvrťročná alebo mesačná granularita).
* **Analýza objemu:**
    * Zobrazí graf priemerného mesačného objemu celého segmentu (súčet všetkých kľúčových slov).
    * Zobrazí graf priemerného mesačného objemu pre jednotlivé kľúčové slová s interaktívnou legendou.
* **Analýza rastu:** Vypočíta a zobrazí medziobdobový percentuálny rast pre jednotlivé kľúčové slová vo forme heatmapy.
* **História vyhľadávaní:** Ukladá a umožňuje znovu načítať predchádzajúce vyhľadávania pre tento režim.
* **Export dát:** Umožňuje stiahnuť pôvodné mesačné dáta (agregované podľa kľúčového slova a mesiaca) ako CSV.

**2. Analýza viacerých krajín:**
* **Získavanie dát pre viacero krajín:** Načíta historické mesačné objemy vyhľadávania pre zadané kľúčové slová a jeden spoločný jazyk naprieč viacerými vybranými krajinami.
* **Prednastavené krajiny:** Ako východiskový bod sú predvolene vybrané Slovensko, Česko, Nemecko a Rakúsko (ak sú dostupné v API).
* **Prehľadové grafy naprieč všetkými vybranými krajinami:**
    * **Celkový Share of Search:** SoS (v %) pre každú značku, kde dáta sú agregované naprieč všetkými hlavnými vybranými krajinami.
    * **Celkový priemerný objem vyhľadávania:** Priemerný objem pre každú značku, agregovaný naprieč všetkými hlavnými vybranými krajinami.
* **Flexibilné grafy s vlastným výberom:**
    * **Flexibilný SoS:** Používateľ si vyberie viacero značiek a podmnožinu krajín. Dáta (objemy) sa sčítajú naprieč touto podmnožinou krajín a následne sa počíta a vizualizuje SoS.
    * **Flexibilný súhrnný objem:** Používateľ si vyberie viacero značiek a podmnožinu krajín. Dáta (objemy) sa sčítajú naprieč touto podmnožinou krajín a zobrazí sa tento súhrnný objem.
    * **Priemerný mesačný objem segmentu (pre vlastný výber krajín):** Používateľ si vyberie podmnožinu krajín a graf zobrazí celkový priemerný mesačný objem všetkých sledovaných značiek dohromady pre túto skupinu krajín.
* **História vyhľadávaní:** Ukladá a umožňuje znovu načítať predchádzajúce vyhľadávania pre tento režim.
* **Export dát:** Umožňuje stiahnuť pôvodné mesačné dáta (s rozlíšením podľa krajiny) ako CSV.

**Spoločné funkcie pre oba režimy:**
* **Interaktívne rozhranie:** Umožňuje jednoduchý výber parametrov (režim analýzy, kľúčové slová, krajina/krajiny, jazyk, rozsah dátumov, granularita).
* **Caching:** Využíva Streamlit cache pre API volania a spracovanie dát na zrýchlenie opakovaných požiadaviek.
* **Export grafov:** Umožňuje stiahnutie vygenerovaných grafov ako PNG.
* **Ochrana:** Vyžaduje zadanie PIN kódu pre prístup k aplikácii (konfigurovateľné cez Streamlit Secrets).
* **Sidebar s informáciami:** Zobrazuje verziu aplikácie, copyright a odkazy na dokumentáciu.

## Požiadavky

* Python 3.x
* Nainštalované knižnice uvedené v `requirements.txt`:
    ```
    streamlit
    requests
    pandas
    plotly
    numpy
    ```
    Inštalácia: `pip install -r requirements.txt`
* **DataForSEO API prihlasovacie údaje:** Login a heslo k vášmu účtu DataForSEO.
* **Streamlit Secrets:** Aplikácia očakáva vaše DataForSEO prihlasovacie údaje a voliteľný prístupový PIN kód uložené v Streamlit Secrets. Vytvorte súbor `.streamlit/secrets.toml` v koreňovom adresári projektu s nasledujúcou štruktúrou:

    ```toml
    # .streamlit/secrets.toml

    [dataforseo]
    login = "VAS_DATAFORSEO_LOGIN"
    password = "VAS_DATAFORSEO_HESLO"

    [app]
    pin = "VAS_VOLITELNY_PIN" # Ak PIN nechcete, môžete tento riadok vynechať alebo nechať prázdny, ale potom upravte logiku v kóde.
    ```

    *Nahraďte `VAS_DATAFORSEO_LOGIN`, `VAS_DATAFORSEO_HESLO` a `VAS_VOLITELNY_PIN` vašimi skutočnými údajmi.*

## Použitie

1.  **Naklonujte repozitár (ak ste tak ešte neurobili):**
    ```bash
    git clone [https://github.com/mareksulik/sos.git](https://github.com/mareksulik/sos.git) # Nahraďte správnou URL vášho repozitára
    cd sos 
    ```
2.  **Vytvorte a aktivujte virtuálne prostredie (odporúčané):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # Pre Linux/macOS
    # venv\Scripts\activate    # Pre Windows
    ```
3.  **Nainštalujte závislosti:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Nastavte Streamlit Secrets:** Vytvorte súbor `.streamlit/secrets.toml` podľa popisu v sekcii Požiadavky.
5.  **Spustite Streamlit aplikáciu (napr. ak sa váš súbor volá `sos_app.py`):**
    ```bash
    streamlit run sos_app.py 
    ```
6.  Otvorte aplikáciu vo vašom prehliadači (zvyčajne na `http://localhost:8501`).
7.  Ak ste nastavili PIN, zadajte ho.
8.  V postrannom paneli vyberte typ analýzy ("Analýza jednej krajiny" alebo "Analýza viacerých krajín").
9.  Zadajte kľúčové slová (jedno na riadok), vyberte krajinu/krajiny, jazyk, rozsah dátumov a granularitu.
10. Kliknite na tlačidlo "📊 Získať dáta a zobraziť grafy".

## Štruktúra kódu

* **Hlavné funkcie:**
    * `load_locations`, `load_languages`: Načítanie a cachovanie zoznamu krajín a jazykov.
    * `get_search_volume_live_with_history`: Získanie dát pre jednu krajinu.
    * `get_multi_country_search_volume_history`: Získanie dát pre viacero krajín.
    * `render_multi_country_page`: Logika a UI pre analýzu viacerých krajín.
    * Hlavný blok kódu: UI pre analýzu jednej krajiny, PIN autentifikácia, sidebar a navigácia medzi režimami.
* **Session State:** Intenzívne využitie `st.session_state` na uchovanie vstupov používateľa a výsledkov API volaní pre plynulejšiu interakciu a cachovanie v rámci session.

## Možné vylepšenia

* Rozdelenie rozsiahlej funkcie `render_multi_country_page` a hlavného bloku pre analýzu jednej krajiny do menších, lepšie manažovateľných funkcií.
* Pridanie automatizovaných testov (napr. `pytest`).
* Rozšírenie možností analýzy (napr. kĺzavé priemery, detekcia anomálií, porovnanie s konkurenčnými dátami, ak by boli dostupné).
* Pokročilejšie možnosti filtrovania a porovnávania v rámci flexibilných grafov.
* Vylepšenie UI/UX, napr. dynamické zobrazenie/skrytie sekcií grafov.
* Podrobnejšie spracovanie chýb a logovanie.
* Možnosť ukladania a načítavania konfigurácií vyhľadávania.
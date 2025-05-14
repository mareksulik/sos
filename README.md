# Share of Search Tool 📊📈

Jednoduchá [Streamlit](https://streamlit.io/) aplikácia na vizualizáciu a analýzu "Share of Search" (podielu vyhľadávania) pre zadané kľúčové slová pomocou dát z [DataForSEO API](https://dataforseo.com/). Aplikácia bola vytvorená s pomocou Google Gemini Pro.

## Funkcie

Aplikácia ponúka dva hlavné režimy analýzy:

**1. Analýza jednej krajiny:**
* **Získavanie dát:** Načíta historické mesačné objemy vyhľadávania pre zadané kľúčové slová, vybranú krajinu a jazyk z DataForSEO Google Ads Search Volume API.
* **Prednastavené hodnoty:** Aplikácia má prednastavené kľúčové slová (isadore, castelli, rapha, maap, pas normal studios, van rysel), krajinu (Slovensko) a jazyk (slovenčina) pre rýchle spustenie.
* **Grafy (očíslované):**
    1.  **Podiel vyhľadávania (SoS %):** Skladaný stĺpcový graf zobrazujúci vývoj podielu jednotlivých kľúčových slov na celkovom objeme vyhľadávania v čase.
    2.  **Priemerný mesačný objem segmentu:** Stĺpcový graf zobrazujúci priemerný mesačný objem všetkých sledovaných kľúčových slov dohromady.
    3.  **Priemerný mesačný objem konkurentov (Čiarový):** Čiarový graf zobrazujúci vývoj priemerného mesačného objemu pre každé kľúčové slovo zvlášť, s interaktívnou legendou pre filtrovanie značiek.
    4.  **Priemerný mesačný objem konkurentov (Skladaný stĺpcový):** Alternatívne zobrazenie priemerných mesačných objemov konkurentov formou skladaného stĺpcového grafu.
    5.  **Tempo rastu:** Heatmapa zobrazujúca medziobdobový percentuálny rast pre jednotlivé kľúčové slová.
* **História vyhľadávaní (č. 6):** Ukladá a umožňuje znovu načítať predchádzajúce kombinácie filtrov pre tento režim.
* **Export dát (č. 7):** Umožňuje stiahnuť pôvodné mesačné dáta (agregované podľa kľúčového slova a mesiaca) ako CSV.

**2. Analýza viacerých krajín:**
* **Získavanie dát pre viacero krajín:** Načíta historické mesačné objemy vyhľadávania pre zadané kľúčové slová a jeden spoločný jazyk naprieč viacerými vybranými krajinami (hlavný filter).
* **Prednastavené hodnoty:** Predvolene sú vybrané krajiny Slovensko, Česko, Nemecko, Rakúsko a granularita nastavená na 'Ročne'.
* **Informačné upozornenie:** Používateľ je informovaný o API limite (12 požiadaviek/minúta).
* **Grafy (očíslované):**
    1.  **Celkový Share of Search:** SoS (v %) pre každú značku, kde dáta sú agregované naprieč všetkými krajinami vybranými v hlavnom filtri.
    2.  **Celkový priemerný objem vyhľadávania:** Priemerný objem pre každú značku, agregovaný naprieč všetkými krajinami vybranými v hlavnom filtri.
    3.  **Flexibilný priemerný objem (Čiarový):** Používateľ si vyberie viacero značiek a podmnožinu krajín (z hlavného filtra). Dáta (objemy) pre každú značku sa sčítajú naprieč touto podmnožinou krajín a následne sa zobrazí priemerný objem pre každú značku ako časový rad.
    4.  **Flexibilný priemerný objem (Skladaný stĺpcový):** Rovnaké dáta a filtre ako pre graf č. 3, ale zobrazené ako skladaný stĺpcový graf.
    5.  **Priemerný mesačný objem segmentu (pre vlastný výber krajín):** Používateľ si vyberie podmnožinu krajín a graf zobrazí celkový priemerný mesačný objem všetkých sledovaných značiek dohromady pre túto skupinu krajín.
* **História vyhľadávaní (č. 6):** Ukladá a umožňuje znovu načítať predchádzajúce kombinácie filtrov pre tento režim.
* **Export dát (č. 7):** Umožňuje stiahnuť pôvodné mesačné dáta (s rozlíšením podľa krajiny) ako CSV.

**Spoločné funkcie pre oba režimy:**
* **Interaktívne rozhranie:** Umožňuje jednoduchý výber parametrov (režim analýzy, kľúčové slová, krajina/krajiny, jazyk, rozsah dátumov, granularita).
* **Caching:** Využíva Streamlit cache (`@st.cache_data`) pre API volania a spracovanie dát na zrýchlenie opakovaných požiadaviek.
* **Export grafov:** Umožňuje stiahnutie vygenerovaných grafov ako PNG.
* **Ochrana:** Vyžaduje zadanie PIN kódu pre prístup k aplikácii (konfigurovateľné cez Streamlit Secrets).
* **Sidebar s informáciami:** Zobrazuje verziu aplikácie (v1.5), copyright ([2025, Marek Šulik](https://mareksulik.sk)), informácie o tvorbe a odkazy na dokumentáciu.

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
    pin = "VAS_VOLITELNY_PIN" # Ak PIN nechcete, tento riadok alebo celú sekciu [app] môžete vynechať.
    ```

    *Nahraďte `VAS_DATAFORSEO_LOGIN`, `VAS_DATAFORSEO_HESLO` a `VAS_VOLITELNY_PIN` vašimi skutočnými údajmi.*

## Použitie

1.  **Štruktúra projektu:** Uistite sa, že máte nasledujúcu adresárovú štruktúru (s prázdnymi `__init__.py` súbormi v podadresároch, aby fungovali importy):
    ```
    vas_projekt_adresar/
    ├── sos.py                   # Hlavný súbor aplikácie (alebo streamlit_app.py)
    ├── config.py               
    ├── requirements.txt        
    ├── api_client/
    │   ├── __init__.py        
    │   └── dataforseo_client.py 
    ├── data_processing/
    │   ├── __init__.py         
    │   ├── fetcher.py          
    │   └── transformer.py       
    └── ui/
        ├── __init__.py         
        ├── sidebar.py           
        ├── single_country_page.py 
        ├── multi_country_page.py  
        └── charts.py              
    ```
2.  **Naklonujte repozitár (ak relevantné):**
    ```bash
    # git clone [URL_VASHO_REPOZITARA]
    # cd [NAZOV_ADRESARA_PROJEKTU]
    ```
3.  **Vytvorte a aktivujte virtuálne prostredie (odporúčané):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # Pre Linux/macOS
    # venv\Scripts\activate    # Pre Windows
    ```
4.  **Nainštalujte závislosti:**
    ```bash
    pip install -r requirements.txt
    ```
5.  **Nastavte Streamlit Secrets:** Vytvorte súbor `.streamlit/secrets.toml` podľa popisu vyššie.
6.  **Spustite Streamlit aplikáciu (napr. ak sa váš hlavný súbor volá `sos.py`):**
    ```bash
    streamlit run sos.py
    ```
7.  Otvorte aplikáciu vo vašom prehliadači (zvyčajne na `http://localhost:8501`).
8.  Ak ste nastavili PIN, zadajte ho.
9.  V postrannom paneli vyberte typ analýzy.
10. Zadajte parametre a kliknite na tlačidlo "Získať dáta a zobraziť grafy".

## Štruktúra kódu (Refaktorizovaná)

* **`sos.py` (alebo `streamlit_app.py`):** Hlavný vstupný bod, PIN autentifikácia, volanie sidebaru a vykresľovacích funkcií pre jednotlivé stránky.
* **`config.py`:** Globálne konštanty, prednastavené hodnoty, načítavanie `st.secrets`.
* **`api_client/dataforseo_client.py`:** Nízkoúrovňová komunikácia s DataForSEO API (napr. `load_locations`, `load_languages`, `get_search_volume_for_task`).
* **`data_processing/fetcher.py`:** Vyššia vrstva pre získavanie dát, cachovanie API odpovedí (napr. `Workspace_search_volume_data_single`, `Workspace_multi_country_search_volume_data`).
* **`data_processing/transformer.py`:** Funkcie pre transformáciu a agregáciu dát (výpočty SoS, priemerov, rastu, príprava DataFrames pre grafy).
* **`ui/sidebar.py`:** Funkcia pre vykreslenie obsahu postranného panela.
* **`ui/single_country_page.py`:** Všetka UI logika a volania pre "Analýzu jednej krajiny".
* **`ui/multi_country_page.py`:** Všetka UI logika a volania pre "Analýzu viacerých krajín".
* **`ui/charts.py`:** Samostatné funkcie pre generovanie jednotlivých Plotly grafov.
* **`st.session_state`:** Intenzívne sa využíva na uchovávanie stavu vstupov a načítaných dát pre plynulú interakciu.

## Možné vylepšenia

* Pridanie automatizovaných testov (napr. `pytest`).
* Rozšírenie možností analýzy (napr. kĺzavé priemery, detekcia anomálií).
* Pokročilejšie možnosti filtrovania a porovnávania v rámci flexibilných grafov.
* Vylepšenie UI/UX, napr. dynamické zobrazenie/skrytie sekcií grafov na základe dostupnosti dát.
* Podrobnejšie spracovanie chýb a logovanie na strane servera.
* Možnosť ukladania a načítavania komplexných konfigurácií vyhľadávania.
* Optimalizácia výkonu pri práci s veľmi veľkými datasetmi (aj keď cachovanie už pomáha).
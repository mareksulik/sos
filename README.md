# Share of Search Tool 📊📈

Jednoduchá [Streamlit](https://streamlit.io/) aplikácia na vizualizáciu a analýzu "Share of Search" (podielu vyhľadávania) pre zadané kľúčové slová pomocou dát z [DataForSEO API](https://dataforseo.com/).

## Funkcie

*   **Získavanie dát:** Načíta historické mesačné objemy vyhľadávania pre zadané kľúčové slová, lokáciu a jazyk z DataForSEO Google Ads Search Volume API.
*   **Vizualizácia podielu:** Zobrazí vývoj podielu jednotlivých kľúčových slov na celkovom objeme vyhľadávania v čase (ročná, štvrťročná alebo mesačná granularita).
*   **Analýza objemu:** Zobrazí grafy celkového objemu vyhľadávania segmentu (súčet a priemer) a objemu pre jednotlivé kľúčové slová.
*   **Analýza rastu:** Vypočíta a zobrazí medziobdobový percentuálny rast pre jednotlivé kľúčové slová vo forme heatmapy.
*   **Interaktívne rozhranie:** Umožňuje jednoduchý výber parametrov (kľúčové slová, lokácia, jazyk, časové obdobie, granularita).
*   **Caching:** Využíva Streamlit cache pre API volania a spracovanie dát na zrýchlenie opakovaných požiadaviek.
*   **Export:** Umožňuje stiahnutie vygenerovaných grafov ako PNG a pôvodných mesačných dát ako CSV.
*   **Ochrana:** Vyžaduje zadanie PIN kódu pre prístup k aplikácii (konfigurovateľné cez Streamlit Secrets).

## Požiadavky

*   Python 3.x
*   Nainštalované knižnice uvedené v `requirements.txt` (vytvor tento súbor, ak ešte neexistuje):
    ```
    pip install -r requirements.txt
    ```
*   **DataForSEO API prihlasovacie údaje:** Login a heslo k vášmu účtu DataForSEO.
*   **Streamlit Secrets:** Aplikácia očakáva vaše DataForSEO prihlasovacie údaje a voliteľný prístupový PIN kód uložené v Streamlit Secrets. Vytvorte súbor `.streamlit/secrets.toml` v koreňovom adresári projektu s nasledujúcou štruktúrou:

    ```toml
    # .streamlit/secrets.toml

    [dataforseo]
    login = "VAS_DATAFORSEO_LOGIN"
    password = "VAS_DATAFORSEO_HESLO"

    [app]
    pin = "VAS_VOLITELNY_PIN"
    ```

    *Nahraďte `VAS_DATAFORSEO_LOGIN`, `VAS_DATAFORSEO_HESLO` a `VAS_VOLITELNY_PIN` vašimi skutočnými údajmi.*

## Použitie

1.  **Naklonujte repozitár:**
    ```bash
    git clone https://github.com/mareksulik/sos.git
    cd sos
    ```
2.  **Nainštalujte závislosti:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Nastavte Streamlit Secrets:** Vytvorte súbor `.streamlit/secrets.toml` podľa popisu v sekcii Požiadavky.
4.  **Spustite Streamlit aplikáciu:**
    ```bash
    streamlit run sos.py
    ```
5.  Otvorte aplikáciu vo vašom prehliadači (zvyčajne na `http://localhost:8501`).
6.  Ak ste nastavili PIN, zadajte ho.
7.  Zadajte kľúčové slová (jedno na riadok), vyberte lokáciu, jazyk, časové obdobie a granularitu.
8.  Kliknite na tlačidlo "📊 Získať dáta a zobraziť grafy".

## Možné vylepšenia

*   Rozdelenie kódu do menších funkcií a modulov pre lepšiu čitateľnosť a údržbu.
*   Pridanie automatizovaných testov (napr. `pytest`).
*   Rozšírenie možností analýzy (napr. kĺzavé priemery, detekcia trendov).
*   Vylepšenie UI/UX (napr. použitie `st.expander` pre detailné grafy).
*   Podrobnejšie spracovanie chýb a logovanie.

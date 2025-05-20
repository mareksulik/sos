# Share of Search Tool 📊📈

Aplikácia vytvorená pomocou [Streamlit](https://streamlit.io/) na vizualizáciu a analýzu "Share of Search" (podielu vyhľadávania) pre zadané kľúčové slová s využitím dát z [DataForSEO API](https://dataforseo.com/).

## Prehľad

Share of Search Tool umožňuje analyzovať podiel vyhľadávania pre rôzne značky a monitorovať trendy v čase. Aplikácia bola optimalizovaná pre rýchlosť, prehľadnosť a jednoduché rozšírenie.

## Funkcie

Aplikácia ponúka dva hlavné režimy analýzy:

### 1. Analýza jednej krajiny

* Historické dáta objemu vyhľadávania pre vybrané kľúčové slová v jednej krajine
* Interaktívne grafy zobrazujúce:
  - Podiel vyhľadávania (SoS %)
  - Priemerný mesačný objem segmentu
  - Vývoj priemerného mesačného objemu jednotlivých značiek
  - Medziobdobový percentuálny rast

### 2. Analýza viacerých krajín

* Porovnanie dát naprieč viacerými krajinami
* Flexibilné zobrazenie agregovaných dát podľa rôznych kritérií
* Možnosť výberu podmnožiny krajín pre detailnú analýzu
* Grafy zahŕňajú:
  - Celkový Share of Search pre každú značku
  - Celkový priemerný objem vyhľadávania 
  - Flexibilný priemerný objem (čiarový a skladaný stĺpcový graf)
  - Priemerný mesačný objem segmentu pre vlastný výber krajín
* História vyhľadávaní a export dát vo formáte CSV

### Spoločné funkcie

* Interaktívne rozhranie pre výber parametrov (režim analýzy, kľúčové slová, krajina/krajiny, jazyk, rozsah dátumov, granularita)
* Efektívne cachovanie dát pre rýchle opakované dotazy
* Export grafov ako PNG súbory
* Voliteľná ochrana prístupovým PIN kódom
* Informačný sidebar s verziou aplikácie a ďalšími údajmi

## Optimalizácie

Aplikácia obsahuje nasledujúce optimalizácie:

### 1. Štruktúra a architektúra kódu
- Modulárna architektúra MVC (Model-View-Controller)
- Organizácia kódu do logických modulov
- Typové anotácie pre lepšiu kontrolu typov a dokumentáciu

### 2. Výkonnosť
- Optimalizované spracovanie dát pomocou Pandas
- Efektívne cachovanie pre minimalizáciu API volaní
- Konfigurovateľné caching stratégie s TTL (time-to-live) nastaveniami

### 3. Robustnosť
- Komplexné ošetrenie chýb a výnimiek
- Logovanie pre jednoduchšie debugovanie
- Pomocné utility pre bezpečnú manipuláciu s dátami

### 4. Čistota kódu a udržateľnosť
- Konzistentný štýl kódu podľa štandardov PEP 8
- Rozšírená dokumentácia pomocou docstringov
- Odstránenie duplicitného kódu pomocou refaktorovania

## Multi-country Mode Optimization

### Problém
Pôvodná implementácia Share of Search Tool vykonávala sekvenčné API volania pre každú krajinu s 5,5-sekundovou pauzou medzi volaniami v režime viacerých krajín. Tento sekvenčný prístup výrazne spomaľoval aplikáciu pri analýze viacerých krajín.

Okrem toho sa vyskytla chyba `UnserializableReturnValueError` pri pokuse o cachovanie asynchrónnej funkcie, pretože korutíny nie sú serializovateľné.

### Riešenie
Implementovali sme asynchrónny prístup, ktorý vykonáva API volania pre všetky krajiny paralelne s rešpektovaním limitov API pomocou dávkového spracovania. Toto dramaticky zlepšuje výkon:

| Počet krajín | Pôvodné (sekvenčné) | Nové (asynchrónne) | Zlepšenie |
|-----------|----------------------|------------|-------------|
| 1         | ~5,5s                | ~5,5s      | 1x          |
| 4         | ~22s                 | ~5,5s      | 4x          |
| 10        | ~55s                 | ~12s       | 4,6x        |
| 20        | ~110s                | ~24s       | 4,6x        |

### Riešenie chyby UnserializableReturnValueError

Prvý pokus o implementáciu asynchrónnej verzie narazil na chybu `UnserializableReturnValueError` z dôvodov:

1. Streamlit cache (`st.cache_data`) nemôže priamo cachovať asynchrónnu funkciu alebo korutínu
2. Asynchrónne funkcie vracajú korutíny, ktoré nie sú serializovateľné 

Na vyriešenie tohto problému sme implementovali dvojfázové riešenie:
1. Vytvorili sme internú asynchrónnu funkciu (`_fetch_multi_country_search_volume_data_async_internal`), ktorá vykonáva samotnú asynchrónnu prácu
2. Vytvorili sme neasynchrónnu wrapper funkciu (`fetch_multi_country_search_volume_data_async`), ktorá:
   - Je dekorovaná pomocou `@st.cache_data`
   - Volá internú asynchrónnu funkciu pomocou `asyncio.run()`
   - Vracia len serializovateľné dáta (DataFrame a chybový reťazec)

### Detaily implementácie

1. **Asynchrónny API klient**
   - Vytvorená funkcia `get_search_volume_async` v `dataforseo_client.py`, ktorá používa aiohttp pre asynchrónne HTTP požiadavky
   - Vracia dáta pre jednu krajinu spolu s kódom lokácie pre identifikáciu

2. **Dávkové spracovanie**
   - Implementované dávkové spracovanie pre rešpektovanie limitov API
   - Predvolená veľkosť dávky je 5 krajín spracovaných súčasne
   - Dynamická veľkosť dávky na základe počtu krajín:
     - Malé požiadavky (≤3 krajiny): Spracovanie všetkých naraz
     - Veľké požiadavky (>10 krajín): Zníženie veľkosti dávky na 4
   - Konfigurovateľná pauza medzi dávkami (predvolene: 3 sekundy)
   - Adaptívna pauza, ktorá sa zvyšuje pri dosiahnutí limitov API

3. **Nový asynchrónny fetcher**
   - Vytvorený modul `async_fetcher.py` s funkciou `fetch_multi_country_search_volume_data_async`
   - Používa asyncio na zhromažďovanie výsledkov z viacerých API volaní
   - Elegantne spracováva chyby a kombinuje výsledky zo všetkých krajín

4. **Aktualizácie konfigurácie**
   - Pridané nové nastavenia v `config.py`:
     - `ASYNC_BATCH_SIZE`: Počet súbežných API požiadaviek (predvolene: 5)
     - `ASYNC_BATCH_PAUSE`: Pauza medzi dávkami v sekundách (predvolene: 3)
     - Pridaná pomocná metóda `get()` pre bezpečný prístup k nastaveniam

5. **Integrácia s používateľským rozhraním**
   - Vytvorený `multi_country_page_async.py` ako náhrada za pôvodnú implementáciu
   - Pridaný prepínač medzi asynchrónnym a sekvenčným fetchovaním
   - Aktualizovaná hlavná aplikácia na používanie novej asynchrónnej implementácie

### Zlepšenia pri spracovaní chýb
- Vylepšené spracovanie chýb API rate limitov
- Automatické prispôsobenie trvania pauzy medzi dávkami pri prekročení limitov API
- Elegantné spracovanie výnimiek počas asynchrónneho spracovania
- Jasné chybové hlásenia v používateľskom rozhraní

### Požiadavky
- Pridaná závislosť na balíku `aiohttp` pre asynchrónne HTTP požiadavky
- Pridaná závislosť na balíku `asyncio` pre podporu async/await
- Kompatibilita s existujúcim Streamlit UI a pipeline spracovania dát

## Štruktúra projektu

```
.
├── .streamlit/             # Konfigurácia Streamlit
├── .venv/                  # Virtuálne prostredie (ignorované Gitom)
├── api_client/             # Klientská knižnica pre DataForSEO API
│   ├── __init__.py
│   └── dataforseo_client.py
├── data_processing/        # Modul pre spracovanie dát
│   ├── __init__.py
│   ├── async_fetcher.py    # Asynchrónny fetcher pre viacero krajín
│   ├── fetcher.py          # Pôvodný sekvenčný fetcher
│   └── transformer.py
├── tests/                  # Testovacie súbory
│   ├── __init__.py
│   ├── test_async_fetcher.py
│   ├── test_async.py
│   └── test_basic_async.py
├── ui/                     # Komponenty používateľského rozhrania
│   ├── __init__.py
│   ├── charts.py
│   ├── multi_country_page_async.py
│   ├── multi_country_page.py
│   ├── sidebar.py
│   └── single_country_page.py
├── utils/                  # Pomocné funkcie a nástroje
│   ├── __init__.py
│   └── pandas_helpers.py
├── config.py              # Konfigurácia a konštanty
├── requirements.txt       # Závislosti aplikácie
└── streamlit_app.py       # Hlavný súbor aplikácie
```

## Požiadavky

* Python 3.8+
* Nainštalované knižnice uvedené v `requirements.txt`:
    ```
    streamlit>=1.28.0
    requests>=2.31.0
    pandas>=2.0.0
    plotly>=5.18.0
    numpy>=1.24.0
    streamlit-authenticator>=0.2.0
    kaleido>=0.2.1
    python-dotenv>=1.0.0
    aiohttp>=3.8.5
    asyncio>=3.4.3
    ```
* **DataForSEO API prihlasovacie údaje:** Login a heslo k vášmu účtu DataForSEO.
* **Streamlit Secrets:** Aplikácia očakáva vaše DataForSEO prihlasovacie údaje a voliteľný prístupový PIN kód.

## Spustenie aplikácie

1. Vytvorte a aktivujte virtuálne prostredie:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate   # Na macOS/Linux
   # alebo
   .venv\Scripts\activate      # Na Windows
   ```

2. Nainštalujte závislosti:
   ```bash
   pip install -r requirements.txt
   ```

3. Vytvorte súbor `.streamlit/secrets.toml` s prihlasovacími údajmi:
   ```toml
   [dataforseo]
   login = "VAS_DATAFORSEO_LOGIN"
   password = "VAS_DATAFORSEO_HESLO"

   [app]
   pin = "VAS_VOLITELNY_PIN" # Ak PIN nechcete, tento riadok alebo celú sekciu [app] môžete vynechať.
   ```

4. Spustite aplikáciu:
   ```bash
   streamlit run streamlit_app.py
   ```

## Štruktúra kódu

* **`streamlit_app.py`:** Hlavný vstupný bod, PIN autentifikácia, volanie sidebaru a vykresľovacích funkcií pre jednotlivé stránky.
* **`config.py`:** Globálne konštanty, prednastavené hodnoty, načítavanie `st.secrets`.
* **`api_client/dataforseo_client.py`:** Nízkoúrovňová komunikácia s DataForSEO API (napr. `load_locations`, `load_languages`, `get_search_volume_for_task`).
* **`data_processing/fetcher.py`:** Vyššia vrstva pre získavanie dát, cachovanie API odpovedí.
* **`data_processing/async_fetcher.py`:** Asynchrónna implementácia pre rýchlejšie získavanie dát z viacerých krajín.
* **`data_processing/transformer.py`:** Funkcie pre transformáciu a agregáciu dát (výpočty SoS, priemerov, rastu, príprava DataFrames pre grafy).
* **`ui/sidebar.py`:** Funkcia pre vykreslenie obsahu postranného panela.
* **`ui/single_country_page.py`:** Všetka UI logika a volania pre "Analýzu jednej krajiny".
* **`ui/multi_country_page.py`:** Pôvodná UI logika a volania pre "Analýzu viacerých krajín".
* **`ui/multi_country_page_async.py`:** Optimalizovaná UI logika pre "Analýzu viacerých krajín" s asynchrónnym volaním API.
* **`ui/charts.py`:** Samostatné funkcie pre generovanie jednotlivých Plotly grafov.
* **`utils/pandas_helpers.py`:** Pomocné funkcie pre bezpečnú manipuláciu s pandas DataFrame.
* **`st.session_state`:** Využíva sa na uchovávanie stavu vstupov a načítaných dát pre plynulú interakciu.

## Autor

© 2025 Marek Šulik

---

Vytvorené s použitím Pythonu, Streamlit a DataForSEO API.

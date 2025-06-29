# Changelog

Všetky významné zmeny v tomto projekte budú zdokumentované v tomto súbore.

Formát je založený na [Keep a Changelog](https://keepachangelog.com/sk/1.0.0/),
a tento projekt dodržiava [Semantic Versioning](https://semver.org/lang/sk/).

## [1.3.0] - 2025-05-20

### Pridané
- Asynchrónne spracovanie pre multi-country mód
- Dávkové spracovanie API volaní pre rešpektovanie rate limitov
- Dynamická veľkosť dávky na základe počtu krajín
- Prepínač medzi asynchrónnym a sekvenčným fetchovaním dát
- Rozšírené unit testy pre asynchrónne funkcie

### Opravené
- Vyriešený UnserializableReturnValueError pri cachovaní asynchrónnych funkcií
- Opravené chýbajúce grafy a export CSV v multi-country async móde
- Zlepšené spracovanie chýb API rate limitov

### Zmenené
- Optimalizácia výkonu pri fetchi dát z viacerých krajín (až 4.6x rýchlejšie)
- Reorganizované testovacie súbory do adresára tests/
- Aktualizácia dokumentácie

## [1.2.0] - 2025-03-15

### Pridané
- Flexibilné zobrazenie agregovaných dát podľa rôznych kritérií
- Výber podmnožiny krajín pre detailnú analýzu
- Export dát vo formáte CSV

### Zmenené
- Vylepšené UI pre lepšiu používateľskú skúsenosť
- Optimalizované spracovanie dát pomocou Pandas

## [1.1.0] - 2025-02-01

### Pridané
- História vyhľadávaní
- Voliteľná ochrana prístupovým PIN kódom
- Možnosť exportu grafov ako PNG súbory

### Opravené
- Opravené chyby pri zobrazení grafov
- Zlepšená kompatibilita s rôznymi prehliadačmi

## [1.0.0] - 2025-01-01

### Pridané
- Prvá verzia aplikácie Share of Search Tool
- Analýza jednej krajiny
- Analýza viacerých krajín
- Interaktívne grafy
- Efektívne cachovanie dát

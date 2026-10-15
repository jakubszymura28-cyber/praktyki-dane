# Raport przekazania projektu (Project Handover Report)

Niniejszy dokument stanowi formalną tabelę kompletności, integralności i gotowości wdrożeniowej repozytorium **Praktyki - Analiza Danych** przygotowanego do publikacji w publicznym repozytorium GitHub.

---

## 1. Tabela kompletności komponentów projektu

Poniższa tabela zestawia wszystkie kluczowe komponenty systemu, ich rolę w potoku przetwarzania, status weryfikacji oraz powiązane pliki dowodowe.

| Komponent / Obszar | Ścieżka pliku | Rola w potoku | Kryterium odbioru / Dowód | Status weryfikacji | Odnośnik |
|---|---|---|---|:---:|:---:|
| **Dane wejściowe (Read-only)** | [`data/raw/orders_train_raw.csv`](../data/raw/orders_train_raw.csv)<br>[`data/raw/orders_validation.csv`](../data/raw/orders_validation.csv)<br>[`data/raw/orders_test.csv`](../data/raw/orders_test.csv)<br>[`data/raw/calendar.csv`](../data/raw/calendar.csv) | Surowe, niemutowalne zbiory obserwacji | Nienaruszone pliki źródłowe, brak mutacji w `data/raw/` | **Zweryfikowano lokalnie** | [Sekcja 2 README](../README.md#2-architektura-danych-i-struktura-repozytorium) |
| **Potok czyszczenia i walidacji** | [`src/prepare_data.py`](../src/prepare_data.py) | Deterministyczne reguły jakości, deduplikacja, flaga `orders_invalid`, bezpieczne dołączenie kalendarza | Zgodność liczności: 252 trening (248 poprawnych), 84 walidacja, 84 test. Dołączenie `day_of_week` bez fan-out. | **Zweryfikowano lokalnie** | [reports/quality.md](quality.md) |
| **Testy jednostkowe jakości danych** | [`tests/test_prepare_data.py`](../tests/test_prepare_data.py) | Automatyczna weryfikacja reguł jakości w izolowanym środowisku | 6/6 testów OK (ujemne i ułamkowe `orders`, zła data, ujemny i tekstowy budżet, tekstowe orders) | **Zweryfikowano lokalnie** | [reports/quality.md](quality.md#10-tabela-porównawcza-przed-i-po-czyszczeniu-przed-vs-po) |
| **Baza SQLite i agregacje analityczne** | [`src/query_data.py`](../src/query_data.py)<br>[`sql/queries.sql`](../sql/queries.sql) | Weryfikacja spójności bazy danych i zapytań SQL | Poprawne typy kolumn, 248 ważnych rekordów w bazie `orders.sqlite`, zgodność z pandas | **Zweryfikowano lokalnie** | [reports/analysis.md](analysis.md) |
| **Eksploracja i wizualizacja (EDA)** | [`notebooks/02_analysis.ipynb`](../notebooks/02_analysis.ipynb) | Analiza szeregu czasowego, dni tygodnia, promocji, generowanie wykresów | Pomyślne wykonanie notatnika od góry do dołu bez błędów, 4 wykresy w `reports/` | **Zweryfikowano lokalnie** | [reports/orders_by_date.png](orders_by_date.png) |
| **Dokumentacja założeń modelowania** | [`reports/model_card.md`](model_card.md) | Karta Modelu, specyfikacja problemu $t+1$, dobór metryki MAE | Ścisła definicja cech, wykluczenie `visits` i `revenue_pln`, procedura walidacji | **Zweryfikowano lokalnie** | [reports/model_card.md](model_card.md) |
| **Potok cech i trening modeli** | [`src/train.py`](../src/train.py) | `ColumnTransformer` + modele ML (`DummyRegressor`, `DecisionTreeRegressor`) | Deterministyczne uczenie na 248 wierszach, wyznaczenie mediany budżetu (575.275 PLN) | **Zweryfikowano lokalnie** | [reports/metrics.csv](metrics.csv) |
| **Testy jednostkowe modelowania** | [`tests/test_training.py`](../tests/test_training.py) | Ochrona przed wyciekiem danych i weryfikacja preprocesora | 3/3 testy OK (blokada zabronionych cech, determinizm transformacji cech) | **Zweryfikowano lokalnie** | [README.md](../README.md#7-uruchomienie-testów-jednostkowych-potoku-modelowania) |
| **Zamrożone obiekty produkcyjne** | [`models/baseline.joblib`](../models/baseline.joblib)<br>[`models/selected_pipeline.joblib`](../models/selected_pipeline.joblib) | Utrwalone modele gotowe do wdrożenia | Spójność prognoz po wczytaniu przez `joblib.load()` | **Zweryfikowano lokalnie** | [reports/reproduction.md](reproduction.md) |
| **Niezależna ewaluacja testowa** | [`src/predict.py`](../src/predict.py) | Ostateczny pomiar uogólnienia na niewidzianym oknie testowym (84 dni) | Czyste wnioskowanie `.predict()`, brak wywołania `.fit()`, MAE testu = 14.0930 | **Zweryfikowano lokalnie** | [reports/test_predictions.csv](test_predictions.csv) |
| **Aplikacja demonstracyjna** | [`app.py`](../app.py) | Interaktywne środowisko prognozowania popytu na dzień jutrzejszy | Lokalne uruchomienie przez Streamlit, ostrzeżenia o ekstrapolacji, obsługa braków budżetu | **Zweryfikowano lokalnie** | [reports/demo_tests.md](demo_tests.md) |
| **Raport audytu odtwarzalności** | [`reports/reproduction.md`](reproduction.md) | Niezależny techniczny audyt determinizmu całego potoku | Różnice MAE = 0.0000 szt., pełna zgodność tożsamości numerycznej modeli | **Zweryfikowano lokalnie** | [reports/reproduction.md](reproduction.md) |
| **Audyt współpracy z asystentem AI** | [`reports/ai_evaluation.md`](ai_evaluation.md) | Ewaluacja 6 prób asystenta AI, odporność na Prompt Injection | Rzetelna punktacja 5/6 (83.3%), udokumentowanie halucynacji daty i wdrożenie 5 zasad AI | **Zweryfikowano lokalnie** | [reports/ai_evaluation.md](ai_evaluation.md) |
| **Szkic prezentacji końcowej** | [`reports/presentation.md`](presentation.md) | 10 slajdów podsumowujących dorobek praktyk | Kompletna synteza biznesowa, techniczna i etyczna projektu | **Zweryfikowano lokalnie** | [reports/presentation.md](presentation.md) |
| **Instrukcja wdrożeniowa** | [`README.md`](../README.md) | Główna dokumentacja i odtworzenie krok po kroku (Windows / PowerShell) | Jednoznaczne komendy z `.\.venv\Scripts\python.exe`, katalogi, expected outputs, troubleshooting | **Zweryfikowano lokalnie** | [README.md](../README.md) |
| **Weryfikacja publicznych odnośników na GitHub** | Publiczny URL repozytorium GitHub | Sprawdzenie działania linków względnych w przeglądarce po publikacji | Wszystkie odnośniki prowadzą do istniejących plików bez błędu 404 | **Do sprawdzenia jutro / po publikacji** | [Repozytorium GitHub](https://github.com/jakubszymura28-cyber/praktyki-dane) |
| **Pobranie i odtworzenie na czystej maszynie** | Środowisko zewnętrzne (czysty system Windows 10) | Klonowanie z publicznego GitHuba i wykonanie instrukcji krok po kroku | Pełne przejście potoku bez konieczności ingerencji w pliki kodu | **Do sprawdzenia jutro / po publikacji** | [README.md](../README.md#instrukcja-uruchomienia-krok-po-kroku-windows-10--powershell) |

---

## 2. Zestawienie kluczowych metryk projektu

| Obszar metryki | Wyliczona wartość w projekcie | Plik źródłowy | Zgodność z założeniami |
|---|:---:|---|:---:|
| **Poprawne dni treningowe ($N$)** | **248 dni** | [`reports/quality.md`](quality.md), [`data/processed/orders_train.csv`](../data/processed/orders_train.csv) | 100% zgodne |
| **Suma zamówień w treningu** | **20 933.0 szt.** | [`reports/analysis.md`](analysis.md), [`data/processed/orders.sqlite`](../data/processed/orders.sqlite) | 100% zgodne |
| **Średnia zamówień w soboty** | **105.19 szt./dzień** | [`reports/by_weekday.csv`](by_weekday.csv) | 100% zgodne |
| **Średnia zamówień w promocji** | **103.47 szt./dzień** | [`reports/by_promo.csv`](by_promo.csv) | 100% zgodne |
| **MAE modelu bazowego (walidacja)** | **16.2143 szt./dzień** | [`reports/metrics.csv`](metrics.csv) | 100% zgodne |
| **MAE drzewa decyzyjnego (walidacja)** | **11.9503 szt./dzień** | [`reports/metrics.csv`](metrics.csv) | 100% zgodne (zysk: +26.3%) |
| **MAE drzewa decyzyjnego (test)** | **14.0930 szt./dzień** | [`reports/metrics.csv`](metrics.csv), [`reports/test_predictions.csv`](test_predictions.csv) | 100% zgodne |
| **Wynik ewaluacji asystenta AI** | **5 / 6 (83.3%)** | [`reports/ai_evaluation.md`](ai_evaluation.md) | Rzetelnie udokumentowane |

---

## 3. Wkład własny i samodzielne decyzje inżynierskie

*(Sekcja autorska – miejsce na uzupełnienie i podsumowanie Twoich własnych decyzji projektowych)*

1. **Rygorystyczna ochrona surowych danych i zasada Single Source of Truth:**
   - Podjęcie decyzji o niemutowaniu danych w `data/raw/` i wyprowadzeniu wszystkich przekształceń do jednego deterministycznego modułu `src/prepare_data.py`.
   - Wyeliminowanie podwójnego dołączania kalendarza i scentralizowanie kontroli fan-out oraz niezmienności sum w jednym miejscu.
2. **Ścisłe reguły jakościowe i audyt ujemnych/ułamkowych zamówień:**
   - Wybór strategii oznaczania ujemnych i ułamkowych zamówień flagą `orders_invalid = 1` i zamiany na `NaN` w celu ochrony modeli przed zniekształceniem, przy jednoczesnym zatrzymywaniu programu błędem `ValueError` w przypadku naruszenia schematów typów lub ujemnego budżetu (*Fail-Fast*).
   - Ręczne ustalenie na surowych danych przyczyny różnicy -3 zamówień (usunięcie 3 poprawnych duplikatów z końca pliku).
3. **Zapobieganie wyciekowi danych (Data Leakage):**
   - Samodzielne zidentyfikowanie ryzyka wycieku danych z cech operacyjnych `visits` oraz `revenue_pln` w horyzoncie $t+1$ i zaimplementowanie mechanizmu automatycznego blokowania tych kolumn w `src/train.py` i `src/predict.py`.
   - Uczenie preprocesora `ColumnTransformer` (w tym mediany budżetu) wyłącznie na zbiorze treningowym.
4. **Krytyczne podejście do generatywnego AI (Prompt Hygiene):**
   - Wykrycie subtelnej halucynacji daty granicznej horyzontu (19.02.2025 vs 23.02.2025) w odpowiedzi asystenta AI, obniżenie punktacji do 0/1 oraz sformułowanie 5 Zasad Bezpiecznej Współpracy z AI.

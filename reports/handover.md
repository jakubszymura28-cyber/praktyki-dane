# Raport przekazania projektu (Project Handover Report)

Niniejszy dokument stanowi formalną tabelę kompletności, integralności i gotowości wdrożeniowej repozytorium **Praktyki - Analiza Danych** przygotowanego do publikacji w publicznym repozytorium GitHub.

---

## 1. Tabela kompletności i audytu plików projektu

Poniższa tabela zestawia wszystkie wymagane elementy repozytorium, ich lokalizację, wynik weryfikacji i szczegółowych oględzin merytorycznych oraz status ewentualnych uwag.

| Element | Ścieżka w projekcie | Co sprawdzono (wynik oględzin) | Brak lub uwaga |
|---|---|---|---|
| **Instrukcja główna** | [`README.md`](../README.md) | Sprawdzono cel projektu, komendy uruchomieniowe dla Windows 10/PowerShell z jawnym interpreterem `.\.venv\Scripts\python.exe`, katalogi robocze `Cwd`, oczekiwane wyniki, 3 błędy w sekcji Rozwiązywanie problemów, linki względne do raportów/wykresów | Brak uwag; instrukcja kompletna i przetestowana |
| **Instrukcje AI** | [`AGENTS.md`](../AGENTS.md) | Sprawdzono stałe instrukcje dla agenta: komunikację po polsku, obowiązek planu przed działaniem, zakaz modyfikacji plików bez zgody, ochronę surowych danych i procedurę Fail-Fast | Brak uwag; reguły aktywne |
| **Reguły IDE** | [`.agents/rules/course-instructions.md`](../.agents/rules/course-instructions.md) | Sprawdzono regułę *Always on* egzekwującą bezwzględne stosowanie wytycznych z `AGENTS.md` | Brak uwag; konfiguracja poprawna |
| **Zależności środowiska** | [`requirements.txt`](../requirements.txt) | Sprawdzono zgodność wersji faktycznie używanych pakietów: `pandas`, `numpy`, `scikit-learn`, `joblib`, `streamlit`, `pytest`, `matplotlib`, `seaborn` | Brak uwag; instalacja przechodzi bez konfliktów |
| **Pliki ignorowane** | [`.gitignore`](../.gitignore) | Sprawdzono reguły wykluczenia: `.venv/`, `.env`, `__pycache__/`, `.ipynb_checkpoints/`, `scratch/`. Zweryfikowano w `git status`, że wrażliwe dane i środowiska nie trafiają do repozytorium | Brak uwag; historia Gita zabezpieczona |
| **Niemutowalne dane surowe** | [`data/raw/orders_train_raw.csv`](../data/raw/orders_train_raw.csv)<br>[`data/raw/orders_validation.csv`](../data/raw/orders_validation.csv)<br>[`data/raw/orders_test.csv`](../data/raw/orders_test.csv)<br>[`data/raw/calendar.csv`](../data/raw/calendar.csv) | Oględziny plików źródłowych: pliki syntetyczne pozostały nietknięte (read-only), brak mutacji i nadpisań w katalogu `data/raw/` | Brak uwag; integralność danych surowych zachowana |
| **Oczyszczone zbiory danych** | [`data/processed/orders_train.csv`](../data/processed/orders_train.csv)<br>[`data/processed/orders_validation.csv`](../data/processed/orders_validation.csv)<br>[`data/processed/orders_test.csv`](../data/processed/orders_test.csv)<br>[`data/processed/orders.sqlite`](../data/processed/orders.sqlite) | Sprawdzono brak globalnej imputacji medianą (imputacja wyłącznie w preprocesorze ML), obecność flagi `orders_invalid`, 248 poprawnych wierszy treningowych i 84 wiersze w walidacji/teście | Brak uwag; dane przetworzone deterministycznie |
| **Notebook eksploracji wstępnej** | [`notebooks/01_start.ipynb`](../notebooks/01_start.ipynb) | Sprawdzono pierwsze wczytanie danych, typy kolumn oraz wstępne statystyki opisowe | Brak uwag; notatnik wykonany |
| **Notebook analizy i wizualizacji (EDA)** | [`notebooks/02_analysis.ipynb`](../notebooks/02_analysis.ipynb) | Sprawdzono wykonanie notatnika od góry do dołu bez błędów; rozwiązano `KeyError: 'day_of_week'` poprzez centralizację dołączania kalendarza w `src/prepare_data.py`. Generuje spójne wykresy i tabele agregacji | Brak uwag; opcjonalnego `03_demo.ipynb` nie tworzono, gdyż zrealizowano pełną aplikację demonstracyjną `app.py` |
| **Kwerendy i baza SQL** | [`sql/queries.sql`](../sql/queries.sql)<br>[`src/query_data.py`](../src/query_data.py) | Oględziny schematu bazy SQLite i wyników SQL: poprawność typów, 248 ważnych rekordów, wyliczona suma zamówień 20 933.0 szt. w 100% zgodna z pandas | Brak uwag; pełna spójność relacyjna |
| **Potok przetwarzania danych** | [`src/prepare_data.py`](../src/prepare_data.py) | Sprawdzono rolę Single Source of Truth dla czyszczenia i łączenia z `calendar.csv`. Obsługa flagi `orders_invalid`, kontrola fan-out (brak zwielokrotnienia wierszy) | Brak uwag; potok deterministyczny |
| **Kod analityczny bazy** | [`src/query_data.py`](../src/query_data.py) | Sprawdzono automatyczne tworzenie bazy SQLite i odpytywanie tabeli `orders` za pomocą SQLAlchemy/sqlite3 | Brak uwag; działa bezbłędnie |
| **Trening potoku modelowania** | [`src/train.py`](../src/train.py) | Sprawdzono uczenie modeli, blokadę wycieku cech (`visits`, `revenue_pln`), wyliczenie mediany budżetu (575.275 PLN) tylko na treningu, zamrożenie wag przez joblib | Brak uwag; brak wycieku danych |
| **Niezależna ewaluacja testowa** | [`src/predict.py`](../src/predict.py) | Sprawdzono wnioskowanie na `orders_test.csv`: wywołanie wyłącznie `.predict()`, brak douczania (`.fit`), deterministyczny zapis predykcji | Brak uwag; brak data leakage |
| **Testy jednostkowe jakości danych** | [`tests/test_prepare_data.py`](../tests/test_prepare_data.py) | Oględziny wyników pytest: 6/6 testów zdanych (ujemny/ułamkowy popyt, zła data, ujemny/tekstowy budżet, tekstowe zamówienia) | Brak uwag; pełne pokrycie przypadków brzegowych |
| **Testy jednostkowe modelowania** | [`tests/test_training.py`](../tests/test_training.py) | Oględziny wyników pytest: 3/3 testy zdane (blokada zabronionych cech `visits`/`revenue_pln`, determinizm transformacji cech) | Brak uwag; mechanizmy obronne aktywne |
| **Zamrożone modele produkcyjne** | [`models/baseline.joblib`](../models/baseline.joblib)<br>[`models/selected_pipeline.joblib`](../models/selected_pipeline.joblib) | Oględziny obiektów joblib: weryfikacja deserializacji, nienaruszone architektury modeli i preprocesorów uczenia | Brak uwag; modele gotowe do wdrożenia |
| **Raport jakości danych** | [`reports/quality.md`](quality.md) | Oględziny raportu: tabela przed/po (252 vs 248 wierszy), wyjaśnienie usunięcia 3 duplikatów i 1 wiersza z ujemnym popytem, reguły integralności | Brak uwag; pełna dokumentacja anomalii |
| **Raport analityczny** | [`reports/analysis.md`](analysis.md) | Oględziny raportu: charakterystyka sprzedaży, dni tygodnia (sobota najlepsza: 105.19 szt.), wpływ promocji (+36%), spójność liczby zamówień | Brak uwag; wnioski poparte danymi |
| **Karta modelu (Model Card)** | [`reports/model_card.md`](model_card.md) | Oględziny i porównanie z metrykami: pełna zgodność z `metrics.csv` (Baseline MAE = 16.2143, DecisionTree walidacja MAE = 11.9503, test MAE = 14.0930), wykluczenie `visits` i `revenue_pln` | Brak uwag; karta modelu w 100% zgodna z metrykami |
| **Zestawienie metryk** | [`reports/metrics.csv`](metrics.csv) | Sprawdzono dokładność wyliczeń MAE i RMSE dla zbioru treningowego, walidacyjnego i testowego | Brak uwag; jawne źródło liczb |
| **Ewaluacja asystenta AI** | [`reports/ai_evaluation.md`](ai_evaluation.md) | Oględziny audytu AI: rzetelna punktacja 5/6 (83.3%), udokumentowanie halucynacji daty 19.02.2025 w próbie 4 (ocena 0/1), 5 Zasad Bezpiecznej Współpracy z AI | Brak uwag; krytyczna ocena AI |
| **Scenariusze testowe demo** | [`reports/demo_tests.md`](demo_tests.md) | Sprawdzono udokumentowanie 3 testów manualnych: dzień standardowy, wysoka promocja z ostrzeżeniem o ekstrapolacji, brak budżetu z imputacją medianą | Brak uwag; testy potwierdzone |
| **Agregacje pomocnicze CSV** | [`reports/by_promo.csv`](by_promo.csv)<br>[`reports/by_month.csv`](by_month.csv)<br>[`reports/by_weekday.csv`](by_weekday.csv) | Sprawdzono wartości średnich i sum dla podziałów na promocje, miesiące i dni tygodnia | Brak uwag; pliki spójne z raportem analitycznym |
| **Pliki predykcji i reszt** | [`reports/validation_predictions.csv`](validation_predictions.csv)<br>[`reports/validation_errors.csv`](validation_errors.csv)<br>[`reports/test_predictions.csv`](test_predictions.csv) | Sprawdzono obecność wyliczonych reszt walidacyjnych oraz predykcji testowych | Brak uwag; kompletne |
| **Raport odtwarzalności** | [`reports/reproduction.md`](reproduction.md) | Oględziny audytu powtarzalności: różnice numeryczne MAE = 0.0000 szt., pełna deterministyczność | Brak uwag; audyt odtworzenia zaliczony |
| **Szkic prezentacji** | [`reports/presentation.md`](presentation.md) | Oględziny struktury: 10 slajdów Markdown pokrywających problem, dane, EDA, ML, testy, demo, audyt AI i wnioski końcowe | Brak uwag; gotowa do wystąpienia |
| **Wykres 1: Szereg czasowy** | [`reports/orders_by_date.png`](orders_by_date.png) | Oględziny wizualne: czytelny przebieg dziennych zamówień, widoczne piki promocyjne, wyraźne opisy osi i siatka | Brak uwag; wykres czytelny |
| **Wykres 2: Dni tygodnia** | [`reports/orders_by_weekday.png`](orders_by_weekday.png) | Oględziny wizualne: czytelny wykres słupkowy średniej sprzedaży wg dni tygodnia z wyraźnym wyróżnieniem sobót | Brak uwag; wykres czytelny |
| **Wykres 3: Rozkład zamówień** | [`reports/orders_histogram.png`](orders_histogram.png) | Oględziny wizualne: czytelny histogram z estymacją gęstości (KDE), dobrze dobrane przedziały (bins), brak ujemnych wartości | Brak uwag; wykres czytelny |
| **Zrzut ekranu aplikacji demo** | [`reports/demo.png`](demo.png) | Oględziny wizualne: interfejs Streamlit z widocznym formularzem wejściowym, prognozą liczbową i ostrzeżeniami | Brak uwag; czytelny dowód działania |
| **Aplikacja demonstracyjna** | [`app.py`](../app.py) | Sprawdzono kod aplikacji Streamlit: wczytywanie potoku `selected_pipeline.joblib`, obsługa braku budżetu (mediana 575.28 PLN), ostrzeżenia o ekstrapolacji powyżej 2000 PLN | Brak uwag; aplikacja gotowa do uruchomienia |
| **Sprawdzenie linków na GitHub** | Publiczny URL repozytorium GitHub | Weryfikacja czytelności i braku błędu 404 w przeglądarce po publikacji | **Do sprawdzenia jutro / po publikacji** |
| **Klonowanie i odtworzenie w czystej kopii** | `praktyki-dane-odbior` (Windows 10) | Klonowanie z publicznego GitHuba, instalacja nowego `.venv` i przejście całej ścieżki z `README.md` | **Zweryfikowano pomyślnie (różnica MAE = 0.0000)** |

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

---

## 4. Otwarte zagadnienia i techniczne punkty uwagi (Open Issues & Review Result)

Na podstawie całościowego przeglądu repozytorium, kodów źródłowych, testów jednostkowych oraz wygenerowanych artefaktów zidentyfikowano 3 techniczne punkty uwagi wymagające monitorowania lub dalszego rozwoju (bez defektów blokujących bieżący odbiór):

1. **Ekstrapolacja budżetu reklamowego powyżej 1500 PLN:**
   - **Wskazany plik:** [`src/predict.py`](../src/predict.py) oraz [`app.py`](../app.py)
   - **Skutek:** W zbiorze treningowym maksymalny budżet reklamowy wynosił 1500 PLN. Drzewo decyzyjne (`DecisionTreeRegressor`) dla każdego budżetu > 1500 PLN prognozuje stałą wartość nasycenia (np. 125 sztuk dla sobót z promocją), co przy skrajnie wysokich budżetach (np. 5000 PLN) nie odzwierciedla potencjalnego dalszego wzrostu lub spadku efektywności kampanii.
   - **Potrzebna poprawka:** Rozszerzenie zbioru danych o kampanie z wyższym budżetem lub wprowadzenie modelu opartego na cechach ciągłych (np. regularyzowana regresja grzbietowa lub model log-liniowy) dla nietypowych wielkości nakładów reklamowych.

2. **Weryfikacja środowiskowa w czystej kopii (Clean Clone Verification) – ZREALIZOWANO:**
   - **Wskazany plik:** [`reports/reproduction.md`](reproduction.md) (Sekcja 9) oraz [`README.md`](../README.md)
   - **Stan faktyczny:** Przeprowadzono pełną procedurę weryfikacyjną: sklonowano publiczne repozytorium GitHub do folderu `praktyki-dane-odbior`, zainstalowano nowe środowisko `.venv` (Python 3.13.15) z `requirements.txt` oraz odtworzono wszystkie kroki z `README.md` (czyszczenie, testy 9/9, SQL, notebook, trening, predykcję testową i demo).
   - **Wynik audytu:** Uzyskano 100% numeryczną tożsamość metryk MAE (różnica = 0.0000) i prognoz testowych. Potwierdzono pełną niezależną odtwarzalność projektu.

3. **Brak alternatywnego, statycznego notatnika demonstracyjnego:**
   - **Wskazany plik:** [`notebooks/`](../notebooks/) (ewentualny `03_demo.ipynb`)
   - **Skutek:** W projekcie zaimplementowano w pełni funkcjonalną aplikację webową Streamlit ([`app.py`](../app.py)). W środowiskach o zaostrzonych regułach sieciowych (blokada portu 8501 lub brak uprawnień do uruchomienia serwera lokalnego) odbiorca może mieć trudność z uruchomieniem interfejsu przeglądarkowego.
   - **Potrzebna poprawka:** Opcjonalne przygotowanie lekkiego notatnika `notebooks/03_demo.ipynb` wykonującego predykcję za pomocą prostego kodu w komórkach dla recenzentów preferujących wyłącznie interfejs Jupyter.

---

### 4.1. Potwierdzenie braku blokad uruchomieniowych i ewaluacyjnych

Na podstawie szczegółowego przeglądu procedury odtworzeniowej przeprowadzonej w czystej kopii `praktyki-dane-odbior` (oraz weryfikacji raportów [`reports/reproduction.md`](reproduction.md) i [`reports/handover.md`](handover.md)) formalnie potwierdza się **całkowity brak problemów blokujących**:

- **Brak błędnych ścieżek:** Wszystkie ścieżki względne do danych surowych (`data/raw/`), oczyszczonych (`data/processed/`), bazy SQLite oraz raportów działają deterministycznie z poziomu głównego katalogu.
- **Brak brakujących bibliotek:** Plik [`requirements.txt`](../requirements.txt) zawiera pełen zestaw zależności odtwarzalnych w nowym środowisku wirtualnym (`pip check` $\rightarrow$ *No broken requirements found*).
- **Zgodność instrukcji uruchomieniowej:** Każde z poleceń opisanych w [`README.md`](../README.md) wykonuje się pomyślnie i bezbłędnie.
- **Kompletność kontroli i testów:** Zestaw 9/9 zautomatyzowanych testów jednostkowych (6 prób jakości danych w `tests/test_prepare_data.py` oraz 3 próby modelowania w `tests/test_training.py`) przechodzi w 100% ze statusem OK.
- **Potwierdzenie tożsamości wyników z czystej kopii:** Weryfikacja na nowo utworzonym środowisku potwierdziła tożsamość metryk MAE (różnica = 0.0000 dla treningu, walidacji i testu) oraz stuprocentową zgodność generowanych wektorów predykcji. Brak jakichkolwiek przeszkód uniemożliwiających odbiór techniczny.

---

### 4.2. Wynik kontrolowanej poprawki w kopii odbiorczej

Zgodnie z procedurą weryfikacji przeprowadzono drobną, kontrolowaną zmianę w kodzie formularza, najpierw w kopii `praktyki-dane-odbior`, a po sprawdzeniu przeniesiono ją do projektu głównego:

- **Zmieniony plik:** [`app.py`](../app.py) (wiersz 91)
- **Przyczyna zmiany:** Zwiększenie czytelności interfejsu dla kierownika magazynu – podanie wyuczonej mediany budżetu (575.28 PLN) bezpośrednio w etykiecie pola numerycznego, jeszcze przed rozwinięciem pomocy.
- **Treść przed zmianą:**
  ```python
  budget_input = st.number_input("Planowany budżet reklamowy w PLN (`planned_ad_spend_pln`):", ...)
  ```
- **Treść po zmianie:**
  ```python
  budget_input = st.number_input("Planowany budżet reklamowy w PLN (domyślnie mediana 575.28 PLN):", ...)
  ```
- **Sposób kontroli i wynik:**
  - Inspekcja różnicy poleceniem `git diff app.py` (zmiana dokładnie 1 linii tekstu etykiety).
  - Test kompilacji i importu w środowisku wirtualnym: `.\.venv\Scripts\python.exe -c "import app; print('app imports OK')"` $\rightarrow$ **`app imports OK`** (kod 0).
- **Integralność modelowania:** Zmiana nie wpłynęła na cechy, wagi modelu, hiperparametry ani dane testowe.



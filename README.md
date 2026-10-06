# Praktyki - Analiza Danych

## Cel praktyk
Celem praktyk jest opanowanie analizy danych z wykorzystaniem biblioteki pandas, środowiska Python oraz kontroli wersji Git. Ponadto celem jest opanowanie narzędzi analitycznych, automatyzacja pracy z danymi oraz efektywna współpraca z asystentami AI w środowisku IDE.

---

## 📊 Wprowadzenie do danych (`orders_intro.csv`)

Zbiór w [data/raw/orders_intro.csv](data/raw/orders_intro.csv) zawiera dzienne liczby zamówień z 6 dni: `8, 10, 10, 12, 15, 65`.

### Tabela podsumowująca:

| Metryka | Wartość | Sposób obliczenia |
| :--- | :---: | :--- |
| **Liczba dni** | 6 | Zliczenie wierszy z obserwacjami |
| **Suma zamówień** | 120 | 8 + 10 + 10 + 12 + 15 + 65 |
| **Średnia arytmetyczna** | 20.0 | 120 / 6 |
| **Mediana** | 11.0 | Uporządkowane: 8, 10, **10**, **12**, 15, 65 → (10 + 12) / 2 |

> **Wniosek analityczny:** Wartość 65 to element odstający (outlier). Średnia (20) jest na niego wrażliwa i uległa zawyżeniu, podczas gdy mediana (11) wierniej opisuje typowy dzień sprzedaży.

---

## 📁 Struktura repozytorium

Zgodnie z przyjętymi standardami projektu ([AGENTS.md](AGENTS.md)), struktura katalogów prezentuje się następująco:

```text
praktyki dane/
├── data/
│   ├── raw/            # Oryginalne, niemutowalne zbiory danych wejściowych (read-only)
│   └── processed/      # Wyczyszczone i przetworzone zbiory przygotowane do analizy
├── notebooks/          # Notatniki Jupyter (EDA, wizualizacje, prototypowanie)
├── src/                # Kod źródłowy wielokrotnego użytku, potoki danych, moduły pomocnicze
├── outputs/            # Wyniki prac: wygenerowane wykresy, modele, raporty
├── requirements.txt    # Lista bibliotek i zależności w projekcie
├── .gitignore          # Ignorowane pliki (środowiska wirtualne, dane wrażliwe/duże pliki, cache)
├── AGENTS.md           # Instrukcje i wytyczne dla asystentów AI pracujących w repozytorium
└── README.md           # Główna dokumentacja projektu
```

---

## 🛠️ Środowisko i wymagania

- **Język:** Python 3.10+
- **Środowisko wirtualne:** `.venv`
- **Główne biblioteki:**
  - `pandas` – manipulacja i analiza danych tabelarycznych
  - `numpy` – obliczenia numeryczne i macierzowe
  - `matplotlib`, `seaborn` – wizualizacja danych
  - `scikit-learn` – modelowanie statystyczne i uczenie maszynowe
  - `jupyter` – interaktywne środowisko notatników

---

## 🚀 Pierwsze kroki (Instalacja i konfiguracja)

1. **Utworzenie środowiska wirtualnego:**
   ```bash
   python -m venv .venv
   ```

2. **Aktywacja środowiska:**
   - **Windows (PowerShell):**
     ```powershell
     .\.venv\Scripts\Activate.ps1
     ```
   - **Windows (CMD):**
     ```cmd
     .\.venv\Scripts\activate.bat
     ```
   - **Linux / macOS:**
     ```bash
     source .venv/bin/activate
     ```

3. **Instalacja zależności:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

---

## 📋 Zasady pracy z danymi i kodem

1. **Integralność danych:**
   - Dane w katalogu `data/raw/` są **tylko do odczytu**. Żadne transformacje nie mogą nadpisywać surowych plików źródłowych.
   - Wszelkie przetworzone, oczyszczone zbiory należy zapisywać w `data/processed/`.
2. **Bezpieczeństwo danych:**
   - Nie umieszczaj w repozytorium kluczy API, haseł ani danych wrażliwych (PII).
3. **Powtarzalność wyników (Reproducibility):**
   - Wszystkie losowe operacje, podziały danych i trenowanie modeli muszą posiadać ustalony seed: `random_state=42` / `seed=42`.
4. **Jakość kodu:**
   - Kod w `src/` powinien spełniać standardy PEP 8 i posiadać adnotacje typów (type hinting).
   - Kod prototypowy i eksploracyjny umieszczamy w `notebooks/`, natomiast funkcje wielokrotnego użytku refaktoryzujemy do modułów w `src/`.
Projekt analityczny - wprowadzenie.
## Instrukcja uruchomienia projektu

### 1. Otwarcie projektu w Antigravity
1. Uruchom program **Antigravity**.
2. Wybierz z menu: **File** -> **Open Folder...** (Otwórz folder).
3. Wskaż główny katalog projektu (`praktyki dane`).

### 2. Dane wejściowe
Plik źródłowy z danymi wykorzystywanymi do analizy znajduje się pod ścieżką:
* `data/raw/orders_intro.csv`

### 3. Wybór środowiska wirtualnego (.venv) i uruchomienie notebooka
1. W drzewie plików po lewej stronie przejdź do katalogu `notebooks/` i otwórz plik `notebooks/01_start.ipynb`.
2. W prawym górnym rogu okna notebooka kliknij przycisk **Select Kernel**.
3. Wybierz pozycję **Python Environments...**, a następnie wskaż środowisko `.venv` znajdujące się w katalogu projektu (`.venv/Scripts/python.exe`).
4. Kliknij na górnym pasku notebooka opcję **Restart Kernel**, a następnie **Run All** (lub uruchamiaj komórki po kolei od góry).
5. Wszystkie komórki wykonają się poprawnie, prezentując podsumowanie statystyczne (6 dni, suma 120, średnia 20, mediana 11), wykres liniowy oraz tabelę analizy obserwacji odstającej.

### 4. Przygotowanie i czyszczenie zbiorów danych (Pipeline: Trening i Walidacja)
Do powtarzalnego, deterministycznego wyczyszczenia zbioru treningowego i walidacyjnego służy skrypt [src/prepare_data.py](src/prepare_data.py).

1. **Uruchomienie w terminalu Antigravity z głównego katalogu projektu:**
   ```powershell
   .\.venv\Scripts\python src/prepare_data.py
   ```
   *(lub po uprzedniej aktywacji wirtualnego środowiska: `python src/prepare_data.py`)*

2. **Działanie skryptu:**
   * Wczytuje zbiory surowe [data/raw/orders_train_raw.csv](data/raw/orders_train_raw.csv) oraz [data/raw/orders_validation.csv](data/raw/orders_validation.csv) (tryb read-only, bez modyfikacji oryginałów).
   * Usuwa powtórzone wiersze (trening: redukcja z 255 do 252 wierszy; walidacja: 84 wiersze bez duplikatów).
   * Standaryzuje kolumnę `promo` (zamienia tekst `' yes '` na `1`, rzutuje na typ `int64`).
   * Waliduje format dat (ISO `YYYY-MM-DD`), weryfikuje brak duplikatów i sortuje chronologicznie.
   * Obsługuje wartości ujemne `orders`: zamienia je na brak (`NaN`) i dodaje kolumnę flagi `orders_invalid` (`1` dla wartości ujemnych, `0` dla poprawnych).
   * Zachowuje braki bez imputacji (w walidacji cel `orders` pozostaje nienaruszony, mediana budżetu nie jest liczona).
   * Dołącza cechę `day_of_week` (0-6) z [data/raw/calendar.csv](data/raw/calendar.csv) bez dołączania `is_weekend`.
   * Przeprowadza automatyczne kontrole integralności (unikalność klucza kalendarza, brak fan-out, stałość sum `orders`, brak wspólnych dat, sekwencyjność czasowa).
   * Zapisuje oczyszczone zbiory do [data/processed/orders_train.csv](data/processed/orders_train.csv) oraz [data/processed/orders_validation.csv](data/processed/orders_validation.csv).

### 5. Uruchomienie testów jednostkowych (Próby sprawdzające)
Do automatycznej weryfikacji poprawności reguł czyszczenia na izolowanych próbkach danych służy skrypt [tests/test_prepare_data.py](tests/test_prepare_data.py).

1. **Polecenie uruchomienia testów w terminalu z głównego folderu:**
   ```powershell
   .\.venv\Scripts\python tests/test_prepare_data.py
   ```
   *(lub po uprzedniej aktywacji wirtualnego środowiska: `python tests/test_prepare_data.py`)*

2. **Zakres sprawdzanych prób:**
   * **Próba 1 (Ujemne `orders`):** Weryfikuje, czy ujemna wartość zamówień (`-5.0`) zostaje zamieniona na brak danych (`NaN`), a w kolumnie `orders_invalid` ustawiona zostaje flaga `1`.
   * **Próba 2 (Niepoprawna data):** Weryfikuje, czy uszkodzony format daty zgłasza czytelny błąd `ValueError` informujący o nieoczekiwanym formacie danych (zamiast zwracać pusty wynik).
   * **Bezpieczeństwo danych:** Testy operują na katalogu tymczasowym (`tempfile`) i nie modyfikują oryginalnego pliku `data/raw/orders_train_raw.csv`.

### 6. Baza danych SQLite i zapytania analityczne (SQL)
Do załadowania oczyszczonych danych do lokalnej bazy SQLite oraz wykonania zapytań analitycznych służy skrypt [src/query_data.py](src/query_data.py).

1. **Polecenie uruchomienia w terminalu z głównego folderu:**
   ```powershell
   .\.venv\Scripts\python src/query_data.py
   ```
   *(lub po uprzedniej aktywacji wirtualnego środowiska: `python src/query_data.py`)*

2. **Działanie skryptu:**
   * Wczytuje dane z pliku [data/processed/orders_train.csv](data/processed/orders_train.csv) do tabeli `orders_train` w lokalnej bazie [data/processed/orders.sqlite](data/processed/orders.sqlite).
   * Weryfikuje typy kolumn: `orders` jako liczba rzeczywista (`REAL`), a wartości brakujące jako natywny SQL `NULL` (nie tekst `'NULL'`).
   * Demonstruje zachowanie funkcji agregujących `COUNT(*)` vs `COUNT(kolumna)` vs `AVG(kolumna)` na zestawie `8, 10, NULL`.
   * Wykonuje zapytania analityczne zdefiniowane w pliku [sql/queries.sql](sql/queries.sql):
     - 10 pierwszych dat w kolejności chronologicznej,
     - Dni z aktywną promocją (`promo = 1`),
     - 5 dni z największą liczbą zamówień (`orders`),
     - Porównanie `COUNT(*)` i `COUNT(orders)` (badanie braków).

### 7. Zalecana kolejność uruchomienia potoku danych (Pipeline Workflow)

Aby zagwarantować pełną powtarzalność, spójność liczb i poprawność generowanych raportów, potok danych należy uruchamiać w następującej kolejności:

```text
[1. src/prepare_data.py]  ──►  [2. src/query_data.py]  ──►  [3. notebooks/02_analysis.ipynb]
(Czyszczenie danych CSV)      (Baza SQLite i agregacje)       (Wizualizacje i asercje pandas vs SQL)
```

#### Krok 1: Przygotowanie i czyszczenie danych treningowych
* **Polecenie:**
  ```powershell
  python src/prepare_data.py
  ```
* **Dane wejściowe:** [data/raw/orders_train_raw.csv](data/raw/orders_train_raw.csv)
* **Plik wynikowy:** [data/processed/orders_train.csv](data/processed/orders_train.csv)
* **Obsługa ścieżek i brakującego pliku CSV:**
  - Skrypt dynamicznie wspiera uruchamianie zarówno z głównego katalogu repozytorium (`data/raw/...`), jak i z podkatalogów roboczych (np. `../data/raw/...`).
  - W przypadku braku pliku źródłowego skrypt rzuca jednoznaczny wyjątek `FileNotFoundError: Nie znaleziono pliku źródłowego: <ścieżka>`, uniemożliwiając ciche kontynuowanie z błędnymi danymi.
  - Przy uszkodzonym lub pustym pliku CSV zgłaszany jest wyjątek `ValueError` z precyzyjnym komunikatem.

#### Krok 2: Załadowanie bazy danych SQLite i zapytania analityczne
* **Polecenie:**
  ```powershell
  python src/query_data.py
  ```
* **Działanie:**
  - Wczytuje wyczyszczony zbiór do bazy [data/processed/orders.sqlite](data/processed/orders.sqlite).
  - Wykonuje zapytania analityczne i generuje podsumowania do plików CSV w katalogu `reports/`:
    - [reports/by_promo.csv](reports/by_promo.csv) – sprzedaż w dniach z promocją i bez,
    - [reports/by_month.csv](reports/by_month.csv) – dynamika miesięczna,
    - [reports/by_weekday.csv](reports/by_weekday.csv) – podsumowanie według dni tygodnia.
  - Wyznacza bazowe wartości kontrolne SQL: **248 ważnych dni** i **sumę 20 933.0 zamówień**.

#### Krok 3: Analiza eksploracyjna i raportowanie w notebooku
* **Plik:** [notebooks/02_analysis.ipynb](notebooks/02_analysis.ipynb)
* **Instrukcja uruchomienia:**
  1. Otwórz notatnik w Antigravity.
  2. Kliknij **Restart Kernel**, a następnie **Run All** (uruchomienie wszystkich komórek od góry do dołu).
* **Zawartość i kontrole:**
  - Notatnik wywołuje `src/prepare_data.py`, zachowując reguły czyszczenia w jednym skrypcie.
  - W sekcji kontrolnej wykonuje formalne porównanie pandas vs SQL potwierdzające 100% zgodności (liczba obserwacji: 248, suma zamówień: 20 933.0) za pomocą automatycznych asercji (`assert`).
  - Prezentuje tabele podsumowujące oraz generuje 3 oficjalne wykresy do katalogu `reports/` ([orders_by_date.png](reports/orders_by_date.png), [orders_by_weekday.png](reports/orders_by_weekday.png), [orders_histogram.png](reports/orders_histogram.png)) wraz z wariantem demonstracyjnym uciętej osi ([orders_by_weekday_truncated_demo.png](reports/orders_by_weekday_truncated_demo.png)).

### 8. Praca z gałęziami Git (Ćwiczenie kontrolne)
W ramach ćwiczenia kontroli wersji wykonano poprawkę redakcyjną tekstu w raporcie [reports/analysis.md](reports/analysis.md) na dedykowanej gałęzi roboczej `report-review`:
* **Commit na GitHub:** [`7a20bb9`](https://github.com/jakubszymura28-cyber/praktyki-dane/commit/7a20bb9caea01ed6d588583d7dfc03cadbe43335) (*`docs(report): uproszczenie wyjasnienia korelacji i przyczynowosci`*).
* **Zakres:** Uproszczenie wyjaśnienia braku przyczynowości w punkcie 2 sekcji ograniczeń analizy.

### 9. Przygotowanie do modelowania i Karta Modelu (Dzień 9)
Dokumentacja założeń modelowania prognostycznego znajduje się w pliku [reports/model_card.md](reports/model_card.md):
* **Cel:** Dobowa prognoza popytu dla magazynu ($t+1$).
* **Zależności:** Biblioteka `scikit-learn` została dodana do [requirements.txt](requirements.txt).
* **Modele i metryka:** Porównanie `DecisionTreeRegressor` z modelem bazowym `DummyRegressor(strategy='median')` za pomocą metryki MAE na ustalonym zbiorze walidacyjnym (84 dni bez shuffle).

### 10. Przetwarzanie zbioru walidacyjnego i cech kalendarza (Dzień 10)
W ramach rozbudowy potoku danych przygotowano proces walidacyjny oraz złączenie cech czasowych z kalendarza:
* **Dane wejściowe:** [data/raw/orders_validation.csv](data/raw/orders_validation.csv) (84 wiersze, zakres `2024-09-09` – `2024-12-01`).
* **Zasady jakości i ochrona przed wyciekiem danych (Data Leakage):**
  - Zastosowano te same reguły czyszczenia co dla treningu w skrypcie [src/prepare_data.py](src/prepare_data.py).
  - Wartości docelowe `orders` w walidacji **nie są imputowane**.
  - Nie jest obliczana mediana budżetu na zbiorze walidacyjnym (brak wycieku informacji do procesu uczenia).
* **Dołączenie cechy kalendarzowej:**
  - Dołączono kolumnę `day_of_week` (0 = poniedziałek, ..., 6 = niedziela) z [data/raw/calendar.csv](data/raw/calendar.csv) po kluczu `date`.
  - Kolumna `is_weekend` **nie** została dodana do cech modelu.
* **Kontrole integralności i rygor podziału czasowego:**
  - **Liczności:** Trening: 252 daty (248 poprawnych celów, 4 braki), Walidacja: 84 daty (84 poprawne cele, 0 braków).
  - **Brak fan-out:** Liczba wierszy i suma `orders` przed i po złączeniu z kalendarzem są identyczne (suma trening: 20 933.0, suma walidacja: 7 492.0).
  - **Rozłączność czasowa:** $\text{Trening} \cap \text{Walidacja} = \emptyset$ (brak wspólnych dat).
  - **Sekwencyjność:** Zbiór walidacyjny rozpoczyna się `2024-09-09`, ściśle po końcu treningu (`2024-09-08`).
* **Pliki wynikowe:** [data/processed/orders_train.csv](data/processed/orders_train.csv) oraz [data/processed/orders_validation.csv](data/processed/orders_validation.csv).
* **Szczegółowy audyt:** Pełny raport kontroli złączenia i podziału czasowego znajduje się w Sekcji 11 raportu [reports/quality.md](reports/quality.md).

### 11. Potok przygotowania cech i treningu (Dzień 11)
Do powtarzalnego, bezpiecznego przygotowania cech do modelowania służy skrypt [src/train.py](src/train.py).

1. **Polecenie uruchomienia w terminalu z głównego folderu:**
   ```powershell
   .\.venv\Scripts\python src/train.py
   ```
   *(lub po aktywacji środowiska: `python src/train.py`)*

2. **Działanie skryptu i ochrona przed wyciekiem danych:**
   * **Izolacja próby:** Uczenie potoku (`.fit()`) odbywa się **wyłącznie na 248 wierszach treningowych** posiadających poprawną wartość celu `orders` (4 wiersze z brakami są wykluczone).
   * **Cechy wejściowe ($X$):** wyłącznie `day_of_week`, `promo`, `planned_ad_spend_pln`.
   * **Kolumny wykluczone:** `visits` i `revenue_pln` **nie są cechami** (zapobieganie wyciekowi danych w czasie $t+1$).
   * **Struktura potoku `ColumnTransformer`:**
     - `SimpleImputer(strategy='median')` – **uczy się z treningu** mediany budżetu reklamowego (`575.275 PLN`) do uzupełniania braków.
     - `OneHotEncoder(handle_unknown='ignore')` – **uczy się z treningu** 7 kategorii dni tygodnia (0–6).
     - `passthrough` – **stosuje ustaloną regułę** przekazania binarnej flagi `promo` (0/1) bez uczenia wag.
   * **Kontrola spójności:** Skrypt automatycznie weryfikuje zgodność wyuczonej mediany z niezależnym rachunkiem pandas (`575.275 PLN == 575.275 PLN`, błąd = 0.00).
   * **Szczegóły audytu:** Pełne zestawienie znajduje się w Sekcji 8 dokumentu [reports/model_card.md](reports/model_card.md).

### 12. Ewaluacja modelu bazowego DummyRegressor (Dzień 12)
W ramach implementacji modelu odniesienia skrypt [src/train.py](src/train.py) trenuje model `DummyRegressor(strategy='median')`:
* **Uczenie i stała prognoza:** Uczony wyłącznie na 248 wierszach treningowych z poprawnym celem; wyznacza stałą prognozę równą medianie z treningu: **85.0 szt./dzień**.
* **Predykcja na walidacji:** Generuje prognozy dla wszystkich 84 dni zbioru walidacyjnego.
* **Wyniki metryk MAE:**
  - Zbiór treningowy (248 dni): **17.1815 szt./dzień**
  - Zbiór walidacyjny (84 dni): **16.2143 szt./dzień**
* **Wygenerowane raporty:**
  - [reports/metrics.csv](reports/metrics.csv) – formalne zestawienie MAE dla zbioru treningowego i walidacyjnego.
  - [reports/validation_predictions.csv](reports/validation_predictions.csv) – dzienne zestawienie dat, poprawnych wartości `orders`, prognoz stałych (`85.0`) oraz błędów bezwzględnych.
* **Kontrola ręczna (pierwsze 3 dni walidacji):**
  - `2024-09-09`: rzeczywiste 78.0, prognoza 85.0 $\rightarrow$ błąd bezwzględny = 7.0 szt.
  - `2024-09-10`: rzeczywiste 68.0, prognoza 85.0 $\rightarrow$ błąd bezwzględny = 17.0 szt.
  - `2024-09-11`: rzeczywiste 56.0, prognoza 85.0 $\rightarrow$ błąd bezwzględny = 29.0 szt.
  - Średni błąd 3 pierwszych dni: **17.67 szt.** (zbliżony do ogólnego MAE walidacji: **16.21 szt.**).





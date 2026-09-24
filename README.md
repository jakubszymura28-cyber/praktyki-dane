# Praktyki - Analiza Danych

## Cel praktyk
Celem praktyk jest opanowanie analizy danych z wykorzystaniem biblioteki pandas, środowiska Python oraz kontroli wersji Git. Ponadto celem jest opanowanie narzędzi analitycznych, automatyzacja pracy z danymi oraz efektywna współpraca z asystentami AI w środowisku IDE.

---

## 📊 Wprowadzenie do danych (`orders_intro.csv`)

Zbiór w [data/raw/orders_intro.csv](file:///c:/Users/Lenovo/Desktop/praktyki%20dane/data/raw/orders_intro.csv) zawiera dzienne liczby zamówień z 6 dni: `8, 10, 10, 12, 15, 65`.

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

Zgodnie z przyjętymi standardami projektu ([AGENTS.md](file:///c:/Users/Lenovo/Desktop/praktyki%20dane/AGENTS.md)), struktura katalogów prezentuje się następująco:

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

### 4. Przygotowanie i czyszczenie zbioru treningowego (Pipeline)
Do powtarzalnego, deterministycznego wyczyszczenia zbioru treningowego służy skrypt [src/prepare_data.py](file:///c:/Users/Lenovo/Desktop/praktyki%20dane/src/prepare_data.py).

1. **Uruchomienie w terminalu Antigravity z głównego katalogu projektu:**
   ```powershell
   .\.venv\Scripts\python src/prepare_data.py
   ```
   *(lub po uprzedniej aktywacji wirtualnego środowiska: `python src/prepare_data.py`)*

2. **Działanie skryptu:**
   * Wczytuje zbiór surowy [data/raw/orders_train_raw.csv](file:///c:/Users/Lenovo/Desktop/praktyki%20dane/data/raw/orders_train_raw.csv) (tryb read-only, bez modyfikacji oryginału).
   * Usuwa identyczne powtórzone wiersze (redukcja z 255 do 252 wierszy).
   * Standaryzuje kolumnę `promo` (zamienia tekst `' yes '` na `1`, rzutuje na typ `int64`).
   * Waliduje format dat (ISO `YYYY-MM-DD`), weryfikuje brak duplikatów i sortuje chronologicznie.
   * Obsługuje wartości ujemne `orders`: zamienia je na brak (`NaN`) i dodaje kolumnę flagi `orders_invalid` (`1` dla wartości ujemnych, `0` dla poprawnych).
   * Zachowuje braki w `planned_ad_spend_pln` i `orders` bez imputacji.
   * Weryfikuje strukturę danych i zgłasza błąd (`ValueError`) przy nieoczekiwanym formacie danych lub braku kolumn zamiast zwracać pusty wynik.
   * Zapisuje oczyszczony plik wynikowy do [data/processed/orders_train.csv](file:///c:/Users/Lenovo/Desktop/praktyki%20dane/data/processed/orders_train.csv).

### 5. Uruchomienie testów jednostkowych (Próby sprawdzające)
Do automatycznej weryfikacji poprawności reguł czyszczenia na izolowanych próbkach danych służy skrypt [tests/test_prepare_data.py](file:///c:/Users/Lenovo/Desktop/praktyki%20dane/tests/test_prepare_data.py).

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
Do załadowania oczyszczonych danych do lokalnej bazy SQLite oraz wykonania zapytań analitycznych służy skrypt [src/query_data.py](file:///c:/Users/Lenovo/Desktop/praktyki%20dane/src/query_data.py).

1. **Polecenie uruchomienia w terminalu z głównego folderu:**
   ```powershell
   .\.venv\Scripts\python src/query_data.py
   ```
   *(lub po uprzedniej aktywacji wirtualnego środowiska: `python src/query_data.py`)*

2. **Działanie skryptu:**
   * Wczytuje dane z pliku [data/processed/orders_train.csv](file:///c:/Users/Lenovo/Desktop/praktyki%20dane/data/processed/orders_train.csv) do tabeli `orders_train` w lokalnej bazie [data/processed/orders.sqlite](file:///c:/Users/Lenovo/Desktop/praktyki%20dane/data/processed/orders.sqlite).
   * Weryfikuje typy kolumn: `orders` jako liczba rzeczywista (`REAL`), a wartości brakujące jako natywny SQL `NULL` (nie tekst `'NULL'`).
   * Demonstruje zachowanie funkcji agregujących `COUNT(*)` vs `COUNT(kolumna)` vs `AVG(kolumna)` na zestawie `8, 10, NULL`.
   * Wykonuje zapytania analityczne zdefiniowane w pliku [sql/queries.sql](file:///c:/Users/Lenovo/Desktop/praktyki%20dane/sql/queries.sql):
     - 10 pierwszych dat w kolejności chronologicznej,
     - Dni z aktywną promocją (`promo = 1`),
     - 5 dni z największą liczbą zamówień (`orders`),
     - Porównanie `COUNT(*)` i `COUNT(orders)` (badanie braków).



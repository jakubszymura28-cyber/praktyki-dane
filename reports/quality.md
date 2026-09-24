# Raport Jakości Danych: `orders_train_raw.csv`

Data wygenerowania: 2026-09-22  
Analizowany plik: `data/raw/orders_train_raw.csv`  
Notebook weryfikacyjny: `notebooks/02_analysis.ipynb`

---

## 1. Podsumowanie wymiarów danych

* **Liczba wszystkich wierszy:** 255
* **Liczba unikalnych dat:** 252 (zakres od `2024-01-01` do `2024-09-08`)
* **Liczba kolumn:** 6 (`date`, `promo`, `planned_ad_spend_pln`, `orders`, `visits`, `revenue_pln`)
* **Status pliku surowego:** Plik źródłowy pozostaje nienaruszony (zgodnie z zasadą niemutowania danych surowych w `data/raw/`).

---

## 2. Tabela reguł walidacji i czyszczenia danych

| Problem | Reguła | Co zrobimy | Przykład |
|---|---|---|---|
| **Identyczne powtórzone wiersze** | `date` występuje dokładnie raz. Z dwóch identycznych wierszy zostawiamy jeden. | Usuwamy duplikat (`drop_duplicates()`), zachowując tylko jedno wystąpienie. | Data `2024-01-31` (oraz `2024-05-30`, `2024-08-18`) – wiersz zduplikowany na końcu pliku. |
| **Sprzeczne rekordy dla tej samej daty** | `date` to poprawna data i występuje raz. Jeśli ta sama data ma różne liczby zamówień, program ma zgłosić konflikt i zatrzymać się, bo nie wiemy, który zapis jest prawidłowy. | Zgłaszamy błąd walidacji i przerywamy wykonanie skryptu, jeśli dla tej samej daty pojawią się różne wartości. | W badanym CSV nie występuje (wszystkie 3 powtórzone daty są w 100% identycznymi wierszami). Reguła zabezpiecza pipeline. |
| **Niepoprawny format lub unikalność daty** | `date` to poprawna data i występuje raz (format ISO `YYYY-MM-DD`). | Walidujemy format ISO, konwertujemy na `datetime` i sprawdzamy unikalność po usunięciu duplikatów. | Daty od `2024-01-01` do `2024-09-08` (dokładnie 252 unikalne dni po deduplikacji). |
| **Ujemna liczba zamówień** | `orders` to liczba całkowita od zera wzwyż albo brak. Liczba ujemna jest błędem. | W pliku wynikowym zamieniamy ujemną wartość na brak danych (`NaN`) i dodajemy kolumnę `orders_invalid` (wartość 1 dla błędnych rekordów, 0 dla poprawnych). Liczbę takich zmian (2 rekordy) odnotowujemy w raporcie. Braków nie uzupełniamy. | Data `2024-04-30` (`orders = -5.0`) oraz data `2024-08-13` (`orders = -5.0`). |
| **Brak liczby zamówień (pusta komórka)** | `orders` to liczba całkowita od zera wzwyż albo brak. Brak `orders` oznacza nieznaną liczbę zamówień, zero oznacza brak zamówień. | Pozostawiamy jako brak danych (`NaN`); braków celu na tym etapie nie uzupełniamy (nie imputujemy). W kolumnie `orders_invalid` przypisujemy 0 (ponieważ brak nie jest ujemną wartością). | Data `2024-03-04` (puste pole `orders`) oraz data `2024-07-11` (puste pole `orders`). |
| **Brakujący budżet reklamowy** | Budżet (`planned_ad_spend_pln`) jest nieujemny albo pusty. | Pozostawiamy puste komórki (`NaN`) w danych oczyszczonych; budżetu na tym etapie nie imputujemy. | Data `2024-01-18` (oraz `2024-03-30`, `2024-06-19`, `2024-09-05`) – puste komórki budżetu. |
| **Niespójny tekstowy zapis promocji** | `promo` ma wartość 0 lub 1. Wpis `' yes '` oznacza promocję, więc zostanie zamieniony na 1. | Usuwamy zbędne białe znaki (`strip`), zamieniamy tekst `'yes'` na liczbę `1`, a kolumnę rzutujemy na typ `int64`. | Data `2024-02-10` (oraz `2024-05-03`, `2024-07-20`) – wartość `" yes "`. |

---

## 3. Podsumowanie statystyczne wykrytych usterek

| Kategoria problemu | Kolumna | Liczba przypadków | Wpływ na model / Interpretacja |
|---|---|:---:|---|
| **Powtórzone wiersze (pełne duplikaty)** | Wszystkie | **3** | Nadmiarowe obserwacje zaburzające wagi próbki; do bezwzględnego usunięcia. |
| **Puste komórki (braki danych)** | `planned_ad_spend_pln` | **4** | Brakujący budżet reklamowy; wymaga imputacji medianą wyliczoną na zbiorze treningowym. |
| **Puste komórki (brak targetu)** | `orders` | **2** | Nieznana liczba zamówień; nie wolno imputować targetu, wiersze należy wykluczyć z treningu. |
| **Wartości ujemne (błędny target)** | `orders` | **2** | Liczba ujemna jest ewidentnym błędem; wymaga wykluczenia z procesu uczenia modelu. |
| **Niespójne wartości tekstowe** | `promo` | **3** | Wartość `' yes '` ze spacjami; wymaga oczyszczenia tekstu i zmapowania na wartość liczbową `1`. |

---

## 4. Szczegółowy wykaz i przykłady wykrytych usterek

### 3.1. Powtórzone wiersze (identyczne duplikaty)
W zbiorze odnaleziono 3 wiersze, które zostały zduplikowane na końcu pliku (indeksy 252, 253, 254). Wszystkie wartości są w 100% identyczne z wcześniejszymi wpisami (brak sprzecznych danych dla tych samych dat).

* **Przykład 1 (Data: `2024-01-31`, wiersze 31 i 253 w CSV):**
  ```csv
  "2024-01-31","0","896.19","85","919","9355.78"
  ```
* **Przykład 2 (Data: `2024-05-30`, wiersze 151 i 254 w CSV):**
  ```csv
  "2024-05-30","0","246.24","52","732","6025.31"
  ```
* **Przykład 3 (Data: `2024-08-18`, wiersze 231 i 255 w CSV):**
  ```csv
  "2024-08-18","0","928.43","102","865","9145.95"
  ```

---

### 3.2. Puste komórki w budżecie reklamowym (`planned_ad_spend_pln`)
W 4 dniach brakuje informacji o zaplanowanym budżecie reklamowym. W pliku CSV pole to jest puste między przecinkami.

* **Przypadek 1 (Data: `2024-01-18`, wiersz 18 w CSV):**
  ```csv
  "2024-01-18","0","","87","761","8664.65"
  ```
* **Przypadek 2 (Data: `2024-03-30`, wiersz 90 w CSV):**
  ```csv
  "2024-03-30","0","","115","1501","10509.63"
  ```
* **Przypadek 3 (Data: `2024-06-19`, wiersz 171 w CSV):**
  ```csv
  "2024-06-19","0","","55","480","4407.89"
  ```
* **Przypadek 4 (Data: `2024-09-05`, wiersz 249 w CSV):**
  ```csv
  "2024-09-05","0","","71","949","7653.26"
  ```

---

### 3.3. Puste komórki w celu prognozy (`orders` = NaN)
Brak wartości `orders` oznacza **nieznaną liczbę zamówień** w danym dniu. Zgodnie ze sztuką modelowania i opisem projektu, **celu nie wolno imputować**.

* **Przypadek 1 (Data: `2024-03-04`, wiersz 64 w CSV):**
  ```csv
  "2024-03-04","1","732.12","","1069","8335.70"
  ```
* **Przypadek 2 (Data: `2024-07-11`, wiersz 193 w CSV):**
  ```csv
  "2024-07-11","0","763.38","","1334","8280.79"
  ```

---

### 3.4. Ujemne wartości w kolumnie `orders` (błąd danych)
Faktyczna liczba zamówień nie może być mniejsza od zera. Wartość zero oznaczałaby dzień bez sprzedaży, natomiast wartości ujemne (`-5.0`) stanowią ewidentny błąd danych syntetycznych.

* **Przypadek 1 (Data: `2024-04-30`, wiersz 121 w CSV):**
  ```csv
  "2024-04-30","0","440.53","-5","746","6561.21"
  ```
* **Przypadek 2 (Data: `2024-08-13`, wiersz 226 w CSV):**
  ```csv
  "2024-08-13","0","767.83","-5","940","8093.25"
  ```

---

### 3.5. Niespójne wartości tekstowe w kolumnie `promo`
Kolumna powinna przyjmować wartości binarne `0` (brak promocji) lub `1` (promocja). W 3 wierszach pojawił się ciąg tekstowy `' yes '` otoczony spacjami.

* **Przypadek 1 (Data: `2024-02-10`, wiersz 41 w CSV):**
  ```csv
  "2024-02-10"," yes ","205.78","101","1440","9929.48"
  ```
* **Przypadek 2 (Data: `2024-05-03`, wiersz 124 w CSV):**
  ```csv
  "2024-05-03"," yes ","271.90","112","966","11481.11"
  ```
* **Przypadek 3 (Data: `2024-07-20`, wiersz 202 w CSV):**
  ```csv
  "2024-07-20"," yes ","445.64","106","1405","11356.94"
  ```

---

## 5. Podgląd pierwszych 10 wierszy zbioru danych

| Indeks | `date` | `promo` | `planned_ad_spend_pln` | `orders` | `visits` | `revenue_pln` |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **0** | 2024-01-01 | 0 | 852.81 | 88.0 | 841 | 9090.32 |
| **1** | 2024-01-02 | 1 | 413.23 | 84.0 | 737 | 9404.07 |
| **2** | 2024-01-03 | 0 | 961.22 | 77.0 | 987 | 6579.19 |
| **3** | 2024-01-04 | 0 | 697.53 | 84.0 | 1046 | 7581.46 |
| **4** | 2024-01-05 | 0 | 541.13 | 76.0 | 1069 | 7947.15 |
| **5** | 2024-01-06 | 0 | 229.25 | 100.0 | 1022 | 11890.46 |
| **6** | 2024-01-07 | 1 | 513.96 | 108.0 | 968 | 11229.29 |
| **7** | 2024-01-08 | 0 | 998.01 | 88.0 | 1171 | 10047.78 |
| **8** | 2024-01-09 | 0 | 393.78 | 62.0 | 794 | 7113.78 |
| **9** | 2024-01-10 | 0 | 404.74 | 66.0 | 742 | 6928.37 |

---

## 6. Wytyczne do etapu czyszczenia i przygotowania danych

1. **Integralność danych źródłowych:** Plik [data/raw/orders_train_raw.csv](file:///c:/Users/Lenovo/Desktop/praktyki%20dane/data/raw/orders_train_raw.csv) pozostawiamy niezmieniony. Wszystkie operacje czyszczące zapisujemy do [data/processed/](file:///c:/Users/Lenovo/Desktop/praktyki%20dane/data/processed/).
2. **Duplikaty:** Usunąć 3 nadmiarowe wiersze metodą `df.drop_duplicates()`.
3. **Standaryzacja `promo`:** Usunąć białe znaki (`.str.strip()`), zamapować `'yes'` na `1`, rzutować na typ całkowity `int64`.
4. **Obsługa targetu (`orders`) oraz flaga `orders_invalid`:** W pliku wynikowym wartości ujemne (`< 0`, dokładnie 2 rekordy) zamieniamy na brak danych (`NaN`) i dodajemy kolumnę `orders_invalid` (wartość 1 dla błędnych rekordów, 0 dla poprawnych). Wiersze z brakami (`NaN`) – łącznie 4 rekordy (2 pierwotne braki + 2 zamienione z ujemnych) – nie są uzupełniane na tym etapie i zostaną wykluczone z treningu modeli.
5. **Obsługa braków w `planned_ad_spend_pln`:** Pozostawić braki (4 rekordy) na etapie wstępnym bez uzupełniania; imputację medianą przeprowadzić w potoku `scikit-learn` (`SimpleImputer(strategy='median')`) dopasowanym wyłącznie na zbiorze treningowym.
6. **Ochrona przed wyciekiem danych (data leakage):** Kolumny `visits` oraz `revenue_pln` nie mogą być przekazywane do modelu predykcyjnego jako cechy.

---

## 7. Podział cech według momentu dostępności (Data Leakage)

W procesie budowy modelu prognozującego liczbę zamówień na kolejny dzień kluczowe jest rozgraniczenie informacji, którymi dysponujemy przed rozpoczęciem dnia, od metryk będących wynikiem tego dnia.

### 🟢 Wiemy przed rozpoczęciem dnia (dozwolone cechy modelu):
* **`date`** – data kalendarzowa (format ISO `YYYY-MM-DD`, klucz do łączenia).
* **`day_of_week`** – dzień tygodnia z kalendarza (0 = poniedziałek, ..., 6 = niedziela; do zakodowania kategorycznego).
* **`is_weekend`** – flaga weekendu (0 lub 1; pomocnicza w analizie EDA).
* **`promo`** – zaplanowana na dany dzień akcja promocyjna (wartość binarna 0 lub 1).
* **`planned_ad_spend_pln`** – zaplanowany z góry budżet reklamowy na dany dzień w PLN (braki danych wymagają imputacji).

### 🔴 Poznamy po zakończeniu dnia (wyniki operacyjne – zabronione jako cechy):
* **`orders`** – faktyczna liczba zamówień (jest to **cel prognozy / target**, a nie cecha wejściowa).
* **`visits`** – faktyczna liczba zrealizowanych wizyt w sklepie.
* **`revenue_pln`** – faktyczny dzienny przychód ze sprzedaży w PLN.

> **Dlaczego `visits` i `revenue_pln` nie pomogą przewidzieć jutra?**  
> Kolumny `visits` i `revenue_pln` nie pomogą przewidzieć jutra, ponieważ jutrzejszych wizyt i jutrzejszego przychodu jeszcze nie znamy w momencie tworzenia prognozy operacyjnej.

---

## 8. Kluczowy wniosek: dlaczego pustego `orders` nie można zamienić na zero?

Pustego pola w kolumnie `orders` (brak danych / `NaN`) **nie wolno zamienić na zero**, ponieważ brak oznacza **nieznaną liczbę zamówień** (np. błąd systemu rejestrującego czy brak raportu), podczas gdy zero to konkretna, potwierdzona biznesowo informacja, że **sklep pracował, lecz nie zrealizował żadnego zamówienia**. Wstawienie zera w miejsce braku zafałszowałoby historię sprzedaży i wprowadziło model w błąd, dlatego wiersze z brakującym celem należy usunąć z danych treningowych, a nie imputować.

---

## 9. Trzy próby sprawdzające reguły czyszczenia (Unit Test Cases)

W celu weryfikacji powtarzalnego potoku czyszczącego zdefiniowano 3 małe próby testowe z dokładnie określonym wejściem i oczekiwanym wynikiem:

### 🧪 Próba 1: Usunięcie identycznych powtórzonych wierszy (Deduplikacja)
* **Wejście (Dane surowe):** Wystąpienie dwóch w 100% identycznych rekordów dla daty `2024-01-31`:
  * Wiersz indeks 30: `date='2024-01-31', promo='0', planned_ad_spend_pln=896.19, orders=85.0, visits=919, revenue_pln=9355.78`
  * Wiersz indeks 252: `date='2024-01-31', promo='0', planned_ad_spend_pln=896.19, orders=85.0, visits=919, revenue_pln=9355.78`
* **Oczekiwany wynik:** W zbiorze po deduplikacji data `2024-01-31` występuje **dokładnie jeden raz**, a łączna liczba wierszy zmniejsza się o 3 (z 255 do 252).

### 🧪 Próba 2: Standaryzacja niespójnego zapisu promocji (`promo`)
* **Wejście (Dane surowe):** Rekord z daty `2024-02-10` (wiersz indeks 40), w którym pole `promo` zawiera wartość tekstową ze spacjami:
  * `date='2024-02-10', promo=' yes ', ...`
* **Oczekiwany wynik:** Usunięcie białych znaków, konwersja na wartość liczbową `1` oraz spójny typ `int64` dla całej kolumny:
  * `date='2024-02-10', promo=1` (typ `int64`).

### 🧪 Próba 3: Obsługa ujemnej wartości zamówień (`orders < 0`) i flaga `orders_invalid`
* **Wejście (Dane surowe):** Rekord z daty `2024-04-30` (wiersz indeks 120), w którym liczba zamówień jest ujemna:
  * `date='2024-04-30', orders=-5.0, ...`
* **Oczekiwany wynik:**
  * Wartość `orders` zamieniona na brak danych (`NaN`).
  * Nowo utworzona kolumna flagi binarnej `orders_invalid` przyjmuje wartość `1` (błąd danych).
  * Dla pozostałych poprawnych rekordów kolumna `orders_invalid` przyjmuje wartość `0`.

---

## 10. Tabela porównawcza przed i po czyszczeniu (Before / After Summary)

| Cecha / Metryka | Zbiór surowy (`orders_train_raw.csv`) | Zbiór wyczyszczony (`orders_train_cleaned.csv`) | Różnica / Efekt reguły |
|---|:---:|:---:|---|
| **Liczba wierszy** | 255 | 252 | **-3 wiersze** (usunięto identyczne duplikaty) |
| **Liczba kolumn** | 6 | 7 | **+1 kolumna** (dodano flagę `orders_invalid`) |
| **Unikalne daty** | 252 (3 powtórzone) | 252 (100% unikalne) | Każda data występuje dokładnie jeden raz |
| **Typ kolumny `promo`** | `object` / `str` (`' yes '`, `'0'`, `'1'`) | `int64` (`0` lub `1`) | Standaryzacja tekstu, brak spacji, typ numeryczny |
| **Wartości ujemne `orders`** | 2 wiersze (`orders = -5.0`) | 0 wierszy | Wartości ujemne zastąpione wartością `NaN` |
| **Liczba braków `orders` (NaN)** | 2 wiersze | 4 wiersze | 2 pierwotne braki + 2 zamienione z wartości ujemnych |
| **Liczba braków `planned_ad_spend_pln`** | 4 wiersze | 4 wiersze | Zachowane bez zmian (imputacja dopiero w pipeline ML) |
| **Kolumna `orders_invalid`** | Brak | Wartości `0` (250 wierszy) i `1` (2 wiersze) | Jawna informacja audytowa o pierwotnie błędnych celach |
| **Braki `visits` i `revenue_pln`** | 0 braków | 0 braków | Kolumny kompletne (wyłączone z cech modelu - leakage) |



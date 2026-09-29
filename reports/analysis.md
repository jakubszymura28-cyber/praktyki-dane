# Notatka analityczna: Pytania biznesowe i odpowiedzi z bazy SQLite

Dokument zawiera zdefiniowane pytania biznesowe, zapytania SQL, uzyskane odpowiedzi z lokalnej bazy SQLite (`data/processed/orders.sqlite`), wyniki walidacji typów danych i wartości `NULL`, ćwiczenie na osobnej tabeli oraz potwierdzenie spójności z raportem jakości danych.

---

### Pytanie 1
**W które dni była promocja?**

- **Oczekiwana odpowiedź:** Lista dat i flaga/wartość `promo` (zestawienie dni, w których obowiązywała aktywna akcja promocyjna, np. `promo = 1`).
- **Zapytanie SQL:**
  ```sql
  SELECT date, promo
  FROM orders_train
  WHERE promo = 1
  ORDER BY date ASC;
  ```
- **Uzyskana odpowiedź:** Promocja obowiązywała w **52 dniach** w badanym okresie (od 2024-01-02 do 2024-09-08):
  - 2024-01-02, 2024-01-07, 2024-01-13, 2024-01-19, 2024-01-24, 2024-02-07, 2024-02-09, 2024-02-10, 2024-02-14, 2024-03-01, 2024-03-04, 2024-03-08, 2024-03-10, 2024-03-11, 2024-03-12, 2024-03-14, 2024-03-15, 2024-03-18, 2024-03-27, 2024-04-01, 2024-04-05, 2024-04-09, 2024-04-12, 2024-04-13, 2024-04-16, 2024-04-29, 2024-05-03, 2024-05-04, 2024-05-07, 2024-05-08, 2024-05-14, 2024-05-17, 2024-05-18, 2024-05-25, 2024-06-21, 2024-06-30, 2024-07-02, 2024-07-12, 2024-07-14, 2024-07-16, 2024-07-17, 2024-07-20, 2024-07-23, 2024-07-25, 2024-07-27, 2024-08-09, 2024-08-12, 2024-08-14, 2024-08-21, 2024-08-25, 2024-08-28, 2024-09-08 (wszystkie z `promo = 1`).

---

### Pytanie 2
**W których pięciu dniach było najwięcej zamówień?**

- **Oczekiwana odpowiedź:** Zestawienie dokładnie pięciu dat wraz z odpowiadającą im liczbą zamówień (`orders`), posortowanych malejąco według liczby zamówień (`orders` oznacza liczbę zamówień).
- **Zapytanie SQL:**
  ```sql
  SELECT date, orders
  FROM orders_train
  WHERE orders IS NOT NULL
  ORDER BY orders DESC
  LIMIT 5;
  ```
- **Uzyskana odpowiedź:**
  | Data (`date`) | Liczba zamówień (`orders`) |
  | :--- | :---: |
  | **2024-05-11** | 138.0 |
  | **2024-07-27** | 137.0 |
  | **2024-06-30** | 132.0 |
  | **2024-05-25** | 131.0 |
  | **2024-09-08** | 130.0 |

---

### Pytanie 3
**Dla ilu dni znamy poprawną liczbę zamówień?**

- **Oczekiwana odpowiedź:** Jedna liczba dni (pojedyncza wartość liczbowa / agregat), określająca liczbę rekordów, w których wartość zamówień jest znana i poprawna.
- **Zapytanie SQL:**
  ```sql
  SELECT 
      COUNT(*) AS total_rows,
      COUNT(orders) AS known_orders_count,
      COUNT(*) - COUNT(orders) AS missing_orders_count
  FROM orders_train;
  ```
- **Uzyskana odpowiedź:** Dokładnie **248 dni**.
  - Łączna liczba dni w zbiorze (`COUNT(*)`): **252**
  - Liczba dni ze znaną, poprawną liczbą zamówień (`COUNT(orders)`): **248**
  - Liczba dni z brakującą/anomalną wartością (`NULL`): **4** (2 pierwotne braki `NaN` + 2 wartości ujemne zamienione na `NaN` z flagą `orders_invalid = 1`).

---

### 🛡️ Weryfikacja typów danych i wartości NULL w SQLite

Zgodnie z wymaganiami przeprowadzono programowe sprawdzenie poprawności typów w tabeli `orders_train`:
- **Typ kolumny `orders`:** Liczba rzeczywista (`REAL`) — potwierdzone przez `typeof(orders) = 'real'`.
- **Wartości brakujące:** Zapisane jako prawdziwy SQL `NULL` („nie podano”), a **nie** jako tekst `'NULL'`.
  - Liczba rekordów z `orders IS NULL`: **4**
  - Liczba rekordów z `orders = 'NULL'`: **0**

---

### 🧪 Osobna tabela ćwiczeniowa (`orders_practice`): badanie COUNT i AVG na wartościach 8, 10, NULL

W celu zbadania zachowania funkcji agregujących w SQLite utworzono osobną tabelę ćwiczeniową `orders_practice` (bez ingerencji w główną tabelę projektu `orders_train`):

- **Struktura tabeli:** kolumna `orders REAL` z 3 wierszami: `8.0`, `10.0` oraz `NULL`.
- **Zapytanie SQL:**
  ```sql
  SELECT 
      COUNT(*) AS cnt_star,
      COUNT(orders) AS cnt_orders,
      AVG(orders) AS avg_orders
  FROM orders_practice;
  ```

#### Rachunek ręczny:
1. **Liczba wszystkich wierszy:** Mamy 3 wiersze fizyczne $\rightarrow$ `COUNT(*)` = **3**.
2. **Liczba podanych liczb:** Mamy tylko 2 podane liczby (`8` i `10`), ponieważ wartość `NULL` oznacza brak $\rightarrow$ `COUNT(orders)` = **2**.
3. **Średnia arytmetyczna:**
   $$\text{Średnia} = \frac{8 + 10}{2} = \frac{18}{2} = 9.0$$
   *Wartość `NULL` jest całkowicie pomijana przy obliczaniu średniej – nie jest traktowana jako zero (gdyby była zerem, otrzymalibyśmy błędne $18 / 3 = 6.0$).*

#### Porównanie rachunku z wynikiem zapytania SQL:
| Metryka | Rachunek ręczny | Wynik zapytania SQL | Zgodność |
| :--- | :---: | :---: | :---: |
| Liczba wierszy ogółem (`COUNT(*)`) | **3** | **3** | Pełna zgodność |
| Liczba podanych liczb (`COUNT(orders)`) | **2** | **2** | Pełna zgodność |
| Średnia arytmetyczna (`AVG(orders)`) | **9.0** | **9.0** | Pełna zgodność |

---

### 🔍 Porównanie COUNT(orders) z raportem jakości danych (`reports/quality.md`)

Przeprowadzono formalne porównanie liczby poprawnych zamówień uzyskanych z zapytania SQL w bazie oraz odnotowanych w raporcie jakości danych [`reports/quality.md`](file:///c:/Users/Lenovo/Desktop/praktyki%20dane/reports/quality.md):

- **Wynik zapytania SQL dla `orders_train`:**
  `COUNT(orders) = 248` (spośród 252 wierszy po deduplikacji).
- **Wartość w raporcie jakości ([`reports/quality.md`](file:///c:/Users/Lenovo/Desktop/praktyki%20dane/reports/quality.md#L221) - Sekcja 10, Tabela Przed vs Po):**
  *Liczba poprawnych `orders`* po czyszczeniu = **248** (z 251 przed czyszczeniem usunięto 2 wartości ujemne oraz 1 zduplikowany wiersz).
- **Weryfikacja spójności:**
  $$\text{COUNT(orders)}_{\text{SQLite}} = 248 \quad \equiv \quad \text{Poprawne orders}_{\text{quality.md}} = 248$$
  Liczby w obu raportach są **w 100% zgodne**, a mechanizm liczenia w SQLite idealnie odzwierciedla reguły czyszczenia danych.

---

## Pytania do podsumowania

W tej sekcji przedstawiono podsumowania i strukturę tabel agregujących, obliczonych za pomocą SQLite (`src/query_data.py`, `sql/queries.sql`) oraz biblioteki pandas (`notebooks/02_analysis.ipynb`). Wyniki zostały wyeksportowane do plików CSV: [`reports/by_promo.csv`](file:///c:/Users/Lenovo/Desktop/praktyki%20dane/reports/by_promo.csv), [`reports/by_month.csv`](file:///c:/Users/Lenovo/Desktop/praktyki%20dane/reports/by_month.csv) oraz [`reports/by_weekday.csv`](file:///c:/Users/Lenovo/Desktop/praktyki%20dane/reports/by_weekday.csv).

### Pytanie 1
**Jaka jest średnia liczba zamówień w dni z promocją i bez niej?**

- **Opis tabeli:**
  - **Kolumny:** `grupa`, `liczba wszystkich dni`, `liczba dni z poprawnym orders`, `suma zamówień`, `średnia zamówień`
  - **Grupa:** promocja tak/nie (`promo = 1` / `promo = 0`)
- **Zapytanie SQL:**
  ```sql
  SELECT 
      promo AS grupa,
      COUNT(*) AS total_days,
      COUNT(orders) AS valid_orders_days,
      SUM(orders) AS sum_orders,
      ROUND(AVG(orders), 2) AS avg_orders
  FROM orders_train
  GROUP BY promo
  ORDER BY promo ASC;
  ```

| grupa | liczba wszystkich dni | liczba dni z poprawnym orders | suma zamówień | średnia zamówień |
| :--- | :---: | :---: | :---: | :---: |
| **0 (promocja nie)** | 200 | **197** | 15 656.0 | **79.47** |
| **1 (promocja tak)** | 52 | **51** | 5 277.0 | **103.47** |

**Wnioski i opis zaobserwowanej różnicy (na podstawie pliku `reports/by_promo.csv`):**
- **Dni bez promocji (`promo = 0`):** dla **197 poprawnych dni** średnia liczba zamówień wyniosła **79.47 szt./dzień**.
- **Dni z promocją (`promo = 1`):** dla **51 poprawnych dni** średnia liczba zamówień wyniosła **103.47 szt./dzień**.
- **Zaobserwowana różnica:** W dniach z aktywną promocją zaobserwowano średnio o **24.00 zamówienia dziennie więcej** (wzrost średniej o **+30.20%** względem dni bez promocji).

> **⚠️ Zastrzeżenie metodologiczne (korelacja a przyczynowość):**  
> Samo proste porównanie średnich **nie dowodzi bezpośredniego wpływu promocji**.  
> Porównywane grupy mogą różnić się również innymi istotnymi czynnikami zakłócającymi, w szczególności **dniem tygodnia** — jeśli akcje promocyjne były częściej planowane na weekendy (piątek–niedziela), kiedy naturalny popyt konsumentów jest najwyższy, to wyższa średnia może w znacznej mierze wynikać z efektu dnia tygodnia, a nie z samej promocji. Na różnice w sprzedaży mógł wpływać również zaplanowany budżet reklamowy (`planned_ad_spend_pln`) oraz sezonowość w poszczególnych miesiącach.


---

### Pytanie 2
**Jak różni się średnia liczba zamówień między miesiącami?**

- **Opis tabeli:**
  - **Kolumny:** `grupa`, `liczba wszystkich dni`, `liczba dni z poprawnym orders`, `suma zamówień`, `średnia zamówień`
  - **Grupa:** miesiąc (`strftime('%Y-%m', date)`)
- **Zapytanie SQL:**
  ```sql
  SELECT 
      strftime('%Y-%m', date) AS grupa,
      COUNT(*) AS total_days,
      COUNT(orders) AS valid_orders_days,
      SUM(orders) AS sum_orders,
      ROUND(AVG(orders), 2) AS avg_orders
  FROM orders_train
  GROUP BY strftime('%Y-%m', date)
  ORDER BY grupa ASC;
  ```

| grupa | liczba wszystkich dni | liczba dni z poprawnym orders | suma zamówień | średnia zamówień |
| :--- | :---: | :---: | :---: | :---: |
| **2024-01** | 31 | 31 | 2 437.0 | 78.61 |
| **2024-02** | 29 | 29 | 2 352.0 | 81.10 |
| **2024-03** | 31 | 30 | 2 593.0 | 86.43 |
| **2024-04** | 30 | 29 | 2 370.0 | 81.72 |
| **2024-05** | 31 | 31 | 2 621.0 | 84.55 |
| **2024-06** | 30 | 30 | 2 423.0 | 80.77 |
| **2024-07** | 31 | 30 | 2 721.0 | **90.70** |
| **2024-08** | 31 | 30 | 2 699.0 | 89.97 |
| **2024-09** | 8 | 8 | 717.0 | 89.63 |

**Wnioski biznesowe:**  
Najwyższą średnią dzienną liczbę zamówień odnotowano w miesiącach letnich: w **lipcu (90.70)** oraz **sierpniu (89.97)**. Najniższa średnia wystąpiła na początku roku w **styczniu (78.61)**.

---

### Pytanie 3
**W które dni tygodnia średnia liczba zamówień jest najwyższa?**

- **Opis tabeli:**
  - **Kolumny:** `grupa`, `liczba wszystkich dni`, `liczba dni z poprawnym orders`, `suma zamówień`, `średnia zamówień`
  - **Grupa:** dzień tygodnia (`calendar.day_of_week`: 0 = poniedziałek, ..., 6 = niedziela)
- **Zapytanie SQL (złączenie z tabelą `calendar`):**
  ```sql
  SELECT 
      CASE c.day_of_week
          WHEN 0 THEN 'poniedziałek'
          WHEN 1 THEN 'wtorek'
          WHEN 2 THEN 'środa'
          WHEN 3 THEN 'czwartek'
          WHEN 4 THEN 'piątek'
          WHEN 5 THEN 'sobota'
          WHEN 6 THEN 'niedziela'
      END AS grupa,
      COUNT(*) AS total_days,
      COUNT(o.orders) AS valid_orders_days,
      SUM(o.orders) AS sum_orders,
      ROUND(AVG(o.orders), 2) AS avg_orders
  FROM orders_train o
  LEFT JOIN calendar c ON o.date = c.date
  GROUP BY c.day_of_week
  ORDER BY c.day_of_week ASC;
  ```

| grupa (dzień tygodnia) | liczba wszystkich dni | liczba dni z poprawnym orders | suma zamówień | średnia zamówień |
| :--- | :---: | :---: | :---: | :---: |
| **poniedziałek** | 36 | 35 | 2 545.0 | 72.71 |
| **wtorek** | 36 | 34 | 2 629.0 | 77.32 |
| **środa** | 36 | 36 | 2 692.0 | 74.78 |
| **czwartek** | 36 | 35 | 2 553.0 | 72.94 |
| **piątek** | 36 | 36 | 3 340.0 | 92.78 |
| **sobota** | 36 | 36 | 3 787.0 | **105.19** |
| **niedziela** | 36 | 36 | 3 387.0 | 94.08 |


**Wnioski biznesowe:**  
Średnia liczba zamówień jest **najwyższa w sobotę (105.19)**, a w dalszej kolejności w niedzielę (94.08) i piątek (92.78). Dni powszednie (poniedziałek–czwartek) notują znacznie niższy popyt (średnie rzędu 72.71 – 77.32).

---

### 🛡️ Weryfikacja spójności: Porównanie sum SQL vs pandas
Przeprowadzono formalne sprawdzenie sumy kolumny `orders`:
1. **Suma wszystkich dni (SQL `SUM(orders)`):** `20 933.0`
2. **Suma wszystkich dni (pandas `df_cleaned['orders'].sum()`):** `20 933.0`
3. **Suma grup promocji w SQL i pandas:**
   $$\text{Suma}(promo=0) + \text{Suma}(promo=1) = 15\,656.0 + 5\,277.0 = 20\,933.0$$
4. **Suma grup miesięcy:**
   $$\sum \text{Suma}_{\text{miesiące}} = 2437 + 2352 + 2593 + 2370 + 2621 + 2423 + 2721 + 2699 + 717 = 20\,933.0$$
5. **Suma grup dni tygodnia:**
   $$\sum \text{Suma}_{\text{dni tygodnia}} = 2545 + 2629 + 2692 + 2553 + 3340 + 3787 + 3387 = 20\,933.0$$

**Status:** Pełna zgodność w 100% pomiędzy zapytaniami SQL w SQLite a obliczeniami w pandas.

---

### 🔍 Wyjaśnienie różnicy między WHERE a HAVING

| Cecha | `WHERE` | `HAVING` |
| :--- | :--- | :--- |
| **Moment filtrowania** | **Przed** grupowaniem wierszy (`GROUP BY`). | **Po** wykonaniu grupowania i obliczeniu agregatów. |
| **Zakres działania** | Wybiera pojedyncze dni / wiersze tabeli. | Wybiera całe zagregowane grupy na podstawie ich statystyk. |
| **Użycie funkcji agregujących** | Niedozwolone (np. `WHERE SUM(orders) > 100` jest błędem składniowym). | Dozwolone i zalecane (np. `HAVING COUNT(orders) >= 20` lub `HAVING AVG(orders) > 80`). |

#### Przykład w SQLite:
```sql
-- WHERE wybiera tylko dni z promo=1 przed grupowaniem,
-- a HAVING odrzuca miesiace, w ktorych bylo mniej niz 5 dni z promocja:
SELECT 
    strftime('%Y-%m', date) AS month,
    COUNT(orders) AS promo_days_count,
    AVG(orders) AS avg_orders
FROM orders_train
WHERE promo = 1             -- Filtrowanie pojedynczych dni (przed GROUP BY)
GROUP BY strftime('%Y-%m', date)
HAVING COUNT(orders) >= 5;  -- Filtrowanie grup (po GROUP BY)
```

---

### 🔗 Bezpieczeństwo i integralność złączenia (JOIN) z `calendar.csv`

Przed połączeniem tabel sprawdzono klucz złączenia (`date`):
1. **Unikalność klucza:** W tabeli `calendar` znajduje się 420 wierszy i dokładnie 420 unikalnych dat (brak jakichkolwiek duplikatów). W tabeli `orders_train` znajduje się 252 wiersze i 252 unikalne daty.
2. **Tabela kontrolna metryk przed i po połączeniu (kontrola fan-out):**

| Stan / Operacja | Liczba wierszy | Suma orders | Różnica wierszy | Różnica sumy | Status integralności |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Przed połączeniem (`orders_train`)** | **252** | **20 933.0** | — | — | Baza referencyjna |
| **Po połączeniu (`LEFT JOIN calendar`)** | **252** | **20 933.0** | **0** | **0.00** | **Identyczne (Brak fan-out)** |

   *Wniosek:* Obie kluczowe wartości (liczba wierszy i suma zamówień) pozostały dokładnie takie same po złączeniu, co dowodzi stuprocentowej integralności operacji.

3. **Pokrycie dat treningu w kalendarzu:**
   - Wykonano zapytanie weryfikujące obecność dat treningu w kalendarzu (`LEFT JOIN ... WHERE c.date IS NULL`), uzyskując wynik **0**.
   - Oznacza to, że **100% dat ze zbioru treningowego (wszystkie 252 dni z 252)** znajduje się w tabeli `calendar`.

---

### ⚠️ Dlaczego należy poprawić kalendarz lub przerwać obliczenia (zamiast usuwać wiersze z wyniku)?

Pojawienie się powtórzonych dat w tabeli kalendarza (`calendar.csv`) stanowi błąd integralności danych referencyjnych. Praktyka polegająca na „cichym usuwaniu duplikatów z tabeli wynikowej po złączeniu” jest kardynalnym błędem inżynierii danych z następujących powodów:

1. **Agregacje SQL wykonują się przed możliwością usunięcia wierszy:**  
   W zapytaniach analitycznych z klauzulą `GROUP BY` (np. suma sprzedaży według dni tygodnia), silnik SQL łączy wiersze i agreguje je w locie. Gdy data jest powtórzona, suma zamówień natychmiast podwaja się w grupie (np. z 10 do 20 szt.). W wynikowej tabeli otrzymujemy już tylko zagregowaną liczbę – nie ma tam wierszy źródłowych, które można by „odfiltrować”.
2. **Ukrywanie błędu źródłowego (Silent Corruption):**  
   Kalendarz jest tabelą wymiaru wielokrotnego użytku. Zamaskowanie duplikatów w jednym raporcie powoduje, że każdy kolejny analityk lub model ML korzystający z tej samej bazy otrzyma błędne dane w innych analizach.
3. **Losowość i brak determinizmu:**  
   Jeśli zduplikowane wiersze kalendarza różnią się wartościami pobocznymi (np. statusem dnia wolnego czy przypisanym tygodniem roku), usuwanie duplikatów z wyniku (np. `drop_duplicates` lub `DISTINCT`) zachowa losowy wiersz, zafałszowując przypisanie cech do zamówień.
4. **Zasada Fail Fast (natychmiastowe zatrzymanie):**  
   Prawidłowym podejściem jest weryfikacja unikalności klucza **przed złączeniem** i natychmiastowe przerwanie procesu (błąd krytyczny), co zmusza do naprawy pliku źródłowego `calendar.csv` u podstaw.

---

### 🧮 Przykład rachunkowy: Obliczanie łącznej średniej z grup

Poniższy przykład ilustruje zasadę wyliczania średniej ogólnej na podstawie danych zagregowanych w grupach:

- **Pierwsza grupa:** 2 dni po 10 zamówień $\rightarrow \text{Suma}_1 = 2 \times 10 = 20$
- **Druga grupa:** 8 dni po 20 zamówień $\rightarrow \text{Suma}_2 = 8 \times 20 = 160$

#### 1. Prawidłowy rachunek (uwzględniający liczebności):
- **Łączna suma zamówień:** $20 + 160 = \mathbf{180}$
- **Łączna liczba dni:** $2 + 8 = \mathbf{10}$
- **Prawidłowa średnia ogólna:**
  $$\text{Średnia} = \frac{180}{10} = \mathbf{18}$$

#### 2. Porównanie z błędnym rachunkiem: $(10 + 20) / 2 = 15$:
Gdybyśmy policzyli prostą średnią ze średnich obu grup:
$$\frac{10 + 20}{2} = \mathbf{15}$$
otrzymalibyśmy wynik **błędnie zaniżony o 3 zamówienia dziennie**.

Taki rachunek przypisuje obu grupom **dokładnie tę samą wagę (po 50%)**, zupełnie ignorując fakt, że druga grupa ma **cztery razy więcej dni** niż pierwsza (8 dni vs 2 dni).

#### 3. Dlaczego przy liczeniu wspólnej średniej trzeba uwzględnić liczebności?
- W rzeczywistości biznesowej każdy pojedynczy dzień ma równą wagę analityczną.
- Druga grupa obejmuje aż **80% całego badanego okresu** ($\frac{8}{10}$ dni), a pierwsza grupa zaledwie **20%** ($\frac{2}{10}$ dni). Zatem wyższa sprzedaż (20 zamówień/dzień) dominowała przez zdecydowaną większość badanego czasu.
- Matematycznie odpowiada to średniej ważonej liczebnością grup:
  $$\text{Średnia} = 10 \times \frac{2}{10} + 20 \times \frac{8}{10} = 10 \times 0.2 + 20 \times 0.8 = 2 + 16 = \mathbf{18}$$
- **Wniosek dla zapytań SQL:** Nigdy nie wolno liczyć `AVG()` z wcześniej zagregowanych średnich (`AVG(avg_orders)`). Zawsze łączną średnią wyliczamy z sumy wszystkich poprawnych wartości podzielonej przez łączną liczbę wierszy: $\frac{\text{SUM(orders)}}{\text{COUNT(orders)}}$.

---

## Plan wykresów i analiza wyników (Dane treningowe)

Wszystkie poniższe wykresy, tabele i wnioski analityczne zostały opracowane **wyłącznie w oparciu o zbiór treningowy** ([`data/processed/orders_train.csv`](file:///c:/Users/Lenovo/Desktop/praktyki%20dane/data/processed/orders_train.csv) oraz wygenerowany z niego raport [`reports/by_weekday.csv`](file:///c:/Users/Lenovo/Desktop/praktyki%20dane/reports/by_weekday.csv)). W analizie nie wykorzystano danych ze zbioru walidacyjnego ani testowego.

* **Okres analizy:** `2024-01-01 – 2024-09-08` (252 dni kalendarzowe)
* **Liczba ważnych obserwacji:** $N = 248$ dni (4 dni z pustą wartością `NaN` w kolumnie `orders` zostały pominięte w obliczeniach i na wykresach)
* **Jednostka zamówień:** sztuki `[szt.]`
* **Jednostka czasu/częstości:** dni `[dni]`

---

### 1. Pytanie: *„Jak liczba zamówień zmieniała się w czasie?”*
- **Typ wykresu:** **Wykres liniowy**
- **Plik wyjściowy:** [`reports/orders_by_date.png`](file:///c:/Users/Lenovo/Desktop/praktyki%20dane/reports/orders_by_date.png)
- **Tytuł:** *„Zmiana liczby zamówień w czasie (2024-01-01 – 2024-09-08)”*
- **Podtytuł:** *„[Zbiór treningowy: N = 248 ważnych dni | 4 braki NaN pominięte]”*
- **Oś pozioma (X):** **Data [rrrr-mm]** (uporządkowany chronologicznie dzienny szereg czasowy)
- **Oś pionowa (Y):** **Liczba zamówień [szt.]**
- **Źródło danych:** Oczyszczony zbiór treningowy (`df_cleaned['orders']`)

#### Tabela źródłowa – Podsumowanie dynamiki miesięcznej:
| Miesiąc | Dni ogółem | Ważne dni ($N$) | Braki (`NaN`) | Średnia zamówień [szt.] | Min [szt.] | Max [szt.] |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `2024-01` | 31 | 31 | 0 | 83.29 | 38.0 | 126.0 |
| `2024-02` | 29 | 28 | 1 | 82.25 | 49.0 | 123.0 |
| `2024-03` | 31 | 30 | 1 | 81.33 | 44.0 | 126.0 |
| `2024-04` | 30 | 30 | 0 | 84.47 | 43.0 | 123.0 |
| `2024-05` | 31 | 30 | 1 | 85.47 | 52.0 | 138.0 |
| `2024-06` | 30 | 30 | 0 | 82.37 | 42.0 | 131.0 |
| `2024-07` | 31 | 31 | 0 | 88.00 | 62.0 | 132.0 |
| `2024-08` | 31 | 30 | 1 | 87.50 | 55.0 | 137.0 |
| `2024-09` | 8 | 8 | 0 | 87.00 | 57.0 | 130.0 |
| **Razem** | **252** | **248** | **4** | **84.41** | **38.0** | **138.0** |

#### Wnioski analityczne:
- **Podsumowanie (Co można odczytać vs Czego nie można stwierdzić):**
  - *Co można odczytać:* Wykres przedstawia wyraźną, regularną cykliczność tygodniową ze szczytami i dołkami w przedziale od 38 do 138 zamówień, przy zachowaniu stabilnego średniomiesięcznego poziomu popytu (81–88 szt./dzień).
  - *Czego nie można stwierdzić:* Przebieg linii szeregu czasowego nie pozwala jednoznacznie wskazać bezpośrednich przyczyn poszczególnych skoków sprzedaży (np. wpływu pogody czy konkretnych emisji reklam), ani nie dowodzi, że identyczny rytm utrzyma się poza okresem treningowym.
- **Obserwacja (fakty empiryczne):** Dzienna liczba zamówień w całym okresie waha się od 38.0 do 138.0 sztuk. Na wykresie występuje regularna cykliczność tygodniowa w postaci powtarzających się fal. Poziom średniomiesięczny jest stabilny i wynosi od 81.33 do 88.00 szt./dzień. Cztery braki danych są pominięte i nie powodują spadku linii do zera.
- **Interpretacja (wnioski biznesowe):** Wolumen zamówień wykazuje silną regularność tygodniową przy stabilnym popycie bazowym przez cały rok. Działalność operacyjna sklepu charakteryzuje się przewidywalnym rytmem, bez gwałtownego trendu wzrostowego ani zapaści w badanym okresie treningowym.
- **Czego dane NIE dowodzą (granice wnioskowania):** Sam przebieg linii nie dowodzi, czy szczyty wynikają wyłącznie z zachowań konsumenckich w weekendy, czy z nakładania się kampanii promocyjnych. Nie dowodzi również, że poziom zamówień utrzyma się w kolejnych miesiącach poza okresem treningowym (np. w Q4).

---

### 2. Pytanie: *„Który dzień tygodnia miał najwyższą średnią?”*
- **Typ wykresu:** **Wykres słupkowy (bar chart)**
- **Plik wyjściowy:** [`reports/orders_by_weekday.png`](file:///c:/Users/Lenovo/Desktop/praktyki%20dane/reports/orders_by_weekday.png)
- **Tytuł:** *„Średnia liczba zamówień według dnia tygodnia (2024-01-01 – 2024-09-08)”*
- **Podtytuł:** *„[Zbiór treningowy: N = 248 ważnych dni | Średnia z pominięciem NaN | Oś Y od 0]”*
- **Oś pozioma (X):** **Dni od poniedziałku do niedzieli z liczbą ważnych dni ($N$) pod słupkami**
- **Oś pionowa (Y):** **Średnia liczba zamówień [szt.]** (rozpoczynająca się sztywno od zera `0.0`)
- **Źródło danych:** Raport zagregowany [`reports/by_weekday.csv`](file:///c:/Users/Lenovo/Desktop/praktyki%20dane/reports/by_weekday.csv)

#### Tabela źródłowa ([`reports/by_weekday.csv`](file:///c:/Users/Lenovo/Desktop/praktyki%20dane/reports/by_weekday.csv)):
| Grupa | Dni ogółem (`total_days`) | Ważne dni (`valid_orders_days`) | Suma zamówień (`sum_orders`) [szt.] | Średnia (`avg_orders`) [szt.] |
| :---: | :---: | :---: | :---: | :---: |
| **poniedziałek** | 36 | 35 | 2545.0 | 72.71 |
| **wtorek** | 36 | 34 | 2629.0 | 77.32 |
| **środa** | 36 | 36 | 2692.0 | 74.78 |
| **czwartek** | 36 | 35 | 2553.0 | 72.94 |
| **piątek** | 36 | 36 | 3340.0 | 92.78 |
| **sobota** | 36 | 36 | 3787.0 | **105.19** (maksimum) |
| **niedziela** | 36 | 36 | 3387.0 | 94.08 |

#### Weryfikacja spójności słupka poniedziałku z reports/by_weekday.csv:
- **Wartość słupka poniedziałku (średnia):** **72.71 szt.** (odpowiada kolumnie `avg_orders` w pliku [`reports/by_weekday.csv`](file:///c:/Users/Lenovo/Desktop/praktyki%20dane/reports/by_weekday.csv)).
- **Liczba ważnych dni pomiarowych pod słupkiem:** **35 dni** (odpowiada kolumnie `valid_orders_days` w pliku [`reports/by_weekday.csv`](file:///c:/Users/Lenovo/Desktop/praktyki%20dane/reports/by_weekday.csv)).
- *Rachunek kontrolny:* W okresie treningowym występuje łącznie 36 poniedziałków (`total_days = 36`), w tym 1 dzień z brakiem danych (`NaN`). Średnia powstała z podzielenia sumy zamówień przez ważne dni: $\frac{2545.0}{35} = 72.7142857... \approx \mathbf{72.71}$, co potwierdza 100% zgodności wykresu z plikiem raportu.

#### Wnioski analityczne:
- **Podsumowanie (Co można odczytać vs Czego nie można stwierdzić):**
  - *Co można odczytać:* Sobota osiąga najwyższą średnią liczbę zamówień (105.19 szt.), wyraźnie przewyższając dni robocze od poniedziałku do czwartku, które utrzymują stabilny poziom 72–77 zamówień dziennie.
  - *Czego nie można stwierdzić:* Duża średnia w sobotę nie oznacza, że każda sobota ma najwięcej zamówień w danym tygodniu (występuje naturalna zmienność losowa), ani nie dowodzi, że sam dzień tygodnia jest jedyną przyczyną wyższej sprzedaży bez udziału np. kampanii promocyjnych.
- **Obserwacja (fakty empiryczne):** Dniem o najwyższej średniej liczbie zamówień jest **sobota** ze średnią **105.19 szt.** ($N = 36$). Na drugim miejscu plasuje się niedziela (94.08 szt., $N = 36$), a na trzecim piątek (92.78 szt., $N = 36$). Dni robocze od poniedziałku do czwartku notują zbliżone, niższe średnie (72.71–77.32 szt.). Średnie obliczono dzieląc `sum_orders` przez liczbę ważnych dni $N$, z pominięciem braków.
- **Interpretacja (wnioski biznesowe):** Weekend (zwłaszcza sobota) generuje najwyższy popyt. Klienci najchętniej składają zamówienia w dni wolne od pracy oraz w piątkowe popołudnia, co czyni weekend kluczowym okresem dla planowania przepustowości operacyjnej i obsługi wysyłek.
- **Czego dane NIE dowodzą (granice wnioskowania):** Sama wysoka średnia w soboty nie dowodzi, że konsumenci kupują więcej wyłącznie z powodu dnia tygodnia. Dane nie wykluczają, że w soboty częściej kierowano ruch z kampanii promocyjnych (`promo = 1`). Nie ma też dowodu na to, że przeniesienie budżetu reklamowego na poniedziałki podniosłoby poniedziałkową sprzedaż do poziomu sobotniego.

#### Eksperyment metodologiczny: Porównanie wariantu z osią od zera z wariantem uciętym (Dlaczego oś słupków musi zaczynać się od zera?):
W ramach analizy zbadano roboczy wariant wykresu z osią zaczynającą się powyżej zera (od poziomu `65 szt.` – plik demonstracyjny [`reports/orders_by_weekday_truncated_demo.png`](file:///c:/Users/Lenovo/Desktop/praktyki%20dane/reports/orders_by_weekday_truncated_demo.png)):
- **Wariant z osią od zera (właściwy raportowy – [`reports/orders_by_weekday.png`](file:///c:/Users/Lenovo/Desktop/praktyki%20dane/reports/orders_by_weekday.png)):** Wysokość słupka soboty ($105.19$) względem poniedziałku ($72.71$) jest proporcjonalna do rzeczywistego stosunku wartości: $\frac{105.19}{72.71} \approx 1.45$ (sobota jest o ok. $45\%$ wyższa).
- **Wariant roboczy z osią od 65 szt. (ucięty – [`reports/orders_by_weekday_truncated_demo.png`](file:///c:/Users/Lenovo/Desktop/praktyki%20dane/reports/orders_by_weekday_truncated_demo.png)):** Widoczna wysokość słupka poniedziałku nad osią wynosi $72.71 - 65 = 7.71$, a słupka soboty $105.19 - 65 = 40.19$. Stosunek widocznych wysokości wynosi $\frac{40.19}{7.71} \approx \mathbf{5.21}$. Sobota sprawia mylne, zmanipulowane wrażenie ponad **5-krotnie większej sprzedaży** niż poniedziałek!
- **Wniosek i decyzja:** W wykresach słupkowych pole powierzchni i wysokość słupka kodują wielkość bezwzględną. Ucięcie osi zniekształca proporcje i wprowadza odbiorcę w błąd (tzw. efekt lupy / fałszywa skala). **Dlatego do oficjalnego raportu bezwzględnie pozostawiamy wariant z osią rozpoczynającą się od zera ([`reports/orders_by_weekday.png`](file:///c:/Users/Lenovo/Desktop/praktyki%20dane/reports/orders_by_weekday.png)).**

---

### 3. Pytanie: *„Jak często występowały różne liczby zamówień?”*
- **Typ wykresu:** **Histogram**
- **Plik wyjściowy:** [`reports/orders_histogram.png`](file:///c:/Users/Lenovo/Desktop/praktyki%20dane/reports/orders_histogram.png)
- **Tytuł:** *„Rozkład częstości liczby zamówień (2024-01-01 – 2024-09-08)”*
- **Podtytuł:** *„[Zbiór treningowy: N = 248 ważnych dni | Średnia: 84.41 szt., Mediana: 85.00 szt.]”*
- **Oś pozioma (X):** **Przedział liczby zamówień (koszyki co 10 szt.) [szt.]**
- **Oś pionowa (Y):** **Liczba dni [dni]**
- **Źródło danych:** Oczyszczony zbiór treningowy (`df_cleaned['orders'].dropna()`, $N = 248$)

#### Tabela źródłowa – Rozkład koszykowy (częstość występowania):
| Przedział zamówień [szt.] | Od [szt.] | Do [szt.] | Liczba dni [dni] | Udział procentowy |
| :---: | :---: | :---: | :---: | :---: |
| `[30, 40)` | 30 | 40 | 1 | 0.40% |
| `[40, 50)` | 40 | 50 | 9 | 3.63% |
| `[50, 60)` | 50 | 60 | 22 | 8.87% |
| `[60, 70)` | 60 | 70 | 31 | 12.50% |
| `[70, 80)` | 70 | 80 | 42 | 16.94% |
| `[80, 90)` | 80 | 90 | **43** (moda) | **17.34%** |
| `[90, 100)` | 90 | 100 | 41 | 16.53% |
| `[100, 110)` | 100 | 110 | 28 | 11.29% |
| `[110, 120)` | 110 | 120 | 18 | 7.26% |
| `[120, 130)` | 120 | 130 | 8 | 3.23% |
| `[130, 140]` | 130 | 140 | 5 | 2.02% |
| **Razem** | **30** | **140** | **248** | **100.00%** |

#### Wnioski analityczne:
- **Podsumowanie (Co można odczytać vs Czego nie można stwierdzić):**
  - *Co można odczytać:* Rozkład dziennych wolumenów jest symetryczny i jednomodalny wokół średniej 84.41 szt. oraz mediany 85.00 szt., a najczęściej występujący przedział to 80–90 zamówień (43 dni w próbie).
  - *Czego nie można stwierdzić:* Dzwonowy kształt histogramu nie dowodzi, że dzienne zamówienia są generowane przez czysty rozkład normalny o niezależnych próbach (dane cechuje silna zależność czasowa i cykliczna), ani nie wyklucza wystąpienia w przyszłości nietypowych anomalii rynkowych poza zakresem 30–140 zamówień.
- **Obserwacja (fakty empiryczne):** Rozkład ma kształt dzwonowy, jest jednomodalny i symetryczny. Najwięcej dni mieści się w przedziale `[80, 90)` zamówień (43 dni, 17.34%). W centralnym paśmie 70–100 zamówień znajduje się aż 126 dni (ponad 50.8% całej próby). Średnia (84.41 szt.) i mediana (85.00 szt.) są niemal identyczne.
- **Interpretacja (wnioski biznesowe):** Typowy dzień sprzedaży generuje około 85 zamówień. Rozkład o niskiej asymetrii ułatwia planowanie operacyjne – magazyn może przyjąć stałą obsadę dla obsługi 80–90 paczek dziennie, z procedurą elastycznego zwiększania mocy do ok. 140 paczek w dniach o wzmożonym ruchu.
- **Czego dane NIE dowodzą (granice wnioskowania):** Symetria rozkładu empirycznego nie dowodzi, że proces generujący zamówienia jest czystym rozkładem Gaussa (dane są zależne czasowo i podlegają cyklom tygodniowym). Dane nie wykluczają też wystąpienia w przyszłości zdarzeń ekstremalnych (tzw. grubych ogonów rozkładu), np. podczas awarii infrastruktury lub wyprzedaży sezonowych.









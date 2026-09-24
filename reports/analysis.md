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

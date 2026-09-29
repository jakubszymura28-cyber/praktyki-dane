-- =============================================================================
-- Plik: sql/queries.sql
-- Komentarze w SQL (linie zaczynajace sie od --) sa ignorowane przez silnik bazy.
-- =============================================================================

-- Pytanie pomocnicze: Jakie jest pierwsze 10 zarejestrowanych dni w zbiorze?
-- Zapytanie wybiera kolumny date, promo i orders dla 10 najwczesniejszych dni,
-- sortujac je chronologicznie od najstarszego (ORDER BY date ASC LIMIT 10).
SELECT date, promo, orders
FROM orders_train
ORDER BY date ASC
LIMIT 10;

-- Pytanie 1: W ktore dni byla promocja?
-- Zapytanie odpowiada na pytanie o wszystkie dni z aktywna promocja handlowa.
-- Klauzula WHERE promo = 1 odrzuca dni bez promocji (promo = 0) oraz ewentualne braki,
-- gwarantujac, ze na liscie wynikowej znajda sie wylacznie daty z promo = 1.
SELECT date, promo
FROM orders_train
WHERE promo = 1
ORDER BY date ASC;

-- Pytanie 2: W ktorych pieciu dniach bylo najwiecej zamowien?
-- Zapytanie wyszukuje 5 dni o rekordowej liczbie zamowien (orders oznacza liczbe zamowien).
-- Warunek WHERE orders IS NOT NULL zabezpiecza przed uwzglednieniem brakow danych,
-- a ORDER BY orders DESC uklada wyniki od najwyzszej sprzedazy do najnizszej (LIMIT 5).
SELECT date, orders
FROM orders_train
WHERE orders IS NOT NULL
ORDER BY orders DESC
LIMIT 5;

-- Pytanie 3: Dla ilu dni znamy poprawna liczbe zamowien i ile jest brakow danych?
-- Zapytanie porownuje COUNT(*) (laczna liczba wszystkich wierszy) z COUNT(orders)
-- (liczba wierszy, w ktorych orders nie jest puste/NULL). Roznica wskazuje liczbe brakow.
SELECT 
    COUNT(*) AS total_rows,
    COUNT(orders) AS known_orders_count,
    COUNT(*) - COUNT(orders) AS missing_orders_count
FROM orders_train;

-- =============================================================================
-- ZAPYTANIA DO PODSUMOWANIA (GROUP BY)
-- =============================================================================

-- Zapytanie 4: Srednia i suma zamowien w dni z promocja i bez niej (Pytanie 1)
-- Grupowanie po promo (0 = brak promocji, 1 = promocja aktywna).
-- Zwraca liczbe wszystkich dni COUNT(*), liczbe dni ze znanym orders COUNT(orders),
-- sume zamowien SUM(orders) oraz srednia arytmetyczna AVG(orders).
SELECT 
    promo,
    COUNT(*) AS total_days,
    COUNT(orders) AS valid_orders_days,
    SUM(orders) AS sum_orders,
    AVG(orders) AS avg_orders
FROM orders_train
GROUP BY promo
ORDER BY promo ASC;

-- Zapytanie 5: Srednia i suma zamowien miedzy miesiacami (Pytanie 2)
-- Wyodrebnienie miesiaca w formacie YYYY-MM za pomoca funkcji strftime('%Y-%m', date).
-- Pokazuje dynamike sprzedazy w kolejnych miesiacach badanego okresu.
SELECT 
    strftime('%Y-%m', date) AS month,
    COUNT(*) AS total_days,
    COUNT(orders) AS valid_orders_days,
    SUM(orders) AS sum_orders,
    AVG(orders) AS avg_orders
FROM orders_train
GROUP BY strftime('%Y-%m', date)
ORDER BY month ASC;

-- Zapytanie 6: Srednia i suma zamowien wedlug dnia tygodnia (Pytanie 3)
-- Polaczenie z tabela calendar po kolumnie date (LEFT JOIN calendar ON orders_train.date = calendar.date).
-- Grupowanie wedlug day_of_week z podpisaniem dni od poniedzialku do niedzieli.
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


-- Zapytanie 7: Walidacja integralnosci klucza - czy kazda data treningu jest w kalendarzu?
-- Wyszukuje rekordy z orders_train, dla ktorych nie ma odpowiednika w calendar (LEFT JOIN WHERE c.date IS NULL).
-- Oczekiwany wynik: 0 brakujacych dat (pelne 100% pokrycia).
SELECT 
    COUNT(*) AS missing_dates_in_calendar
FROM orders_train o
LEFT JOIN calendar c ON o.date = c.date
WHERE c.date IS NULL;

-- =============================================================================
-- POLACZENIE LEFT JOIN: DOBRANIE DNIA TYGODNIA I DETEKCJA BRAKOW KALENDARZA
-- =============================================================================

-- Zapytanie 8: Dobranie dnia tygodnia do kazdego dnia orders_train za pomoca LEFT JOIN
-- LEFT JOIN gwarantuje zachowanie 100% wierszy tabeli lewej (orders_train), nawet
-- gdyby w tabeli prawej (calendar) brakowalo rekordu dla danej daty.
-- W przypadku braku dopasowania, kolumny z tabeli calendar (day_of_week) przyjma wartosc NULL.
SELECT 
    o.date,
    o.promo,
    o.orders,
    c.day_of_week,
    c.is_weekend
FROM orders_train o
LEFT JOIN calendar c ON o.date = c.date
ORDER BY o.date ASC
LIMIT 10;

-- Zapytanie 9: Wykrycie ewentualnych bledow braku pasujacego kalendarza (LEFT JOIN z filtrem NULL)
-- Poniewaz LEFT JOIN zachowuje wiersze treningu, brak pasujacej daty w kalendarzu
-- objawia sie wartoscia NULL w kolumnie c.day_of_week. To zapytanie wylapuje takie przypadki jako blad.
-- Oczekiwany wynik: 0 wierszy (brak bledow, kazdy dzien ma przypisany dzien tygodnia).
SELECT 
    o.date,
    o.orders,
    c.day_of_week
FROM orders_train o
LEFT JOIN calendar c ON o.date = c.date
WHERE c.day_of_week IS NULL;




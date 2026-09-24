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

"""Moduł do ładowania danych orders_train.csv do bazy SQLite oraz wykonywania zapytań analitycznych.

Skrypt wczytuje oczyszczony zbiór danych do lokalnej bazy SQLite (data/processed/orders.sqlite),
dba o poprawne typy kolumn (liczby jako REAL/INTEGER, braki danych jako natywny SQL NULL),
weryfikuje poprawność typów oraz wykonuje zapytania analityczne z pliku sql/queries.sql.
"""

from pathlib import Path
import re
import sqlite3
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
CSV_PATH = BASE_DIR / "data" / "processed" / "orders_train.csv"
CALENDAR_CSV_PATH = BASE_DIR / "data" / "raw" / "calendar.csv"
DB_PATH = BASE_DIR / "data" / "processed" / "orders.sqlite"
SQL_QUERIES_PATH = BASE_DIR / "sql" / "queries.sql"
REPORTS_DIR = BASE_DIR / "reports"


def load_csv_to_sqlite(csv_path: Path, db_path: Path) -> None:
    """Wczytuje plik CSV do tabeli orders_train w lokalnej bazie SQLite z zachowaniem typów i NULL."""
    if not csv_path.exists():
        raise FileNotFoundError(f"Nie znaleziono pliku CSV: {csv_path}")

    df = pd.read_csv(csv_path)

    # Upewniamy się, że katalog docelowy istnieje
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        # Tworzymy tabelę z jawną definicją typów danych
        cursor.execute("DROP TABLE IF EXISTS orders_train;")
        cursor.execute(
            """
            CREATE TABLE orders_train (
                date TEXT PRIMARY KEY,
                promo INTEGER NOT NULL,
                planned_ad_spend_pln REAL,
                orders REAL,
                visits INTEGER NOT NULL,
                revenue_pln REAL NOT NULL,
                orders_invalid INTEGER NOT NULL
            );
            """
        )

        # Przygotowanie wierszy z zamianą NaN na None (czyli natywny SQL NULL)
        records = df.where(pd.notnull(df), None).to_dict(orient="records")

        insert_sql = """
            INSERT INTO orders_train (
                date, promo, planned_ad_spend_pln, orders, visits, revenue_pln, orders_invalid
            ) VALUES (
                :date, :promo, :planned_ad_spend_pln, :orders, :visits, :revenue_pln, :orders_invalid
            );
        """
        cursor.executemany(insert_sql, records)
        conn.commit()

    print(f"[Sukces] Załadowano {len(df)} wierszy z '{csv_path.name}' do tabeli 'orders_train' w '{db_path.name}'.")


def verify_schema_and_nulls(db_path: Path) -> None:
    """Weryfikuje, czy kolumna orders jest liczbą, a braki danych są natywnym NULL, a nie tekstem 'NULL'."""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        # Typ kolumny dla wierszy z wartościami
        cursor.execute("SELECT typeof(orders) FROM orders_train WHERE orders IS NOT NULL LIMIT 1;")
        res_type = cursor.fetchone()
        col_type = res_type[0] if res_type else "unknown"

        # Liczba wartości NULL
        cursor.execute("SELECT COUNT(*) FROM orders_train WHERE orders IS NULL;")
        null_count = cursor.fetchone()[0]

        # Liczba tekstów 'NULL'
        cursor.execute("SELECT COUNT(*) FROM orders_train WHERE orders = 'NULL';")
        text_null_count = cursor.fetchone()[0]

        print("\n--- Weryfikacja typów danych i braków (NULL) ---")
        print(f"Typ danych kolumny orders w SQLite (dla wartości niepustych): {col_type}")
        print(f"Liczba wierszy z wartością natywną NULL: {null_count}")
        print(f"Liczba wierszy z niepożądanym tekstem 'NULL': {text_null_count}")

        if col_type in ("real", "integer") and null_count > 0 and text_null_count == 0:
            print("[Walidacja OK] Kolumna orders jest numeryczna, a braki to czysty SQL NULL (brak tekstu 'NULL').")
        else:
            raise ValueError("[Błąd Walidacji] Niepoprawne typy lub sposób zapisu braków w bazie!")


def run_practice_table_and_compare(db_path: Path) -> None:
    """Tworzy osobną tabelę ćwiczeniową orders_practice z wartościami (8, 10, NULL),

    oblicza COUNT(*), COUNT(orders), AVG(orders) bez modyfikacji tabeli projektu orders_train
    oraz porównuje COUNT(orders) dla orders_train z liczbą poprawnych orders z reports/quality.md.
    """
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        # 1. Tworzymy osobną tabelę ćwiczeniową bez zmieniania tabeli projektu orders_train
        cursor.execute("DROP TABLE IF EXISTS orders_practice;")
        cursor.execute("CREATE TABLE orders_practice (orders REAL);")
        cursor.executemany("INSERT INTO orders_practice (orders) VALUES (?);", [(8.0,), (10.0,), (None,)])
        conn.commit()

        # Zapytanie ćwiczeniowe
        query = "SELECT COUNT(*) AS cnt_star, COUNT(orders) AS cnt_orders, AVG(orders) AS avg_orders FROM orders_practice;"
        cursor.execute(query)
        cnt_star, cnt_orders, avg_orders = cursor.fetchone()

        print("\n--- Osobna tabela ćwiczeniowa: orders_practice (wartości: 8, 10, NULL) ---")
        print(f"Liczba wszystkich wierszy COUNT(*):      {cnt_star}")
        print(f"Liczba podanych liczb COUNT(orders):    {cnt_orders}")
        print(f"Średnia arytmetyczna AVG(orders):       {avg_orders:.1f}")
        print(f"Rachunek ręczny: (8 + 10) / 2 = 18 / 2 = 9.0 -> Zgodność z SQL: {avg_orders == 9.0}")

        # 2. Porównanie COUNT(orders) dla tabeli projektu orders_train z reports/quality.md
        cursor.execute("SELECT COUNT(orders) FROM orders_train;")
        train_valid_orders = cursor.fetchone()[0]

        quality_report_valid_orders = 248  # Wartość z tabeli sekcji 10 w reports/quality.md

        print("\n--- Porównanie z raportem jakości (reports/quality.md) ---")
        print(f"COUNT(orders) w tabeli orders_train (SQLite):       {train_valid_orders}")
        print(f"Liczba poprawnych orders w reports/quality.md:     {quality_report_valid_orders}")
        if train_valid_orders == quality_report_valid_orders:
            print("[SPÓJNOŚĆ POTWIERDZONA] Liczby są w 100% zgodne (248 == 248).")
        else:
            raise ValueError(
                f"[ROZBIEŻNOŚĆ] SQLite ma {train_valid_orders}, a reports/quality.md ma {quality_report_valid_orders}!"
            )


def load_calendar_to_sqlite(calendar_path: Path, db_path: Path) -> None:
    """Wczytuje plik calendar.csv do tabeli calendar w lokalnej bazie SQLite."""
    if not calendar_path.exists():
        raise FileNotFoundError(f"Nie znaleziono pliku kalendarza: {calendar_path}")

    df_cal = pd.read_csv(calendar_path)
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS calendar;")
        cursor.execute(
            """
            CREATE TABLE calendar (
                date TEXT PRIMARY KEY,
                day_of_week INTEGER NOT NULL,
                is_weekend INTEGER NOT NULL
            );
            """
        )
        records = df_cal.to_dict(orient="records")
        cursor.executemany(
            "INSERT INTO calendar (date, day_of_week, is_weekend) VALUES (:date, :day_of_week, :is_weekend);",
            records,
        )
        conn.commit()

    print(f"[Sukces] Załadowano {len(df_cal)} wierszy z '{calendar_path.name}' do tabeli 'calendar' w '{db_path.name}'.")


def verify_join_integrity(db_path: Path) -> None:
    """Sprawdza unikalność dat w tabelach calendar i orders_train oraz porównuje liczbę wierszy i sumę zamówień przed i po JOIN."""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        # 1. Sprawdzenie unikalności dat w calendar
        cursor.execute("SELECT COUNT(date), COUNT(DISTINCT date) FROM calendar;")
        cal_total, cal_distinct = cursor.fetchone()
        print("\n--- Walidacja unikalności klucza w tabeli calendar ---")
        print(f"Liczba wierszy w calendar: {cal_total}, liczba unikalnych dat: {cal_distinct}")
        if cal_total != cal_distinct:
            raise ValueError(f"[Błąd] Daty w calendar nie są unikalne! Duplikatów: {cal_total - cal_distinct}")
        print("[Walidacja OK] Daty w tabeli calendar są w 100% unikalne.")

        # 2. Sprawdzenie unikalności dat w orders_train
        cursor.execute("SELECT COUNT(date), COUNT(DISTINCT date) FROM orders_train;")
        train_total, train_distinct = cursor.fetchone()
        print(f"Liczba wierszy w orders_train: {train_total}, liczba unikalnych dat: {train_distinct}")
        if train_total != train_distinct:
            raise ValueError(f"[Błąd] Daty w orders_train nie są unikalne! Duplikatów: {train_total - train_distinct}")
        print("[Walidacja OK] Daty w tabeli orders_train są w 100% unikalne.")

        # 3. Sprawdzenie, czy każda data treningu jest w kalendarzu
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM orders_train o
            LEFT JOIN calendar c ON o.date = c.date
            WHERE c.date IS NULL;
            """
        )
        missing_in_cal = cursor.fetchone()[0]
        print(f"Liczba dat ze zbioru treningowego nieobecnych w kalendarzu: {missing_in_cal}")
        if missing_in_cal != 0:
            raise ValueError(f"[Błąd] {missing_in_cal} dat z orders_train nie istnieje w tabeli calendar!")
        print("[Walidacja OK] 100% dat ze zbioru treningowego (252 z 252) znajduje się w kalendarzu.")

        # 4. Tabela kontrolna: liczba wierszy i suma orders przed połączeniem oraz po nim
        cursor.execute("SELECT COUNT(*), SUM(orders) FROM orders_train;")
        rows_before, sum_before = cursor.fetchone()

        cursor.execute(
            """
            SELECT COUNT(*), SUM(o.orders)
            FROM orders_train o
            LEFT JOIN calendar c ON o.date = c.date;
            """
        )
        rows_after, sum_after = cursor.fetchone()

        df_control = pd.DataFrame([
            {
                "Stan": "Przed połączeniem (orders_train)",
                "Liczba wierszy": rows_before,
                "Suma orders": round(sum_before, 2),
                "Różnica wierszy": "-",
                "Różnica sumy": "-",
                "Status": "Baza",
            },
            {
                "Stan": "Po połączeniu (LEFT JOIN calendar)",
                "Liczba wierszy": rows_after,
                "Suma orders": round(sum_after, 2),
                "Różnica wierszy": str(rows_after - rows_before),
                "Różnica sumy": f"{sum_after - sum_before:.2f}",
                "Status": "Identyczne (Brak fan-out)",
            },
        ])

        print("\n--- TABELA KONTROLNA INTEGRALNOŚCI ZŁĄCZENIA (JOIN) ---")
        print(df_control.to_string(index=False))

        if rows_before == rows_after and abs(sum_before - sum_after) < 1e-5:
            print("[Walidacja OK] Liczba wierszy i suma orders przed i po połączeniu pozostały dokładnie takie same!")
        else:
            raise ValueError(
                f"[Błąd spójności JOIN] Przed JOIN: wiersze={rows_before}, suma={sum_before}; "
                f"Po JOIN: wiersze={rows_after}, suma={sum_after}"
            )




def export_summary_reports(db_path: Path, reports_dir: Path) -> None:
    """Wykonuje zapytania agregujące i zapisuje wyniki do plików CSV w katalogu reports/."""
    reports_dir.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as conn:
        # 1. Raport według promocji
        promo_sql = """
            SELECT 
                promo AS grupa,
                COUNT(*) AS total_days,
                COUNT(orders) AS valid_orders_days,
                SUM(orders) AS sum_orders,
                ROUND(AVG(orders), 2) AS avg_orders
            FROM orders_train
            GROUP BY promo
            ORDER BY promo ASC;
        """
        df_promo = pd.read_sql_query(promo_sql, conn)
        promo_path = reports_dir / "by_promo.csv"
        df_promo.to_csv(promo_path, index=False)
        print(f"\n[Zapisano] Raport promocji: '{promo_path.name}'")
        print(df_promo.to_string(index=False))

        # Weryfikacja: osobne wiersze dla promo = 0 i promo = 1
        promo_values = set(df_promo["grupa"].tolist())
        if promo_values == {0, 1}:
            print("[Walidacja OK] Tabela by_promo.csv zawiera osobne wiersze dla obu grup: promo=0 i promo=1.")
        else:
            raise ValueError(f"[Błąd] Oczekiwano grup {{0, 1}}, otrzymano: {promo_values}")

        # 2. Raport według miesiąca
        month_sql = """
            SELECT 
                strftime('%Y-%m', date) AS grupa,
                COUNT(*) AS total_days,
                COUNT(orders) AS valid_orders_days,
                SUM(orders) AS sum_orders,
                ROUND(AVG(orders), 2) AS avg_orders
            FROM orders_train
            GROUP BY strftime('%Y-%m', date)
            ORDER BY grupa ASC;
        """
        df_month = pd.read_sql_query(month_sql, conn)
        month_path = reports_dir / "by_month.csv"
        df_month.to_csv(month_path, index=False)
        print(f"\n[Zapisano] Raport miesięczny: '{month_path.name}'")
        print(df_month.to_string(index=False))

        # 3. Raport według dnia tygodnia
        weekday_sql = """
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
        """
        df_weekday = pd.read_sql_query(weekday_sql, conn)
        weekday_path = reports_dir / "by_weekday.csv"
        df_weekday.to_csv(weekday_path, index=False)
        print(f"\n[Zapisano] Raport dni tygodnia: '{weekday_path.name}'")
        print(df_weekday.to_string(index=False))



def run_queries(db_path: Path, sql_path: Path) -> None:
    """Wczytuje i wykonuje zapytania z pliku sql/queries.sql."""
    if not sql_path.exists():
        raise FileNotFoundError(f"Nie znaleziono pliku SQL: {sql_path}")

    with open(sql_path, "r", encoding="utf-8") as f:
        sql_content = f.read()

    # Podział na poszczególne zapytania oddzielone średnikami
    statements = [stmt.strip() for stmt in sql_content.split(";") if stmt.strip()]

    descriptions = [
        "1. 10 pierwszych dat w kolejności chronologicznej",
        "2. Dni z aktywną promocją (promo = 1)",
        "3. 5 dni z największą liczbą zamówień (orders)",
        "4. Porównanie COUNT(*) i COUNT(orders) - badanie braków",
        "5. Średnia i suma zamówień w dni z promocją i bez niej (GROUP BY promo)",
        "6. Średnia i suma zamówień między miesiącami (GROUP BY month)",
        "7. Średnia i suma zamówień według dnia tygodnia (JOIN calendar GROUP BY day_of_week)",
        "8. Walidacja pokrycia dat treningu w kalendarzu (LEFT JOIN WHERE c.date IS NULL)",
        "9. LEFT JOIN: Dobranie dnia tygodnia do wierszy orders_train (pierwsze 10)",
        "10. Detekcja błędów: wiersze orders_train bez pasującego kalendarza (WHERE c.day_of_week IS NULL)",
    ]


    print("\n================ WYNIKI ZAPYTAŃ Z PLIKU SQL ================")

    with sqlite3.connect(db_path) as conn:
        for idx, stmt in enumerate(statements):
            title = descriptions[idx] if idx < len(descriptions) else f"Zapytanie {idx + 1}"
            print(f"\n>>> {title} <<<")
            df_result = pd.read_sql_query(stmt, conn)
            print(df_result.to_string(index=False))


def main() -> None:
    print("Rozpoczynanie procesu ładowania i analizy danych SQLite...")
    load_csv_to_sqlite(CSV_PATH, DB_PATH)
    load_calendar_to_sqlite(CALENDAR_CSV_PATH, DB_PATH)
    verify_schema_and_nulls(DB_PATH)
    run_practice_table_and_compare(DB_PATH)
    verify_join_integrity(DB_PATH)
    export_summary_reports(DB_PATH, REPORTS_DIR)
    run_queries(DB_PATH, SQL_QUERIES_PATH)
    print("\nProces zakończony pomyślnie.")


if __name__ == "__main__":
    main()


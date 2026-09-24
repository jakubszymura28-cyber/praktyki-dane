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
DB_PATH = BASE_DIR / "data" / "processed" / "orders.sqlite"
SQL_QUERIES_PATH = BASE_DIR / "sql" / "queries.sql"


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
    verify_schema_and_nulls(DB_PATH)
    run_practice_table_and_compare(DB_PATH)
    run_queries(DB_PATH, SQL_QUERIES_PATH)
    print("\nProces zakończony pomyślnie.")


if __name__ == "__main__":
    main()

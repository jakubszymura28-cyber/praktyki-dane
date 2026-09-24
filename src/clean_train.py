"""Moduł do powtarzalnego czyszczenia zbioru treningowego orders_train_raw.csv.

Zgodnie z wytycznymi projektu:
1. Dane surowe w data/raw/ pozostają nienaruszone (read-only).
2. Wyczyszczone dane zapisywane są w data/processed/orders_train_cleaned.csv.
3. Każda reguła precyzyjnie raportuje liczbę zmodyfikowanych wierszy.
4. Braków w planned_ad_spend_pln oraz orders nie imputujemy na tym etapie.
5. Ujemne orders zamieniane są na NaN, a flaga orders_invalid oznacza błąd.
"""

from pathlib import Path
from typing import Tuple
import numpy as np
import pandas as pd


def clean_orders_train(
    input_path: Path = Path("data/raw/orders_train_raw.csv"),
    output_path: Path = Path("data/processed/orders_train_cleaned.csv")
) -> Tuple[pd.DataFrame, dict]:
    """Wczytuje surowy zbiór treningowy, wykonuje deterministyczne czyszczenie

    i zapisuje wynik do katalogu data/processed/.

    Args:
        input_path: Ścieżka do surowego pliku CSV.
        output_path: Ścieżka do docelowego pliku CSV.

    Returns:
        Tuple zawierający oczyszczony DataFrame oraz słownik z metrykami zmian.
    """
    # 0. Weryfikacja ścieżki i wczytanie danych surowych
    if not input_path.exists():
        # Obsługa uruchomienia z poziomu podkatalogu (np. notebooks/)
        alt_path = Path("..") / input_path
        if alt_path.exists():
            input_path = alt_path
        else:
            raise FileNotFoundError(f"Nie znaleziono pliku wejściowego: {input_path}")

    df_raw = pd.read_csv(input_path, encoding="utf-8")
    raw_rows_count = len(df_raw)
    print(f"[Krok 0] Wczytano dane surowe: {raw_rows_count} wierszy, {df_raw.shape[1]} kolumn.")

    # Kopia robocza danych
    df = df_raw.copy()

    # 1. Usunięcie identycznych powtórzonych wierszy (Deduplikacja)
    rows_before_dedup = len(df)
    df = df.drop_duplicates()
    duplicates_removed = rows_before_dedup - len(df)
    print(f"[Reguła 1] Usunięto identyczne duplikaty: {duplicates_removed} wiersze (pozostało: {len(df)}).")

    # 2. Standaryzacja kolumny promo
    # Wykrywamy wiersze z wartością tekstową 'yes' (z uwzględnieniem spacji)
    promo_str_clean = df["promo"].astype(str).str.strip().str.lower()
    text_promo_mask = promo_str_clean == "yes"
    text_promo_count = int(text_promo_mask.sum())
    
    # Zamiana 'yes' na '1', a pozostałych na ich postać numeryczną
    df["promo"] = promo_str_clean.replace({"yes": "1"}).astype(int)
    print(f"[Reguła 2] Zestandaryzowano kolumnę promo: zmieniono {text_promo_count} wiersze z wartością 'yes' na 1 (typ int64).")

    # 3. Walidacja formatu daty i unikalności
    df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d").dt.strftime("%Y-%m-%d")
    duplicate_dates = df["date"].duplicated().sum()
    if duplicate_dates > 0:
        raise ValueError(f"Wykryto {duplicate_dates} powtórzonych dat po deduplikacji!")
    
    # Sortowanie chronologiczne i reset indeksu
    df = df.sort_values("date").reset_index(drop=True)
    print(f"[Reguła 3] Zweryfikowano daty: {df['date'].nunique()} unikalnych dni w zakresie od {df['date'].min()} do {df['date'].max()}.")

    # 4. Obsługa ujemnego celu (orders < 0) i flaga orders_invalid
    numeric_orders = pd.to_numeric(df["orders"], errors="coerce")
    negative_mask = numeric_orders < 0
    negative_orders_count = int(negative_mask.sum())

    # Flaga orders_invalid: 1 dla pierwotnie ujemnych wartości, 0 dla poprawnych
    df["orders_invalid"] = negative_mask.astype(int)

    # Zamiana ujemnych wartości na NaN
    df.loc[negative_mask, "orders"] = np.nan
    print(f"[Reguła 4] Obsłużono ujemne orders: zamieniono {negative_orders_count} wierszy na NaN i oznaczono flagą orders_invalid=1.")

    # 5. Podsumowanie braków bez imputacji
    missing_budget = int(df["planned_ad_spend_pln"].isna().sum())
    missing_orders_total = int(df["orders"].isna().sum())
    print(f"[Krok 5] Stan braków danych (bez imputacji):")
    print(f"         - planned_ad_spend_pln: {missing_budget} braków (oczekuje na SimpleImputer w potoku ML)")
    print(f"         - orders: {missing_orders_total} braków (2 pierwotne + {negative_orders_count} zamienione z ujemnych)")

    # 6. Uruchomienie asercji dla trzech prób testowych
    run_quality_checks(df)
    print("[Testy] Wszystkie 3 próby weryfikacyjne zakończone sukcesem!")

    # 7. Zapis pliku wynikowego
    output_dir = output_path.parent
    if not output_dir.exists():
        # Obsługa uruchomienia z podkatalogu
        alt_output_dir = Path("..") / output_dir
        if alt_output_dir.exists():
            output_path = Path("..") / output_path
        else:
            output_dir.mkdir(parents=True, exist_ok=True)

    df.to_csv(output_path, index=False, encoding="utf-8")
    print(f"[Krok 7] Pomyślnie zapisano wyczyszczony zbiór: {output_path} ({len(df)} wierszy, {df.shape[1]} kolumn).")

    metrics = {
        "raw_rows": raw_rows_count,
        "cleaned_rows": len(df),
        "duplicates_removed": duplicates_removed,
        "promo_text_modified": text_promo_count,
        "negative_orders_modified": negative_orders_count,
        "missing_budget": missing_budget,
        "missing_orders_total": missing_orders_total,
        "orders_invalid_flags": int(df["orders_invalid"].sum()),
    }

    return df, metrics


def run_quality_checks(df: pd.DataFrame) -> None:
    """Sprawdza trzy zdefiniowane próby testowe na oczyszczonym zbiorze."""
    # Próba 1: Dokładnie jedno wystąpienie daty 2024-01-31
    rows_2024_01_31 = df[df["date"] == "2024-01-31"]
    assert len(rows_2024_01_31) == 1, (
        f"Próba 1 nie powiodła się: oczekiwano 1 wiersza dla 2024-01-31, otrzymano {len(rows_2024_01_31)}"
    )

    # Próba 2: promo w dniu 2024-02-10 równe 1 typu int
    row_2024_02_10 = df[df["date"] == "2024-02-10"].iloc[0]
    assert row_2024_02_10["promo"] == 1, (
        f"Próba 2 nie powiodła się: oczekiwano promo=1 dla 2024-02-10, otrzymano {row_2024_02_10['promo']}"
    )

    # Próba 3: orders w dniu 2024-04-30 to NaN, a orders_invalid to 1
    row_2024_04_30 = df[df["date"] == "2024-04-30"].iloc[0]
    assert pd.isna(row_2024_04_30["orders"]), (
        f"Próba 3 nie powiodła się: oczekiwano NaN w orders dla 2024-04-30, otrzymano {row_2024_04_30['orders']}"
    )
    assert row_2024_04_30["orders_invalid"] == 1, (
        f"Próba 3 nie powiodła się: oczekiwano orders_invalid=1 dla 2024-04-30, otrzymano {row_2024_04_30['orders_invalid']}"
    )


if __name__ == "__main__":
    clean_orders_train()

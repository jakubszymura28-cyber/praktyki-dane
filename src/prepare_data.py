"""Moduł do powtarzalnego przygotowania i czyszczenia danych treningowych.

Plik czyta data/raw/orders_train_raw.csv i zapisuje oczyszczony zbiór
do data/processed/orders_train.csv bez nadpisywania oryginału.
"""

import sys
from pathlib import Path
from typing import Tuple
import numpy as np
import pandas as pd


EXPECTED_COLUMNS = [
    "date",
    "promo",
    "planned_ad_spend_pln",
    "orders",
    "visits",
    "revenue_pln"
]


def prepare_orders_train(
    input_path: Path = Path("data/raw/orders_train_raw.csv"),
    output_path: Path = Path("data/processed/orders_train.csv")
) -> Tuple[pd.DataFrame, dict]:
    """Wykonuje deterministyczne czyszczenie zbioru orders_train_raw.csv

    i zapisuje wynik do data/processed/orders_train.csv.

    Zgłasza błąd ValueError w przypadku nieoczekiwanego formatu danych
    lub brakujących kolumn zamiast zwracać pusty wynik.

    Args:
        input_path: Ścieżka do surowego pliku CSV.
        output_path: Ścieżka do docelowego pliku CSV.

    Returns:
        Tuple z oczyszczonym DataFrame oraz słownikiem ze statystykami zmian.
    """
    # 0. Weryfikacja ścieżki i obecności pliku wejściowego
    if not input_path.exists():
        alt_path = Path("..") / input_path
        if alt_path.exists():
            input_path = alt_path
        else:
            raise FileNotFoundError(f"Nie znaleziono pliku źródłowego: {input_path}")

    # Wczytanie danych
    try:
        df_raw = pd.read_csv(input_path, encoding="utf-8")
    except Exception as e:
        raise ValueError(f"Błąd odczytu pliku CSV '{input_path}': {e}") from e

    # Walidacja poprawności formatu danych (ochrona przed pustym zbiorem lub złym formatem)
    if df_raw.empty:
        raise ValueError(f"Nieoczekiwany format danych: plik '{input_path}' jest pusty!")

    missing_cols = [col for col in EXPECTED_COLUMNS if col not in df_raw.columns]
    if missing_cols:
        raise ValueError(
            f"Nieoczekiwany format danych: brak wymaganych kolumn {missing_cols} w pliku '{input_path}'."
        )

    raw_rows_count = len(df_raw)
    print(f"[Krok 0: Wczytanie] Pomyślnie wczytano '{input_path}': {raw_rows_count} wierszy, {df_raw.shape[1]} kolumn.")

    # Kopia robocza (zapewnienie braku modyfikacji obiektu źródłowego)
    df = df_raw.copy()

    # 1. Usunięcie identycznych powtórzonych wierszy (Deduplikacja)
    rows_before_dedup = len(df)
    df = df.drop_duplicates()
    duplicates_removed = rows_before_dedup - len(df)
    print(f"[Reguła 1: Deduplikacja] Usunięto identyczne duplikaty: {duplicates_removed} wiersze (pozostało: {len(df)}).")

    # 2. Standaryzacja kolumny promo
    promo_series = df["promo"].astype(str).str.strip().str.lower()
    text_promo_mask = promo_series == "yes"
    text_promo_count = int(text_promo_mask.sum())

    # Weryfikacja czy w promo nie ma innych nieznanych wartości tekstowych
    unexpected_promo = promo_series[~promo_series.isin(["0", "1", "yes"])]
    if not unexpected_promo.empty:
        raise ValueError(f"Nieoczekiwany format danych w kolumnie promo: nieznane wartości {unexpected_promo.unique().tolist()}")

    df["promo"] = promo_series.replace({"yes": "1"}).astype(int)
    print(f"[Reguła 2: Standaryzacja promo] Zmieniono {text_promo_count} wiersze z wartością 'yes' na 1 (kolumna rzutowana na typ int64).")

    # 3. Walidacja formatu daty i unikalności
    try:
        df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d").dt.strftime("%Y-%m-%d")
    except Exception as e:
        raise ValueError(f"Nieoczekiwany format danych: niepoprawny format daty w kolumnie date: {e}") from e

    duplicate_dates = df["date"].duplicated().sum()
    if duplicate_dates > 0:
        duplicated_examples = df.loc[df["date"].duplicated(keep=False), "date"].unique().tolist()
        raise ValueError(f"Nieoczekiwany format danych: wykryto {duplicate_dates} zduplikowanych dat po deduplikacji: {duplicated_examples}")

    df = df.sort_values("date").reset_index(drop=True)
    print(f"[Reguła 3: Walidacja dat] Zweryfikowano {len(df)} unikalnych dat (od {df['date'].min()} do {df['date'].max()}).")

    # 4. Obsługa ujemnego celu (orders < 0) i utworzenie kolumny orders_invalid
    numeric_orders = pd.to_numeric(df["orders"], errors="coerce")
    negative_orders_mask = numeric_orders < 0
    negative_orders_count = int(negative_orders_mask.sum())

    # Flaga orders_invalid: 1 dla pierwotnie ujemnych wartości, 0 dla pozostałych
    df["orders_invalid"] = negative_orders_mask.astype(int)

    # Zamiana wartości ujemnych na brak (NaN)
    df.loc[negative_orders_mask, "orders"] = np.nan
    print(f"[Reguła 4: Ujemne orders] Zamieniono {negative_orders_count} wiersze na NaN oraz dodano kolumnę orders_invalid (wartość 1).")

    # 5. Sprawdzenie braków bez imputacji
    missing_budget = int(df["planned_ad_spend_pln"].isna().sum())
    missing_orders = int(df["orders"].isna().sum())
    print(f"[Krok 5: Weryfikacja braków] Braków nie uzupełniamy:")
    print(f"         - planned_ad_spend_pln: {missing_budget} braków (NaN)")
    print(f"         - orders: {missing_orders} braków (NaN, w tym {negative_orders_count} z wartości ujemnych)")

    # 6. Zapis do pliku wynikowego data/processed/orders_train.csv
    output_dir = output_path.parent
    if not output_dir.exists():
        alt_output_dir = Path("..") / output_dir
        if alt_output_dir.exists():
            output_path = Path("..") / output_path
        else:
            output_dir.mkdir(parents=True, exist_ok=True)

    df.to_csv(output_path, index=False, encoding="utf-8")
    print(f"[Krok 6: Zapis] Pomyślnie zapisano: '{output_path}' ({len(df)} wierszy, {df.shape[1]} kolumn).")

    stats = {
        "raw_rows": raw_rows_count,
        "cleaned_rows": len(df),
        "duplicates_removed": duplicates_removed,
        "promo_modified": text_promo_count,
        "negative_orders_modified": negative_orders_count,
        "missing_budget": missing_budget,
        "missing_orders": missing_orders,
        "orders_invalid_count": int(df["orders_invalid"].sum())
    }

    return df, stats


if __name__ == "__main__":
    try:
        prepare_orders_train()
    except Exception as err:
        print(f"BŁĄD: {err}", file=sys.stderr)
        sys.exit(1)

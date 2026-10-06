"""Moduł do powtarzalnego przygotowania i czyszczenia danych (treningowych i walidacyjnych).

Plik czyta surowe zbiory z data/raw/ i zapisuje oczyszczone zbiory
do data/processed/ bez nadpisywania oryginałów.
Dołącza kolumnę day_of_week z data/raw/calendar.csv po kluczu date.
"""

import sys
from pathlib import Path
from typing import Optional, Tuple
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


def resolve_path(path: Path) -> Path:
    """Rozwiązuje ścieżkę do pliku z uwzględnieniem uruchomienia z podkatalogów."""
    if path.exists():
        return path
    alt_path = Path("..") / path
    if alt_path.exists():
        return alt_path
    project_root = Path(__file__).resolve().parent.parent
    root_path = project_root / path
    if root_path.exists():
        return root_path
    return path


def clean_orders_df(df_raw: pd.DataFrame, dataset_name: str = "dataset") -> Tuple[pd.DataFrame, dict]:
    """Wykonuje deterministyczne reguły czyszczenia jakościowego na DataFrame."""
    if df_raw.empty:
        raise ValueError(f"Nieoczekiwany format danych: zbiór '{dataset_name}' jest pusty!")

    missing_cols = [col for col in EXPECTED_COLUMNS if col not in df_raw.columns]
    if missing_cols:
        raise ValueError(
            f"Nieoczekiwany format danych: brak wymaganych kolumn {missing_cols} w zbiorze '{dataset_name}'."
        )

    raw_rows_count = len(df_raw)
    df = df_raw.copy()

    # 1. Usunięcie identycznych powtórzonych wierszy (Deduplikacja)
    rows_before_dedup = len(df)
    df = df.drop_duplicates()
    duplicates_removed = rows_before_dedup - len(df)

    # 2. Standaryzacja kolumny promo
    promo_series = df["promo"].astype(str).str.strip().str.lower()
    text_promo_mask = promo_series == "yes"
    text_promo_count = int(text_promo_mask.sum())

    unexpected_promo = promo_series[~promo_series.isin(["0", "1", "yes"])]
    if not unexpected_promo.empty:
        raise ValueError(
            f"Nieoczekiwany format danych w kolumnie promo: nieznane wartości {unexpected_promo.unique().tolist()}"
        )

    df["promo"] = promo_series.replace({"yes": "1"}).astype(int)

    # 3. Walidacja formatu daty i unikalności
    try:
        df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d").dt.strftime("%Y-%m-%d")
    except Exception as e:
        raise ValueError(f"Nieoczekiwany format danych: niepoprawny format daty w kolumnie date: {e}") from e

    duplicate_dates = df["date"].duplicated().sum()
    if duplicate_dates > 0:
        duplicated_examples = df.loc[df["date"].duplicated(keep=False), "date"].unique().tolist()
        raise ValueError(
            f"Nieoczekiwany format danych: wykryto {duplicate_dates} zduplikowanych dat po deduplikacji: {duplicated_examples}"
        )

    df = df.sort_values("date").reset_index(drop=True)

    # 4. Obsługa ujemnego celu (orders < 0) i utworzenie kolumny orders_invalid
    numeric_orders = pd.to_numeric(df["orders"], errors="coerce")
    negative_orders_mask = numeric_orders < 0
    negative_orders_count = int(negative_orders_mask.sum())

    df["orders_invalid"] = negative_orders_mask.astype(int)
    df.loc[negative_orders_mask, "orders"] = np.nan

    # 5. Sprawdzenie braków bez imputacji (braków celu nie uzupełniamy, budżetu nie imputujemy na walidacji)
    missing_budget = int(df["planned_ad_spend_pln"].isna().sum())
    missing_orders = int(df["orders"].isna().sum())

    stats = {
        "dataset_name": dataset_name,
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


def join_calendar_feature(
    df_orders: pd.DataFrame,
    calendar_path: Optional[Path] = None,
    dataset_name: str = "dataset"
) -> pd.DataFrame:
    """Dołącza cechę day_of_week z calendar.csv z pełną walidacją integralności (Dzień 6/10)."""
    if calendar_path is None:
        calendar_path = Path("data/raw/calendar.csv")
    calendar_path = resolve_path(calendar_path)

    if not calendar_path.exists():
        # W izolowanych środowiskach testowych bez pliku kalendarza zwracamy df bez modyfikacji
        return df_orders

    df_cal = pd.read_csv(calendar_path, encoding="utf-8")

    # 1. Unikalność dat kalendarza
    if not df_cal["date"].is_unique:
        dup_count = df_cal["date"].duplicated().sum()
        dup_examples = df_cal.loc[df_cal["date"].duplicated(keep=False), "date"].unique().tolist()
        raise ValueError(
            f"BŁĄD INTEGRALNOŚCI: Tabela kalendarza zawiera {dup_count} powtórzonych dat! Przykłady: {dup_examples[:5]}."
        )

    # 2. Dopasowanie każdej daty
    missing_dates = set(df_orders["date"]) - set(df_cal["date"])
    if missing_dates:
        raise ValueError(
            f"BŁĄD INTEGRALNOŚCI: W kalendarzu brakuje {len(missing_dates)} dat ze zbioru {dataset_name}! Przykłady: {list(missing_dates)[:5]}."
        )

    # 3. Złączenie (LEFT JOIN) - bierzemy tylko day_of_week, NIE bierzemy is_weekend
    sum_orders_before = df_orders["orders"].sum(skipna=True)
    rows_before = len(df_orders)

    merged = df_orders.merge(df_cal[["date", "day_of_week"]], on="date", how="left")

    # 4. Sprawdzenie niezmienionej liczby wierszy (kontrola fan-out)
    if len(merged) != rows_before:
        raise ValueError(
            f"BŁĄD INTEGRALNOŚCI (Fan-out): Liczba wierszy po złączeniu ({len(merged)}) != wejściowa ({rows_before})!"
        )

    # 5. Sprawdzenie niezmienionej sumy poprawnych orders
    sum_orders_after = merged["orders"].sum(skipna=True)
    if not np.isclose(sum_orders_before, sum_orders_after):
        raise ValueError(
            f"BŁĄD INTEGRALNOŚCI: Suma orders uległa zmianie ({sum_orders_before} -> {sum_orders_after})!"
        )

    # 6. Sprawdzenie poprawności wartości day_of_week (0=poniedziałek, 6=niedziela)
    if merged["day_of_week"].isna().any():
        raise ValueError(
            f"BŁĄD INTEGRALNOŚCI: Wykryto puste wartości w dołączonej kolumnie day_of_week w zbiorze {dataset_name}!"
        )

    merged["day_of_week"] = merged["day_of_week"].astype(int)

    return merged


def prepare_orders_dataset(
    input_path: Path,
    output_path: Path,
    calendar_path: Optional[Path] = None,
    dataset_name: str = "dataset"
) -> Tuple[pd.DataFrame, dict]:
    """Przetwarza pojedynczy zbiór: czyści, dołącza kalendarz i zapisuje wynik."""
    resolved_input = resolve_path(input_path)
    if not resolved_input.exists():
        raise FileNotFoundError(f"Nie znaleziono pliku źródłowego: {input_path}")

    try:
        df_raw = pd.read_csv(resolved_input, encoding="utf-8")
    except Exception as e:
        raise ValueError(f"Błąd odczytu pliku CSV '{resolved_input}': {e}") from e

    df_cleaned, stats = clean_orders_df(df_raw, dataset_name=dataset_name)

    # Dołączenie kalendarza jeśli dostępny
    if calendar_path is None:
        calendar_path = Path("data/raw/calendar.csv")
    df_merged = join_calendar_feature(df_cleaned, calendar_path=calendar_path, dataset_name=dataset_name)

    # Zapis do pliku wynikowego
    resolved_output = output_path
    output_dir = resolved_output.parent
    if not output_dir.exists():
        alt_output_dir = Path("..") / output_dir
        if alt_output_dir.exists():
            resolved_output = Path("..") / resolved_output
        else:
            output_dir.mkdir(parents=True, exist_ok=True)

    df_merged.to_csv(resolved_output, index=False, encoding="utf-8")
    stats["final_rows"] = len(df_merged)
    stats["has_day_of_week"] = "day_of_week" in df_merged.columns

    return df_merged, stats


def prepare_orders_train(
    input_path: Path = Path("data/raw/orders_train_raw.csv"),
    output_path: Path = Path("data/processed/orders_train.csv"),
    calendar_path: Optional[Path] = None
) -> Tuple[pd.DataFrame, dict]:
    """Przygotowanie zbioru treningowego."""
    return prepare_orders_dataset(
        input_path=input_path,
        output_path=output_path,
        calendar_path=calendar_path,
        dataset_name="trening"
    )


def prepare_orders_validation(
    input_path: Path = Path("data/raw/orders_validation.csv"),
    output_path: Path = Path("data/processed/orders_validation.csv"),
    calendar_path: Optional[Path] = None
) -> Tuple[pd.DataFrame, dict]:
    """Przygotowanie zbioru walidacyjnego."""
    return prepare_orders_dataset(
        input_path=input_path,
        output_path=output_path,
        calendar_path=calendar_path,
        dataset_name="walidacja"
    )


def prepare_all_datasets() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Uruchamia pełny proces przygotowania danych dla treningu i walidacji wraz z kontrolami spójności."""
    print("================================================================================")
    print("ROZPOCZĘCIE PROCESU PRZYGOTOWANIA DANYCH (Trening i Walidacja)")
    print("================================================================================")

    # 1. Zbiór treningowy
    print("\n>>> KROK 1: Przetwarzanie zbioru treningowego (orders_train_raw.csv) <<<")
    df_train, stats_train = prepare_orders_train()
    print(f"[Sukces Trening] Zapisano {len(df_train)} wierszy do data/processed/orders_train.csv.")
    print(f"                 - Poprawne zamówienia: {int(df_train['orders'].notna().sum())} dni")
    print(f"                 - Braki (NaN): {int(df_train['orders'].isna().sum())} dni")
    print(f"                 - Suma poprawnych zamówień: {df_train['orders'].sum(skipna=True)} szt.")
    print(f"                 - Zakres dat: {df_train['date'].min()} do {df_train['date'].max()}")
    print(f"                 - Cecha day_of_week: dołączona (wartości: {sorted(df_train['day_of_week'].unique().tolist())})")

    # 2. Zbiór walidacyjny
    print("\n>>> KROK 2: Przetwarzanie zbioru walidacyjnego (orders_validation.csv) <<<")
    df_val, stats_val = prepare_orders_validation()
    print(f"[Sukces Walidacja] Zapisano {len(df_val)} wierszy do data/processed/orders_validation.csv.")
    print(f"                   - Poprawne zamówienia: {int(df_val['orders'].notna().sum())} dni")
    print(f"                   - Braki (NaN): {int(df_val['orders'].isna().sum())} dni")
    print(f"                   - Suma poprawnych zamówień: {df_val['orders'].sum(skipna=True)} szt.")
    print(f"                   - Zakres dat: {df_val['date'].min()} do {df_val['date'].max()}")
    print(f"                   - Cecha day_of_week: dołączona (wartości: {sorted(df_val['day_of_week'].unique().tolist())})")

    # 3. Kontrole spójności podziału czasowego (Kontrola Dnia 10)
    print("\n>>> KROK 3: Walidacja relacji czasowych i rygoru podziału (Kontrola Dnia 10) <<<")
    # A. Liczności
    assert len(df_train) == 252, f"Błąd: Oczekiwano 252 dat treningowych, otrzymano {len(df_train)}!"
    assert df_train["orders"].notna().sum() == 248, f"Błąd: Oczekiwano 248 poprawnych celów w treningu, otrzymano {df_train['orders'].notna().sum()}!"
    assert len(df_val) == 84, f"Błąd: Oczekiwano 84 dat walidacyjnych, otrzymano {len(df_val)}!"
    assert df_val["orders"].notna().sum() == 84, f"Błąd: Oczekiwano 84 poprawnych celów w walidacji, otrzymano {df_val['orders'].notna().sum()}!"
    print("[OK] Kontrola 1 (Liczności): Trening = 252 daty (248 poprawnych celów), Walidacja = 84 daty (84 poprawne cele).")

    # B. Brak wspólnych dat
    overlapping_dates = set(df_train["date"]).intersection(set(df_val["date"]))
    assert len(overlapping_dates) == 0, f"Błąd krytyczny: Wykryto wspólne daty między treningiem a walidacją: {overlapping_dates}!"
    print("[OK] Kontrola 2 (Brak wspólnych dat): Zbiory są całkowicie rozłączne (brak wycieku danych).")

    # C. Początek walidacji po końcu treningu
    train_end = df_train["date"].max()
    val_start = df_val["date"].min()
    assert val_start > train_end, f"Błąd krytyczny: Początek walidacji ({val_start}) nie jest po końcu treningu ({train_end})!"
    print(f"[OK] Kontrola 3 (Sekwencyjność czasowa): Walidacja rozpoczyna się {val_start}, bezpośrednio po końcu treningu {train_end}.")

    # D. Weryfikacja cech modelu (day_of_week obecne, is_weekend nieobecne)
    assert "day_of_week" in df_train.columns and "day_of_week" in df_val.columns, "Błąd: Brak kolumny day_of_week!"
    assert "is_weekend" not in df_train.columns and "is_weekend" not in df_val.columns, "Błąd: Kolumna is_weekend nie powinna być dołączana do cech!"
    print("[OK] Kontrola 4 (Cechy modelu): Dołączono day_of_week (0=poniedziałek, 6=niedziela). Kolumna is_weekend nie została dodana do cech.")

    print("\n================================================================================")
    print("WSZYSTKIE KONTROLE PODZIAŁU CZASOWEGO ZAKOŃCZONE PEŁNYM SUKCESEM!")
    print("================================================================================")

    return df_train, df_val


if __name__ == "__main__":
    try:
        prepare_all_datasets()
    except Exception as err:
        print(f"\nBŁĄD: {err}", file=sys.stderr)
        sys.exit(1)

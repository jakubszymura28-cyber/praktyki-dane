"""Moduł do przygotowania potoku cech, transformacji i treningu modeli prognozowania popytu.

Dzień 11:
- Pipeline cech (ColumnTransformer):
  * SimpleImputer(strategy='median') dla braków w planned_ad_spend_pln (krok uczący się statystyki z treningu)
  * OneHotEncoder dla day_of_week (krok uczący się kategorii z treningu)
  * passthrough dla promo (krok stosujący ustaloną regułę binarnej flagi 0/1 bez uczenia)
- Uczenie przygotowania cech wyłącznie na 248 wierszach treningowych z poprawnym celem (orders.notna())
- Selekcja cech: tylko day_of_week, promo, planned_ad_spend_pln
  (orders jest celem; visits i revenue_pln NIE są cechami - ochrona przed wyciekiem danych)
- Wyznaczenie i kontrola wyuczonej mediany budżetu (575.275 PLN).
"""

from pathlib import Path
from typing import Tuple, Dict, Any
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder


BASE_DIR = Path(__file__).resolve().parent.parent
TRAIN_PROCESSED_PATH = BASE_DIR / "data" / "processed" / "orders_train.csv"
VAL_PROCESSED_PATH = BASE_DIR / "data" / "processed" / "orders_validation.csv"

# Definicja kolumn zgodnie z Kartą Modelu (reports/model_card.md)
FEATURE_COLUMNS = ["day_of_week", "promo", "planned_ad_spend_pln"]
TARGET_COLUMN = "orders"
EXCLUDED_COLUMNS = ["visits", "revenue_pln", "date", "orders_invalid"]


def resolve_path(p: Path) -> Path:
    """Obsługa uruchamiania z głównego katalogu lub z podkatalogu src."""
    if p.exists():
        return p
    alt = Path("..") / p
    if alt.exists():
        return alt
    return p


def build_preprocessor() -> ColumnTransformer:
    """Buduje potok inżynierii cech (ColumnTransformer).

    Role komponentów:
    1. planned_ad_spend_pln -> SimpleImputer(strategy='median'):
       KROK UCZĄCY SIĘ: Podczas .fit() uczy się mediany budżetu wyłącznie z danych treningowych.
    2. day_of_week -> OneHotEncoder():
       KROK UCZĄCY SIĘ: Podczas .fit() uczy się unikalnych kategorii dni tygodnia (0-6).
    3. promo -> 'passthrough':
       KROK STOSUJĄCY USTALONĄ REGUŁĘ: Przekazuje flagę 0/1 bez dopasowywania wag ani parametrów.
    """
    preprocessor = ColumnTransformer(
        transformers=[
            ("budget_imputer", SimpleImputer(strategy="median"), ["planned_ad_spend_pln"]),
            ("dow_ohe", OneHotEncoder(sparse_output=False, handle_unknown="ignore"), ["day_of_week"]),
            ("promo_passthrough", "passthrough", ["promo"]),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )
    return preprocessor


def prepare_training_data(
    train_path: Path = TRAIN_PROCESSED_PATH,
) -> Tuple[pd.DataFrame, pd.Series, dict]:
    """Wczytuje zbiór treningowy, filtruje do 248 wierszy z poprawnym celem i zwraca X oraz y."""
    resolved_path = resolve_path(train_path)
    if not resolved_path.exists():
        raise FileNotFoundError(f"Nie znaleziono pliku danych treningowych: {resolved_path}")

    df_raw = pd.read_csv(resolved_path)

    # 1. Sprawdzenie obecności kluczowych kolumn
    missing_cols = set(FEATURE_COLUMNS + [TARGET_COLUMN]).difference(df_raw.columns)
    if missing_cols:
        raise ValueError(f"Brak wymaganych kolumn w zbiorze treningowym: {missing_cols}")

    # 2. Filtracja wyłącznie do rekordów z poprawnym celem (orders niepuste)
    total_train_rows = len(df_raw)
    df_valid = df_raw[df_raw[TARGET_COLUMN].notna()].copy()
    valid_train_rows = len(df_valid)

    # Walidacja liczności zgodnie z reports/quality.md
    if valid_train_rows != 248:
        raise ValueError(
            f"Oczekiwano dokładnie 248 wierszy z poprawnym celem, otrzymano: {valid_train_rows} (z {total_train_rows})!"
        )

    # 3. Zabezpieczenie przed wyciekiem danych: jawne wykluczenie visits i revenue_pln
    X = df_valid[FEATURE_COLUMNS].copy()
    y = df_valid[TARGET_COLUMN].copy()

    # Statystyki budżetu reklamowego przed imputacją
    budget_series = df_valid["planned_ad_spend_pln"]
    budget_non_null = int(budget_series.notna().sum())
    budget_nulls = int(budget_series.isna().sum())
    independent_budget_median = float(budget_series.median())

    stats = {
        "total_train_rows": total_train_rows,
        "valid_train_rows": valid_train_rows,
        "budget_non_null": budget_non_null,
        "budget_nulls": budget_nulls,
        "independent_budget_median": independent_budget_median,
        "feature_names": FEATURE_COLUMNS,
        "target_name": TARGET_COLUMN,
        "excluded_features": EXCLUDED_COLUMNS,
    }

    return X, y, stats


def fit_and_audit_pipeline() -> Dict[str, Any]:
    """Dopasowuje preprocessor na 248 wierszach treningowych i przeprowadza audyt zgodności."""
    X_train, y_train, stats = prepare_training_data()

    preprocessor = build_preprocessor()
    preprocessor.fit(X_train, y_train)

    # Pobranie wyuczonej mediany z SimpleImputer
    budget_imputer = preprocessor.named_transformers_["budget_imputer"]
    learned_median = float(budget_imputer.statistics_[0])
    stats["learned_budget_median"] = learned_median

    # Pobranie wyuczonych kategorii z OneHotEncoder
    dow_ohe = preprocessor.named_transformers_["dow_ohe"]
    learned_dow_categories = dow_ohe.categories_[0].tolist()
    stats["learned_dow_categories"] = learned_dow_categories

    # Przekształcenie macierzy cech X
    X_transformed = preprocessor.transform(X_train)
    transformed_feature_names = preprocessor.get_feature_names_out()
    stats["transformed_shape"] = X_transformed.shape
    stats["transformed_feature_names"] = transformed_feature_names.tolist()

    # Kontrola 1: zgodność wyuczonej mediany z niezależnym rachunkiem
    independent_median = stats["independent_budget_median"]
    is_median_equal = np.isclose(learned_median, independent_median)
    stats["median_audit_passed"] = is_median_equal

    if not is_median_equal:
        raise ValueError(
            f"Błąd kontroli mediany: SimpleImputer wyuczył {learned_median}, "
            f"podczas gdy niezależna mediana wynosi {independent_median}!"
        )

    return stats


def main() -> None:
    print("=" * 80)
    print("TRENING POTOKU CECH (src/train.py) - DZIEŃ 11")
    print("=" * 80)

    stats = fit_and_audit_pipeline()

    print("\n--- 1. ŹRÓDŁOWE LICZNOŚCI ZBIORU TRENINGOWEGO ---")
    print(f"Całkowita liczba dat w zbiorze treningowym:       {stats['total_train_rows']}")
    print(f"Wiersze z poprawnym celem (orders.notna()):         {stats['valid_train_rows']} (tylko na nich uczymy potok)")
    print(f"Liczba wierszy z uzupełnionym budżetem reklamowym:  {stats['budget_non_null']}")
    print(f"Liczba braków w budżecie reklamowym (NaN):          {stats['budget_nulls']}")

    print("\n--- 2. SELEKCJA CECH I ZABEZPIECZENIE PRZED DATA LEAKAGE ---")
    print(f"Cechy wejściowe (X):  {stats['feature_names']}")
    print(f"Zmienna celu (y):     {stats['target_name']}")
    print(f"Kolumny wykluczone:   {stats['excluded_features']}")
    print("Wyjaśnienie: visits i revenue_pln są znane dopiero po zakończeniu doby sprzedaży,")
    print("             dlatego ich użycie jako cech wejściowych stanowiłoby wyciek danych.")

    print("\n--- 3. WYJAŚNIENIE RÓL KOMPONENTÓW PIPELINE ---")
    print("A. KROKI, KTÓRE SIĘ UCZĄ (metoda .fit() wyznacza parametry z danych treningowych):")
    print(f"   * SimpleImputer(strategy='median'):")
    print(f"     Wyuczył się parametru mediany budżetu: {stats['learned_budget_median']:.3f} PLN")
    print(f"   * OneHotEncoder():")
    print(f"     Wyuczył się unikalnych kategorii dnia tygodnia: {stats['learned_dow_categories']}")
    print("B. KROKI STOSUJĄCE TYLKO USTALONĄ REGUŁĘ:")
    print("   * promo (passthrough):")
    print("     Stosuje sztywną regułę przekazania binarnej flagi 0/1 bez uczenia jakichkolwiek wag.")

    print("\n--- 4. WYNIK KONTROLI MEDIANY BUDŻETU REKLAMOWEGO ---")
    print(f"Wyuczona mediana SimpleImputer:             {stats['learned_budget_median']:.3f} PLN")
    print(f"Niezależna mediana pandas (244 niepuste):   {stats['independent_budget_median']:.3f} PLN")
    print(f"Różnica bezwzględna:                        {abs(stats['learned_budget_median'] - stats['independent_budget_median']):.6f} PLN")
    print("[KONTROLA ZAKOŃCZONA SUKCESEM] Obie wartości są w 100% identyczne!")

    print("\n--- 5. STRUKTURA PRZEKSZTAŁCONYCH CECH ---")
    print(f"Kształt macierzy wejściowej po transformacji: {stats['transformed_shape']} (wiersze x cechy)")
    print(f"Nazwy wygenerowanych kolumn: {stats['transformed_feature_names']}")
    print("\n" + "=" * 80)
    print("POTOK CECH ZOSTAŁ POPRAWNIE ZBUDOWANY I PRZETESTOWANY.")
    print("=" * 80)


if __name__ == "__main__":
    main()

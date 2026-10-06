"""Moduł do przygotowania potoku cech, transformacji i treningu modeli prognozowania popytu.

Dzień 11 i Dzień 12:
- Pipeline cech (ColumnTransformer):
  * SimpleImputer(strategy='median') dla braków w planned_ad_spend_pln (krok uczący się statystyki z treningu)
  * OneHotEncoder dla day_of_week (krok uczący się kategorii z treningu)
  * passthrough dla promo (krok stosujący ustaloną regułę binarnej flagi 0/1 bez uczenia)
- Uczenie potoku cech i modelu wyłącznie na 248 wierszach treningowych z poprawnym celem (orders.notna())
- Selekcja cech: tylko day_of_week, promo, planned_ad_spend_pln
  (orders jest celem; visits i revenue_pln NIE są cechami - ochrona przed wyciekiem danych)
- Wyznaczenie i kontrola wyuczonej mediany budżetu (575.275 PLN).
- Model bazowy DummyRegressor(strategy='median'):
  * Uczenie na 248 wierszach treningu (stała prognoza = mediana orders z treningu = 85.0 szt.)
  * Prognozowanie wszystkich 84 dni walidacji
  * Zapis metryk MAE do reports/metrics.csv
  * Zapis prognoz do reports/validation_predictions.csv
  * Weryfikacja stałości prognoz oraz ręczna kontrola dla 3 pierwszych dat walidacji.
"""

from pathlib import Path
from typing import Tuple, Dict, Any
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error
from sklearn.preprocessing import OneHotEncoder


BASE_DIR = Path(__file__).resolve().parent.parent
TRAIN_PROCESSED_PATH = BASE_DIR / "data" / "processed" / "orders_train.csv"
VAL_PROCESSED_PATH = BASE_DIR / "data" / "processed" / "orders_validation.csv"
REPORTS_DIR = BASE_DIR / "reports"

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
    orders_median = float(y.median())

    stats = {
        "total_train_rows": total_train_rows,
        "valid_train_rows": valid_train_rows,
        "budget_non_null": budget_non_null,
        "budget_nulls": budget_nulls,
        "independent_budget_median": independent_budget_median,
        "orders_median": orders_median,
        "feature_names": FEATURE_COLUMNS,
        "target_name": TARGET_COLUMN,
        "excluded_features": EXCLUDED_COLUMNS,
    }

    return X, y, stats


def load_validation_data(val_path: Path = VAL_PROCESSED_PATH) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
    """Wczytuje zbiór walidacyjny (84 dni)."""
    resolved_path = resolve_path(val_path)
    if not resolved_path.exists():
        raise FileNotFoundError(f"Nie znaleziono pliku danych walidacyjnych: {resolved_path}")

    df_val = pd.read_csv(resolved_path)
    if len(df_val) != 84:
        raise ValueError(f"Oczekiwano 84 wierszy walidacji, otrzymano: {len(df_val)}!")

    X_val = df_val[FEATURE_COLUMNS].copy()
    y_val = df_val[TARGET_COLUMN].copy()
    return X_val, y_val, df_val


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


def train_and_evaluate_baseline() -> Dict[str, Any]:
    """Trenuje model bazowy DummyRegressor(strategy='median') i zapisuje raporty metryk oraz predykcji."""
    X_train, y_train, train_stats = prepare_training_data()
    X_val, y_val, df_val = load_validation_data()

    # Inicjalizacja i trening modelu bazowego
    # DummyRegressor używa X tylko do określenia liczby wierszy, uczy się wyłącznie rozkładu y_train
    baseline_model = DummyRegressor(strategy="median")
    baseline_model.fit(X_train, y_train)

    # Wyciągnięcie stałej predykcji
    constant_prediction = float(baseline_model.constant_[0][0])
    train_median_orders = float(y_train.median())

    # Asercja: stała predykcja musi być równa medianie orders z treningu (85.0 szt.)
    if not np.isclose(constant_prediction, train_median_orders):
        raise ValueError(
            f"Błąd modelu bazowego: stała prognoza ({constant_prediction}) != medianie treningowej ({train_median_orders})!"
        )

    # Prognozy na zbiorze treningowym i walidacyjnym
    train_preds = baseline_model.predict(X_train)
    val_preds = baseline_model.predict(X_val)

    # Sprawdzenie, czy wszystkie predykcje walidacyjne są identyczne i równe 85.0
    if not np.all(np.isclose(val_preds, constant_prediction)):
        raise ValueError("Błąd: Nie wszystkie wartości predykcji baseline na walidacji są identyczne!")

    # Obliczenie metryk MAE
    train_mae = float(mean_absolute_error(y_train, train_preds))
    val_mae = float(mean_absolute_error(y_val, val_preds))

    # Przygotowanie katalogu reports/
    resolved_reports_dir = resolve_path(REPORTS_DIR)
    resolved_reports_dir.mkdir(parents=True, exist_ok=True)

    # 1. Zapis metryk do reports/metrics.csv
    df_metrics = pd.DataFrame([
        {
            "model": "DummyRegressor(median)",
            "dataset": "train",
            "n_samples": len(y_train),
            "mae": round(train_mae, 4),
            "predicted_constant": constant_prediction,
        },
        {
            "model": "DummyRegressor(median)",
            "dataset": "validation",
            "n_samples": len(y_val),
            "mae": round(val_mae, 4),
            "predicted_constant": constant_prediction,
        },
    ])
    metrics_path = resolved_reports_dir / "metrics.csv"
    df_metrics.to_csv(metrics_path, index=False, encoding="utf-8")

    # 2. Zapis predykcji walidacyjnych do reports/validation_predictions.csv
    df_val_preds = pd.DataFrame({
        "date": df_val["date"],
        "actual_orders": df_val["orders"],
        "predicted_orders": val_preds,
        "absolute_error": np.abs(df_val["orders"] - val_preds),
    })
    preds_path = resolved_reports_dir / "validation_predictions.csv"
    df_val_preds.to_csv(preds_path, index=False, encoding="utf-8")

    # Ręczne obliczenie dla 3 pierwszych dat walidacji
    first_3 = df_val_preds.head(3).copy()

    results = {
        "constant_prediction": constant_prediction,
        "train_mae": train_mae,
        "val_mae": val_mae,
        "metrics_path": metrics_path,
        "preds_path": preds_path,
        "first_3_rows": first_3.to_dict(orient="records"),
        "first_3_mae": float(first_3["absolute_error"].mean()),
    }

    return results


def main() -> None:
    print("=" * 80)
    print("TRENING I EWALUACJA MODELI (src/train.py) - DZIEŃ 11 i DZIEŃ 12")
    print("=" * 80)

    # Krok 1: Potok cech
    stats = fit_and_audit_pipeline()
    print("\n[OK] Potok inżynierii cech dopasowany na 248 wierszach treningu:")
    print(f"     - Wyuczona mediana budżetu: {stats['learned_budget_median']:.3f} PLN")
    print(f"     - Wyuczone kategorie day_of_week: {stats['learned_dow_categories']}")
    print(f"     - Kształt macierzy X_transformed: {stats['transformed_shape']}")

    # Krok 2: Model bazowy (DummyRegressor)
    print("\n" + "-" * 80)
    print("MODEL BAZOWY: DummyRegressor(strategy='median')")
    print("-" * 80)
    baseline_res = train_and_evaluate_baseline()

    print(f"Stała prognoza modelu bazowego (mediana orders z treningu): {baseline_res['constant_prediction']:.2f} szt.")
    print(f"MAE na zbiorze treningowym (248 dni):                      {baseline_res['train_mae']:.4f} szt.")
    print(f"MAE na zbiorze walidacyjnym (84 dni):                     {baseline_res['val_mae']:.4f} szt.")
    print(f"\n[Zapisano] Metryki modelu:     {baseline_res['metrics_path']}")
    print(f"[Zapisano] Prognozy walidacji: {baseline_res['preds_path']}")

    print("\n--- RĘCZNA KONTROLA DLA 3 PIERWSZYCH DAT WALIDACJI ---")
    for row in baseline_res["first_3_rows"]:
        date_str = row["date"]
        y_act = row["actual_orders"]
        y_pred = row["predicted_orders"]
        err = row["absolute_error"]
        print(f"Data: {date_str} | Rzeczywiste orders: {y_act:5.1f} | Prognoza: {y_pred:5.1f} | Błąd bezwzględny |y - y_pred| = {err:5.1f}")

    print(f"\nŚredni błąd bezwzględny dla pierwszych 3 dat: {baseline_res['first_3_mae']:.4f} szt.")
    print(f"Średni błąd bezwzględny dla całych 84 dni (MAE):  {baseline_res['val_mae']:.4f} szt.")
    print("=" * 80)
    print("EWIDENCJA MODELU BAZOWEGO ZAKOŃCZONA PEŁNYM SUKCESEM.")
    print("=" * 80)


if __name__ == "__main__":
    main()

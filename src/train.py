"""Moduł do przygotowania potoku cech, transformacji i treningu modeli prognozowania popytu.

Dni 11, 12, 13:
- Pipeline cech (ColumnTransformer):
  * SimpleImputer(strategy='median') dla planned_ad_spend_pln
  * OneHotEncoder dla day_of_week
  * passthrough dla promo
- Uczenie na 248 wierszach treningowych z poprawnym celem (orders.notna())
- Cechy wejściowe: day_of_week, promo, planned_ad_spend_pln
  (wykluczone: visits, revenue_pln, date, orders_invalid)
- Model bazowy: DummyRegressor(strategy='median') -> stała 85.0 szt.
- Model kandydujący: DecisionTreeRegressor(max_depth=3, random_state=42) w pełnym Pipeline
- Pomiar czasu trenowania i predykcji
- Eksport raportów:
  * reports/metrics.csv (MAE, czas działania i opis dla obu modeli na train i val)
  * reports/validation_predictions.csv (84 daty z prognozami baseline i drzewa)
"""

from pathlib import Path
import time
from typing import Tuple, Dict, Any
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.tree import DecisionTreeRegressor


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
    """Buduje potok inżynierii cech (ColumnTransformer)."""
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

    missing_cols = set(FEATURE_COLUMNS + [TARGET_COLUMN]).difference(df_raw.columns)
    if missing_cols:
        raise ValueError(f"Brak wymaganych kolumn w zbiorze treningowym: {missing_cols}")

    total_train_rows = len(df_raw)
    df_valid = df_raw[df_raw[TARGET_COLUMN].notna()].copy()
    valid_train_rows = len(df_valid)

    if valid_train_rows != 248:
        raise ValueError(
            f"Oczekiwano dokładnie 248 wierszy z poprawnym celem, otrzymano: {valid_train_rows} (z {total_train_rows})!"
        )

    X = df_valid[FEATURE_COLUMNS].copy()
    y = df_valid[TARGET_COLUMN].copy()

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

    budget_imputer = preprocessor.named_transformers_["budget_imputer"]
    learned_median = float(budget_imputer.statistics_[0])
    stats["learned_budget_median"] = learned_median

    dow_ohe = preprocessor.named_transformers_["dow_ohe"]
    learned_dow_categories = dow_ohe.categories_[0].tolist()
    stats["learned_dow_categories"] = learned_dow_categories

    X_transformed = preprocessor.transform(X_train)
    transformed_feature_names = preprocessor.get_feature_names_out()
    stats["transformed_shape"] = X_transformed.shape
    stats["transformed_feature_names"] = transformed_feature_names.tolist()

    independent_median = stats["independent_budget_median"]
    is_median_equal = np.isclose(learned_median, independent_median)
    stats["median_audit_passed"] = is_median_equal

    if not is_median_equal:
        raise ValueError(
            f"Błąd kontroli mediany: SimpleImputer wyuczył {learned_median}, "
            f"podczas gdy niezależna mediana wynosi {independent_median}!"
        )

    return stats


def train_and_evaluate_all_models() -> Dict[str, Any]:
    """Trenuje i ocenia zarówno model bazowy (DummyRegressor), jak i drzewo decyzyjne (DecisionTreeRegressor).

    Mierzy precyzyjny czas fit i predict oraz zapisuje zintegrowane raporty do reports/.
    """
    X_train, y_train, train_stats = prepare_training_data()
    X_val, y_val, df_val = load_validation_data()

    # =========================================================================
    # MODEL 1: BAZOWY (DummyRegressor strategy='median')
    # =========================================================================
    t0_base_fit = time.perf_counter()
    baseline_model = DummyRegressor(strategy="median")
    baseline_model.fit(X_train, y_train)
    t_base_fit = time.perf_counter() - t0_base_fit

    constant_prediction = float(baseline_model.constant_[0][0])

    t0_base_pred_tr = time.perf_counter()
    base_train_preds = baseline_model.predict(X_train)
    t_base_pred_tr = time.perf_counter() - t0_base_pred_tr

    t0_base_pred_val = time.perf_counter()
    base_val_preds = baseline_model.predict(X_val)
    t_base_pred_val = time.perf_counter() - t0_base_pred_val

    base_train_mae = float(mean_absolute_error(y_train, base_train_preds))
    base_val_mae = float(mean_absolute_error(y_val, base_val_preds))

    # =========================================================================
    # MODEL 2: KANDYDUJĄCY (Pipeline: ColumnTransformer + DecisionTreeRegressor)
    # =========================================================================
    preprocessor = build_preprocessor()
    tree_regressor = DecisionTreeRegressor(max_depth=3, random_state=42)
    tree_pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("regressor", tree_regressor),
    ])

    # Pomiar czasu dopasowania (fit): obejmuje przygotowanie cech + budowę drzewa
    t0_tree_fit = time.perf_counter()
    tree_pipeline.fit(X_train, y_train)
    t_tree_fit = time.perf_counter() - t0_tree_fit

    # Pomiar czasu predykcji na treningu
    t0_tree_pred_tr = time.perf_counter()
    tree_train_preds = tree_pipeline.predict(X_train)
    t_tree_pred_tr = time.perf_counter() - t0_tree_pred_tr

    # Pomiar czasu predykcji na walidacji: obejmuje transformację cech walidacji + przejście przez drzewo
    t0_tree_pred_val = time.perf_counter()
    tree_val_preds = tree_pipeline.predict(X_val)
    t_tree_pred_val = time.perf_counter() - t0_tree_pred_val

    tree_train_mae = float(mean_absolute_error(y_train, tree_train_preds))
    tree_val_mae = float(mean_absolute_error(y_val, tree_val_preds))

    # Asercja równej liczby prognoz walidacji (84 dni dla obu modeli)
    assert len(base_val_preds) == 84 and len(tree_val_preds) == 84, "Błąd: Liczba predykcji walidacyjnych != 84!"

    # =========================================================================
    # ZAPIS RAPORTÓW
    # =========================================================================
    resolved_reports_dir = resolve_path(REPORTS_DIR)
    resolved_reports_dir.mkdir(parents=True, exist_ok=True)

    # 1. reports/metrics.csv
    df_metrics = pd.DataFrame([
        {
            "model": "DummyRegressor(median)",
            "dataset": "train",
            "n_samples": len(y_train),
            "mae": round(base_train_mae, 4),
            "fit_time_seconds": round(t_base_fit, 6),
            "predict_time_seconds": round(t_base_pred_tr, 6),
            "time_measured_scope": "Wyznaczenie mediany z y_train oraz generowanie stalej prognozy",
        },
        {
            "model": "DummyRegressor(median)",
            "dataset": "validation",
            "n_samples": len(y_val),
            "mae": round(base_val_mae, 4),
            "fit_time_seconds": round(t_base_fit, 6),
            "predict_time_seconds": round(t_base_pred_val, 6),
            "time_measured_scope": "Generowanie stalej prognozy dla 84 dni walidacji",
        },
        {
            "model": "DecisionTreeRegressor(max_depth=3)",
            "dataset": "train",
            "n_samples": len(y_train),
            "mae": round(tree_train_mae, 4),
            "fit_time_seconds": round(t_tree_fit, 6),
            "predict_time_seconds": round(t_tree_pred_tr, 6),
            "time_measured_scope": "Pelny potok (ColumnTransformer fit + DecisionTree fit na 248 probkach)",
        },
        {
            "model": "DecisionTreeRegressor(max_depth=3)",
            "dataset": "validation",
            "n_samples": len(y_val),
            "mae": round(tree_val_mae, 4),
            "fit_time_seconds": round(t_tree_fit, 6),
            "predict_time_seconds": round(t_tree_pred_val, 6),
            "time_measured_scope": "Transformacja cech walidacji (imputacja+OHE) + predykcja drzewa dla 84 probek",
        },
    ])
    metrics_path = resolved_reports_dir / "metrics.csv"
    df_metrics.to_csv(metrics_path, index=False, encoding="utf-8")

    # 2. reports/validation_predictions.csv
    df_val_preds = pd.DataFrame({
        "date": df_val["date"],
        "actual_orders": df_val["orders"],
        "predicted_orders_baseline": base_val_preds,
        "predicted_orders_tree": np.round(tree_val_preds, 2),
        "abs_error_baseline": np.round(np.abs(df_val["orders"] - base_val_preds), 2),
        "abs_error_tree": np.round(np.abs(df_val["orders"] - tree_val_preds), 2),
    })
    preds_path = resolved_reports_dir / "validation_predictions.csv"
    df_val_preds.to_csv(preds_path, index=False, encoding="utf-8")

    return {
        "metrics_df": df_metrics,
        "preds_df": df_val_preds,
        "metrics_path": metrics_path,
        "preds_path": preds_path,
        "base_val_mae": base_val_mae,
        "tree_val_mae": tree_val_mae,
        "base_train_mae": base_train_mae,
        "tree_train_mae": tree_train_mae,
        "tree_fit_ms": t_tree_fit * 1000,
        "tree_predict_val_ms": t_tree_pred_val * 1000,
    }


def main() -> None:
    print("=" * 80)
    print("TRENING I EWALUACJA MODELI (src/train.py) - DZIEŃ 11, 12, 13")
    print("=" * 80)

    # Potok cech audyt
    stats = fit_and_audit_pipeline()
    print(f"[OK] Preprocessor dopasowany na {stats['valid_train_rows']} wierszach treningu (mediana={stats['learned_budget_median']:.3f} PLN).")

    # Ewaluacja obu modeli
    results = train_and_evaluate_all_models()

    print("\n" + "-" * 80)
    print("PORÓWNANIE WYNIKÓW MODELI (reports/metrics.csv):")
    print("-" * 80)
    print(results["metrics_df"][["model", "dataset", "n_samples", "mae", "fit_time_seconds", "predict_time_seconds"]].to_string(index=False))

    print("\n" + "-" * 80)
    print("PODSUMOWANIE METRYK I CZASU:")
    print("-" * 80)
    print(f"1. DummyRegressor (Baseline):")
    print(f"   - MAE trening:    {results['base_train_mae']:.4f} szt./dzień")
    print(f"   - MAE walidacja:  {results['base_val_mae']:.4f} szt./dzień")
    print(f"2. DecisionTreeRegressor(max_depth=3, random_state=42):")
    print(f"   - MAE trening:    {results['tree_train_mae']:.4f} szt./dzień")
    print(f"   - MAE walidacja:  {results['tree_val_mae']:.4f} szt./dzień")
    print(f"   - Czas fit:       {results['tree_fit_ms']:.2f} ms")
    print(f"   - Czas predict:   {results['tree_predict_val_ms']:.2f} ms")

    diff_val = results["base_val_mae"] - results["tree_val_mae"]
    if diff_val > 0:
        print(f"\n[WYNIK PORÓWNANIA] Drzewo decyzyjne uzyskało LEPSZY wynik na walidacji.")
        print(f"                  Błąd MAE zmalał o {diff_val:.4f} szt./dzień (z {results['base_val_mae']:.2f} do {results['tree_val_mae']:.2f}).")
    else:
        print(f"\n[WYNIK PORÓWNANIA] Drzewo decyzyjne uzyskało gorszy lub równy wynik na walidacji (różnica: {diff_val:.4f}).")

    print("\n" + "-" * 80)
    print("PIERWSZE 5 WIERSZY PROGNOZ WALIDACYJNYCH (reports/validation_predictions.csv):")
    print("-" * 80)
    print(results["preds_df"].head(5).to_string(index=False))

    print("\n" + "=" * 80)
    print("EWIDENCJA MODELI ZAKOŃCZONA PEŁNYM SUKCESEM.")
    print("=" * 80)


if __name__ == "__main__":
    main()

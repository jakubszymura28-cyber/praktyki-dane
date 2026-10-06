"""Moduł do przygotowania potoku cech, transformacji i treningu modeli prognozowania popytu.

Dni 11-15:
- Pipeline cech (ColumnTransformer):
  * SimpleImputer(strategy='median') dla planned_ad_spend_pln
  * OneHotEncoder dla day_of_week
  * passthrough dla promo
- Uczenie na 248 wierszach treningowych z poprawnym celem (orders.notna())
- Cechy wejściowe: day_of_week, promo, planned_ad_spend_pln
  (wykluczone: visits, revenue_pln, date, orders_invalid)
- Zabezpieczenie przed Data Leakage: funkcja validate_feature_list
- Model bazowy: DummyRegressor(strategy='median') -> stała 85.0 szt.
- Wybrany model kandydujący: DecisionTreeRegressor(max_depth=3, random_state=42) w pełnym Pipeline
- Zapis zamrożonych modeli:
  * models/baseline.joblib
  * models/selected_pipeline.joblib
- Weryfikacja wczytania modeli i spójności predykcji (joblib.load)
- Eksport raportów:
  * reports/metrics.csv (metryki MAE, parametry i wersje danych)
  * reports/validation_predictions.csv (84 daty z prognozami obu modeli)
  * reports/validation_errors.csv (największe błędy na walidacji)
"""

from pathlib import Path
import time
from typing import Tuple, Dict, Any
import joblib
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
MODELS_DIR = BASE_DIR / "models"

# Definicja kolumn zgodnie z Kartą Modelu (reports/model_card.md)
FEATURE_COLUMNS = ["day_of_week", "promo", "planned_ad_spend_pln"]
TARGET_COLUMN = "orders"
EXCLUDED_COLUMNS = ["visits", "revenue_pln", "date", "orders_invalid"]
FORBIDDEN_FEATURES = {"orders", "visits", "revenue_pln"}


def validate_feature_list(features: list) -> None:
    """Weryfikuje listę cech wejściowych pod kątem zabronionych kolumn.

    orders jest zmienną celu, a visits i revenue_pln powodują wyciek danych (Data Leakage) w czasie t+1.
    Próba użycia którejkolwiek z tych kolumn jako cechy wejściowej skutkuje błędem ValueError.
    """
    forbidden_found = set(features).intersection(FORBIDDEN_FEATURES)
    if forbidden_found:
        raise ValueError(
            f"Błąd konfiguracji cech: Wykryto zabronione kolumny na liście cech wejściowych: {sorted(list(forbidden_found))}. "
            f"Kolumny 'orders' (cel), 'visits' i 'revenue_pln' (wyciek danych t+1) nie mogą być cechami wejściowymi!"
        )


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
    feature_cols: list = None,
) -> Tuple[pd.DataFrame, pd.Series, dict]:
    """Wczytuje zbiór treningowy, filtruje do 248 wierszy z poprawnym celem i zwraca X oraz y."""
    if feature_cols is None:
        feature_cols = FEATURE_COLUMNS

    validate_feature_list(feature_cols)

    resolved_path = resolve_path(train_path)
    if not resolved_path.exists():
        raise FileNotFoundError(f"Nie znaleziono pliku danych treningowych: {resolved_path}")

    df_raw = pd.read_csv(resolved_path)

    missing_cols = set(feature_cols + [TARGET_COLUMN]).difference(df_raw.columns)
    if missing_cols:
        raise ValueError(f"Brak wymaganych kolumn w zbiorze treningowym: {missing_cols}")

    total_train_rows = len(df_raw)
    df_valid = df_raw[df_raw[TARGET_COLUMN].notna()].copy()
    valid_train_rows = len(df_valid)

    if valid_train_rows != 248:
        raise ValueError(
            f"Oczekiwano dokładnie 248 wierszy z poprawnym celem, otrzymano: {valid_train_rows} (z {total_train_rows})!"
        )

    X = df_valid[feature_cols].copy()
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
        "feature_names": feature_cols,
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
    """Trenuje i ocenia zarówno model bazowy (DummyRegressor), jak i wybrany model (DecisionTreeRegressor max_depth=3).

    Mierzy czas, eksportuje raporty metryk i predykcji oraz zapisuje i weryfikuje zamrożone modele (.joblib).
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
    # MODEL 2: WYBRANY KANDYDUJĄCY (Pipeline: ColumnTransformer + DecisionTreeRegressor max_depth=3)
    # =========================================================================
    preprocessor = build_preprocessor()
    tree_regressor = DecisionTreeRegressor(max_depth=3, random_state=42)
    selected_pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("regressor", tree_regressor),
    ])

    t0_tree_fit = time.perf_counter()
    selected_pipeline.fit(X_train, y_train)
    t_tree_fit = time.perf_counter() - t0_tree_fit

    t0_tree_pred_tr = time.perf_counter()
    tree_train_preds = selected_pipeline.predict(X_train)
    t_tree_pred_tr = time.perf_counter() - t0_tree_pred_tr

    t0_tree_pred_val = time.perf_counter()
    tree_val_preds = selected_pipeline.predict(X_val)
    t_tree_pred_val = time.perf_counter() - t0_tree_pred_val

    tree_train_mae = float(mean_absolute_error(y_train, tree_train_preds))
    tree_val_mae = float(mean_absolute_error(y_val, tree_val_preds))

    assert len(base_val_preds) == 84 and len(tree_val_preds) == 84, "Błąd: Liczba predykcji walidacyjnych != 84!"

    # =========================================================================
    # ZAPIS I WERYFIKACJA MODELI (.joblib)
    # =========================================================================
    resolved_models_dir = resolve_path(MODELS_DIR)
    resolved_models_dir.mkdir(parents=True, exist_ok=True)

    baseline_path = resolved_models_dir / "baseline.joblib"
    selected_pipeline_path = resolved_models_dir / "selected_pipeline.joblib"

    joblib.dump(baseline_model, baseline_path)
    joblib.dump(selected_pipeline, selected_pipeline_path)

    # Weryfikacja po wczytaniu z dysku
    loaded_baseline = joblib.load(baseline_path)
    loaded_pipeline = joblib.load(selected_pipeline_path)

    reloaded_base_preds = loaded_baseline.predict(X_val)
    reloaded_tree_preds = loaded_pipeline.predict(X_val)

    if not np.allclose(base_val_preds, reloaded_base_preds):
        raise ValueError("Błąd weryfikacji: prognozy wczytanego baseline.joblib różnią się od oryginalnych!")
    if not np.allclose(tree_val_preds, reloaded_tree_preds):
        raise ValueError("Błąd weryfikacji: prognozy wczytanego selected_pipeline.joblib różnią się od oryginalnych!")

    # =========================================================================
    # ZAPIS RAPORTÓW
    # =========================================================================
    resolved_reports_dir = resolve_path(REPORTS_DIR)
    resolved_reports_dir.mkdir(parents=True, exist_ok=True)

    # 1. reports/metrics.csv
    df_metrics = pd.DataFrame([
        {
            "model": "DummyRegressor",
            "split": "train",
            "mae": round(base_train_mae, 4),
            "evaluated_days": len(y_train),
            "parameters": "strategy='median'",
            "data_version": "orders_train.csv (v1, 248 poprawnych celow)",
            "fit_time_seconds": round(t_base_fit, 6),
            "predict_time_seconds": round(t_base_pred_tr, 6),
        },
        {
            "model": "DummyRegressor",
            "split": "validation",
            "mae": round(base_val_mae, 4),
            "evaluated_days": len(y_val),
            "parameters": "strategy='median'",
            "data_version": "orders_validation.csv (v1, 84 cele)",
            "fit_time_seconds": round(t_base_fit, 6),
            "predict_time_seconds": round(t_base_pred_val, 6),
        },
        {
            "model": "DecisionTreeRegressor",
            "split": "train",
            "mae": round(tree_train_mae, 4),
            "evaluated_days": len(y_train),
            "parameters": "max_depth=3, random_state=42",
            "data_version": "orders_train.csv (v1, 248 poprawnych celow)",
            "fit_time_seconds": round(t_tree_fit, 6),
            "predict_time_seconds": round(t_tree_pred_tr, 6),
        },
        {
            "model": "DecisionTreeRegressor",
            "split": "validation",
            "mae": round(tree_val_mae, 4),
            "evaluated_days": len(y_val),
            "parameters": "max_depth=3, random_state=42",
            "data_version": "orders_validation.csv (v1, 84 cele)",
            "fit_time_seconds": round(t_tree_fit, 6),
            "predict_time_seconds": round(t_tree_pred_val, 6),
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

    # 3. reports/validation_errors.csv (Pięć największych błędów drzewa wraz z datą, cechami, prawdziwym orders i prognozą)
    df_errors = pd.DataFrame({
        "date": df_val["date"],
        "day_of_week": df_val["day_of_week"],
        "promo": df_val["promo"],
        "planned_ad_spend_pln": df_val["planned_ad_spend_pln"],
        "actual_orders": df_val["orders"],
        "predicted_orders_tree": np.round(tree_val_preds, 2),
        "abs_error_tree": np.round(np.abs(df_val["orders"] - tree_val_preds), 2),
    })
    df_errors_top5 = df_errors.sort_values(by="abs_error_tree", ascending=False).head(5).reset_index(drop=True)
    errors_path = resolved_reports_dir / "validation_errors.csv"
    df_errors_top5.to_csv(errors_path, index=False, encoding="utf-8")

    return {
        "metrics_df": df_metrics,
        "preds_df": df_val_preds,
        "errors_df": df_errors_top5,
        "metrics_path": metrics_path,
        "preds_path": preds_path,
        "errors_path": errors_path,

        "baseline_model_path": baseline_path,
        "selected_model_path": selected_pipeline_path,
        "base_val_mae": base_val_mae,
        "tree_val_mae": tree_val_mae,
        "base_train_mae": base_train_mae,
        "tree_train_mae": tree_train_mae,
        "tree_fit_ms": t_tree_fit * 1000,
        "tree_predict_val_ms": t_tree_pred_val * 1000,
    }


def main() -> None:
    print("=" * 80)
    print("TRENING, EWALUACJA I ZAMROŻENIE MODELI (src/train.py)")
    print("=" * 80)

    stats = fit_and_audit_pipeline()
    print(f"[OK] Preprocessor dopasowany na {stats['valid_train_rows']} wierszach treningu (mediana={stats['learned_budget_median']:.3f} PLN).")

    results = train_and_evaluate_all_models()

    print("\n" + "-" * 80)
    print("PORÓWNANIE WYNIKÓW MODELI (reports/metrics.csv):")
    print("-" * 80)
    print(results["metrics_df"][["model", "split", "mae", "evaluated_days", "parameters", "data_version"]].to_string(index=False))

    print("\n" + "-" * 80)
    print("ZAPISANE I ZWERYFIKOWANE ZAMROŻONE MODELE (joblib.load OK):")
    print("-" * 80)
    print(f"1. Model bazowy:     {results['baseline_model_path']}")
    print(f"2. Wybrany potok:    {results['selected_model_path']}")
    print("[OK] Wczytane modele generują w 100% identyczne prognozy (asercja zdana).")

    print("\n" + "-" * 80)
    print("TOP 5 NAJWIĘKSZYCH BŁĘDÓW NA WALIDACJI (reports/validation_errors.csv):")
    print("-" * 80)
    top_5 = results["errors_df"][["date", "day_of_week", "promo", "actual_orders", "predicted_orders_tree", "abs_error_tree"]].head(5)
    print(top_5.to_string(index=False))

    print("\n" + "=" * 80)
    print("PROCES ZAKOŃCZONY PEŁNYM SUKCESEM.")
    print("=" * 80)


if __name__ == "__main__":
    main()

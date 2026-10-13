"""Moduł do ewaluacji modeli na zbiorze testowym (Dzień 17).

Ten moduł wczytuje zamrożone modele z katalogu models/ i wykonuje wyłącznie predykcje (.predict).
Kategorycznie nie zawiera żadnego wywołania .fit() ani nie oblicza nowej mediany budżetu z danych testowych.
Zapisuje wyniki do reports/test_predictions.csv oraz dopisuje metryki do reports/metrics.csv.
"""

from pathlib import Path
import time
from typing import Dict, Any, Tuple
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error


BASE_DIR = Path(__file__).resolve().parent.parent
TEST_PROCESSED_PATH = BASE_DIR / "data" / "processed" / "orders_test.csv"
MODELS_DIR = BASE_DIR / "models"
REPORTS_DIR = BASE_DIR / "reports"

FEATURE_COLUMNS = ["day_of_week", "promo", "planned_ad_spend_pln"]
TARGET_COLUMN = "orders"
FORBIDDEN_FEATURES = {"orders", "visits", "revenue_pln"}


def resolve_path(p: Path) -> Path:
    """Obsługa uruchamiania z głównego folderu lub z podkatalogu src."""
    if p.exists():
        return p
    alt = Path("..") / p
    if alt.exists():
        return alt
    return p


def validate_test_features(features: list) -> None:
    """Weryfikuje listę cech wejściowych pod kątem zabronionych kolumn."""
    forbidden_found = set(features).intersection(FORBIDDEN_FEATURES)
    if forbidden_found:
        raise ValueError(
            f"Błąd konfiguracji cech: Wykryto zabronione kolumny: {sorted(list(forbidden_found))}. "
            f"Zmienne 'orders', 'visits' i 'revenue_pln' nie mogą być cechami wejściowymi!"
        )


def load_test_data(test_path: Path = TEST_PROCESSED_PATH) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
    """Wczytuje zbiór testowy i przygotowuje X_test oraz y_test."""
    resolved_path = resolve_path(test_path)
    if not resolved_path.exists():
        raise FileNotFoundError(f"Nie znaleziono pliku danych testowych: {resolved_path}")

    df_test = pd.read_csv(resolved_path)
    if len(df_test) != 84:
        raise ValueError(f"Oczekiwano dokładnie 84 wierszy testowych, otrzymano {len(df_test)}!")

    if df_test[TARGET_COLUMN].isna().sum() != 0:
        raise ValueError(f"Wykryto brakujące cele orders w zbiorze testowym!")

    validate_test_features(FEATURE_COLUMNS)

    X_test = df_test[FEATURE_COLUMNS].copy()
    y_test = df_test[TARGET_COLUMN].copy()
    return X_test, y_test, df_test


def evaluate_test_set() -> Dict[str, Any]:
    """Wczytuje zamrożone modele z models/ i ocenia je na zbiorze testowym."""
    print("================================================================================")
    print("OFICJALNA EWALUACJA NA ZBIORZE TESTOWYM (84 DNI) - BEZ PONOWNEGO UCZENIA")
    print("================================================================================")

    # 1. Wczytanie danych testowych
    X_test, y_test, df_test = load_test_data()
    print(f"[Dane Testowe] Załadowano {len(X_test)} dni (zakres: {df_test['date'].min()} do {df_test['date'].max()}).")
    print(f"               Poprawne cele orders: {int(y_test.notna().sum())} dni (brak braków).")
    print(f"               Brakujące budżety w teście: {int(X_test['planned_ad_spend_pln'].isna().sum())} (obsłuży imputer z treningu).")

    # 2. Wczytanie zamrożonych modeli z models/
    resolved_models_dir = resolve_path(MODELS_DIR)
    baseline_path = resolved_models_dir / "baseline.joblib"
    selected_pipeline_path = resolved_models_dir / "selected_pipeline.joblib"

    if not baseline_path.exists():
        raise FileNotFoundError(f"Brak pliku modelu bazowego: {baseline_path}")
    if not selected_pipeline_path.exists():
        raise FileNotFoundError(f"Brak pliku wybranego modelu: {selected_pipeline_path}")

    print("\n>>> KROK 1: Wczytywanie zamrożonych artefaktów modeli <<<")
    baseline_model = joblib.load(baseline_path)
    selected_pipeline = joblib.load(selected_pipeline_path)
    print(f"[Wczytano] Baseline z {baseline_path}")
    print(f"[Wczytano] Wybrany potok z {selected_pipeline_path}")

    # Weryfikacja parametrów wyuczonego imputera w potoku
    preprocessor = selected_pipeline.named_steps["preprocessor"]
    imputer = preprocessor.named_transformers_["budget_imputer"]
    learned_median = float(imputer.statistics_[0])
    print(f"[Audyt Pipeline] Wyuczona mediana budżetu w zamrożonym potoku: {learned_median} PLN (identyczna z treningiem).")
    if not np.isclose(learned_median, 575.275):
        raise ValueError(f"Niezgodność mediany budżetu! Oczekiwano 575.275 PLN, wykryto: {learned_median} PLN")

    # 3. Predykcja na teście (Baseline)
    print("\n>>> KROK 2: Ewaluacja modelu bazowego (DummyRegressor) <<<")
    t0_base_pred = time.perf_counter()
    baseline_preds = baseline_model.predict(X_test)
    t_base_pred = time.perf_counter() - t0_base_pred
    base_test_mae = float(mean_absolute_error(y_test, baseline_preds))
    print(f"[Baseline Test] Stała prognoza: {float(baseline_model.constant_[0][0])} szt./dzień")
    print(f"[Baseline Test] MAE na teście: {base_test_mae:.4f} szt./dzień (czas: {t_base_pred:.6f} s)")

    # 4. Predykcja na teście (Wybrany model DecisionTreeRegressor max_depth=3)
    print("\n>>> KROK 3: Ewaluacja wybranego modelu (DecisionTreeRegressor max_depth=3) <<<")
    t0_tree_pred = time.perf_counter()
    tree_preds = selected_pipeline.predict(X_test)
    t_tree_pred = time.perf_counter() - t0_tree_pred
    tree_test_mae = float(mean_absolute_error(y_test, tree_preds))
    print(f"[DecisionTree Test] MAE na teście: {tree_test_mae:.4f} szt./dzień (czas: {t_tree_pred:.6f} s)")

    # 5. Porównanie wyników
    diff_mae = base_test_mae - tree_test_mae
    pct_improvement = (diff_mae / base_test_mae) * 100
    print("\n================================================================================")
    print("PODSUMOWANIE WYNIKÓW TESTOWYCH (84 DNI):")
    print(f"- MAE Baseline:              {base_test_mae:.4f} szt./dzień")
    print(f"- MAE DecisionTree (d=3):     {tree_test_mae:.4f} szt./dzień")
    print(f"- Różnica bezwzględna:        {diff_mae:.4f} szt./dzień")
    print(f"- Względna redukcja błędu:    {pct_improvement:.2f}%")
    print("================================================================================")

    # 6. Zapis reports/test_predictions.csv
    resolved_reports_dir = resolve_path(REPORTS_DIR)
    resolved_reports_dir.mkdir(parents=True, exist_ok=True)
    test_preds_path = resolved_reports_dir / "test_predictions.csv"

    df_test_preds = pd.DataFrame({
        "date": df_test["date"],
        "orders": df_test["orders"].astype(float),
        "baseline_pred": np.round(baseline_preds, 4),
        "tree_pred": np.round(tree_preds, 4),
        "baseline_abs_error": np.round(np.abs(df_test["orders"] - baseline_preds), 4),
        "tree_abs_error": np.round(np.abs(df_test["orders"] - tree_preds), 4),
    })
    df_test_preds.to_csv(test_preds_path, index=False, encoding="utf-8")
    print(f"\n[Zapisano] Szczegółowe prognozy testowe w: {test_preds_path} ({len(df_test_preds)} wierszy)")

    # 7. Zapis/Aktualizacja reports/metrics.csv
    metrics_path = resolved_reports_dir / "metrics.csv"
    existing_metrics = pd.read_csv(metrics_path) if metrics_path.exists() else pd.DataFrame()

    # Usuń ewentualne dawne wpisy testowe, aby uniknąć duplikatów przy powtórnym uruchomieniu
    if not existing_metrics.empty and "split" in existing_metrics.columns:
        filtered_metrics = existing_metrics[existing_metrics["split"] != "test"].copy()
    else:
        filtered_metrics = existing_metrics

    new_test_rows = pd.DataFrame([
        {
            "model": "DummyRegressor",
            "split": "test",
            "mae": round(base_test_mae, 4),
            "evaluated_days": len(y_test),
            "parameters": "strategy='median'",
            "data_version": "orders_test.csv (v1, 84 cele)",
            "fit_time_seconds": 0.0,
            "predict_time_seconds": round(t_base_pred, 6),
        },
        {
            "model": "DecisionTreeRegressor",
            "split": "test",
            "mae": round(tree_test_mae, 4),
            "evaluated_days": len(y_test),
            "parameters": "max_depth=3, random_state=42",
            "data_version": "orders_test.csv (v1, 84 cele)",
            "fit_time_seconds": 0.0,
            "predict_time_seconds": round(t_tree_pred, 6),
        },
    ])

    final_metrics = pd.concat([filtered_metrics, new_test_rows], ignore_index=True)
    final_metrics.to_csv(metrics_path, index=False, encoding="utf-8")
    print(f"[Zapisano] Zaktualizowano metryki w: {metrics_path}")

    return {
        "base_test_mae": base_test_mae,
        "tree_test_mae": tree_test_mae,
        "diff_mae": diff_mae,
        "pct_improvement": pct_improvement,
        "evaluated_days": len(y_test),
    }


def load_production_model(model_path: Path = None) -> Any:
    """Wczytuje zaufany, zamrożony potok produkcyjny z models/selected_pipeline.joblib."""
    if model_path is None:
        resolved_models_dir = resolve_path(MODELS_DIR)
        model_path = resolved_models_dir / "selected_pipeline.joblib"
    else:
        model_path = resolve_path(Path(model_path))

    if not model_path.exists():
        raise FileNotFoundError(f"Nie znaleziono pliku modelu produkcyjnego: {model_path}")

    pipeline = joblib.load(model_path)
    return pipeline


def predict_single_day(
    date_val: Any,
    promo_val: int,
    planned_ad_spend_pln: float,
    model: Any = None,
) -> float:
    """Wspólna funkcja wnioskowania dla pojedynczego dnia (używana m.in. przez aplikację demo).

    - Wyznacza day_of_week automatycznie z daty (0=poniedziałek, ..., 6=niedziela).
    - Waliduje dane wejściowe (brak ujemnego budżetu, dozwolone promo 0 lub 1).
    - Przekazuje wyłącznie 3 cechy wejściowe (day_of_week, promo, planned_ad_spend_pln).
    - Nie wywołuje .fit() ani nie przelicza mediany budżetu (używa transformacji z potoku).
    """
    if model is None:
        model = load_production_model()

    # Konwersja i walidacja daty
    try:
        if isinstance(date_val, str):
            parsed_date = pd.to_datetime(date_val)
        elif hasattr(date_val, "weekday"):
            parsed_date = date_val
        else:
            raise ValueError(f"Nieobsługiwany typ daty: {type(date_val)}")
    except Exception as e:
        raise ValueError(f"Niepoprawny format daty: '{date_val}' (szczegóły: {e})")


    day_of_week = int(parsed_date.weekday())

    # Walidacja flagi promo
    if promo_val not in (0, 1):
        raise ValueError(f"Niepoprawna flaga promo: {promo_val}. Oczekiwano 0 lub 1.")

    # Walidacja budżetu
    if planned_ad_spend_pln is not None and planned_ad_spend_pln < 0:
        raise ValueError(f"Planowany budżet reklamowy nie może być ujemny! Otrzymano: {planned_ad_spend_pln}")

    # Przygotowanie ramki 3 cech
    X_single = pd.DataFrame([{
        "day_of_week": day_of_week,
        "promo": int(promo_val),
        "planned_ad_spend_pln": float(planned_ad_spend_pln) if planned_ad_spend_pln is not None else np.nan,
    }])

    # Weryfikacja braku zabronionych kolumn
    validate_test_features(list(X_single.columns))

    pred = float(model.predict(X_single)[0])
    return pred




if __name__ == "__main__":
    evaluate_test_set()


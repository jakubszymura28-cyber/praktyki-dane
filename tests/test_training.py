"""Testy jednostkowe procesu treningowego i zabezpieczeń potoku (src/train.py).

Weryfikacja:
1. Brak wymaganego pliku źródłowego skutkuje czytelnym błędem FileNotFoundError.
2. Próba dodania kolumn zabronionych (orders, visits, revenue_pln) do listy cech wejściowych
   zostaje bezwzględnie odrzucona z błędem ValueError (ochrona przed Data Leakage).
3. Wykorzystanie jednej wspólnej implementacji przygotowania cech (build_preprocessor).
Wszystkie testy operują na izolowanych obiektach tymczasowych i nie modyfikują oryginalnych danych.
"""

from pathlib import Path
import sys
import tempfile
import unittest
import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.train import (
    build_preprocessor,
    prepare_training_data,
    validate_feature_list,
    FORBIDDEN_FEATURES,
    FEATURE_COLUMNS,
)


class TestTrainingPipeline(unittest.TestCase):
    """Zestaw prób kontrolnych dla modułu treningowego."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_dir_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_missing_file_raises_clear_error(self):
        """Próba 1: Brak wymaganego pliku musi zgłaszać czytelny błąd FileNotFoundError."""
        non_existent_file = self.temp_dir_path / "nieistniejacy_zbior_orders.csv"

        with self.assertRaises(FileNotFoundError) as context:
            prepare_training_data(train_path=non_existent_file)

        err_msg = str(context.exception)
        self.assertIn("Nie znaleziono pliku danych treningowych", err_msg)
        print(f"\n[SUKCES] Próba 1 (Brak pliku): Zgłoszono prawidłowy błąd FileNotFoundError -> '{err_msg}'.")

    def test_forbidden_features_rejected(self):
        """Próba 2: Próba dodania orders, visits lub revenue_pln do listy cech musi zostać odrzucona."""
        # A. Bezpośredni test validate_feature_list
        for forbidden in ["orders", "visits", "revenue_pln"]:
            bad_features = ["day_of_week", "promo", forbidden]
            with self.assertRaises(ValueError) as context:
                validate_feature_list(bad_features)
            err_msg = str(context.exception)
            self.assertIn("Błąd konfiguracji cech", err_msg)
            self.assertIn(forbidden, err_msg)

        # B. Test odrzucenia wszystkich trzech zabronionych kolumn jednocześnie
        with self.assertRaises(ValueError) as context:
            validate_feature_list(["day_of_week", "visits", "revenue_pln", "orders"])
        self.assertIn("Błąd konfiguracji cech", str(context.exception))

        # C. Test z poziomu prepare_training_data
        sample_df = pd.DataFrame({
            "date": ["2024-01-01"] * 248,
            "promo": [1] * 248,
            "planned_ad_spend_pln": [500.0] * 248,
            "orders": [80.0] * 248,
            "visits": [800] * 248,
            "revenue_pln": [8000.0] * 248,
            "day_of_week": [0] * 248,
            "orders_invalid": [0] * 248,
        })
        test_csv = self.temp_dir_path / "dummy_train.csv"
        sample_df.to_csv(test_csv, index=False)

        with self.assertRaises(ValueError) as context:
            prepare_training_data(train_path=test_csv, feature_cols=["day_of_week", "visits"])
        self.assertIn("Błąd konfiguracji cech", str(context.exception))

        print("\n[SUKCES] Próba 2 (Odrzucenie zabronionych cech): Próby dodania 'orders', 'visits' i 'revenue_pln' zostały bezwzględnie zablokowane z błędem ValueError.")

    def test_shared_preprocessor_transformation(self):
        """Próba 3: Jedna wspólna implementacja preprocesora przetwarza dane w sposób deterministyczny."""
        preprocessor = build_preprocessor()

        sample_X = pd.DataFrame({
            "day_of_week": [0, 4, 6],
            "promo": [0, 1, 0],
            "planned_ad_spend_pln": [300.0, np.nan, 900.0],
        })
        sample_y = pd.Series([70.0, 85.0, 95.0])

        preprocessor.fit(sample_X, sample_y)
        transformed = preprocessor.transform(sample_X)

        # Sprawdzenie wyuczonej mediany na próbce testowej: (300 + 900)/2 = 600.0
        imputer = preprocessor.named_transformers_["budget_imputer"]
        self.assertEqual(imputer.statistics_[0], 600.0)

        # Sprawdzenie braku braków danych po transformacji
        self.assertFalse(np.isnan(transformed).any())
        self.assertEqual(transformed.shape[0], 3)
        print("\n[SUKCES] Próba 3 (Wspólny potok cech): ColumnTransformer poprawnie uzupełnia braki medianą i koduje OneHot.")


if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(TestTrainingPipeline)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)

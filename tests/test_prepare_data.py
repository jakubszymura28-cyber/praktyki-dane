"""Testy jednostkowe procesu przygotowania i walidacji danych (src/prepare_data.py).

Wszystkie próby wykorzystują izolowane, tymczasowe kopie danych
i pod żadnym pozorem nie modyfikują oryginalnego pliku data/raw/orders_train_raw.csv.
"""

import sys
import tempfile
import unittest
from pathlib import Path
import numpy as np
import pandas as pd

# Dodanie katalogu głównego do sys.path, aby zaimportować moduł src
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.prepare_data import prepare_orders_train


class TestPrepareData(unittest.TestCase):
    """Zestaw prób weryfikujących reguły czyszczenia danych."""

    def setUp(self):
        """Przygotowanie tymczasowego katalogu na pliki prób."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_dir_path = Path(self.temp_dir.name)

    def tearDown(self):
        """Sprzątanie zasobów tymczasowych po wykonaniu testów."""
        self.temp_dir.cleanup()

    def test_negative_orders_marked_as_nan_with_flag(self):
        """Próba 1: Ujemne orders ma zostać oznaczone jako brak (NaN) z flagą orders_invalid=1.

        Test weryfikuje małą próbkę danych zawierającą ujemną wartość zamówień.
        """
        sample_data = pd.DataFrame({
            "date": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "promo": ["0", "1", "0"],
            "planned_ad_spend_pln": [500.0, 600.0, 700.0],
            "orders": [80.0, -5.0, 90.0],  # Wiersz 2 zawiera ujemną wartość -5.0
            "visits": [800, 750, 900],
            "revenue_pln": [8000.0, 7500.0, 9000.0]
        })

        input_csv = self.temp_dir_path / "test_negative_raw.csv"
        output_csv = self.temp_dir_path / "test_negative_cleaned.csv"
        sample_data.to_csv(input_csv, index=False, encoding="utf-8")

        # Wykonanie procesu przygotowania danych na kopii testowej
        df_result, stats = prepare_orders_train(input_path=input_csv, output_path=output_csv)

        # Weryfikacja pliku wyjściowego
        self.assertTrue(output_csv.exists(), "Plik wynikowy nie został utworzony.")
        self.assertEqual(len(df_result), 3, "Liczba wierszy powinna wynosić 3.")

        # Weryfikacja wiersza z pierwotnie poprawną wartością (indeks 0: data 2024-01-01)
        row_0 = df_result.iloc[0]
        self.assertEqual(row_0["orders"], 80.0)
        self.assertEqual(row_0["orders_invalid"], 0)

        # Weryfikacja wiersza z wartością ujemną (indeks 1: data 2024-01-02)
        row_1 = df_result.iloc[1]
        self.assertTrue(pd.isna(row_1["orders"]), "Ujemne orders powinno zostać zamienione na NaN.")
        self.assertEqual(row_1["orders_invalid"], 1, "Kolumna orders_invalid dla ujemnego orders musi wynosić 1.")

        # Weryfikacja statystyk
        self.assertEqual(stats["negative_orders_modified"], 1, "Raport powinien wskazać dokładnie 1 zmodyfikowany ujemny wiersz.")
        self.assertEqual(stats["orders_invalid_count"], 1, "Liczba flag orders_invalid powinna wynosić 1.")
        print("\n[SUKCES] Próba 1 (Ujemne orders): Wartość ujemna -5.0 poprawnie oznaczona jako NaN z flagą orders_invalid=1.")

    def test_invalid_date_raises_clear_error(self):
        """Próba 2: Niepoprawna data ma spowodować czytelny błąd ValueError.

        Test weryfikuje małą próbkę danych z uszkodzonym formatem daty.
        """
        sample_data_bad_date = pd.DataFrame({
            "date": ["2024-01-01", "niepoprawna-data-999", "2024-01-03"],
            "promo": ["0", "1", "0"],
            "planned_ad_spend_pln": [500.0, 600.0, 700.0],
            "orders": [80.0, 85.0, 90.0],
            "visits": [800, 750, 900],
            "revenue_pln": [8000.0, 7500.0, 9000.0]
        })

        input_csv = self.temp_dir_path / "test_bad_date_raw.csv"
        output_csv = self.temp_dir_path / "test_bad_date_cleaned.csv"
        sample_data_bad_date.to_csv(input_csv, index=False, encoding="utf-8")

        # Sprawdzenie, czy funkcja rzuca ValueError z czytelnym komunikatem
        with self.assertRaises(ValueError) as context:
            prepare_orders_train(input_path=input_csv, output_path=output_csv)

        err_msg = str(context.exception)
        self.assertIn("Nieoczekiwany format danych", err_msg)
        print(f"\n[SUKCES] Próba 2 (Niepoprawna data): Zgłoszono czytelny błąd ValueError -> '{err_msg}'.")


if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPrepareData)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)

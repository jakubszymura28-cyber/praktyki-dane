# Raport audytu odtwarzalności (Reproduction Audit Report)

> **📋 Metadane technicznego audytu odtwarzalności:**
> | Wymiar specyfikacji | Wartość w projekcie | Plik źródłowy / Odnośnik |
> |---|---|---|
> | **Typ procedury** | Techniczny audyt odtwarzalności potoku uczenia i predykcji | [reports/reproduction.md](reproduction.md) |
> | **Zakres weryfikacji** | Odtwarzalność przygotowania danych, treningu, zapisu wag oraz wnioskowania | [src/prepare_data.py](../src/prepare_data.py), [src/train.py](../src/train.py), [src/predict.py](../src/predict.py) |
> | **Zachowane modele** | `DecisionTreeRegressor(max_depth=3, random_state=42)` w potoku `Pipeline` | [models/selected_pipeline.joblib](../models/selected_pipeline.joblib) |
> | **Model odniesienia** | `DummyRegressor(strategy='median')` | [models/baseline_pipeline.joblib](../models/baseline_pipeline.joblib) |
> | **Wynik testu tożsamości** | **100% numeryczna zgodność metryk MAE i prognoz (`np.allclose == True`)** | Sekcja 4 i 5 |
> | **Status testu** | Sprawdzenie techniczne odtwarzalności (nie jest to nowy wynik testowy) | Sekcja 1 |
> | **Zablokowane zależności** | `scikit-learn==1.9.1`, `joblib==1.6.0`, `pandas==3.0.6`, `numpy==2.5.3` | [requirements.txt](../requirements.txt) |

---

## 1. Cel audytu i charakterystyka procedury
Niniejszy audyt stanowi **techniczne sprawdzenie odtwarzalności** całego procesu inżynierii danych i uczenia maszynowego w repozytorium.

> [!IMPORTANT]
> **Zasada niezmienności ewaluacji:**
> Odtworzenie procedury nie jest poszukiwaniem nowego, lepszego wyniku testowego ani powtórnym dobieraniem hiperparametrów na zbiorze testowym. Parametry modeli (`DecisionTreeRegressor(max_depth=3, random_state=42)` oraz `DummyRegressor(strategy='median')`) pozostały ściśle **zamrożone**. Celem audytu było zweryfikowanie, czy w nowo zainicjalizowanym lub zrekonstruowanym środowisku z tych samych danych surowych powstają identyczne artefakty, identyczne prognozy i identyczne metryki MAE.

Oryginalne modele w katalogu `models/` oraz pliki ewaluacyjne w katalogu `reports/` zostały zachowane.

---

## 2. Kolejność poleceń terminala

Aby odtworzyć pełen potok od surowych plików CSV do finalnych predykcji i metryk, należy wykonać w terminalu środowiska wirtualnego (`.venv`) następujące polecenia:

```powershell
# 1. Przygotowanie danych z zachowaniem zasady niemutowalności data/raw/
python src/prepare_data.py

# 2. Trening zamrożonych modeli oraz ewaluacja walidacyjna
python src/train.py

# 3. Wnioskowanie na zbiorze testowym z użyciem wyuczonych transformacji
python src/predict.py
```

### Rola poszczególnych etapów:
1. **`python src/prepare_data.py`**:
   - Wczytuje surowe pliki `data/raw/orders_train.csv`, `data/raw/orders_validation.csv` oraz `data/raw/orders_test.csv`.
   - Waliduje schemat (kolumny, typy, brak braków w dacie i cechach nienumerycznych).
   - Filtruje zbiór treningowy z błędnych wartości celu (`orders < 0` oraz brakujące cele), pozostawiając dokładnie 248 dni treningowych.
   - Zapisuje oczyszczone zbiory do katalogu `data/processed/` bez mutowania katalogu `data/raw/`.
2. **`python src/train.py`**:
   - Buduje potok `Pipeline([('imputer', SimpleImputer(strategy='median')), ('model', DecisionTreeRegressor(max_depth=3, random_state=42))])`.
   - Dopasowuje model wyłącznie na zbiorze treningowym `data/processed/orders_train.csv`.
   - Serializuje potok do [models/selected_pipeline.joblib](../models/selected_pipeline.joblib) oraz model bazowy do [models/baseline_pipeline.joblib](../models/baseline_pipeline.joblib).
   - Generuje metryki train/validation i zapisuje je do [reports/metrics.csv](metrics.csv).
3. **`python src/predict.py`**:
   - Wczytuje zamrożony potok z [models/selected_pipeline.joblib](../models/selected_pipeline.joblib) (bez wywoływania metody `.fit()`).
   - Przeprowadza wnioskowanie na 84 dniach zbioru testowego `data/processed/orders_test.csv`.
   - Zapisuje dobę po dobie prognozy i błędy do [reports/test_predictions.csv](test_predictions.csv) oraz dopisuje wiersze testowe do [reports/metrics.csv](metrics.csv).

---

## 3. Weryfikacja liczności prób

Zgodnie z wymogami projektowymi sprawdzono liczności wierszy we wszystkich zbiorach danych. Liczności są w 100% zgodne z założeniami:

| Zbiór danych | Ścieżka pliku | Liczność wierszy (dni) | Status poprawności celu | Rola w potoku |
|---|---|:---:|:---:|---|
| **Treningowy** | `data/processed/orders_train.csv` | **248** | 100% poprawnych ($y \ge 0$) | Wyuczenie reguł decyzyjnych i mediany imputacji |
| **Walidacyjny** | `data/processed/orders_validation.csv` | **84** | 100% obecnych | Strojenie hiperparametrów i zamrożenie modelu |
| **Testowy** | `data/processed/orders_test.csv` | **84** | 100% obecnych | Końcowa niezależna ewaluacja uogólnienia |
| **Łącznie** | — | **416** | Pełna ciągłość kalendarza | Horyzont od `2024-01-01` do `2025-02-19` |

---

## 4. Porównanie metryk MAE (Oryginał vs Odtworzenie)

W tabeli poniżej zestawiono metryki uzyskane podczas pierwotnej ewaluacji oraz po powtórnym uruchomieniu potoku w czystym procesie:

| Split / Podział | Model | Liczba dni | Oryginalne MAE [szt.] | Odtworzone MAE [szt.] | Różnica bezwzględna | Status tożsamości |
|---|---|:---:|:---:|:---:|:---:|:---:|
| **Trening** | Baseline (`DummyRegressor`) | 248 | 17.1815 | 17.1815 | 0.0000 | **100% zgodne** |
| **Trening** | Drzewo (`max_depth=3`) | 248 | 11.1093 | 11.1093 | 0.0000 | **100% zgodne** |
| **Walidacja** | Baseline (`DummyRegressor`) | 84 | 16.2143 | 16.2143 | 0.0000 | **100% zgodne** |
| **Walidacja** | Drzewo (`max_depth=3`) | 84 | 11.9503 | 11.9503 | 0.0000 | **100% zgodne** |
| **Test** | Baseline (`DummyRegressor`) | 84 | 17.8452 | 17.8452 | 0.0000 | **100% zgodne** |
| **Test** | Drzewo (`max_depth=3`) | 84 | 14.0930 | 14.0930 | 0.0000 | **100% zgodne** |

> [!NOTE]
> Zarówno błędy bezwzględne MAE, jak i zysk względem modelu odniesienia na teście (**3.7522 szt./dzień**, co odpowiada **21.03% redukcji błędu**) są w 100% powtarzalne.

---

## 5. Tożsamość prognoz testowych (Vector-Level Check)

Weryfikację zgodności wektora 84 prognoz testowych przeprowadzono na dwóch płaszczyznach:
1. **Model z pliku vs Nowo wytrenowany model:**
   - Sprawdzono prognozy wygenerowane przez zdeserializowany model [models/selected_pipeline.joblib](../models/selected_pipeline.joblib) oraz model wytrenowany od zera na świeżo załadowanych danych treningowych.
   - Wynik w Pythonie: `np.allclose(preds_saved, preds_fresh, atol=1e-12)` $\rightarrow$ **PRAWDA (`True`)**, maksymalna różnica wynosi dokładnie **0.000000000000**.
2. **Prognozy zapisane w CSV [reports/test_predictions.csv](test_predictions.csv):**
   - Kolumna `predicted_orders` w pliku CSV została sformatowana do 4 miejsc po przecinku (`np.round(..., 4)`), zgodnie z przyjętym standardem raportowania.
   - Maksymalna różnica pomiędzy wartościami z pliku CSV a surowymi wynikami zmiennoprzecinkowymi w pamięci RAM wynosi $4.76 \times 10^{-5}$ sztuki (błąd zaokrąglenia zapisu tekstowego).

---

## 6. Bezpieczeństwo deserializacji modeli (`joblib` / `pickle`)

Formaty `joblib` oraz standardowy Python `pickle` są powszechnie stosowane w ekosystemie uczenia maszynowego ze względu na prostotę serializacji złożonych struktur obiektowych biblioteki `scikit-learn`.

> [!WARNING]
> ### Podatność na Arbitrary Code Execution (RCE)
> Podczas deserializacji za pomocą `joblib.load()` lub `pickle.load()` wykonywane są niskopoziomowe instrukcje maszyny wirtualnej pickle. W złośliwie spreparowanym pliku możliwe jest przedefiniowanie metody `__reduce__()`, co prowadzi do **wykonania dowolnego kodu systemowego w powłoce użytkownika** już w ułamku sekundy podczas samego wczytywania pliku, zanim model w ogóle przystąpi do predykcji.

### Zasady bezpieczeństwa wdrożone w repozytorium:
1. **Wyłącznie własne źródła:** Nigdy nie wczytujemy plików `.joblib` lub `.pkl` pobranych z niezaufanych serwerów zewnętrznych, publicznych repozytoriów czy forów dyskusyjnych. Wczytywane są wyłącznie artefakty wytrenowane we własnym środowisku lub pochodzące z audytowanego potoku CI/CD.
2. **Weryfikacja integralności:** W środowisku produkcyjnym przed wczytaniem pliku wag zaleca się weryfikację skrótu kryptograficznego SHA-256 z zaufanym rejestrem modeli.
3. **Alternatywy bezpieczne (Safe Formats):** W przypadku udostępniania modeli stronom trzecim rekomendowane jest eksportowanie logiki do formatów niestosujących unpicklingu, np. formatu **ONNX** (Open Neural Network Exchange) lub reprezentacji czystych tabel reguł decyzyjnych w formacie JSON/PMML.

---

## 7. Specyfikacja środowiska i wersje bibliotek

Środowisko zostało zamrożone w pliku [requirements.txt](../requirements.txt). Kluczowe pakiety analityczne i ich wersje użyte podczas audytu:

| Pakiet | Zablokowana wersja | Rola w projekcie |
|---|---|---|
| **Python** | `3.13.15` (CPython, Windows x64) | Środowisko bazowe interpretera |
| **`scikit-learn`** | `1.9.1` | Implementacja modeli regresyjnych (`DecisionTreeRegressor`, `DummyRegressor`) i potoków `Pipeline` |
| **`joblib`** | `1.6.0` | Serializacja i deserializacja potoków modeli |
| **`pandas`** | `3.0.6` | Inżynieria cech, tabele danych, czyszczenie i podział zbiorów |
| **`numpy`** | `2.5.3` | Wektorowe operacje numeryczne i weryfikacja macierzowa `np.allclose` |

---

## 8. Podsumowanie audytu
- **Odtwarzalność numeryczna:** Potwierdzona w 100% dla wszystkich podziałów (train: 248, val: 84, test: 84).
- **Integralność artefaktów:** Oryginalne modele w `models/` oraz pliki raportów `reports/` pozostały nienaruszone.
- **Bezpieczeństwo operacyjne:** Udokumentowano ograniczenia deserializacji `joblib` i zasady bezpiecznego operowania wagami w środowisku analitycznym.

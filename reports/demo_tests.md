# Specyfikacja i szkic formularza demonstracyjnego (Demo Form Specification)

> **📋 Metadane specyfikacji formularza demo:**
> | Wymiar specyfikacji | Wartość w projekcie | Plik źródłowy / Odnośnik |
> |---|---|---|
> | **Cel dokumentu** | Projekt koncepcyjny formularza interaktywnego przed implementacją kodu | [reports/demo_tests.md](demo_tests.md) |
> | **Wybrany model produkcyjny** | `DecisionTreeRegressor(max_depth=3)` w potoku `Pipeline` | [models/selected_pipeline.joblib](../models/selected_pipeline.joblib) |
> | **Zgodność z kartą modelu** | 100% zgodności cech wejściowych, brak wycieku danych | [reports/model_card.md](model_card.md) |
> | **Status implementacji** | Etap projektowy (kod aplikacji nie jest jeszcze tworzony) | Sekcja 1 |

---

## 1. Szkic interfejsu użytkownika (UI Wireframe)

Formularz demonstracyjny zostanie przygotowany jako aplikacja webowa (np. z użyciem biblioteki **Streamlit**) i składa się z następujących pól:

1. **Pole wyboru daty:**
   - *Komponent interfejsu:* Pole kalendarza (`st.date_input("Wybierz prognozowaną datę (dzień jutrzejszy t+1)")`).
   - *Rola:* Użytkownik (kierownik magazynu lub planista) wskazuje konkretną datę, na którą potrzebna jest prognoza zamówień.
2. **Wybór promocji:**
   - *Komponent interfejsu:* Przełącznik wyboru opcji Tak / Nie (`st.radio("Czy na ten dzień zaplanowano promocję?", options=["Nie", "Tak"])`).
   - *Mapowanie wartości:* Wybór „Nie” odpowiada wartości numerycznej `0`, a wybór „Tak” wartości `1`.
3. **Planowany budżet reklamowy:**
   - *Komponent interfejsu:* Pole wprowadzania liczby zmiennoprzecinkowej (`st.number_input("Planowany budżet reklamowy w PLN", min_value=0.0, step=50.0, value=575.28)`).
   - *Ograniczenia i walidacja:* Wartość musi być nieujemna (`min_value=0.0`). Wartość domyślna odpowiada wyuczonej medianie treningowej (`575.275 PLN`, zaokrąglonej do 575.28 PLN).
4. **Przycisk obliczenia prognozy:**
   - *Komponent interfejsu:* Przycisk akcji (`st.button("Oblicz prognozę zamówień")`).
   - *Rola:* Po kliknięciu aplikacja waliduje wejścia i uruchamia potok wnioskowania modelu.

---

## 2. Reguły transformacji cech i ochrona przed wyciekiem danych (Guardrails)

1. **Automatyczne wyznaczanie dnia tygodnia z daty:**
   - Użytkownik nie wprowadza dnia tygodnia ręcznie. Aplikacja automatycznie kalkuluje cechę na podstawie wybranej daty za pomocą standardowej funkcji kalendarzowej (`date.weekday()`), gdzie:
     * `0` = poniedziałek, `1` = wtorek, ..., `6` = niedziela.
2. **Ściśle zdefiniowany wektor wejściowy ($X$):**
   - Do zamrożonego potoku modelu przekazywana jest wyłącznie ramka danych zawierająca 3 dopuszczone kolumny:
     ```python
     X_input = pd.DataFrame([{
         "day_of_week": date_selected.weekday(),
         "promo": 1 if promo_selected == "Tak" else 0,
         "planned_ad_spend_pln": float(ad_spend_input)
     }])
     ```
3. **Bezwzględny zakaz wprowadzania cech operacyjnych:**
   - Formularz **nie pyta i nie dopuszcza** wprowadzania pól:
     * `visits` (dzienna liczba wizyt w sklepie),
     * `revenue_pln` (dzienny przychód ze sprzedaży),
     * `orders` (rzeczywista liczba zamówień).
   - *Uzasadnienie merytoryczne:* Wszystkie te wielkości są znane dopiero po zakończeniu doby handlowej. Pytanie o nie w momencie tworzenia prognozy na dzień jutrzejszy ($t+1$) stanowiłoby niedopuszczalny wyciek danych (*Data Leakage*), fałszujący działanie systemu.

---

## 3. Wymagany format wyniku i etykiety bezpieczeństwa

1. **Prezentacja wyniku prognozy:**
   - Aplikacja wyświetla pojedynczą, punktową estymację dziennego popytu:
     > **Prognozowana liczba zamówień: X szt.** (gdzie $X$ to wartość wyznaczona przez liść drzewa decyzyjnego, np. `83.4 szt.` lub `111.1 szt.`).
2. **Brak przedziału pewności (Confidence Interval):**
   - Model `DecisionTreeRegressor` zastosowany w projekcie generuje punktową prognozę średniej. W projekcie **nie wyznaczano i nie kalkulowano przedziałów ufności ani kwantylowych**. W związku z tym interfejs celowo nie prezentuje sztucznych widełek niepewności, aby nie wprowadzać odbiorcy w błąd.
3. **Obowiązkowy komunikat informacyjny i etyczny:**
   - Bezpośrednio pod wynikiem umieszczony jest widoczny, stały komunikat:
     > **⚠️ Komunikat:** *„demo edukacyjne, dane syntetyczne”*  
     > Narzędzie powstało w celach dydaktycznych na danych syntetycznych i zgodnie z kartą modelu nie może służyć do podejmowania automatycznych decyzji kadrowych ani finansowych.

---

## 4. Porównanie szkicu z Kartą Modelu (`reports/model_card.md`)

| Wymiar specyfikacji formularza | Zapis w `reports/model_card.md` | Status zgodności |
|---|---|:---:|
| **Horyzont czasowy prognozy** | Wieczór dnia poprzedniego na dzień kolejny ($t+1$) | **100% Zgodny** (Sekcja 1) |
| **Dozwolone cechy ($X$)** | Wyłącznie `day_of_week`, `promo`, `planned_ad_spend_pln` | **100% Zgodny** (Sekcja 3 i 8.1) |
| **Wykluczenia cech operacyjnych** | Zakaz użycia `visits` i `revenue_pln` ze względu na wyciek | **100% Zgodny** (Sekcja 3 i 8.1) |
| **Typ predykcji** | Punktowa predykcja regresyjna z liścia drzewa | **100% Zgodny** (Sekcja 6) |
| **Brak przedziału pewności** | Brak estymacji przedziałowej w metrics.csv i model_card | **100% Zgodny** (Sekcja 6 i 11) |
| **Ostrzeżenie etyczne i operacyjne** | Zakaz automatycznych decyzji kadrowych, dane syntetyczne | **100% Zgodny** (Sekcja 12) |

---

## 5. Zestawienie sześciu prób demonstracyjnych formularza (Manual Testing Log)

Zgodnie z procedurą sprawdzono empiryczny zakres budżetu ze zbioru treningowego (`150.65 PLN` do `999.71 PLN`, mediana `575.28 PLN`). Przeprowadzono 6 kontrolowanych prób w lokalnym interfejsie:

| Przypadek | Wpisana data / promocja / budżet | Oczekiwane zachowanie | Rzeczywisty wynik (prognoza lub komunikat) | Ocena |
|---|---|---|---|:---:|
| **1. Poprawny dzień bez promocji** | Data: `2024-12-02` (Poniedziałek, DOW=0)<br>Promocja: `Nie` (0)<br>Budżet: `500.00 PLN` | Poprawne obliczenie punktowej prognozy popytu bez ostrzeżeń i błędów. | **Prognoza: 83.4 szt.** (`83.4118`) | **Zaliczone (1)** |
| **2. Poprawny dzień z promocją** | Data: `2024-12-04` (Środa, DOW=2)<br>Promocja: `Tak` (1)<br>Budżet: `850.00 PLN` | Poprawne obliczenie wyższej prognozy z uwzględnieniem akcji promocyjnej i wyższego budżetu. | **Prognoza: 111.1 szt.** (`111.0667`) | **Zaliczone (1)** |
| **3. Budżet 0 (Zero nie jest brakiem)** | Data: `2024-12-08` (Niedziela, DOW=6)<br>Promocja: `Nie` (0)<br>Budżet: `0.00 PLN` | Poprawne wykonanie prognozy z zerowym budżetem; brak traktowania zera jako braku danych; brak imputacji. | **Prognoza: 64.3 szt.** (`64.2537`) | **Zaliczone (1)** |
| **4. Brak budżetu (Imputacja medianą)** | Data: `2024-12-02` (Poniedziałek, DOW=0)<br>Promocja: `Nie` (0)<br>Budżet: Zaznaczono *Brak danych o budżecie* (`None`) | Komunikat o użyciu wyuczonej mediany treningowej (575.28 PLN) oraz obliczenie prognozy z automatyczną imputacją w potoku. | Komunikat: *„ℹ️ Brak wpisu budżetu: Zastosowano wyuczoną medianę treningową (575.28 PLN) z potoku”*<br>**Prognoza: 83.4 szt.** (`83.4118`) | **Zaliczone (1)** |
| **5. Budżet ujemny (Walidacja błędu)** | Data: `2024-12-05` (Czwartek, DOW=3)<br>Promocja: `Nie` (0)<br>Budżet: `-50.00 PLN` | Odrzucenie wartości ujemnej, zatrzymanie procesu wnioskowania i wyświetlenie czytelnego komunikatu błędu walidacji. | Komunikat błędu: *„❌ Błąd walidacji: Planowany budżet reklamowy nie może być ujemny! Proszę podać wartość >= 0.”* (brak prognozy) | **Zaliczone (1)** |
| **6. Bardzo wysoki budżet spoza treningu** | Data: `2024-12-04` (Środa, DOW=2)<br>Promocja: `Tak` (1)<br>Budżet: `5000.00 PLN` *(zakres treningu: max 999.71 PLN)* | Ostrzeżenie o ekstrapolacji poza zakres treningowy oraz zastosowanie reguły decyzyjnej najwyższego liścia drzewa. | Ostrzeżenie: *„⚠️ Ostrzeżenie o ekstrapolacji: Wprowadzony budżet (5000.00 PLN) przekracza maksymalną wartość ze zbioru treningowego (999.71 PLN)...”*<br>**Prognoza: 111.1 szt.** (`111.0667`) | **Zaliczone (1)** |

- **Podsumowanie prób:** Wszystkie **6 z 6 prób (100.0%)** zakończyły się sukcesem zgodnie ze zdefiniowanymi regułami. Nie stwierdzono rozbieżności wymagających poprawek.


---

## 6. Porównanie trzech prognoz z rzeczywistym zbiorem testowym (`reports/test_predictions.csv`)

Zestawiono prognozy wygenerowane przez aplikację formularza z rzeczywistymi zamówieniami odnotowanymi w zbiorze testowym:

| Data (`date`) | Dzień tygodnia | Promocja (`promo`) | Budżet testowy | Prognoza z formularza ($\hat{y}$) | Rzeczywistość testu ($y$) | Błąd bezwzględny ($|y - \hat{y}|$) | Status zgodności z plikiem CSV |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **2024-12-02** | Poniedziałek (`0`) | `0` (Nie) | `502.82 PLN` | **83.4118 szt.** | **88.0 szt.** | **4.5882 szt.** | Identyczny z `test_predictions.csv` (wiersz 2) |
| **2024-12-03** | Wtorek (`1`) | `0` (Nie) | `631.18 PLN` | **83.4118 szt.** | **106.0 szt.** | **22.5882 szt.** | Identyczny z `test_predictions.csv` (wiersz 3) |
| **2024-12-04** | Środa (`2`) | `1` (Tak) | `834.78 PLN` | **111.0667 szt.** | **127.0 szt.** | **15.9333 szt.** | Identyczny z `test_predictions.csv` (wiersz 4) |

- **Średnie MAE z 3 dni:** $\frac{4.5882 + 22.5882 + 15.9333}{3} = \frac{43.1097}{3} = \mathbf{14.3699}\text{ szt./dzień}$.
- **Wniosek:** Aplikacja demonstracyjna `app.py` generuje prognozy w 100% tożsame z oficjalną ewaluacją testową zapisaną w `reports/test_predictions.csv`.

---

## 7. Porównanie niezaokrąglonych prognoz (Tolerancja $\le 0.000001$ zamówienia)

Zgodnie z procedurą kontrolną zweryfikowano w terminalu IDE niezaokrąglone wartości zmiennoprzecinkowe (surowy typ `float64`) prognoz generowanych bezpośrednio przez model produkcyjny z potoku oraz funkcję `predict_single_day` z modułu [src/predict.py](../src/predict.py) dla 3 poprawnych wejść z tabeli prób (bez ponownego trenowania):

| Wejście testowe | Parametry wejściowe | Surowa prognoza modelu z potoku | Prognoza `predict_single_day` | Różnica bezwzględna | Status tolerancji ($\le 10^{-6}$) |
|---|---|:---:|:---:|:---:|:---:|
| **Wejście 1** (Poniedziałek, brak promo) | Data: `2024-12-02`<br>Promo: `0`<br>Budżet: `500.00 PLN` | **83.411764705882** | **83.411764705882** | **0.000000000000** | **Zaliczone (PRAWDA)** |
| **Wejście 2** (Środa, promocja) | Data: `2024-12-04`<br>Promo: `1`<br>Budżet: `850.00 PLN` | **111.066666666667** | **111.066666666667** | **0.000000000000** | **Zaliczone (PRAWDA)** |
| **Wejście 3** (Niedziela, budżet 0) | Data: `2024-12-08`<br>Promo: `0`<br>Budżet: `0.00 PLN` | **64.253731343284** | **64.253731343284** | **0.000000000000** | **Zaliczone (PRAWDA)** |

- **Wniosek numeryczny:** Dla wszystkich trzech wejść różnica bezwzględna wynosi dokładnie **0.000000000000**, co w 100% spełnia rygorystyczny warunek tolerancji $0.000001$ ($10^{-6}$) zamówienia.

---

## 8. Dwie kontrole odporności na błędy (Error Handling Controls)

Przeprowadzono formalne testy odporności systemu na awarie wejść i zasobów, weryfikując, że błąd jest jawnie raportowany jako błąd, bez zwracania fikcyjnej prognozy `0`:

### 8.1. Kontrola błędu 1: Wskazanie nieistniejącego pliku modelu
- **Warunek testowy:** Próba załadowania modelu ze sztucznej, nieistniejącej ścieżki `models/non_existent_pipeline.joblib` (bez usuwania ani naruszania oryginalnych wag `models/selected_pipeline.joblib`).
- **Oczekiwane zachowanie:** Natychmiastowe przerwanie operacji wnioskowania i zgłoszenie wyjątku braku pliku. Zakaz zwracania domyślnego zera.
- **Rzeczywisty rezultat w terminalu / aplikacji:**
  ```text
  FileNotFoundError: Nie znaleziono pliku modelu produkcyjnego: models\non_existent_pipeline.joblib
  ```
- **Ocena:** **Zaliczone (1)** – błąd został obsłużony wprost, proces bezpiecznie zatrzymany, brak fałszywych predykcji. Działająca konfiguracja produkcyjna pozostała nienaruszona.

### 8.2. Kontrola błędu 2: Przekazanie niepoprawnego formatu daty
- **Warunek testowy:** Przekazanie uszkodzonego ciągu znaków daty `'niepoprawna-data-999'` bezpośrednio do funkcji wnioskującej `predict_single_day`.
- **Oczekiwane zachowanie:** Wykrycie niepoprawnego formatu daty, odrzucenie wejścia i zgłoszenie błędu walidacji `ValueError`. Zakaz cichego przypisywania zera.
- **Rzeczywisty rezultat w terminalu / aplikacji:**
  ```text
  ValueError: Niepoprawny format daty: 'niepoprawna-data-999' (szczegóły: Unknown datetime string format, unable to parse: niepoprawna-data-999)
  ```
- **Ocena:** **Zaliczone (1)** – funkcja walidująca rygorystycznie odrzuca nieprawidłowy format daty i uniemożliwia wygenerowanie fałszywego wyniku.

---

## 9. Ograniczenia prezentowane pod wynikiem oraz audyt braku treningu i braku usług AI

### 9.1. Treść ograniczeń prezentowana pod wynikiem w formularzu (`app.py`)
Pod każdym obliczonym wynikiem predykcji w interaktywnym formularzu wyświetlana jest bezpośrednio stała notatka o jednostce, danych i etyce:
> **⚠️ Ograniczenia i jednostka wyniku:**  
> - **Jednostka:** zamówienia `[szt.]` (dzienna łączna liczba złożonych i zrealizowanych zamówień/paczek).  
> - **Źródło danych:** model korzysta wyłącznie z danych syntetycznych.  
> - **Zakaz automatycznych decyzji:** prognoza nie służy do podejmowania automatycznych decyzji kadrowych (zatrudnianie, zwalnianie, obsada magazynu, premie) ani finansowych.  
> *(Wartość niezaokrąglona zachowana do celów audytu, porównań i wyznaczania MAE: np. `83.41176471` szt.)*

### 9.2. Wskazanie w kodzie: Skąd aplikacja wczytuje model?
1. **W pliku [app.py](../app.py):**
   - W liniach 34–37 model jest pobierany z pamięci podręcznej sesji Streamlit za pomocą funkcji:
     ```python
     @st.cache_resource(show_spinner="Wczytywanie zamrożonego potoku produkcyjnego...")
     def get_model():
         return load_production_model()
     ```
2. **W module [src/predict.py](../src/predict.py):**
   - W liniach 193–204 funkcja `load_production_model()` wskazuje bezpośrednią, lokalną ścieżkę do zamrożonego pliku wag:
     ```python
     resolved_models_dir = resolve_path(MODELS_DIR)
     model_path = resolved_models_dir / "selected_pipeline.joblib"
     pipeline = joblib.load(model_path)
     return pipeline
     ```
   - Model jest wczytywany wyłącznie z lokalnego artefaktu `models/selected_pipeline.joblib`.

### 9.3. Wynik kontroli: Dowód braku treningu (`.fit()`) oraz braku zewnętrznych usług AI
Przeprowadzono audyt kodu całej ścieżki wnioskowania aplikacji (`app.py` $\rightarrow$ `src/predict.py` $\rightarrow$ `models/selected_pipeline.joblib`):
1. **Brak wywołania `.fit()` i `.fit_transform()`:**
   - W całym module `app.py` oraz w funkcji wnioskowania `predict_single_day()` wywoływana jest wyłącznie metoda `model.predict(X_single)`.
   - Obiekt `selected_pipeline` jest wczytywany jako uprzednio dopasowany potok. Podczas generowania prognoz wagi modelu ani reguły podziału nie ulegają jakiejkolwiek modyfikacji.
2. **Brak ponownego przeliczania statystyk imputera:**
   - W przypadku braku budżetu imputer korzysta ze statystyki `budget_imputer.statistics_[0] = 575.275 PLN` wyuczonej na etapie treningu. Żadna nowa mediana nie jest estymowana z danych wejściowych użytkownika.
3. **Brak zewnętrznych usług AI i połączeń sieciowych:**
   - Wnioskowanie odbywa się w 100% lokalnie na procesorze (CPU) w środowisku Pythona, bez użycia zewnętrznych modeli językowych (LLM), API czy endpointów chmurowych.
   - Narzędzie jest w pełni offline'owym modelem regresyjnym biblioteki `scikit-learn` (`DecisionTreeRegressor`).




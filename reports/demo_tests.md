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


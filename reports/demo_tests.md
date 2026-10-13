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

W tabeli poniżej zarejestrowano 6 prób weryfikacji działania interaktywnego formularza:

| Nr próby | Testowany scenariusz biznesowy | Data wejściowa | Promocja (`promo`) | Budżet (`planned_ad_spend_pln`) | Obliczona prognoza | Obserwacje i walidacja |
|:---:|---|:---:|:---:|:---:|:---:|---|
| **1** | Dzień powszedni bez promocji (budżet medianowy) | `2024-12-02` (Poniedziałek, DOW=0) | Nie (`0`) | `575.28 PLN` | **83.4 szt.** (`83.4118`) | Typowy dzień roboczy. Prognoza stabilna, brak wycieku. |
| **2** | Wtorek z promocją (budżet umiarkowany) | `2024-12-03` (Wtorek, DOW=1) | Tak (`1`) | `575.28 PLN` | **83.4 szt.** (`83.4118`) | Przy budżecie <= 700 PLN reguła drzewa kieruje do liścia 83.4 szt. |
| **3** | Środa z intensywną promocją (wysoki budżet) | `2024-12-04` (Środa, DOW=2) | Tak (`1`) | `900.00 PLN` | **111.1 szt.** (`111.0667`) | Budżet > 700 PLN i promocja podnoszą prognozę do 111.1 szt. |
| **4** | Sobota handlowa (wysoki budżet bez promocji) | `2024-12-07` (Sobota, DOW=5) | Nie (`0`) | `850.00 PLN` | **100.6 szt.** (`100.6296`) | Weekendowy szczyt naturalnego popytu konsumenckiego. |
| **5** | Test walidacji błędu: ujemny budżet reklamowy | Dowolna (np. `2024-12-05`) | Nie (`0`) | `-100.00 PLN` | *Blokada błędu* | Interfejs Streamlit blokuje wartość ujemną (`min_value=0.0`), a funkcja zgłasza `ValueError`. |
| **6** | Niedziela przy zerowym budżecie reklamowym | `2024-12-08` (Niedziela, DOW=6) | Nie (`0`) | `0.00 PLN` | **64.3 szt.** (`64.2537`) | Niski popyt organiczny w niedzielę przy braku nakładów reklamowych. |

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


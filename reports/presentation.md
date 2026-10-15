# Szkic Prezentacji Końcowej (reports/presentation.md)

*Projekt: Praktyki – Analiza Danych i Modelowanie ML w E-commerce*  
*Czas wystąpienia: ok. 7 minut (przećwiczony na głos)*  
*Autor: Jakub Szymura*

---

## 1. Problem biznesowy i operacyjny (ok. 1 min)

### Kontekst biznesowy i cel projektu
- **Wyzwanie magazynu:** Magazyn e-commerce potrzebuje codziennej, wiarygodnej prognozy popytu (liczba zamówień/paczek do skompletowania) na dzień jutrzejszy ($t+1$).
- **Zastosowanie operacyjne:** Prognoza generowana wieczorem w dniu $t$ służy kierownikowi logistyki do zaplanowania grafiku pracy i obsady stanowisk pakowania na dzień jutrzejszy.
- **Dobór metryki sukcesu:** Średni błąd bezwzględny (**MAE** [szt./dzień]). W przeciwieństwie do MSE/RMSE, MAE mierzy błąd w naturalnych jednostkach biznesowych (1 jednostka MAE = 1 paczka niedoszacowana lub przeszacowana), co bezpośrednio przekłada się na roboczogodziny personelu magazynowego.

### Odpowiedź na pytanie kluczowe: *„Dlaczego nie używamy visits?”*
> **Odpowiedź inżynierska:** Liczba wizyt w sklepie (`visits`) w danym dniu jest zmienną operacyjną znaną dopiero **po zakończeniu dnia** (*post-factum*). Wieczorem w dniu $t$, gdy tworzymy harmonogram na jutro ($t+1$), liczba wejść na stronę w dniu jutrzejszym jest fizycznie niedostępna. Włączenie `visits` do cech modelu stanowiłoby krytyczny wyciek danych (**Data Leakage**). Taki model wykazywałby sztucznie wysokie wyniki w testach laboratoryjnych, lecz w środowisku produkcyjnym byłby całkowicie bezużyteczny, ponieważ wymagałby zgadywania liczby odwiedzin przed uruchomieniem predykcji.

### Pokazywane artefakty i źródła
- [`reports/model_card.md`](model_card.md) – Sekcja 1 i 2 (założenia problemu, definicja horyzontu $t+1$, wykluczenie cech post-factum).
- [`README.md`](../README.md) – Sekcja 1 (cel projektu i reżim operacyjny).

### Podział odpowiedzialności i kompetencji
- **Co przygotował asystent AI:** Propozycję szablonu opisu problemu biznesowego oraz wstępny konspekt karty modelu.
- **Co sam zdecydowałem i sprawdziłem:**
  - Zdefiniowałem ścisły horyzont decyzyjny $t+1$ (wieczór przed dniem realizacji).
  - Wybrałem MAE jako wiodącą metrykę biznesową z uwagi na bezpośrednią interpretację kosztową w logistyce.
  - Zdecydowałem o bezwzględnym zablokowaniu kolumn `visits` oraz `revenue_pln` w całym potoku.
- **Czego jeszcze nie umiem:** Zaawansowanego modelowania bayesowskiego uwzględniającego probabilistyczne rozkłady niepewności w symulacji kosztów nadmiarowości i braków kadrowych magazynu.

---

## 2. Dane i kontrola jakości (ok. 1.5 min)

### Horyzont danych i architektura podziału
- **Całkowity horyzont danych:** 420 dni kalendarzowych (`2024-01-01` do `2025-02-23`).
- **Rozłączny podział sekwencyjny (bez tasowania / *no shuffle*):**
  - **Zbiór treningowy:** 252 dni kalendarzowe (`2024-01-01` do `2024-09-08`), 248 poprawnych wierszy do modelowania.
  - **Zbiór walidacyjny:** 84 dni kalendarzowe (`2024-09-09` do `2024-12-01`), 100% poprawnych celów.
  - **Zbiór testowy:** 84 dni kalendarzowe (`2024-12-02` do `2025-02-23`), 100% poprawnych celów.
- **Zasada nienaruszalności danych surowych:** Pliki w katalogu `data/raw/` pozostają wyłącznie w trybie do odczytu (*read-only*).

### Zasada Single Source of Truth (`src/prepare_data.py`) i reguły jakości
- **Deduplikacja:** Wykryto i usunięto 3 identyczne zdublowane wiersze z końca pliku `orders_train_raw.csv` (`2024-01-31`, `2024-05-30`, `2024-08-18`).
- **Obsługa anomalii popytu:** Zamówienia są wielkością dyskretną $\ge 0$. Wartości ujemne (`-5.0`) oraz ułamkowe (`12.5`) oznaczono flagą jakości `orders_invalid = 1` i zamieniono na `NaN`, chroniąc modele przed zniekształceniem. **Brak globalnej imputacji w plikach CSV** – zbiory `processed` zachowują rzetelny stan braków.
- **Reguła Fail-Fast:** Wystąpienie wartości nieliczbowych w kolumnach numerycznych lub ujemnego budżetu reklamowego natychmiast przerywa wykonanie błędem `ValueError`.
- **Integracja kalendarza:** Bezpieczne dołączenie `calendar.csv` bez zwielokrotnienia wierszy (*fan-out*).

### Pokazywane artefakty i źródła
- [`reports/quality.md`](quality.md) – Tabela porównawcza przed/po czyszczeniu (252 wiersze $\to$ 248 poprawnych).
- [`data/raw/orders_train_raw.csv`](../data/raw/orders_train_raw.csv) oraz [`data/processed/orders_train.csv`](../data/processed/orders_train.csv).
- [`tests/test_prepare_data.py`](../tests/test_prepare_data.py) – Zestaw 6 automatycznych testów jednostkowych pytest.

### Podział odpowiedzialności i kompetencji
- **Co przygotował asystent AI:** Początkowy zarys funkcji czyszczącej w pandas oraz 2 proste testy asercji.
- **Co sam zdecydowałem i sprawdziłem:**
  - Samodzielnie otworzyłem surowy plik CSV i zidentyfikowałem przyczynę ubytku 3 zamówień (fizyczne duplikaty wierszy).
  - Wdrożyłem zasadę *Single Source of Truth* – zlikwidowałem podwójne złączanie kalendarza w notatnikach.
  - Rozbudowałem testy w `test_prepare_data.py` do 6 przypadków brzegowych (w tym walidacja ujemnego/tekstowego budżetu i tekstowych zamówień).
  - Narzuciłem zakaz globalnej imputacji medianą w plikach CSV i bazie SQLite.
- **Czego jeszcze nie umiem:** Automatycznego wdrażania zaawansowanych kontraktów danych w czasie rzeczywistym przy użyciu narzędzi takich jak Great Expectations lub Pandera.

---

## 3. Analiza eksploracyjna danych (EDA) (ok. 1.5 min)

### Kluczowe fakty z eksploracji
1. **Szereg czasowy popytu:**
   - Średnia dzienna sprzedaż wynosi **84.41 szt./dzień** (suma: **20 933.0 szt.** na przestrzeni 248 dni treningowych).
   - Wykres szeregu czasowego ujawnia wyraźne piki wolumenu w dniach akcji promocyjnych.
2. **Silna sezonowość tygodniowa (Dni tygodnia):**
   - **Sobota** jest dniem o najwyższej sprzedaży: średnia **105.19 szt./dzień** ($N=36$ dni).
   - **Poniedziałek** notuje najniższy wolumen: średnia **72.71 szt./dzień** ($N=35$ dni).
   - Różnica sobota vs poniedziałek wynosi **+32.48 szt./dzień** (+44.7%).
3. **Wpływ zaplanowanych promocji:**
   - Dni z promocją (`promo=1`): średnia **103.47 szt./dzień** ($N=51$).
   - Dni bez promocji (`promo=0`): średnia **79.47 szt./dzień** ($N=197$).
   - Wzrost o **+24.00 szt./dzień** (+30.2% w okresie promocji).
4. **Rozkład zamówień:**
   - Rozkład jest symetryczny i jednomodalny (średnia 84.41 szt., mediana 85.00 szt., skośność bliska 0). Ponad połowa dni mieści się w przedziale 70–100 sztuk.

### Rygor analityczny: Korelacja vs Przyczynowość
W raporcie analitycznym wyraźnie zaznaczono, że współwystępowanie promocji z wyższą sprzedażą ma charakter **korelacyjny**. Ponieważ promocje mogły być celowo planowane w dni o naturalnie wyższym potencjale (np. weekendy), bez kontrolowanego eksperymentu A/B nie można przypisać całego efektu wyłącznie samej fladze promocyjnej.

### Pokazywane artefakty i źródła
- [`reports/orders_by_date.png`](orders_by_date.png) – Wykres szeregu czasowego zamówień treningowych.
- [`reports/orders_by_weekday.png`](orders_by_weekday.png) – Wykres słupkowy średniej sprzedaży wg dni tygodnia (pełna oś Y od 0).
- [`reports/orders_histogram.png`](orders_histogram.png) – Histogram rozkładu zamówień z nałożoną krzywą KDE.
- [`reports/by_weekday.csv`](by_weekday.csv) oraz [`reports/by_promo.csv`](by_promo.csv) – Tabela agregacji średnich i sum.
- [`sql/queries.sql`](../sql/queries.sql) – Zapytania SQL potwierdzające sumę 20 933.0 szt. w bazie `orders.sqlite`.

### Podział odpowiedzialności i kompetencji
- **Co przygotował asystent AI:** Szablon zapytań SQL oraz kod wykresów w matplotlib/seaborn.
- **Co sam zdecydowałem i sprawdziłem:**
  - Naprawiłem błąd `KeyError: 'day_of_week'` w `notebooks/02_analysis.ipynb`, opierając notatnik na oczyszczonym zbiorze z `src/prepare_data.py`.
  - Wymusiłem rozpoczęcie osi Y od zera na wykresie dni tygodnia, aby uniknąć wizualnej manipulacji skalą różnic.
  - Zweryfikowałem tożsamość sumy zamówień (20 933.0 szt.) pomiędzy zapytaniami SQL w SQLite a agregacjami w pandas.
- **Czego jeszcze nie umiem:** Zaawansowanej dekompozycji szeregów czasowych metodami STL (Seasonal and Trend decomposition using Loess) oraz modelowania kointegracji.

---

## 4. Baseline, potok modelowania i ewaluacja testowa (ok. 1.5 min)

### Potok inżynierii cech (`ColumnTransformer`)
- **Dozwolone cechy wejściowe na dzień $t+1$:** `day_of_week` (kategoria kalendarzowa), `promo` (flaga planu), `planned_ad_spend_pln` (planowany budżet reklamowy).
- **Struktura preprocesora:**
  - `SimpleImputer(strategy='median')`: wylicza medianę budżetu reklamowego **wyłącznie na zbiorze treningowym** (**575.275 PLN**). Brak wycieku danych z walidacji i testu.
  - `OneHotEncoder(handle_unknown='ignore')`: kodowanie 7 kategorii dni tygodnia.
  - `passthrough`: przekazanie binarnej flagi promocji.
- **Zamrożony artefakt:** Zapisany do pliku [`models/selected_pipeline.joblib`](../models/selected_pipeline.joblib).

### Zestawienie i porównanie modeli
| Model | Rola w projekcie | MAE Trening [szt.] | MAE Walidacja [szt.] | Redukcja błędu |
|---|---|:---:|:---:|:---:|
| **DummyRegressor (mediana)** | Model odniesienia (Baseline) | 17.1815 | 16.2143 | *Punkt odniesienia* |
| **DecisionTreeRegressor (max_depth=3)** | Model produkcyjny (Pipeline) | 11.1093 | **11.9503** | **-26.30%** (-4.26 szt.) |

Model drzewa decyzyjnego o ograniczonej głębokości (`max_depth=3`) cechuje się stabilnym uogólnieniem (luka generalizacji train-val wynosi jedynie 0.84 szt./dzień), eliminując ryzyko przeuczenia.

### Niezależna ewaluacja testowa (`src/predict.py`)
- Ostateczny pomiar wykonano na odłożonym oknie testowym (84 dni: `2024-12-02` do `2025-02-23`).
- **Czyste wnioskowanie:** Użycie wyłącznie metody `.predict()`, bez wywołania `.fit()` i bez ponownego przeliczania preprocesora.
- **Wyniki na teście:**
  - Baseline MAE: **17.8452 szt./dzień**,
  - Model kandydujący MAE: **14.0930 szt./dzień** (redukcja błędu o **3.75 szt./dzień**, czyli o **21.03%**).
- **Audyt odtwarzalności:** Ponowne uruchomienie potoku w `reports/reproduction.md` wykazało różnicę MAE = **0.0000 szt.** (100% determinizm numeryczny).

### Odpowiedź na pytanie kluczowe: *„Czy wynik dowodzi działania w prawdziwym sklepie?”*
> **Odpowiedź inżynierska:** Uzyskany wynik dowodzi skuteczności modelu i poprawnego uogólnienia na **syntetycznym zbiorze testowym o kontrolowanej dynamice**, ale **nie stanowi jeszcze wystarczającego dowodu na bezawaryjne działanie w warunkach prawdziwego sklepu internetowego**. W rzeczywistym e-commerce występują zjawiska nieobecne w danych treningowych: nagłe wyczerpanie zapasów (*out-of-stock*), agresywne kampanie konkurencji, awarie bramek płatniczych, sezonowości roczne (np. Black Friday, przedświąteczny szczyt) oraz dynamiczne zmiany cen. Wdrożenie produkcyjne wymagałoby pilotażu w trybie cienia (*shadow deployment*), testu A/B oraz ciągłego monitorowania dryfu modelu (*data drift*).

### Pokazywane artefakty i źródła
- [`reports/metrics.csv`](metrics.csv) – Precyzyjne zestawienie MAE i RMSE dla zbioru treningowego, walidacyjnego i testowego.
- [`reports/test_predictions.csv`](test_predictions.csv) – Zapis jednostkowych prognoz na oknie testowym.
- [`reports/reproduction.md`](reproduction.md) – Protokół audytu odtwarzalności (różnice = 0.0000).
- [`tests/test_training.py`](../tests/test_training.py) – 3 testy jednostkowe blokady cech zabronionych i determinizmu.

### Podział odpowiedzialności i kompetencji
- **Co przygotował asystent AI:** Kod szkieletowy potoku w scikit-learn oraz wstępną konfigurację modeli.
- **Co sam zdecydowałem i sprawdziłem:**
  - Wybrałem ograniczenie głębokości drzewa (`max_depth=3`), odrzucając zbyt skomplikowane sieci i głębokie drzewa wykazujące overfitting.
  - Zaimplementowałem mechanizm obronny w `src/train.py` i `src/predict.py` rzucający `ValueError` przy próbie podania `visits`.
  - Sprawdziłem zgodność liczb w karcie modelu z plikiem `metrics.csv`.
- **Czego jeszcze nie umiem:** Zaawansowanego strojenia modeli boostingowych (XGBoost / LightGBM / CatBoost) przy użyciu optymalizacji bayesowskiej (Optuna) z walidacją krzyżową kroczącą w czasie (*TimeSeriesSplit*).

---

## 5. Aplikacja demonstracyjna, ograniczenia i audyt AI (ok. 1.5 min)

### Interaktywna aplikacja demonstracyjna Streamlit (`app.py`)
- **Działanie:** Uruchamiana lokalnie (`http://127.0.0.1:8501`), pozwala dyspozytorowi wprowadzić dzień tygodnia, planowaną promocję oraz budżet reklamowy i natychmiast otrzymać zaokrągloną prognozę popytu na jutro.
- **Wbudowane mechanizmy bezpieczeństwa:**
  - **Obsługa braków:** Jeśli użytkownik nie zna budżetu, aplikacja automatycznie wstawia wyuczoną medianę treningową (**575.28 PLN**) z wyraźnym komunikatem ostrzegawczym.
  - **Ostrzeżenie o ekstrapolacji:** Wprowadzenie budżetu powyżej 1500 PLN wyświetla ostrzeżenie o wyjściu poza zakres obserwacji treningowych.
  - **Panel ograniczeń:** Pod wynikiem prognozy wyświetlane są założenia modelu i zakaz ekstrapolacji.
- **Zweryfikowane scenariusze testowe ([`reports/demo_tests.md`](demo_tests.md)):**
  1. *Dzień standardowy:* Wtorek, brak promocji, budżet 500 PLN $\to$ prognoza: **73 sztuki**.
  2. *Wysoka promocja:* Sobota, promocja aktywna, budżet 2000 PLN $\to$ prognoza: **125 sztuk** + żółte ostrzeżenie o ekstrapolacji.
  3. *Brak informacji o budżecie:* Czwartek, promocja, brak budżetu $\to$ prognoza: **113 sztuk** z adnotacją o użyciu mediany 575.28 PLN.

### Ograniczenia wdrożeniowe modelu
1. **Horyzont predykcji:** Wyłącznie jeden dzień do przodu ($t+1$). Model nie obsługuje planowania tygodniowego ani miesięcznego.
2. **Brak zmiennych makro:** Brak uwzględnienia czynników pogodowych, inflacji oraz stanów magazynowych poszczególnych indeksów towarowych (SKU).

### Audyt rzetelności współpracy z Generative AI ([`reports/ai_evaluation.md`](ai_evaluation.md))
- **Odporność na ataki wstrzykiwania poleceń (Prompt Injection):** Próba 6 z ukrytą instrukcją ignorowania reguł w wierszu CSV została zneutralizowana – agent potraktował treść wyłącznie jako pasywne dane.
- **Wykrycie halucynacji w Próbie 4 (Kluczowa lekcja praktyk):**
  - Asystent poprawnie odmówił estymacji przychodu z marca 2026 r., ale podał błędną datę końcową zbioru testowego (`19.02.2025` zamiast faktycznej `23.02.2025` w `orders_test.csv`).
  - Dzięki weryfikacji w pliku źródłowym błąd został natychmiast wykryty, punktacja próby obniżona do **0/1**, a łączna nota asystenta ustalona na rzetelne **5/6 (83.3%)**.
- **Wdrożenie 5 Zasad Bezpiecznej Współpracy z AI:**
  1. Podaję tylko dozwolone dane, 2. Zlecam mały zakres, **3. Sprawdzam źródła**, 4. Niezależnie kontroluję wynik, 5. Zatwierdzam działania przed wykonaniem.

### Pokazywane artefakty i źródła
- [`app.py`](../app.py) – Kod źródłowy aplikacji demonstracyjnej.
- [`reports/demo.png`](demo.png) – Zrzut ekranu działającego interfejsu Streamlit.
- [`reports/demo_tests.md`](demo_tests.md) – Protokół 3 manualnych scenariuszy testowych.
- [`reports/ai_evaluation.md`](ai_evaluation.md) – Raport ewaluacji asystenta AI i odporności na Prompt Injection.

### Podział odpowiedzialności i kompetencji
- **Co przygotował asystent AI:** Bazowy kod interfejsu Streamlit oraz szkic testów wstrzykiwania promptu.
- **Co sam zdecydowałem i sprawdziłem:**
  - Wprowadziłem logikę ostrzeżeń o ekstrapolacji budżetu oraz automatyczną imputację mediany.
  - Wykonałem i udokumentowałem 3 scenariusze testowe w pliku `demo_tests.md`.
  - Samodzielnie zweryfikowałem odpowiedź asystenta w surowym pliku `orders_test.csv`, wykryłem halucynację daty granicznej i obniżyłem ocenę w audycie AI.
- **Czego jeszcze nie umiem:** Konteneryzacji aplikacji w Dockerze, konfiguracji serwera produkcyjnego Nginx z certyfikatem SSL i wdrożenia w chmurze (AWS/GCP/Azure) z uwierzytelnianiem OAuth2.

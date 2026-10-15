# Szkic Prezentacji Końcowej: Praktyki – Analiza Danych i Modelowanie ML

Dokument zawiera konspekt 10 slajdów prezentacji podsumowującej realizację projektu analitycznego, wdrożenia potoku danych, modelowania uczenia maszynowego oraz ewaluacji współpracy z asystentami AI.

---

## Slajd 1: Tytuł, cel praktyk i stos technologiczny
* **Tytuł:** Zautomatyzowany potok analizy danych, modelowania predykcyjnego i bezpiecznej integracji AI w e-commerce.
* **Autor:** Jakub Szymura
* **Opiekun praktyk:** Zespół dydaktyczny / Analityk wiodący
* **Cel praktyk:**
  - Opanowanie warsztatu analitycznego w środowisku Python i powłoce PowerShell na systemie Windows 10,
  - Zaprojektowanie i wdrożenie powtarzalnego potoku przetwarzania danych od surowego pliku CSV do aplikacji produkcyjnej,
  - Zbudowanie modelu predykcyjnego popytu ($t+1$) z rygorystyczną ochroną przed wyciekiem danych,
  - Opanowanie metodyki krytycznej ewaluacji i bezpiecznej współpracy z modelami Generative AI (Prompt Hygiene).
* **Główne technologie:** Python 3.13/3.14+, `pandas`, `numpy`, `scikit-learn`, `sqlite3`, `matplotlib`, `seaborn`, `streamlit`, `joblib`, Git.

---

## Slajd 2: Problem biznesowy i architektura danych
* **Wyzwanie operacyjne:** Magazyn e-commerce potrzebuje codziennej, wiarygodnej prognozy zapotrzebowania (liczba paczek do skompletowania na dzień jutrzejszy $t+1$), aby optymalnie planować obsadę personelu i grafiki pracy.
* **Horyzont danych (420 dni kalendarzowych: `2024-01-01` do `2025-02-23`):**
  - **Zbiór treningowy:** 252 dni kalendarzowe (`2024-01-01` do `2024-09-08`), 248 poprawnych celów (4 braki).
  - **Zbiór walidacyjny:** 84 dni (`2024-09-09` do `2024-12-01`), 100% poprawnych celów.
  - **Zbiór testowy:** 84 dni (`2024-12-02` do `2025-02-23`), 100% poprawnych celów.
* **Architektura podziału sekwencyjnego:**
  - Całkowita rozłączność czasowa: $\text{Trening} \cap \text{Walidacja} \cap \text{Test} = \emptyset$.
  - Zakaz losowego tasowania (*no shuffle*) – zachowanie naturalnej przyczynowości szeregu czasowego.

---

## Slajd 3: Inżynieria jakości danych i zasada Fail-Fast
* **Niemutowalne dane źródłowe:** Wszystkie pliki w `data/raw/` pozostają w trybie tylko do odczytu (read-only).
* **Single Source of Truth (`src/prepare_data.py`):**
  - **Deduplikacja:** Wykrycie i usunięcie 3 identycznych powtórzonych wierszy z końca pliku treningowego (`2024-01-31`, `2024-05-30`, `2024-08-18`).
  - **Obsługa ujemnych i ułamkowych orders:** Liczba zamówień jest zmienną dyskretną $\ge 0$. Wartości ujemne (-5.0) oraz ułamkowe (12.5) oznaczane są flagą jakości `orders_invalid = 1` i zamieniane na `NaN`, co chroni modele przed zakłóceniem bez odrzucania całego zbioru.
  - **Zasada Fail-Fast:** W przypadku uszkodzenia schematu (nieliczbowy tekst w budżecie lub zamówieniach) oraz ujemnego budżetu reklamowego program natychmiast przerywa działanie czytelnym wyjątkiem `ValueError`.
* **Automatyczne testy jednostkowe:** Moduł `tests/test_prepare_data.py` pokrywa 6 prób jakościowych na izolowanych kopiach tymczasowych (100% testów zaliczonych).

---

## Slajd 4: Eksploracyjna analiza danych (EDA) i kluczowe fakty
* **Fakt 1: Szczyt sprzedażowy w soboty ([`reports/orders_by_weekday.png`](orders_by_weekday.png)):**
  - Sobota osiąga najwyższą średnią: **105.19 szt./dzień** ($N=36$ dni), podczas gdy poniedziałek notuje najniższy wolumen: **72.71 szt./dzień** ($N=35$ dni).
  - Średnia sobotnia jest o **+44.7% wyższa** niż poniedziałkowa (pełna oś Y od zera zapobiega manipulacji percepcją różnic).
* **Fakt 2: Wyższy wolumen w dniach promocji ([`reports/orders_by_date.png`](orders_by_date.png)):**
  - Dni z aktywną promocją (`promo=1`): średnia **103.47 szt./dzień** ($N=51$).
  - Dni bez promocji (`promo=0`): średnia **79.47 szt./dzień** ($N=197$).
  - Wzrost o **+24.00 szt./dzień** (+30.2% w okresie promocji).
* **Fakt 3: Symetria rozkładu popytu ([`reports/orders_histogram.png`](orders_histogram.png)):**
  - Średnia (84.41 szt.) i mediana (85.00 szt.) są niemal identyczne; ponad 50% dni mieści się w stabilnym przedziale 70–100 zamówień.
* **Rygor wnioskowania:** Zgodnie z zasadami analitycznymi w raporcie jawnie rozróżniono korelację od przyczynowości (promocja współwystępuje z wyższą sprzedażą, ale mogła być celowo planowana na weekendy).

---

## Slajd 5: Architektura przygotowania cech i ochrona przed Data Leakage
* **Reżim prognozy wieczornej na dzień jutrzejszy ($t+1$):**
  - Dopuszczalne cechy wejściowe: `day_of_week` (cecha kalendarza), `promo` (zaplanowana akcja), `planned_ad_spend_pln` (zaplanowany budżet).
  - **Bezwzględnie zakazane cechy operacyjne:** Kolumny `visits` oraz `revenue_pln` są znane dopiero po zakończeniu dnia. Ich użycie stanowiłoby krytyczny wyciek danych (*Data Leakage*), fałszujący skuteczność wdrożeniową.
* **Potok transformacji `ColumnTransformer` (`src/train.py`):**
  - `SimpleImputer(strategy='median')`: uczy się mediany budżetu wyłącznie z 248 wierszy treningowych (**575.275 PLN**).
  - `OneHotEncoder(handle_unknown='ignore')`: kodowanie 7 kategorii dni tygodnia.
  - `passthrough`: przekazanie binarnej flagi promocji.
* **Testy odporności:** Moduł `tests/test_training.py` weryfikuje automatyczne odrzucenie zabronionych cech wyjątkiem `ValueError`.

---

## Slajd 6: Porównanie modeli i zysk jakościowy
* **Metryka ewaluacji:** Średni błąd bezwzględny (**MAE** [szt./dzień]) na ustalonym oknie walidacyjnym (84 dni).
* **Wyniki ewaluacji modeli:**
  | Model | Rola w projekcie | MAE Trening [szt.] | MAE Walidacja [szt.] | Czas uczenia | Czas predykcji (84 dni) |
  |---|---|:---:|:---:|:---:|:---:|
  | **DummyRegressor(median)** | Model odniesienia (Baseline) | 17.1815 | 16.2143 | < 1 ms | ~ 1 ms |
  | **DecisionTreeRegressor(max_depth=3)** | Model produkcyjny (Pipeline) | 11.1093 | **11.9503** | ~ 9.7 ms | ~ 3.8 ms |
* **Kluczowy rezultat biznesowy:**
  - Drzewo decyzyjne obniża błąd MAE o **4.2640 szt./dzień** na walidacji (względna redukcja błędu o **26.30%**).
  - Model prosty (`max_depth=3`) uogólnia stabilnie bez przeuczenia (niewielka luka generalizacji 0.84 szt.).

---

## Slajd 7: Zamrożenie modeli i ostateczna ewaluacja na teście
* **Zamrożone artefakty w katalogu `models/`:**
  - `models/baseline.joblib` – zamrożony model stałej mediany (85.0 szt.),
  - `models/selected_pipeline.joblib` – kompletny zamrożony potok (`ColumnTransformer` + Drzewo Decyzyjne).
* **Niezależna ewaluacja testowa (`src/predict.py`):**
  - Wykonana na odłożonym oknie testowym (84 dni: `2024-12-02` do `2025-02-23`).
  - **Czyste wnioskowanie predykcyjne:** Moduł wywołuje wyłącznie metodę `.predict()`. Kategoryczny zakaz wywołania `.fit()` i zakaz wyliczania mediany z testu.
* **Ostateczne wyniki na teście:**
  - Baseline MAE: **17.8452 szt./dzień**,
  - Model kandydujący MAE: **14.0930 szt./dzień** (redukcja błędu o **3.75 szt./dzień**, czyli o **21.0%**).
* **Audyt odtwarzalności (`reports/reproduction.md`):** 100% numeryczna tożsamość metryk MAE przy powtórnym uruchomieniu (różnica = 0.0000 szt.).

---

## Slajd 8: Aplikacja demonstracyjna Streamlit (`app.py`)
* **Cel wdrożenia:** Umożliwienie kierownikowi magazynu interaktywnego wygenerowania prognozy popytu na jutro z poziomu przeglądarki internetowej.
* **Architektura aplikacji demonstracyjnej:**
  - Lokalne uruchomienie przez bibliotekę Streamlit pod adresem `http://127.0.0.1:8501`.
  - Wykorzystanie wspólnej funkcji wnioskowania `src.predict.predict_single_day` i zamrożonego modelu `models/selected_pipeline.joblib`.
* **Zabezpieczenia jakościowe interfejsu ([`reports/demo_tests.md`](demo_tests.md)):**
  - Obsługa braku informacji o budżecie reklamowym (automatyczne użycie wyuczonej mediany treningowej 575.28 PLN z czytelnym komunikatem informacyjnym).
  - Ostrzeżenia o ekstrapolacji przy podaniu nietypowego budżetu (> 1500 PLN).
  - Brak jakiegokolwiek douczania modelu i brak połączeń z zewnętrznymi API.
  - Widoczny panel ograniczeń i założeń modelu bezpośrednio pod wynikiem prognozy.

---

## Slajd 9: Rzetelność analityczna i audyt współpracy z AI
* **Metodyka audytu asystenta AI ([`reports/ai_evaluation.md`](ai_evaluation.md)):**
  - Zdefiniowanie 6 formalnych prób przed uruchomieniem poleceń.
  - Skuteczna obrona przed atakiem **Indirect Prompt Injection** (komórka CSV z poleceniem ignorowania reguł potraktowana jako pasywny tekst).
* **Kluczowa lekcja audytu – Studium przypadku Próby 4:**
  - Model prawidłowo odmówił zmyślenia przychodu z marca 2026 r., ale podał błędną datę końcową horyzontu danych (`19.02.2025` zamiast rzeczywistej `23.02.2025` w `orders_test.csv`).
  - Weryfikator pierwotnie bezkrytycznie przyznał punkt 1/1, nie otwierając pliku źródłowego. Po weryfikacji w źródle ocenę obniżono do **0**, a wynik zestawu do **5/6 (83.3%)**.
* **5 Zasad Bezpiecznej Współpracy z AI:**
  1. Podaję tylko dozwolone dane | 2. Zlecam mały zakres | 3. **Sprawdzam źródła** | 4. Niezależnie kontroluję wynik | 5. Zatwierdzam działania przed wykonaniem.

---

## Slajd 10: Podsumowanie osiągnięć i wnioski wdrożeniowe
* **Główne rezultaty projektu:**
  - Zbudowano w 100% powtarzalny, deterministyczny potok danych w języku Python i Git na systemie Windows 10.
  - Osiągnięto redukcję błędu prognozy popytu o ponad 21-26% względem modelu odniesienia.
  - Zapewniono pełną przejrzystość audytową: formalna Karta Modelu, raport odtwarzalności i aplikacja demonstracyjna.
* **Doświadczenie inżynierskie:**
  - Opanowanie pracy w reżimie *Fail-Fast*, ochrony przed *Data Leakage* oraz tworzenia zautomatyzowanych testów jednostkowych.
  - Wykształcenie krytycznej postawy wobec generatywnej sztucznej inteligencji – przejście od biernego odbioru do aktywnego audytu i weryfikacji źródeł.
* **Perspektywy dalszego rozwoju:**
  - Wdrożenie automatycznego potoku CI/CD (GitHub Actions) do uruchamiania testów jednostkowych przy każdym pull requeście.
  - Rozbudowa zbioru cech o zjawiska pogodowe oraz kalendarz świąt nietypowych.

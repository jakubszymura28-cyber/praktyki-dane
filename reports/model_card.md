# Karta modelu (Model Card): Prognozowanie dziennej liczby zamówień

## 1. Zadanie biznesowe i cel prognozy
Wieczorem każdego dnia przewiduję liczbę zamówień na następny dzień. 

Celem biznesowym modelu jest dostarczenie kierownikowi magazynu oraz zespołowi logistyki wiarygodnej prognozy popytu z jednodniowym wyprzedzeniem (horyzont prognozy $t+1$). Dzięki tej informacji zespół może z wyprzedzeniem zaplanować odpowiednią liczbę pracowników magazynowych, przygotować stanowiska do pakowania paczek oraz optymalnie zaplanować odbiory przesyłek przez kurierów.

---

## 2. Zmienna celu (Target)
- **Nazwa kolumny:** `orders`
- **Jednostka:** sztuki `[szt.]` (dzienna łączna liczba złożonych i poprawnych zamówień).
- **Zasada traktowania braków celu:** W analizie i modelowaniu **nie uzupełniamy brakującego celu**. Dni z brakującą lub niepoprawną wartością zamówień (`NaN`, dawne wartości ujemne) są zachowywane w raportach jakości, lecz są bezwzględnie **wykluczane z procesu uczenia i ewaluacji modelu**.

---

## 3. Dozwolone cechy wejściowe (Features)
Do budowy modelu dopuszczone są wyłącznie trzy cechy, które są w 100% znane wieczorem w momencie tworzenia prognozy na dzień jutrzejszy:

1. **`day_of_week` — dzień tygodnia**
   - *Skąd znamy tę cechę przed prognozowanym dniem:* Wynika bezpośrednio ze standardowego kalendarza. Tworząc prognozę w poniedziałek wieczorem, z całkowitą pewnością wiemy, że kolejnym dniem jest wtorek (`day_of_week = 1`). Kalendarz obejmuje wszystkie daty i nie ujawnia przyszłej liczby zamówień.
2. **`promo` — zaplanowana promocja**
   - *Skąd znamy tę cechę przed prognozowanym dniem:* Wszelkie akcje promocyjne, kody rabatowe, banery na stronie głównej oraz wysyłki newsletterów są ustalane przez dział marketingu w harmonogramie promocyjnym z wyprzedzeniem co najmniej kilkudniowym. Wieczorem przed dniem emisji wiadomo, czy promocja będzie aktywna (`1`), czy nie (`0`).
3. **`planned_ad_spend_pln` — planowany budżet reklamy w PLN**
   - *Skąd znamy tę cechę przed prognozowanym dniem:* Dzienny budżet na płatne kampanie reklamowe (np. Google Ads, Meta Ads) jest zatwierdzany i wprowadzany do systemów reklamowych w planie mediowym przed rozpoczęciem danej doby. Wieczorem znamy dokładną kwotę zaplanowaną do wydania na jutrzejszy dzień.

---

## 4. Dlaczego `visits` i `revenue_pln` z przyszłego dnia NIE MOGĄ być wejściami do modelu?
Użycie kolumn `visits` (liczba wizyt na stronie) oraz `revenue_pln` (przychód ze sprzedaży w PLN) jako cech wejściowych jest **kategorycznie niedozwolone** z fundamentalnego powodu metodologicznego:

- **Brak dostępności w momencie prognozy:** Obie te zmienne powstają **w trakcie trwania dnia sprzedaży i są znane dopiero po jego zakończeniu** (wieczorem danego dnia lub następnego poranka po podsumowaniu utargu).
- **Zjawisko wycieku danych w czasie (Data Leakage):** Gdybyśmy wieczorem w przeddzień sprzedaży próbowali podać modelowi jutrzejszą liczbę wizyt lub jutrzejszy przychód, model korzystałby z wiedzy o przyszłości, do której żaden człowiek ani system w rzeczywistości nie ma dostępu. Model nauczony na takich zmiennych osiągałby sztucznie idealne wyniki w testach, ale byłby **całkowicie bezużyteczny na produkcji**, ponieważ w momencie tworzenia prognozy nikt nie potrafiłby podać jutrzejszego przychodu.

---

## 5. Reguła modelu bazowego (Baseline) i model kandydujący

### Model bazowy (Baseline):
- **Narzędzie:** `DummyRegressor(strategy="median")` z biblioteki `scikit-learn`.
- **Reguła predykcji:** Model bazowy ignoruje cechy i na każdy kolejny dzień przewiduje zawsze tę samą stałą wartość: **medianę poprawnych zamówień (`orders`) wyznaczoną wyłącznie ze zbioru treningowego** (wartość referencyjna: **85.00 szt.**).
- **Rola baseline'u:** Wyznacza punkt odniesienia dla każdego bardziej skomplikowanego algorytmu. Jeśli model zaawansowany nie potrafi osiągnąć błędu mniejszego niż prosta mediana, nie powinien trafić na produkcję (choć w pierwszym etapie nie ma bezwzględnego wymogu pokonania baseline'u).

### Model kandydujący (Candidate Model):
- **Narzędzie:** Drzewo decyzyjne `DecisionTreeRegressor(max_depth=3, random_state=42)`.
- **Uzasadnienie struktury:** Ograniczenie głębokości drzewa do maksymalnie 3 poziomów zapobiega nadmiernemu dopasowaniu (overfitting) do próby treningowej i tworzy czytelne, interpretowalne biznesowo reguły decyzyjne oparte na dniu tygodnia, promocji i budżecie reklamowym.
- **Opcjonalne rozszerzenie:** Klasyczna regresja liniowa (`LinearRegression`) może zostać dodana wyłącznie po kompletnym wdrożeniu i ewaluacji modelu minimalnego.

---

## 6. Metryka sukcesu i procedura porównania modeli
- **Główna miara jakości:** **MAE (Mean Absolute Error — Średni błąd bezwzględny)**.
  $$\text{MAE} = \frac{1}{N} \sum_{i=1}^{N} |y_i - \hat{y}_i|$$
  - **Zasada oceny:** **Im mniejszy MAE, tym lepiej** (model myli się przeciętnie o mniejszą liczbę paczek/dzień).
  - **Jednostka metryki:** Zamówienia na dzień `[szt./dzień]`.
- **Rygor porównania modeli:**
  - Wszystkie modele (baseline oraz modele kandydujące) **będą porównywane na dokładnie tych samych dniach** w ramach ustalonego zbioru walidacyjnego (84 kolejne dni od `2024-09-09` do `2024-12-01`).
- **Miary i analizy pomocnicze:**
  - **Czas działania:** Pomiar czasu uczenia i generowania prognozy (efektywność obliczeniowa).
  - **Rozkład błędów według dnia tygodnia:** Szczegółowa analiza wielkości błędu MAE w podziale na poszczególne dni tygodnia (poniedziałek–niedziela), aby sprawdzić, czy model nie wykazuje asymetrycznych błędów w kluczowe dni (np. w weekendy przy wzmożonym popycie).

### Wniosek metodologiczny z porównania modeli z baseline'em:
- **Co dokładnie porównujemy:**
  Oceniając obie prognozy na tych samych dniach zbioru walidacyjnego, porównujemy, o ile przeciętnie sztuk zamówień dzienne predykcje modelu kandydującego ($\hat{y}_i$) różnią się od rzeczywistej sprzedaży ($y_i$) w zestawieniu ze stałą predykcją bazową ($\hat{y}_{\text{base}} = 85.00\text{ szt.}$).
- **Właściwy wniosek z wyniku porównania:**
  Jeżeli model kandydujący (np. drzewo decyzyjne) osiągnie niższe MAE niż baseline, oznacza to wyłącznie, że **jego prognozy w badanym oknie walidacyjnym są przeciętnie bliższe realizacji niż stała mediana ze zbioru treningowego**. Wskazuje to, że uwzględnienie cech wejściowych (`day_of_week`, `promo`, `planned_ad_spend_pln`) pozwala skuteczniej redukować przeciętny błąd dopasowania do danych w tym konkretnym okresie niż prosta reguła bez cech.
- **Czego samo to porównanie NIE POZWALA rozstrzygnąć (granice wnioskowania):**
  1. **Nie dowodzi nauczenia się „rzeczywistych zależności” ani przyczynowości:** Lepszy wynik MAE nie stanowi dowodu na to, że model pojął rzeczywiste mechanizmy rynkowe czy relacje przyczynowo-skutkowe. Model mógł wychwycić korelacje pozorne, specyficzne zbieżności kalendarzowe charakterystyczne dla generatora syntetycznego lub skompensować przeszacowania w jedne dni niedoszacowaniami w inne.
  2. **Nie gwarantuje uogólnienia (generalizacji) poza badany okres:** Niższy błąd na 84 dniach walidacji nie rozstrzyga, jak model zachowa się przy zmianie reżimu rynkowego (np. w dynamicznym okresie świątecznym Q4) ani na rzeczywistych danych ze sklepu internetowego.
  3. **Nie rozstrzyga o strukturze i dotkliwości błędów skrajnych:** MAE traktuje wszystkie odchylenia liniowo i uśrednia je po całym okresie. Samo porównanie MAE nie pozwala stwierdzić, czy model nie generuje bardzo dużych, kosztownych operacyjnie pomyłek w pojedyncze, newralgiczne dni (np. w dni szczytowe, powodując paraliż magazynu).


---

## 7. Podział danych i rygor czasowy

### Schemat podziału 420 kolejnych dni (od 2024-01-01):
```text
[Trening: 252 daty]  ──►  [Walidacja: 84 daty]  ──►  [Test: 84 daty]
(2024-01-01 – 2024-09-08)   (kolejne 84 daty)         (ostatnie 84 daty)
```
> **⚠️ Rygor ewaluacji:** **Nie pobieramy jeszcze testu.** Zbiór testowy pozostaje całkowicie odłożony i nietknięty do momentu ostatecznej weryfikacji wybranego modelu.

### Zgodność z raportem jakości danych (`reports/quality.md`):
- W wyznaczonym oknie treningowym znajduje się dokładnie **252 unikalne daty**, jednak tylko **248 dni ma poprawny cel (`orders`) do uczenia** (4 dni zawierają braki `NaN`, w tym 2 pierwotne braki oraz 2 wartości ujemne zidentyfikowane podczas audytu jakości).
- **Zasada nienaruszalności granic podziału:**
  - **Nie uzupełniamy brakujących `orders`** (nie stosujemy sztucznej imputacji zmiennej celu).
  - **Nie przesuwamy granic podziału czasowego** — okres treningowy to sztywno pierwsze 252 dni w kalendarzu. Cztery dni z brakami są po prostu pomijane podczas trenowania modeli, a nie „uzupełniane” poprzez pobranie kolejnych 4 dni z okresu walidacyjnego.

### Jak losowe mieszanie dni (Random Shuffle) zmieniłoby pytanie badawcze?
- **Prawdziwe pytanie biznesowe:** *„Mając pełną wiedzę historyczną do dnia $t$, czy potrafimy trafnie przewidzieć nieznaną jeszcze liczbę zamówień jutro ($t+1$)?”* Jest to zadanie **prognozowania w przód (ekstrapolacji w czasie)**.
- **Skutek losowego mieszania dni (np. standardowego `train_test_split(shuffle=True)`):**
  - Losowe przemieszanie spowodowałoby, że w zbiorze treningowym znalazłyby się zarówno dni z początku roku, jak i z miesięcy późniejszych (np. z sierpnia i września), a do zbioru testowego trafiłyby pojedyncze dni „wycięte” ze środka (np. wtorek w maju).
  - W efekcie pytanie badawcze zmieniłoby się z prognozowania przyszłości na **interpolację (odgadywanie brakujących punktów wewnątrz znanego już okresu)**. Model „przewidując” sprzedaż w maju, znałby już ogólny poziom popytu, trendy i zachowania klientów z kolejnych miesięcy.
  - Zjawisko to stanowi **wyciek danych w czasie (Temporal Data Leakage)** — model uzyskuje w testach nierealistycznie optymistyczne wyniki (iluzja wysokiej skuteczności), ale w praktyce wdrożeniowej (np. 9 września, stając w obliczu realnej, nieznanej przyszłości) byłby całkowicie bezradny.

### Własna zasada postępowania z danymi:
> **Zasada inżynierii modelu:**  
> **Wybór modelu oraz strojenie hiperparametrów przeprowadzam wyłącznie na zbiorze walidacyjnym, a końcową ocenę skuteczności wykonuję tylko raz na nietkniętym teście.**

### Obsługa braków w cechach:
W oczyszczonych danych zachowujemy braki w cechach (np. brakujący budżet reklamowy `planned_ad_spend_pln`). Ewentualną medianę do ich uzupełnienia wyznaczamy **wyłącznie z danych treningowych wewnątrz potoku `Pipeline`** (np. za pomocą `SimpleImputer(strategy="median")`), co gwarantuje pełną izolację zbioru walidacyjnego i testowego.

---

## 8. Potok przygotowania cech i audyt wyuczonej mediany budżetu (Dzień 11)

W ramach wdrożenia potoku w [src/train.py](src/train.py) zaimplementowano formalny proces inżynierii cech (`ColumnTransformer`) uczony wyłącznie na **248 wierszach** zbioru treningowego posiadających poprawny cel (`orders.notna()`).

### 8.1. Zdefiniowana lista wejść i wykluczeń
- **Cechy wejściowe ($X$):** wyłącznie `day_of_week`, `promo`, `planned_ad_spend_pln`.
- **Zmienna celu ($y$):** `orders`.
- **Kolumny wykluczone (bezwzględny zakaz użycia jako cechy):**
  - `visits` (wizyty) oraz `revenue_pln` (przychód) — są znane dopiero po zakończeniu doby sprzedaży, ich użycie w przewidywaniu na jutro ($t+1$) stanowiłoby kardynalny wyciek danych (Data Leakage).
  - `date` (identyfikator czasowy) oraz `orders_invalid` (flaga audytowa jakości).

### 8.2. Role komponentów potoku (Uczenie vs Ustalona reguła)
| Komponent | Obsługiwana cecha | Rola w potoku | Co dokładnie robi krok |
|---|:---:|:---:|---|
| `SimpleImputer(strategy='median')` | `planned_ad_spend_pln` | **Uczy się (`fit`)** | Oblicza i zapamiętuje medianę budżetu z danych treningowych (`575.275 PLN`), aby uzupełnić ewentualne braki. |
| `OneHotEncoder(handle_unknown='ignore')` | `day_of_week` | **Uczy się (`fit`)** | Wyznacza unikalny zbiór kategorii dni tygodnia `[0, 1, 2, 3, 4, 5, 6]` z treningu i tworzy 7 kolumn binarnych. |
| `passthrough` | `promo` | **Stosuje ustaloną regułę** | Przekazuje binarną flagę (0 lub 1) bez dopasowywania wag ani uczenia jakichkolwiek parametrów z danych. |

### 8.3. Źródłowe liczności i kontrola zgodności mediany budżetu
Uczenie przygotowania cech przeprowadzono ściśle na 248 wierszach treningowych z poprawnym celem:
- **Łączna liczba wierszy w zbiorze treningowym:** 252.
- **Liczba wierszy z poprawnym celem do uczenia:** 248 (wykluczono 4 braki celu).
- **Liczba wierszy z uzupełnionym budżetem reklamowym:** 244.
- **Liczba braków budżetu (`NaN`):** 4.

#### Tabela kontroli mediany budżetu reklamowego:
| Metoda obliczenia | Wartość mediany budżetu | Źródło danych | Status kontroli |
|---|:---:|:---:|:---:|
| **Wyuczona statystyka `SimpleImputer`** | **575.275 PLN** | `imputer.statistics_[0]` w `src/train.py` | Baza |
| **Niezależne obliczenie agenta (pandas)** | **575.275 PLN** | 244 niepuste budżety z 248 wierszy treningu | Identyczne |
| **Różnica bezwzględna** | **0.000 PLN** | Różnica numeryczna | **100% Zgodności** |

Wynik kontroli potwierdza, że potok cech w [src/train.py](src/train.py) uczy się dokładnie na właściwym podzbiorze obserwacji, nie powoduje wycieku danych i poprawnie uzupełnia braki planowanego budżetu reklamowego.

---

## 9. Wyniki ewaluacji modelu bazowego DummyRegressor (Dzień 12)

Model bazowy `DummyRegressor(strategy='median')` został wytrenowany na 248 wierszach zbioru treningowego i przetestowany na całym oknie walidacyjnym (84 dni).

### 9.1. Stała predykcja i metryki błędu MAE
- **Wyuczona stała prognoza ($\hat{y}$):** **85.00 szt.** (równa dokładnie medianie z 248 obserwacji treningowych).
- **Zapisane pliki wyników:**
  - [reports/metrics.csv](metrics.csv) – zestawienie metryk MAE dla treningu i walidacji.
  - [reports/validation_predictions.csv](validation_predictions.csv) – tabela predykcji i błędów bezwzględnych dla każdego z 84 dni walidacji.

| Zbiór danych | Liczba próbek ($N$) | Wyuczona stała predykcja | MAE (Średni błąd bezwzględny) |
|---|:---:|:---:|:---:|
| **Treningowy (`train`)** | 248 dni | 85.0 szt. | **17.1815 szt./dzień** |
| **Walidacyjny (`validation`)** | 84 dni | 85.0 szt. | **16.2143 szt./dzień** |

### 9.2. Ręczna kontrola dla 3 pierwszych dat walidacji
W celu weryfikacji poprawności obliczeń wyznaczono błędy bezwzględne $|y_i - \hat{y}_i|$ dla pierwszych 3 dni zbioru walidacyjnego:

| Data ($t$) | Rzeczywiste zamówienia ($y$) | Prognoza baseline ($\hat{y}$) | Różnica ($y - \hat{y}$) | Błąd bezwzględny $|y - \hat{y}|$ |
|:---:|:---:|:---:|:---:|:---:|
| `2024-09-09` | 78.0 szt. | 85.0 szt. | -7.0 szt. | **7.0 szt.** |
| `2024-09-10` | 68.0 szt. | 85.0 szt. | -17.0 szt. | **17.0 szt.** |
| `2024-09-11` | 56.0 szt. | 85.0 szt. | -29.0 szt. | **29.0 szt.** |

- **Średni błąd bezwzględny pierwszych 3 dat:**
  $$\text{MAE}_{3\text{ dni}} = \frac{7.0 + 17.0 + 29.0}{3} = \frac{53.0}{3} \approx 17.6667\text{ szt./dzień}$$
- **Porównanie z całym oknem walidacyjnym:**
  Średni błąd na pierwszych 3 dniach ($17.67\text{ szt.}$) jest zbliżony do średniego błędu na całym 84-dniowym okresie walidacji ($16.21\text{ szt.}$). Wszystkie prognozy baseline'u są identyczne i równe $85.0\text{ szt.}$.

---

## 10. Ewaluacja modelu kandydującego DecisionTreeRegressor i porównanie z baseline'em (Dzień 13)

W potoku [src/train.py](src/train.py) zintegrowano model kandydujący `DecisionTreeRegressor(max_depth=3, random_state=42)` połączony w jeden spójny obiekt `Pipeline` z preprocesorem cech (`SimpleImputer`, `OneHotEncoder`, `passthrough`).

### 10.1. Rygor próby i pomiar czasu działania
- **Próba ucząca:** Identyczne **248 wierszy treningowych** z poprawnym celem (0 wycieku danych).
- **Próba walidacyjna:** Dokładnie te same **84 dni walidacji** (`2024-09-09` do `2024-12-01`), na których oceniono model bazowy.
- **Zakres pomiaru czasu wykonania (`time.perf_counter()`):**
  - **Czas dopasowania potoku (`fit_time`):** ~**9.66 ms** (0.0097 s). Zmierzono łączny czas dopasowania preprocesora (`fit` imputera budżetu i kodera OneHot) oraz budowy 3-poziomowego drzewa decyzyjnego na 248 próbkach.
  - **Czas generowania prognoz walidacji (`predict_time`):** ~**3.79 ms** (0.0038 s). Zmierzono łączny czas przekształcenia 84 próbek walidacyjnych przez preprocesor oraz przejścia przez reguły decyzyjne drzewa.

### 10.2. Tabela porównawcza modeli (zapisana w `reports/metrics.csv`)

| `model` | `split` | `mae` [szt.] | `evaluated_days` | `parameters` | `data_version` |
|---|:---:|:---:|:---:|---|---|
| **`DummyRegressor`** | `train` | **17.1815** | 248 | `strategy='median'` | `orders_train.csv (v1, 248 poprawnych celów)` |
| **`DummyRegressor`** | `validation` | **16.2143** | 84 | `strategy='median'` | `orders_validation.csv (v1, 84 cele)` |
| **`DecisionTreeRegressor`** | `train` | **11.1093** | 248 | `max_depth=3, random_state=42` | `orders_train.csv (v1, 248 poprawnych celów)` |
| **`DecisionTreeRegressor`** | `validation` | **11.9503** | 84 | `max_depth=3, random_state=42` | `orders_validation.csv (v1, 84 cele)` |

> **⚠️ Rygor ewaluacji:** Tabela obejmuje wyłącznie zbiory `train` i `validation`. **Wyników zbioru testowego jeszcze nie ma** – zbiór testowy pozostaje nienaruszony do końcowej ewaluacji.


### 10.3. Wnioski z porównania modeli
1. **Redukcja błędu bezwzględnego:**
   Model drzewa decyzyjnego osiągnął na oknie walidacyjnym błąd **MAE = 11.95 szt./dzień**, co oznacza spadek błędu o **4.26 szt./dzień** (poprawa o ~26.3%) względem modelu bazowego (**16.21 szt./dzień**).
2. **Zachowanie uogólnienia (brak overfittingu):**
   Błąd walidacyjny drzewa ($11.95$) jest bardzo zbliżony do błędu treningowego ($11.11$), co potwierdza, że ograniczenie głębokości drzewa do `max_depth=3` skutecznie uchroniło model przed nadmiernym dopasowaniem do szumu w danych uczących.
3. **Integralność danych:**
   Wyniki uzyskano bez jakichkolwiek modyfikacji danych surowych ani arbitralnych zmian w regułach czyszczenia – porównanie obu modeli przeprowadzono w 100% rzetelnie na ustalonym oknie walidacyjnym.





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


### 10.3. Rachunek procentowej poprawy i interpretacja biznesowa
- **Wartości źródłowe z [reports/metrics.csv](metrics.csv):**
  - $\text{MAE}_{\text{baseline}}$ (walidacja): **16.2143 szt./dzień**
  - $\text{MAE}_{\text{drzewo d=3}}$ (walidacja): **11.9503 szt./dzień**
- **Różnica w zamówieniach:**
  $$\Delta \text{MAE} = 16.2143 - 11.9503 = \mathbf{4.2640\text{ szt./dzień}}$$
- **Obliczenie procentowej poprawy:**
  $$\frac{\text{MAE}_{\text{baseline}} - \text{MAE}_{\text{drzewo}}}{\text{MAE}_{\text{baseline}}} \times 100\% = \frac{16.2143 - 11.9503}{16.2143} \times 100\% = \frac{4.2640}{16.2143} \times 100\% = \mathbf{26.30\%}$$

> **Własna interpretacja analityczna:**  
> **MAE to średni błąd predykcji wyrażony w fizycznych jednostkach popytu (zamówieniach na dzień), natomiast obliczona wartość 26.30% stanowi względną redukcję tego błędu (zmniejszenie przeciętnej pomyłki o ponad 4 sztuki na dobę), a NIE odsetek idealnie trafionych prognoz ani wskaźnik „accuracy”.** W zadaniu regresji ciągłej przewidujemy liczbę paczek, dlatego miara procentowa informuje o skali ograniczenia niedoszacowań i przeszacowań magazynowych.

### 10.4. Rozkład MAE według dnia tygodnia na walidacji (84 dni)
W całym 84-dniowym oknie walidacyjnym każdy dzień tygodnia występuje **dokładnie 12 razy** ($12 \times 7 = 84$ dni). Zestawienie błędów wykazuje kluczowe źródła przewagi modelu kandydującego:

| Dzień tygodnia (`day_of_week`) | Liczba dni na walidacji | MAE Baseline (`Dummy`) | MAE Drzewo (`d=3`) | Różnica MAE | Wniosek biznesowy |
|:---:|:---:|:---:|:---:|:---:|---|
| **Poniedziałek (0)** | 12 | 10.67 szt. | 10.91 szt. | +0.24 szt. | Zbliżone błędy na początku tygodnia |
| **Wtorek (1)** | 12 | 14.67 szt. | 10.06 szt. | **-4.61 szt.** | Wyraźna redukcja błędu |
| **Środa (2)** | 12 | 16.58 szt. | 12.12 szt. | **-4.46 szt.** | Lepsze dopasowanie środka tygodnia |
| **Czwartek (3)** | 12 | 13.42 szt. | 10.37 szt. | **-3.05 szt.** | Stabilniejsza prognoza |
| **Piątek (4)** | 12 | 13.67 szt. | 13.18 szt. | **-0.49 szt.** | Porównywalna jakość |
| **Sobota (5)** | 12 | 28.83 szt. | 12.98 szt. | **-15.85 szt.** | **Kluczowa eliminacja potężnego błędu stałej mediany w weekend!** |
| **Niedziela (6)** | 12 | 15.67 szt. | 14.04 szt. | **-1.63 szt.** | Lepsze uchwycenie niedzielnego popytu |
| **Suma / Średnia** | **84 dni** | **16.21 szt.** | **11.95 szt.** | **-4.26 szt.** | **Kontrola liczności: 12 × 7 = 84 dni (100% próby walidacji)** |

> **🔬 Hipoteza badawcza (możliwa przyczyna największych błędów):**  
> Jedną z głównych przyczyn występowania największych błędów modelu drzewa (np. niedoszacowania w dniach `2024-10-04`, `2024-11-02`, `2024-11-10`, `2024-11-28`) jest **brak informacji o ogólnym trendzie czasowym, czyli stopniowej zmianie i wzroście bazowego poziomu zamówień w czasie** (np. sezonowe ożywienie popytu w IV kwartale przed okresem świątecznym).  
> Model opiera swoje reguły wyłącznie na bieżącym dniu tygodnia, pojedynczej fladze promocji i budżecie reklamowym, nie posiadając cech reprezentujących upływ czasu ani średnich kroczących popytu z ostatnich dni.  
> *Uwaga metodologiczna: powyższe przypuszczenie stanowi **hipotezę analityczną**, a nie ustalony i udowodniony fakt.*

Pięć największych błędów walidacji wyeksportowano do pliku [reports/validation_errors.csv](validation_errors.csv).

### 10.5. Eksperymentalny wariant głębszego drzewa (`max_depth=5`)

Zgodnie z procedurą sprawdzono wyłącznie jeden dodatkowy wariant hiperparametru na tych samych 248 wierszach treningu i 84 walidacji:
- `max_depth=5, random_state=42`:
  * MAE trening (248 dni): **8.3212 szt./dzień**
  * MAE walidacja (84 dni): **11.1029 szt./dzień**
  * Procentowa redukcja błędu vs Baseline: **31.52%**
- **Uzasadnienie ostatecznego wyboru `max_depth=3`:**
  Model `max_depth=3` cechuje się znacznie mniejszą luką generalizacji ($\text{MAE}_{\text{val}} - \text{MAE}_{\text{train}} = 11.95 - 11.11 = 0.84\text{ szt.}$) w porównaniu do wariantu `max_depth=5` ($11.10 - 8.32 = 2.78\text{ szt.}$). Drzewo o głębokości 3 jest bezpieczniejsze w warunkach produkcyjnych, wysoce interpretowalne i odporne na przeuczenie do szumu w danych uczących.

### 10.6. Zamrożenie modeli (Serialization) i ograniczenia
Ostatecznie wybrane modele zostały seryjnie utrwalone w formacie binarnym w katalogu `models/`:
1. [models/baseline.joblib](file:///c:/Users/Lenovo/Desktop/praktyki%20dane/models/baseline.joblib) – zamrożony model bazowy `DummyRegressor(strategy='median')`.
2. [models/selected_pipeline.joblib](file:///c:/Users/Lenovo/Desktop/praktyki%20dane/models/selected_pipeline.joblib) – zamrożony pełny potok produkcyjny `Pipeline(preprocessor + DecisionTreeRegressor(max_depth=3, random_state=42))`.

- **Weryfikacja integralności:** Po ponownym załadowaniu obiektów przez `joblib.load()` wygenerowane predykcje walidacyjne były w 100% numerycznie zgodne z predykcjami pierwotnymi (`assert np.allclose(...)`).
- **Ograniczenia produkcyjne:**
  - Model prognozuje popyt wyłącznie w oparciu o `day_of_week`, planowaną promocję `promo` oraz zatwierdzony budżet reklamowy `planned_ad_spend_pln`.
  - Nie uwzględnia nietypowych anomalii makroekonomicznych ani nagłych awarii serwisu.
  - Zbiór testowy pozostaje nienaruszony do momentu ostatecznego odbioru projektu.






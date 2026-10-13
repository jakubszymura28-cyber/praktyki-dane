"""Aplikacja demonstracyjna w Streamlit do prognozowania dziennej liczby zamówień.

Zgodna ze specyfikacją w reports/demo_tests.md oraz kartą modelu reports/model_card.md.
Wczytuje zamrożony potok models/selected_pipeline.joblib i używa wspólnej funkcji
wnioskowania src.predict.predict_single_day (bez ponownego trenowania i bez przeliczania mediany).
"""

from datetime import date, timedelta
from pathlib import Path
import streamlit as st

from src.predict import load_production_model, predict_single_day


# Konfiguracja strony
st.set_page_config(
    page_title="Prognoza zamówień – Demo edukacyjne",
    page_icon="📦",
    layout="centered",
)

WEEKDAYS_PL = [
    "Poniedziałek (0)",
    "Wtorek (1)",
    "Środa (2)",
    "Czwartek (3)",
    "Piątek (4)",
    "Sobota (5)",
    "Niedziela (6)",
]


@st.cache_resource(show_spinner="Wczytywanie zamrożonego potoku produkcyjnego...")
def get_model():
    """Wczytuje z pamięci podręcznej zamrożony potok modeli bez ponownego dopasowywania."""
    return load_production_model()


def main():
    st.title("📦 Prognozowanie dziennej liczby zamówień")
    st.caption("Demonstracyjny formularz predykcyjny dla kierownika magazynu (horyzont prognozy $t+1$)")

    # Stałe ostrzeżenie etyczne i operacyjne
    st.warning(
        "⚠️ **Uwaga:** Demo edukacyjne, dane syntetyczne. Narzędzie służy wyłącznie do celów poglądowych "
        "i zgodnie z zasadami Responsible AI (Sekcja 12 karty modelu) nie może być podstawą do "
        "podejmowania automatycznych decyzji kadrowych ani finansowych."
    )

    st.markdown("---")
    st.subheader("1. Parametry planowanego dnia")

    # Domyślna data: jutro (horyzont t+1)
    tomorrow = date.today() + timedelta(days=1)
    
    col1, col2 = st.columns(2)
    with col1:
        date_input = st.date_input(
            "Data prognozy (dzień jutrzejszy $t+1$):",
            value=tomorrow,
            help="Dzień tygodnia zostanie automatycznie wyliczony z wybranej daty.",
        )
    with col2:
        promo_choice = st.radio(
            "Planowana akcja promocyjna:",
            options=["Nie", "Tak"],
            index=0,
            horizontal=True,
            help="Informacja z harmonogramu działu marketingu.",
        )

    promo_val = 1 if promo_choice == "Tak" else 0
    calculated_dow = date_input.weekday()
    dow_name = WEEKDAYS_PL[calculated_dow]

    st.info(f"📅 **Automatycznie wyznaczony dzień tygodnia:** {dow_name}")

    # Budżet reklamowy w PLN
    col_b1, col_b2 = st.columns([2, 1])
    with col_b2:
        st.write("")
        st.write("")
        budget_missing = st.checkbox(
            "Brak danych o budżecie",
            value=False,
            help="Zaznacz, jeśli budżet nie jest znany. Aplikacja użyje wyuczonej mediany treningowej (575.28 PLN).",
        )

    with col_b1:
        budget_input = st.number_input(
            "Planowany budżet reklamowy w PLN (`planned_ad_spend_pln`):",
            value=575.28,
            step=50.0,
            format="%.2f",
            disabled=budget_missing,
            help="Zakres danych w treningu: 150.65 PLN – 999.71 PLN. Zero nie jest brakiem danych.",
        )

    st.markdown("---")
    
    # Przycisk obliczenia prognozy
    if st.button("🚀 Oblicz prognozę zamówień", type="primary"):
        # Walidacja danych wejściowych
        effective_budget = None if budget_missing else budget_input

        if not budget_missing and effective_budget < 0.0:
            st.error("❌ Błąd walidacji: Planowany budżet reklamowy nie może być ujemny! Proszę podać wartość >= 0.")
            return

        if not budget_missing and effective_budget > 999.71:
            st.warning(
                f"⚠️ **Ostrzeżenie o ekstrapolacji:** Wprowadzony budżet ({effective_budget:.2f} PLN) "
                f"przekracza maksymalną wartość ze zbioru treningowego (999.71 PLN). "
                f"Model drzewa decyzyjnego nie ekstrapoluje trendów liniowych i zastosuje regułę dla najwyższego przedziału."
            )

        if budget_missing:
            st.info("ℹ️ **Brak wpisu budżetu:** Zastosowano wyuczoną medianę treningową (575.28 PLN) z potoku.")

        try:
            model = get_model()
            prediction = predict_single_day(
                date_val=date_input,
                promo_val=promo_val,
                planned_ad_spend_pln=effective_budget,
                model=model,
            )

            st.success("✅ Prognoza została obliczona pomyślnie!")
            
            # Prezentacja punktowego wyniku
            st.metric(
                label="Prognozowana dzienna liczba zamówień",
                value=f"{prediction:.1f} szt.",
                help="Punktowa prognoza wyznaczona przez liść zamrożonego drzewa decyzyjnego.",
            )

            budget_display = "Mediana z treningu (575.28 PLN)" if budget_missing else f"{effective_budget:.2f} PLN"
            st.markdown(
                f"""
                **Podsumowanie wejść modelu:**
                - **Data:** `{date_input.strftime('%Y-%m-%d')}` ({dow_name})
                - **Promocja (`promo`):** `{promo_val}` ({promo_choice})
                - **Planowany budżet (`planned_ad_spend_pln`):** `{budget_display}`
                - **Użyty model:** `DecisionTreeRegressor(max_depth=3, random_state=42)` w potoku `Pipeline`
                """
            )


            st.info(
                "ℹ️ **Informacja o niepewności:** Zgodnie z metodyką projektu model generuje prognozę punktową. "
                "W projekcie nie kalkulowano przedziałów pewności (Confidence Intervals), dlatego widełki nie są wyświetlane."
            )

        except Exception as e:
            st.error(f"Wystąpił błąd podczas wnioskowania: {e}")

    # Stopka
    st.markdown("---")
    st.caption("Praktyki - Analiza Danych | Artefakty: models/selected_pipeline.joblib | Raporty: reports/model_card.md")


if __name__ == "__main__":
    main()

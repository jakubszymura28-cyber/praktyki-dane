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
    budget_input = st.number_input(
        "Planowany budżet reklamowy w PLN (`planned_ad_spend_pln`):",
        min_value=0.0,
        max_value=100000.0,
        value=575.28,
        step=50.0,
        format="%.2f",
        help="Wartość domyślna odpowiada medianie ze zbioru treningowego (575.28 PLN). Wartości ujemne są zablokowane.",
    )

    st.markdown("---")
    
    # Przycisk obliczenia prognozy
    if st.button("🚀 Oblicz prognozę zamówień", type="primary"):
        # Walidacja danych wejściowych
        if budget_input < 0.0:
            st.error("Błąd walidacji: Budżet reklamowy nie może być ujemny!")
            return

        try:
            model = get_model()
            prediction = predict_single_day(
                date_val=date_input,
                promo_val=promo_val,
                planned_ad_spend_pln=budget_input,
                model=model,
            )

            st.success("✅ Prognoza została obliczona pomyślnie!")
            
            # Prezentacja punktowego wyniku
            st.metric(
                label="Prognozowana dzienna liczba zamówień",
                value=f"{prediction:.1f} szt.",
                help="Punktowa prognoza wyznaczona przez liść zamrożonego drzewa decyzyjnego.",
            )

            st.markdown(
                f"""
                **Podsumowanie wejść modelu:**
                - **Data:** `{date_input.strftime('%Y-%m-%d')}` ({dow_name})
                - **Promocja (`promo`):** `{promo_val}` ({promo_choice})
                - **Planowany budżet (`planned_ad_spend_pln`):** `{budget_input:.2f} PLN`
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

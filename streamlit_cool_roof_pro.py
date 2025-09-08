import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Kalkulator Dachu Chłodnego PRO", page_icon="🌞", layout="wide")

st.title("🌞 Kalkulator Dachu Chłodnego – Wersja PRO")

# --- Sidebar inputs ---
st.sidebar.header("Parametry wejściowe")

roof_area = st.sidebar.number_input("Powierzchnia dachu (m²)", min_value=50, max_value=50000, value=1000, step=50)

roof_type = st.sidebar.selectbox("Rodzaj dachu", ["Papa/Bitumiczny", "Beton", "Blacha"])

# --- SR/ε defaults by material ---
defaults = {
    "Papa/Bitumiczny": {"SR": 0.10, "ε": 0.90},
    "Beton": {"SR": 0.55, "ε": 0.90},
    "Blacha": {"SR": 0.70, "ε": 0.85},
}
sr_default = defaults[roof_type]["SR"]
e_default = defaults[roof_type]["ε"]

sr = st.sidebar.number_input("TSR / SR (0–1)", min_value=0.0, max_value=1.0, value=sr_default, step=0.01)
emissivity = st.sidebar.number_input("Emisyjność (ε)", min_value=0.0, max_value=1.0, value=e_default, step=0.01)

# --- Solar load input ---
solar_load = st.sidebar.number_input(
    "Roczny ładunek słoneczny H (kWh/m²·rok)", min_value=500, max_value=2500, value=1248, step=10,
    help="Wartość znajdziesz np. w PVGIS (https://re.jrc.ec.europa.eu/pvg_tools/en/)"
)

# --- AC efficiency ---
ac_eff = st.sidebar.selectbox(
    "Sprawność klimatyzacji (EER)",
    ["Stary system (EER≈9)", "Standardowy (EER≈11)", "Nowoczesny (EER≈13)"]
)
ac_map = {"Stary system (EER≈9)": 9, "Standardowy (EER≈11)": 11, "Nowoczesny (EER≈13)": 13}
eer = ac_map[ac_eff]

# --- Cooling fraction ---
f_cool = st.sidebar.slider("Udział zysków obciążających chłodzenie f_chł", 0.1, 1.0, 1.0, 0.1)

# --- Energy price & CO₂ factor ---
elec_price = st.sidebar.number_input("Cena energii elektrycznej (zł/kWh)", min_value=0.2, max_value=2.0, value=0.7, step=0.05)
co2_factor = st.sidebar.number_input("Współczynnik emisji CO₂ (kg/kWh)", min_value=0.1, max_value=1.5, value=0.82, step=0.01)

# --- Reference black roof (comparison) ---
sr_ref, emissivity_ref = 0.05, 0.90
absorptance_ref = 1 - sr_ref
absorptance_new = 1 - sr

# --- CALCULATIONS ---
deltaQ = (absorptance_ref - absorptance_new) * solar_load * roof_area  # kWh/rok energii cieplnej
annual_kwh = deltaQ * f_cool / (eer / 3.412)  # przeliczenie przez COP
annual_cost = annual_kwh * elec_price
annual_co2 = annual_kwh * co2_factor

years = np.arange(1, 21)
cum_kwh = annual_kwh * years
cum_cost = annual_cost * years
cum_co2 = annual_co2 * years

# --- KPIs ---
col1, col2, col3 = st.columns(3)
col1.metric("Roczne oszczędności energii", f"{annual_kwh:,.0f} kWh")
col2.metric("Roczne oszczędności kosztów", f"{annual_cost:,.0f} zł")
col3.metric("Roczna redukcja CO₂", f"{annual_co2:,.0f} kg")

# --- Plots ---
df = pd.DataFrame({
    "Rok": years,
    "Energia (kWh)": cum_kwh,
    "Koszty (zł)": cum_cost,
    "CO₂ (kg)": cum_co2,
})
fig = px.line(df, x="Rok", y=df.columns[1:], markers=True, title="20-letnie oszczędności – kumulacja")
st.plotly_chart(fig, use_container_width=True)

# --- Assumptions section ---
with st.expander("📑 Założenia i wzory"):
    st.markdown(f"""
    **Wzory:**
    - Absorptancja: α = 1 – SR
    - ΔQ = (α_ref – α_new) · H · S
    - E_el = ΔQ · f_chł / COP, gdzie COP = EER / 3.412
    - Koszt = E_el · cena energii
    - CO₂ = E_el · EF_CO₂

    **Wartości przyjęte:**
    - Dach referencyjny: SR = {sr_ref}, ε = {emissivity_ref}
    - Dach proponowany: SR = {sr:.2f}, ε = {emissivity:.2f}
    - Powierzchnia S = {roof_area} m²
    - H = {solar_load} kWh/m²·rok
    - f_chł = {f_cool}
    - EER = {eer}
    - Cena energii = {elec_price} zł/kWh
    - EF CO₂ = {co2_factor} kg/kWh
    """)

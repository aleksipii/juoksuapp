import streamlit as st
import pandas as pd
import os
from datetime import datetime
import matplotlib.pyplot as plt

DATA_FILE = "juoksudata.csv"
TAVOITE = 600

st.set_page_config(page_title="Juoksuseuranta 600 km", layout="centered")

st.title("🏃 600 km Juoksutavoite")

# Lataa tai luo data
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE, parse_dates=["Päivä"])
else:
    df = pd.DataFrame(columns=["Päivä", "Kilometrit", "Kommentti"])

# --- Uusi merkintä ---
st.header("Lisää juoksu")

with st.form("run_form"):
    päivä = st.date_input("Päivä", datetime.today())
    kilometrit = st.number_input("Kilometrit", min_value=0.0, step=0.5)
    kommentti = st.text_input("Kommentti (vapaaehtoinen)")
    submit = st.form_submit_button("Tallenna")

    if submit:
        new_entry = pd.DataFrame([{
            "Päivä": päivä,
            "Kilometrit": kilometrit,
            "Kommentti": kommentti
        }])
        df = pd.concat([df, new_entry], ignore_index=True)
        df.to_csv(DATA_FILE, index=False)
        st.success("Juoksu tallennettu!")

# --- Yhteenveto ---
if not df.empty:
    df["Viikko"] = df["Päivä"].dt.isocalendar().week
    df["Vuosi"] = df["Päivä"].dt.year

    total_km = df["Kilometrit"].sum()
    jäljellä = max(TAVOITE - total_km, 0)
    prosentti = min(total_km / TAVOITE, 1.0)

    st.header("🎯 Tavoitteen eteneminen")
    st.progress(prosentti)
    st.metric("Juostu yhteensä", f"{total_km:.1f} km")
    st.metric("Matkaa 600 km tavoitteeseen", f"{jäljellä:.1f} km")

    # Viikkoseuranta
    current_week = datetime.today().isocalendar()[1]
    current_year = datetime.today().year

    weekly_km = df[
        (df["Viikko"] == current_week) &
        (df["Vuosi"] == current_year)
    ]["Kilometrit"].sum()

    st.metric("Tämän viikon kilometrit", f"{weekly_km:.1f} km")

    # Kehitysgraafi
    st.header("📈 Kehitys")

    df_sorted = df.sort_values("Päivä")
    df_sorted["Kumulatiivinen"] = df_sorted["Kilometrit"].cumsum()

    fig, ax = plt.subplots()
    ax.plot(df_sorted["Päivä"], df_sorted["Kumulatiivinen"])
    ax.axhline(600)
    ax.set_xlabel("Päivä")
    ax.set_ylabel("Kumulatiiviset km")

    st.pyplot(fig)

    st.header("📋 Kaikki juoksut")
    st.dataframe(df_sorted[["Päivä", "Kilometrit", "Kommentti"]])
else:
    st.info("Ei vielä tallennettuja juoksuja.")

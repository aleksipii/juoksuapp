import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

# ------------------
# ASETUKSET
# ------------------
DATA_FILE = "juoksudata.csv"
KOKONAISTAVOITE = 600
VIIKKOTAVOITE = 35

st.set_page_config(
    page_title="Juoksuapp",
    page_icon="🏃",
    layout="centered"
)

# ------------------
# TUMMA TILA
# ------------------
st.markdown("""
<style>
body {
    background-color: #0e1117;
    color: white;
}
</style>
""", unsafe_allow_html=True)

st.title("🏃 Juoksuapp")

# ------------------
# DATA
# ------------------
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE, parse_dates=["Päivä"])
else:
    df = pd.DataFrame(columns=["Päivä", "Kilometrit", "Kommentti"])

# ------------------
# LISÄÄ JUOKSU
# ------------------
st.subheader("➕ Lisää juoksu")

with st.form("run_form"):
    päivä = st.date_input("Päivä", datetime.today())
    kilometrit = st.number_input("Kilometrit", min_value=0.0, step=0.5)
    kommentti = st.text_input("Kommentti")
    submit = st.form_submit_button("Tallenna")

    if submit:
        new_row = pd.DataFrame([{
            "Päivä": päivä,
            "Kilometrit": kilometrit,
            "Kommentti": kommentti
        }])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(DATA_FILE, index=False)
        st.success("Tallennettu!")

# ------------------
# DASHBOARD
# ------------------
if not df.empty:
    df["Viikko"] = df["Päivä"].dt.isocalendar().week
    df["Vuosi"] = df["Päivä"].dt.year

    total_km = df["Kilometrit"].sum()

    # 🎯 Kokonaistavoite
    st.subheader("🎯 Kesän kokonaistavoite")
    st.progress(min(total_km / KOKONAISTAVOITE, 1.0))
    st.metric("Juostu", f"{total_km:.1f} km", f"{KOKONAISTAVOITE-total_km:.1f} km jäljellä")

    # 🏆 Viikkoputki
    st.subheader("🏆 Viikkoputki")

    weekly_summary = (
        df.groupby(["Vuosi", "Viikko"])["Kilometrit"]
        .sum()
        .reset_index()
        .sort_values(["Vuosi", "Viikko"])
    )

    streak = 0
    max_streak = 0

    for km in weekly_summary["Kilometrit"]:
        if km > 0:
            streak += 1
            max_streak = max(max_streak, streak)
        else:
            streak = 0

    st.metric("Nykyinen putki", f"{streak} viikkoa")
    st.metric("Pisimmän putken ennätys", f"{max_streak} viikkoa")

    # 🔮 Ennuste
    st.subheader("🔮 Ennuste")

    first_day = df["Päivä"].min()
    days_running = (datetime.today() - first_day).days + 1
    avg_km_per_day = total_km / max(days_running, 1)
    avg_km_per_week = avg_km_per_day * 7

    if avg_km_per_day > 0:
        days_to_goal = (KOKONAISTAVOITE - total_km) / avg_km_per_day
        predicted_date = datetime.today() + timedelta(days=days_to_goal)
        prediction_text = predicted_date.strftime("%d.%m.%Y")
    else:
        prediction_text = "Ei vielä ennustettavissa"

    st.metric(
        "Arvioitu 600 km saavutuspäivä",
        prediction_text,
        f"{avg_km_per_week:.1f} km / viikko"
    )

    # 📅 Viikkotavoite
    st.subheader("📅 Viikkotavoite")

    current_week = datetime.today().isocalendar()[1]
    weekly_km = df[df["Viikko"] == current_week]["Kilometrit"].sum()
    st.progress(min(weekly_km / VIIKKOTAVOITE, 1.0))
    st.metric("Tämä viikko", f"{weekly_km:.1f} km", f"Tavoite {VIIKKOTAVOITE} km")

    # 🏅 Saavutukset
    st.subheader("🏅 Saavutukset")

    def achievement(name, threshold):
        if total_km >= threshold:
            st.success(f"✅ {name} ({threshold} km)")
        else:
            st.info(f"🔒 {name} ({threshold} km)")

    achievement("Pronssi", 100)
    achievement("Hopea", 300)
    achievement("Kulta", 600)

    # 📈 Ennuste-graafi
    st.subheader("📈 Ennuste: oma tahti vs tavoite")

    df_sorted = df.sort_values("Päivä")
    df_sorted["Kumulatiivinen"] = df_sorted["Kilometrit"].cumsum()

    start_date = df_sorted["Päivä"].min()
    end_date = start_date + timedelta(days=120)
    total_days = (end_date - start_date).days

    target_dates = pd.date_range(start_date, end_date)
    target_km = [KOKONAISTAVOITE * (i / total_days) for i in range(len(target_dates))]

    fig, ax = plt.subplots()
    ax.plot(df_sorted["Päivä"], df_sorted["Kumulatiivinen"], label="Sinun kehitys")
    ax.plot(target_dates, target_km, linestyle="--", label="Tavoitevauhti")
    ax.axhline(KOKONAISTAVOITE)
    ax.legend()
    ax.set_xlabel("Päivä")
    ax.set_ylabel("Km")
    st.pyplot(fig)

    # 📋 Historia
    st.subheader("📋 Juoksuhistoria")
    st.dataframe(df_sorted[["Päivä", "Kilometrit", "Kommentti"]])

else:
    st.info("Lisää ensimmäinen juoksu.")

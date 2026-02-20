import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

# ==================
# ASETUKSET
# ==================
KOKONAISTAVOITE = 600
VIIKKOTAVOITE = 35

st.set_page_config(
    page_title="Juoksuapp",
    page_icon="🏃",
    layout="centered"
)

# ==================
# TUMMA TILA
# ==================
st.markdown("""
<style>
body { background-color: #0e1117; color: white; }
</style>
""", unsafe_allow_html=True)

st.title("🏃 Juoksuapp")

# ==================
# KÄYTTÄJÄ (MONIKÄYTTÄJÄ)
# ==================
st.sidebar.title("👤 Käyttäjä")
username = st.sidebar.text_input("Käyttäjänimi")

if username.strip() == "":
    st.warning("Anna käyttäjänimi jatkaaksesi")
    st.stop()

DATA_FILE = f"data_{username}.csv"

# ==================
# DATA
# ==================
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
else:
    df = pd.DataFrame(columns=["ID", "Päivä", "Kilometrit", "Kommentti"])

# pakotetaan oikeat tyypit
if not df.empty:
    df["Päivä"] = pd.to_datetime(df["Päivä"], errors="coerce")
    df = df.dropna(subset=["Päivä"])

# varmista ID
if "ID" not in df.columns:
    df["ID"] = range(len(df))

# ==================
# LISÄÄ JUOKSU
# ==================
st.subheader("Lisää juoksu")

with st.form("run_form"):
    päivä = st.date_input("Päivä", datetime.today())
    kilometrit = st.number_input("Kilometrit", min_value=0.0, step=0.5)
    kommentti = st.text_input("Kommentti")
    submit = st.form_submit_button("Tallenna")

    if submit:
        new_row = pd.DataFrame([{
            "ID": datetime.now().timestamp(),
            "Päivä": päivä,
            "Kilometrit": kilometrit,
            "Kommentti": kommentti
        }])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(DATA_FILE, index=False)
        st.success("Tallennettu!")
        st.experimental_rerun()

# ==================
# POISTA JUOKSU
# ==================
st.subheader("🗑️ Poista juoksu")

if not df.empty:
    delete_id = st.selectbox(
        "Valitse poistettava juoksu",
        df["ID"],
        format_func=lambda x: (
            f"{df.loc[df['ID'] == x, 'Päivä'].dt.strftime('%d.%m.%Y').values[0]} – "
            f"{df.loc[df['ID'] == x, 'Kilometrit'].values[0]} km"
        )
    )

    if st.button("❌ Poista valittu juoksu"):
        df = df[df["ID"] != delete_id]
        df.to_csv(DATA_FILE, index=False)
        st.success("Juoksu poistettu")
        st.experimental_rerun()
else:
    st.info("Ei poistettavia juoksuja.")

# ==================
# DASHBOARD
# ==================
if not df.empty:
    df["Viikko"] = df["Päivä"].dt.isocalendar().week
    df["Vuosi"] = df["Päivä"].dt.year

    total_km = df["Kilometrit"].sum()

    # 🎯 Kokonaistavoite
    st.subheader("🎯 Kesän kokonaistavoite")
    st.progress(min(total_km / KOKONAISTAVOITE, 1.0))
    st.metric(
        "Juostu",
        f"{total_km:.1f} km",
        f"{KOKONAISTAVOITE - total_km:.1f} km jäljellä"
    )

    # 🏆 Viikkoputki
    st.subheader("🏆 Viikkoputki")

    weekly = (
        df.groupby(["Vuosi", "Viikko"])["Kilometrit"]
        .sum()
        .reset_index()
        .sort_values(["Vuosi", "Viikko"])
    )

    streak = 0
    max_streak = 0

    for km in weekly["Kilometrit"]:
        if km > 0:
            streak += 1
            max_streak = max(max_streak, streak)
        else:
            streak = 0

    st.metric("Nykyinen putki", f"{streak} viikkoa")
    st.metric("Pisimmän putken ennätys", f"{max_streak} viikkoa")

    if streak == 0 and len(weekly) > 1:
        st.error("🚨 Viikkoputki katkesi! Tee lenkki tällä viikolla.")
    else:
        st.success("🔥 Putki elää!")

    # 🔮 Ennuste
    st.subheader("🔮 Ennuste")

    first_day = df["Päivä"].min()
    days_running = max((datetime.today() - first_day).days, 1)
    avg_km_day = total_km / days_running
    avg_km_week = avg_km_day * 7

    if avg_km_day > 0:
        days_left = (KOKONAISTAVOITE - total_km) / avg_km_day
        predicted = datetime.today() + timedelta(days=days_left)
        prediction = predicted.strftime("%d.%m.%Y")
    else:
        prediction = "Ei vielä ennustettavissa"

    st.metric(
        "600 km saavutetaan arviolta",
        prediction,
        f"{avg_km_week:.1f} km / viikko"
    )

    # 📅 Viikkotavoite
    st.subheader("📅 Viikkotavoite")

    current_week = datetime.today().isocalendar()[1]
    weekly_km = df[df["Viikko"] == current_week]["Kilometrit"].sum()

    st.progress(min(weekly_km / VIIKKOTAVOITE, 1.0))
    st.metric(
        "Tämä viikko",
        f"{weekly_km:.1f} km",
        f"Tavoite {VIIKKOTAVOITE} km"
    )

    # 🏅 Saavutukset
    st.subheader("🏅 Saavutukset")

    for name, km in [("Pronssi", 100), ("Hopea", 300), ("Kulta", 600)]:
        if total_km >= km:
            st.success(f"✅ {name} ({km} km)")
        else:
            st.info(f"🔒 {name} ({km} km)")

    # 📈 Ennuste-graafi
    st.subheader("📈 Oma tahti vs tavoite")

    df_sorted = df.sort_values("Päivä").copy()
    df_sorted["Kumulatiivinen"] = df_sorted["Kilometrit"].cumsum()

    start = df_sorted["Päivä"].min()
    end = start + timedelta(days=120)
    days = (end - start).days

    target_dates = pd.date_range(start, end)
    target_km = [KOKONAISTAVOITE * (i / days) for i in range(len(target_dates))]

    fig, ax = plt.subplots()
    ax.plot(df_sorted["Päivä"], df_sorted["Kumulatiivinen"], label="Sinä")
    ax.plot(target_dates, target_km, "--", label="Tavoitevauhti")
    ax.axhline(KOKONAISTAVOITE)
    ax.legend()
    ax.set_xlabel("Päivä")
    ax.set_ylabel("Kilometrit")
    st.pyplot(fig)

    # 📋 Historia
    st.subheader("📋 Juoksuhistoria")
    st.dataframe(df_sorted[["Päivä", "Kilometrit", "Kommentti"]])

else:
    st.info("Lisää ensimmäinen juoksu.")

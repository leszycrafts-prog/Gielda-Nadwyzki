from datetime import datetime
import os
import pandas as pd
import streamlit as st

# Konfiguracja strony
st.set_page_config(
    page_title="Giełda Przesunięć Międzymagazynowych & Toxic", layout="wide"
)

DB_FILE = "baza_nadwyzek.csv"
HISTORY_FILE = "baza_historii.csv"

# Oficjalna lista sklepów Leroy Merlin do wyboru z rozwijanego menu
SKLEPY_LM = [
    "Wybierz sklep...",
    "Białystok",
    "Bielsko-Biała",
    "Bydgoszcz",
    "Bytom",
    "Częstochowa",
    "Gdańsk - Szadółki",
    "Gdańsk - Oliwa",
    "Gdynia",
    "Gliwice",
    "Gorzów Wielkopolski",
    "Grudziądz",
    "Jelenia Góra",
    "Kalisz",
    "Katowice",
    "Kielce",
    "Koszalin",
    "Kraków - Czyżyny",
    "Kraków - Bonarka",
    "Kraków - Zakopiańska",
    "Legnica",
    "Lublin",
    "Łódź - Manufaktura",
    "Łódź - Port Łódź",
    "Marki koło Warszawy",
    "Nowy Sącz",
    "Olsztyn",
    "Opole",
    "Piaseczno koło Warszawy",
    "Piła",
    "Płock",
    "Poznań - Franowo",
    "Poznań - Komorniki",
    "Radom",
    "Rumia",
    "Rybnik",
    "Rzeszów",
    "Siedlce",
    "Sosnowiec",
    "Szczecin",
    "Tarnów",
    "Toruń",
    "Wałbrzych",
    "Warszawa - Al. Krakowska",
    "Warszawa - Górczewska",
    "Warszawa - Modlińska",
    "Warszawa - Ostrobramska",
    "Włocławek",
    "Wrocław - Bielany",
    "Wrocław - Korona",
    "Wrocław - Krakowska",
    "Zabrze",
    "Zamość",
    "Zielona Góra",
]


# Funkcja do wczytywania głównej bazy z pliku CSV
def load_data():
  if os.path.exists(DB_FILE):
    try:
      return pd.read_csv(DB_FILE)
    except Exception:
      pass
  return pd.DataFrame(columns=[
      "id",
      "sklep",
      "dzial",
      "ref",
      "nazwa",
      "ilosc",
      "typ",
      "kontakt",
      "status",
      "data_dodania",
  ])


# Funkcja do zapisu głównej bazy
def save_data(df):
  df.to_csv(DB_FILE, index=False)


# Funkcja do wczytywania historii rezerwacji / cesji
def load_history():
  if os.path.exists(HISTORY_FILE):
    try:
      return pd.read_csv(HISTORY_FILE)
    except Exception:
      pass
  return pd.DataFrame(columns=[
      "id",
      "data",
      "sklep_zrodlowy",
      "sklep_docelowy",
      "ref",
      "nazwa",
      "ilosc",
      "typ",
      "kontakt_oferujacy",
      "status",
  ])


# Funkcja do zapisu historii
def save_history(df):
  df.to_csv(HISTORY_FILE, index=False)


df = load_data()
history_df = load_history()

st.title("📦 Giełda Przesunięć Międzymagazynowych & Toxic")
st.markdown(
    "Centralny system wymiany nadwyżek użytkowych i zapasów trudno zbywalnych."
)

menu = st.tabs([
    "🔍 Szukaj Towaru",
    "➕ Dodaj Nadwyżkę",
    "📋 Rezerwacje i Cesje",
    "⚙️ Zarządzanie Bazą",
])

# --- TAB 1: SZUKAJ TOWARU & AUTOMATYCZNA CESJA ---
with menu[0]:
  st.header("Wyszukiwarka i Rezerwacja / Cesja")
  search_query = st.text_input("Wpisz nazwę, numer ref lub dział:", "").lower()

  if not df.empty:
    filtered_df = df[
        df.apply(
            lambda row: search_query in str(row["nazwa"]).lower()
            or search_query in str(row["ref"]).lower()
            or search_query in str(row["dzial"]).lower()
            or search_query in str(row["sklep"]).lower(),
            axis=1,
        )
    ].reset_index(drop=True)

    st.write(f"Znaleziono pozycji: {len(filtered_df)}")

    for i, row in filtered_df.iterrows():
      with st.container():
        col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
        with col1:
          st.markdown(
              f"**{row['nazwa']}** (Ref: `{row['ref']}`)\nSklep:"
              f" {row['sklep']} | Dział: {row['dzial']}"
          )
        with col2:
          st.markdown(f"Dostępne: **{row['ilosc']} szt.**\nTyp: {row['typ']}")
        with col3:
          st.markdown(f"Status: {row['status']}\nKontakt: {row['kontakt']}")
        with col4:
          if int(row["ilosc"]) > 0:
            with st.form(key=f"res_form_{i}"):
              ilosc_do_rezerwacji = st.number_input(
                  "Ile sztuk potrzebujesz?",
                  min_value=1,
                  max_value=int(row["ilosc"]),
                  value=min(1, int(row["ilosc"])),
                  key=f"num_{i}",
              )
              # Wybór sklepu zamawiającego z rozwijanej listy
              sklep_zamawiajacy = st.selectbox(
                  "Twój Sklep / Oddział", SKLEPY_LM, key=f"shop_{i}"
              )
              submit_res = st.form_submit_button("Rezerwuj / Cesja")

              if submit_res:
                if sklep_zamawiajacy == "Wybierz sklep...":
                  st.error("Wybierz swój sklep z listy!")
                else:
                  ilosc_pobrana = int(ilosc_do_rezerwacji)
                  ilosc_akt = int(row["ilosc"])
                  real_idx = df[df["id"] == row["id"]].index[0]

                  # 1. Zapisujemy zdarzenie do historii rezerwacji
                  new_hist_id = (
                      int(history_df["id"].max()) + 1
                      if not history_df["id"].empty
                      and pd.notna(history_df["id"].max())
                      else 1
                  )
                  nowy_wpis_historii = pd.DataFrame([{
                      "id": new_hist_id,
                      "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                      "sklep_zrodlowy": row["sklep"],
                      "sklep_docelowy": sklep_zamawiajacy,
                      "ref": row["ref"],
                      "nazwa": row["nazwa"],
                      "ilosc": ilosc_pobrana,
                      "typ": row["typ"],
                      "kontakt_oferujacy": row["kontakt"],
                      "status": "Oczekuje na cesję",
                  }])
                  history_df = pd.concat(
                      [history_df, nowy_wpis_historii], ignore_index=True
                  )
                  save_history(history_df)

                  # 2. Aktualizujemy stan głównej giełdy
                  if ilosc_pobrana >= ilosc_akt:
                    df = df.drop(real_idx).reset_index(drop=True)
                    komunikat = f"Pobrano ostatnie sztuki! Zarejestrowano cesję dla {sklep_zamawiajacy}."
                  else:
                    df.at[real_idx, "ilosc"] = ilosc_akt - ilosc_pobrana
                    komunikat = f"Zarezerwowano {ilosc_pobrana} szt. dla {sklep_zamawiajacy}. Zgłoszenie trafiło do historii."

                  if not df.empty:
                    df["id"] = range(1, len(df) + 1)

                  save_data(df)
                  st.toast(komunikat, icon="✅")
                  st.rerun()
          else:
            st.markdown("*Brak sztuk do pobrania*")
        st.divider()
  else:
    st.info("Brak wpisów w bazie.")

# --- TAB 2: DODAJ NADWYŻKĘ ---
with menu[1]:
  st.header("Dodaj nową nadwyżkę lub zapas Toxic")
  with st.form("add_form"):
    col_a, col_b = st.columns(2)
    with col_a:
      # Wybór sklepu wystawiającego z rozwijanej listy
      sklep = st.selectbox("Nazwa Twojego Sklepu", SKLEPY_LM)
      dzial = st.text_input("Dział (np. Ogród, Narzędzia)")
      ref = st.text_input("Numer referencyjny (Ref)")
      nazwa = st.text_input("Nazwa towaru")
    with col_b:
      ilosc = st.number_input("Ilość sztuk", min_value=1, value=1)
      typ = st.selectbox(
          "Typ zgłoszenia",
          ["Nadwyżka magazynowa", "Zapas Toxic", "Końcówka serii", "Inne"],
      )
      kontakt = st.text_input("Kontakt (telefon / e-mail)")

    submitted = st.form_submit_button("Dodaj do giełdy")
    if submitted:
      if sklep == "Wybierz sklep..." or not nazwa or not ref:
        st.error(
            "Wybierz sklep z listy oraz wypełnij wymagane pola (Nazwa, Ref)!"
        )
      else:
        new_id = (
            int(df["id"].max()) + 1
            if not df["id"].empty and pd.notna(df["id"].max())
            else 1
        )
        nowy_wpis = pd.DataFrame([{
            "id": new_id,
            "sklep": sklep,
            "dzial": dzial,
            "ref": ref,
            "nazwa": nazwa,
            "ilosc": ilosc,
            "typ": typ,
            "kontakt": kontakt,
            "status": "Dostępne",
            "data_dodania": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }])
        df = pd.concat([df, nowy_wpis], ignore_index=True)
        df["id"] = range(1, len(df) + 1)
        save_data(df)
        st.toast("Pomyślnie dodano produkt do giełdy!", icon="🚀")
        st.rerun()

# --- TAB 3: REZERWACJE I CESJE (HISTORIA DLA KOORDYNATORÓW) ---
with menu[2]:
  st.header("📋 Rejestr Rezerwacji i Oczekujących Cesji")
  st.markdown(
      "Tutaj koordynatorzy i sklepy mogą sprawdzić, jakie rezerwacje zostały"
      " zgłoszone z giełdy. Po zrealizowaniu oficjalnej cesji w systemie można"
      " zaktualizować status lub usunąć wpis."
  )

  if not history_df.empty:
    edited_history = st.data_editor(
        history_df, num_rows="dynamic", key="history_editor"
    )

    if st.button("💾 Zapisz zmiany w historii cesji"):
      save_history(edited_history)
      st.toast("Historia rezerwacji została zaktualizowana!", icon="💾")
      st.rerun()
  else:
    st.info(
        "Brak zarejestrowanych rezerwacji. Gdy sklepy zaczną pobierać towar z"
        " giełdy, pojawią się tutaj."
    )

# --- TAB 4: ZARZĄDZAJ BAZĄ ---
with menu[3]:
  st.header("⚙️ Zarządzanie główną bazą giełdy")
  st.markdown(
      "Panel administracyjny do bezpośredniej korekty stanów lub usuwania"
      " błędnych wpisów."
  )

  if not df.empty:
    edited_df = st.data_editor(df, num_rows="dynamic", key="data_editor_db")

    if st.button("💾 Zapisz zmiany w giełdzie"):
      edited_df["id"] = range(1, len(edited_df) + 1)
      save_data(edited_df)
      st.toast("Giełda została zaktualizowana!", icon="💾")
      st.rerun()
  else:
    st.info("Brak towarów na giełdzie.")

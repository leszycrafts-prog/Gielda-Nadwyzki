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

# Oficjalna lista sklepów Leroy Merlin
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


def save_data(df):
  df.to_csv(DB_FILE, index=False)


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
      "dzial",
      "ref",
      "nazwa",
      "ilosc",
      "typ",
      "kontakt_oferujacy",
      "status",
  ])


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

# --- TAB 1: SZUKAJ TOWARU & REZERWACJA Z ZABEZPIECZENIEM KONKURENCYJNYM ---
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
              sklep_zamawiajacy = st.selectbox(
                  "Twój Sklep / Oddział", SKLEPY_LM, key=f"shop_{i}"
              )
              submit_res = st.form_submit_button("Rezerwuj / Cesja")

              if submit_res:
                if sklep_zamawiajacy == "Wybierz sklep...":
                  st.error("Wybierz swój sklep z listy!")
                else:
                  # KLUCZOWY KROK: Pobieramy najświeższy stan z bazy w ułamku sekundy kliknięcia!
                  live_df = load_data()
                  live_history = load_history()

                  # Szukamy tego samego produktu po unikalnym ID w aktualnym pliku
                  match_item = live_df[live_df["id"] == row["id"]]

                  if match_item.empty:
                    st.error(
                        "⚠️ Ten towar został już w całości pobrany przez kogoś"
                        " innego w międzyczasie! Odśwież stronę."
                    )
                  else:
                    real_idx = match_item.index[0]
                    ilosc_akt = int(live_df.at[real_idx, "ilosc"])
                    ilosc_pobrana = int(ilosc_do_rezerwacji)

                    if ilosc_pobrana > ilosc_akt:
                      st.error(
                          f"⚠️ Ktoś właśnie zarezerwował część towaru! Dostępne"
                          f" jest teraz tylko {ilosc_akt} szt."
                      )
                    else:
                      # Zapis do historii
                      new_hist_id = (
                          int(live_history["id"].max()) + 1
                          if not live_history["id"].empty
                          and pd.notna(live_history["id"].max())
                          else 1
                      )
                      nowy_wpis_historii = pd.DataFrame([{
                          "id": new_hist_id,
                          "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                          "sklep_zrodlowy": row["sklep"],
                          "sklep_docelowy": sklep_zamawiajacy,
                          "dzial": row["dzial"],
                          "ref": row["ref"],
                          "nazwa": row["nazwa"],
                          "ilosc": ilosc_pobrana,
                          "typ": row["typ"],
                          "kontakt_oferujacy": row["kontakt"],
                          "status": "🔴 Oczekuje na cesję",
                      }])
                      live_history = pd.concat(
                          [live_history, nowy_wpis_historii], ignore_index=True
                      )
                      save_history(live_history)

                      # Aktualizacja stanu w żywej bazie
                      if ilosc_pobrana >= ilosc_akt:
                        live_df = live_df.drop(real_idx).reset_index(drop=True)
                        komunikat = f"Pobrano ostatnie sztuki! Zarejestrowano cesję dla {sklep_zamawiajacy}."
                      else:
                        live_df.at[real_idx, "ilosc"] = (
                            ilosc_akt - ilosc_pobrana
                        )
                        komunikat = f"Zarezerwowano {ilosc_pobrana} szt. dla {sklep_zamawiajacy}."

                      if not live_df.empty:
                        live_df["id"] = range(1, len(live_df) + 1)

                      save_data(live_df)
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
        live_df = load_data()
        new_id = (
            int(live_df["id"].max()) + 1
            if not live_df["id"].empty and pd.notna(live_df["id"].max())
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
        live_df = pd.concat([live_df, nowy_wpis], ignore_index=True)
        live_df["id"] = range(1, len(live_df) + 1)
        save_data(live_df)
        st.toast("Pomyślnie dodano produkt do giełdy!", icon="🚀")
        st.rerun()

# --- TAB 3: AKTYWNE REZERWACJE I AUTOMATYCZNE ZWRACANIE ---
with menu[2]:
  st.header("📋 Oczekujące Cesje i Rezerwacje")
  st.markdown(
      "Tutaj znajdują się wyłącznie **aktywne cesje**. Po zmianie statusu na"
      " **🟢 Zrealizowany** lub **⚪ Anulowany** pozycja zniknie z tej tabeli i"
      " trafi do archiwum na dole."
  )

  history_df_live = load_history()
  oczekujace_df = history_df_live[
      history_df_live["status"] == "🔴 Oczekuje na cesję"
  ].copy()

  if not oczekujace_df.empty:
    column_config = {
        "status": st.column_config.SelectboxColumn(
            "Status Cesji",
            help="Zmień status rezerwacji",
            options=["🔴 Oczekuje na cesję", "🟢 Zrealizowany", "⚪ Anulowany"],
            required=True,
        )
    }

    edited_oczekujace = st.data_editor(
        oczekujace_df,
        column_config=column_config,
        num_rows="fixed",
        key="oczekujace_editor",
    )

    if st.button("💾 Zapisz zmiany w cesjach"):
      live_hist = load_history()
      live_db = load_data()

      for idx, row in edited_oczekujace.iterrows():
        hist_match = live_hist[live_hist["id"] == row["id"]]
        if not hist_match.empty:
          hist_idx = hist_match.index[0]
          stary_status = live_hist.at[hist_idx, "status"]
          nowy_status = row["status"]

          if stary_status != nowy_status:
            live_hist.at[hist_idx, "status"] = nowy_status

            if nowy_status == "⚪ Anulowany":
              match_gielda = live_db[
                  (live_db["sklep"] == row["sklep_zrodlowy"])
                  & (live_db["ref"] == row["ref"])
              ]
              if not match_gielda.empty:
                g_idx = match_gielda.index[0]
                live_db.at[g_idx, "ilosc"] = (
                    int(live_db.at[g_idx, "ilosc"]) + int(row["ilosc"])
                )
              else:
                g_new_id = (
                    int(live_db["id"].max()) + 1
                    if not live_db["id"].empty and pd.notna(live_db["id"].max())
                    else 1
                )
                zwracany_wiersz = pd.DataFrame([{
                    "id": g_new_id,
                    "sklep": row["sklep_zrodlowy"],
                    "dzial": row["dzial"],
                    "ref": row["ref"],
                    "nazwa": row["nazwa"],
                    "ilosc": row["ilosc"],
                    "typ": row["typ"],
                    "kontakt": row["kontakt_oferujacy"],
                    "status": "Dostępne",
                    "data_dodania": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }])
                live_db = pd.concat([live_db, zwracany_wiersz], ignore_index=True)

              if not live_db.empty:
                live_db["id"] = range(1, len(live_db) + 1)
              save_data(live_db)

      save_history(live_hist)
      st.toast("Zapisano zmiany w cesjach!", icon="💾")
      st.rerun()
  else:
    st.info("Brak oczekujących cesji. Wszystkie sprawy są zrealizowane!")

  st.divider()

  with st.expander("📦 Zobacz Archiwum Zrealizowanych / Anulowanych Cesji"):
    current_hist = load_history()
    zrealizowane = current_hist[
        current_hist["status"] != "🔴 Oczekuje na cesję"
    ].copy()
    if not zrealizowane.empty:
      st.dataframe(zrealizowane, use_container_width=True)
    else:
      st.info("Brak zrealizowanych lub anulowanych cesji w archiwum.")

# --- TAB 4: ZARZĄDZAJ BAZĄ ---
with menu[3]:
  st.header("⚙️ Zarządzanie główną bazą giełdy")
  st.markdown("Panel administracyjny do ręcznej korekty bazy.")

  current_db = load_data()
  if not current_db.empty:
    edited_df = st.data_editor(
        current_db, num_rows="dynamic", key="data_editor_db"
    )

    if st.button("💾 Zapisz zmiany w giełdzie"):
      edited_df["id"] = range(1, len(edited_df) + 1)
      save_data(edited_df)
      st.toast("Giełda została zaktualizowana!", icon="💾")
      st.rerun()
  else:
    st.info("Brak towarów na giełdzie.")

  st.divider()

  with st.expander("🔐 Strefa Administratora (Wymagane hasło)"):
    haslo_admina = st.text_input(
        "Podaj hasło administratora:", type="password", key="admin_pass"
    )

    if haslo_admina == "LeroyAdmin2026":
      st.success("Hasło poprawne! Odblokowano strefę zarządzania.")
      if st.button("🧹 Wyczyść wszystko (Reset giełdy i historii)"):
        pusta_baza = pd.DataFrame(columns=[
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
        pusta_historia = pd.DataFrame(columns=[
            "id",
            "data",
            "sklep_zrodlowy",
            "sklep_docelowy",
            "dzial",
            "ref",
            "nazwa",
            "ilosc",
            "typ",
            "kontakt_oferujacy",
            "status",
        ])

        save_data(pusta_baza)
        save_history(pusta_historia)
        st.toast("Wyczyszczono wszystkie bazy do zera!", icon="🧹")
        st.rerun()
    elif haslo_admina != "":
      st.error("Błędne hasło!")

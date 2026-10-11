from datetime import datetime
import os
import pandas as pd
import streamlit as st

# Konfiguracja strony
st.set_page_config(
    page_title="Giełda Przesunięć Międzymagazynowych & Toxic", layout="wide"
)

DB_FILE = "baza_nadwyzek.csv"


# Funkcja do wczytywania bazy z pliku CSV
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


# Funkcja do zapisu bazy
def save_data(df):
  df.to_csv(DB_FILE, index=False)


df = load_data()

st.title("📦 Giełda Przesunięć Międzymagazynowych & Toxic")
st.markdown(
    "Centralny system wymiany nadwyżek użytkowych i zapasów trudno zbywalnych."
)

menu = st.tabs(["🔍 Szukaj Towaru", "➕ Dodaj Nadwyżkę / Toxic", "📋 Zarządzaj"])

# --- TAB 1: SZUKAJ TOWARU & CZĘŚCIOWA REZERWACJA ---
with menu[0]:
  st.header("Wyszukiwarka i Rezerwacja / Cesja")
  search_query = st.text_input("Wpisz nazwę, numer ref lub dział:", "").lower()

  if not df.empty:
    # Filtrowanie z resetowaniem indeksu, aby uniknąć pomieszania wierszy
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
              sklep_zamawiajacy = st.text_input(
                  "Twój Sklep / Oddział", key=f"shop_{i}"
              )
              submit_res = st.form_submit_button("Rezerwuj / Cesja")

              if submit_res:
                if not sklep_zamawiajacy:
                  st.error("Podaj nazwę swojego sklepu!")
                else:
                  ilosc_pobrana = int(ilosc_do_rezerwacji)
                  ilosc_akt = int(row["ilosc"])

                  # Szukamy prawdziwego wiersza w bazie głównej po unikalnym ID
                  real_idx = df[df["id"] == row["id"]].index[0]

                  if ilosc_pobrana >= ilosc_akt:
                    df.at[real_idx, "ilosc"] = 0
                    df.at[
                        real_idx, "status"
                    ] = f"Zarezerwowane ({sklep_zamawiajacy})"
                  else:
                    df.at[real_idx, "ilosc"] = ilosc_akt - ilosc_pobrana
                    new_id = (
                        int(df["id"].max()) + 1
                        if not df["id"].empty and pd.notna(df["id"].max())
                        else 1
                    )
                    nowy_wiersz = pd.DataFrame([{
                        "id": new_id,
                        "sklep": sklep_zamawiajacy,
                        "dzial": row["dzial"],
                        "ref": row["ref"],
                        "nazwa": row["nazwa"],
                        "ilosc": ilosc_pobrana,
                        "typ": row["typ"],
                        "kontakt": row["kontakt"],
                        "status": f"Częściowa rezerwacja",
                        "data_dodania": datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                    }])
                    df = pd.concat([df, nowy_wiersz], ignore_index=True)

                  save_data(df)
                  st.toast(
                      f"Zarezerwowano {ilosc_pobrana} szt. dla"
                      f" {sklep_zamawiajacy}!",
                      icon="✅",
                  )
                  st.rerun()
          else:
            st.markdown("*Brak sztuk do pobrania*")
        st.divider()
  else:
    st.info("Brak wpisów w bazie.")

# --- TAB 2: DODAJ NADWYŻKĘ / TOXIC ---
with menu[1]:
  st.header("Dodaj nową nadwyżkę lub zapas Toxic")
  with st.form("add_form"):
    col_a, col_b = st.columns(2)
    with col_a:
      sklep = st.text_input("Nazwa Sklepu (np. Zielona Góra)")
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
      if not sklep or not nazwa or not ref:
        st.error("Wypełnij wymagane pola (Sklep, Nazwa, Ref)!")
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
        save_data(df)
        st.toast("Pomyślnie dodano produkt do giełdy!", icon="🚀")
        st.rerun()

# --- TAB 3: ZARZĄDZAJ (PEŁNA EDYCJA I USUWANIE) ---
with menu[2]:
  st.header("Zarządzanie bazą (Edycja i Usuwanie)")
  st.markdown(
      "Tutaj możesz bezpośrednio klikać i edytować dowolne komórki (np. zmienić"
      " status na *Zwolnione*, zmniejszyć ilość, edytować tekst) lub zaznaczyć"
      " wiersze i je skasować."
  )

  if not df.empty:
    edited_df = st.data_editor(df, num_rows="dynamic", key="data_editor_db")

    if st.button("💾 Zapisz zmiany w bazie"):
      # Automatyczne ponowne numerowanie ID od 1 wzwyż po usunięciach
      edited_df["id"] = range(1, len(edited_df) + 1)
      save_data(edited_df)
      st.toast("Zmiany zostały zapisane na stałe w bazie!", icon="💾")
      st.rerun()
  else:
    st.info("Brak danych do zarządzania.")

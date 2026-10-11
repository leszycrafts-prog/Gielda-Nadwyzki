# 📦 Retail Inter-Store Transfer & Dead Stock Exchange (Giełda Przesunięć)

Wewnętrzna platforma webowa zaprojektowana w celu usprawnienia gospodarki magazynowej, redukcji zapasów zalegających (tzw. zapasów trudnozbywalnych / Toxic) oraz płynnej wymiany nadwyżek towarowych pomiędzy oddziałami sieci handlowej.

## 🚀 Kluczowe Funkcjonalności
* **Wyszukiwarka i rezerwacja częściowa:** Szybkie filtrowanie towarów po referencji, nazwie lub dziale z możliwością pobrania dokładnej liczby sztuk (bez blokowania całej puli dla innych sklepów).
* **Zarządzanie stanami w czasie rzeczywistym:** Interaktywny pulpit administratora pozwalający na bieżącą aktualizację statusów, edycję ilości oraz usuwanie pozycji.
* **Trwałość danych:** Mechanizm automatycznego zapisu stanu bazy danych zapewniający bezpieczeństwo informacji między sesjami.
* **Lekka architektura:** Rozwiązanie oparte na Pythonie i Streamlit, gotowe do szybkiego wdrożenia na serwerze lokalnym lub w chmurze.

## 🛠️ Stos Technologiczny
* **Język:** Python 3.x
* **Interfejs:** Streamlit
* **Przetwarzanie danych:** Pandas
* **Persistencja:** Lokalne bazy danych CSV / plikowe

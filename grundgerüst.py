import streamlit as st
import pandas as pd
import uuid
import datetime
import gspread


# --------------------------
# Google Sheets Verbindung (nur über Link in Secrets)
# --------------------------
def connect_gsheet(sheet_name="Wetterdaten"):
    """
    Verbindet die App mit einem öffentlich geteilten Google Sheet.
    Der Link kommt aus Streamlit Secrets: st.secrets["google_sheet"]["url"]
    """
    try:
        sheet_url = st.secrets["google_sheet"]["url"]
    except KeyError:
        st.error("Bitte den Google Sheet Link in den Streamlit Secrets unter [google_sheet] → url eintragen!")
        st.stop()

    try:
        client = gspread.public()  # Zugriff auf öffentliches Sheet
        sheet = client.open_by_url(sheet_url).sheet1
        st.success("Mit Google Sheet verbunden ✅")
        return sheet
    except Exception as e:
        st.error(f"Fehler beim Verbinden: {e}")
        st.stop()


# --------------------------
# Datenklassen
# --------------------------
class WetterMessung:
    def __init__(self, datum, temperatur, niederschlag, sonnenstunden=None,
                 id=None, standort="Musterstadt"):
        self.id = id or str(uuid.uuid4())
        self.datum = pd.to_datetime(datum)
        self.temperatur = temperatur
        self.niederschlag = niederschlag
        self.sonnenstunden = sonnenstunden if sonnenstunden is not None else 6.0
        self.standort = standort

    def als_dict(self):
        return {
            "ID": self.id,
            "Datum": self.datum.strftime("%Y-%m-%d %H:%M:%S"),
            "Temperatur": self.temperatur,
            "Niederschlag": self.niederschlag,
            "Sonnenstunden": self.sonnenstunden,
            "Standort": self.standort
        }


# --------------------------
# Basisklasse
# --------------------------
class WetterDaten:
    def __init__(self):
        self.messungen = []

    def hinzufuegen(self, messung):
        self.messungen.append(messung)

    def als_dataframe(self):
        df = pd.DataFrame([m.als_dict() for m in self.messungen])
        if not df.empty:
            df['Datum'] = pd.to_datetime(df['Datum'])
            df = df.sort_values('Datum')
        return df

    def loesche_messungen(self, ids):
        self.messungen = [m for m in self.messungen if m.id not in ids]

    # --------------------------
    # Daten mit Google Sheets speichern
    # --------------------------
    def speichern_gsheet(self, sheet):
        df = self.als_dataframe()
        if df.empty:
            return
        sheet.clear()
        sheet.update([df.columns.values.tolist()] + df.values.tolist())

    def laden_gsheet(self, sheet):
        data = sheet.get_all_records()
        for row in data:
            self.hinzufuegen(WetterMessung(
                row["Datum"], row["Temperatur"], row["Niederschlag"],
                row.get("Sonnenstunden", 6.0),
                id=row.get("ID"),
                standort=row.get("Standort", "Musterstadt")
            ))


# --------------------------
# Erweiterung: WetterAnalyse
# --------------------------
class WetterAnalyse(WetterDaten):
    def extremwerte(self, ort_filter="Alle"):
        df = self.als_dataframe()
        if df.empty:
            return None, None
        if ort_filter != "Alle":
            df = df[df['Standort'] == ort_filter]
        if df.empty:
            return None, None
        max_idx = df['Temperatur'].idxmax()
        min_idx = df['Temperatur'].idxmin()
        return df.loc[max_idx], df.loc[min_idx]

    def jahresstatistik(self, ort_filter="Alle"):
        df = self.als_dataframe()
        if ort_filter != "Alle":
            df = df[df['Standort'] == ort_filter]
        if df.empty:
            return None
        return {
            "durchschnittstemperatur": df['Temperatur'].mean(),
            "gesamtniederschlag": df['Niederschlag'].sum(),
            "gesamte_sonnenstunden": df['Sonnenstunden'].sum()
        }


# --------------------------
# Haupt-App
# --------------------------
def main():
    st.title("🌤️ Wetterweiser - Minimal")
    wd = WetterAnalyse()

    # Verbindung zu Google Sheet
    sheet = connect_gsheet("Wetterdaten")

    # Daten aus Google Sheet laden
    wd.laden_gsheet(sheet)

    # DataFrame anzeigen
    st.dataframe(wd.als_dataframe())


if __name__ == "__main__":
    main()

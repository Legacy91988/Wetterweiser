import streamlit as st
import pandas as pd
import uuid
import datetime
import gspread

# --------------------------
# Google Sheets Verbindung über Secrets (kein Service Account nötig)
# --------------------------
def connect_gsheet():
    """
    Verbindet die App mit einem Google Sheet über den Link aus Streamlit Secrets.
    """
    try:
        sheet_url = st.secrets["google_sheet"]["url"]
        gc = gspread.oauth()  # OAuth flow mit lokalem Browser, nur einmal nötig
        sh = gc.open_by_url(sheet_url)
        worksheet = sh.sheet1
        st.success("Google Sheet verbunden ✅")
        return worksheet
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
        try:
            data = sheet.get_all_records()
        except gspread.exceptions.APIError:
            data = []
        for row in data:
            self.hinzufuegen(WetterMessung(
                row.get("Datum", datetime.datetime.now()),
                row.get("Temperatur", 0),
                row.get("Niederschlag", 0),
                row.get("Sonnenstunden", 6.0),
                id=row.get("ID"),
                standort=row.get("Standort","Musterstadt")
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
    st.title("🌤️ Wetterweiser - Minimal (Sheet-Link Version)")
    wd = WetterAnalyse()

    # Verbindung zu Google Sheet
    sheet = connect_gsheet()

    # Daten aus Google Sheet laden
    wd.laden_gsheet(sheet)

    # DataFrame anzeigen (optional)
    st.dataframe(wd.als_dataframe())

if __name__ == "__main__":
    main()

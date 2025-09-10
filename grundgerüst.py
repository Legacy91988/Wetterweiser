import streamlit as st
import pandas as pd
import uuid
import datetime

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

    def laden_csv(self, csv_url):
        df = pd.read_csv(csv_url)
        for _, row in df.iterrows():
            self.hinzufuegen(WetterMessung(
                datum=row["Datum"],
                temperatur=row["Temperatur"],
                niederschlag=row["Niederschlag"],
                sonnenstunden=row.get("Sonnenstunden", 6.0),
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
    st.title("🌤️ Wetterweiser - Minimal (CSV-Version)")

    # WetterAnalyse Instanz
    wd = WetterAnalyse()

    # Google Sheet CSV-Link
    csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTIFjrGtLkaGP_daFfwgjHkb44_YgimPNhfDcrmvJiua1-h7wLfEaCvkaFgIgWbbcCFC7TKtCGvawGl/pub?gid=0&single=true&output=csv"

    # Daten laden
    wd.laden_csv(csv_url)

    # DataFrame anzeigen
    st.dataframe(wd.als_dataframe())

if __name__ == "__main__":
    main()

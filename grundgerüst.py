import streamlit as st
import pandas as pd
import uuid
import json
from datetime import datetime
from github import Github

# --------------------------
# Einstellungen für GitHub
# --------------------------
GITHUB_REPO = "Legacy91988/Wetterweiser"   # <--- hier GitHub Repo eintragen
BRANCH = "main"                           # <--- hier Branch eintragen
DATEI_NAME = "wetterdaten.json"           # JSON-Datei für die Wetterdaten

# --------------------------
# Datenklassen
# --------------------------
class WetterMessung:
    def __init__(self, datum, temperatur, niederschlag, sonnenstunden=6.0, id=None, standort="Musterstadt"):
        self.id = id or str(uuid.uuid4())
        self.datum = pd.to_datetime(datum)
        self.temperatur = temperatur
        self.niederschlag = niederschlag
        self.sonnenstunden = sonnenstunden
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

    # --------------------------
    # JSON lokal oder GitHub
    # --------------------------
    def laden(self, github=None):
        if github:
            try:
                repo = github.get_repo(GITHUB_REPO)
                content = repo.get_contents(DATEI_NAME, ref=BRANCH)
                data = json.loads(content.decoded_content.decode())
            except:
                data = []
        else:
            try:
                with open(DATEI_NAME, "r") as f:
                    data = json.load(f)
            except FileNotFoundError:
                data = []

        for row in data:
            self.hinzufuegen(WetterMessung(
                row["Datum"], row["Temperatur"], row["Niederschlag"],
                row.get("Sonnenstunden",6.0),
                id=row.get("ID"),
                standort=row.get("Standort","Musterstadt")
            ))

    def speichern(self, github=None):
        df = [m.als_dict() for m in self.messungen]
        if github:
            repo = github.get_repo(GITHUB_REPO)
            try:
                content = repo.get_contents(DATEI_NAME, ref=BRANCH)
                repo.update_file(content.path, "Update Wetterdaten", json.dumps(df, indent=2), content.sha, branch=BRANCH)
            except:
                repo.create_file(DATEI_NAME, "Create Wetterdaten", json.dumps(df, indent=2), branch=BRANCH)
        else:
            with open(DATEI_NAME, "w") as f:
                json.dump(df, f, indent=2)

# --------------------------
# Haupt-App
# --------------------------
def main():
    st.title("🌤️ Wetterweiser - Minimal mit GitHub")

    # GitHub Verbindung (falls Token vorhanden)
    github = None
    if "github_token" in st.secrets.get("github", {}):
        github = Github(st.secrets["github"]["github_token"])

    wd = WetterDaten()
    wd.laden(github)

    # Zeige Daten
    st.dataframe(wd.als_dataframe())

    # Formular für neue Messungen
    with st.form("neue_messung"):
        datum = st.date_input("Datum", value=pd.Timestamp.today())
        temperatur = st.number_input("Temperatur", value=20.0)
        niederschlag = st.number_input("Niederschlag", value=0.0)
        sonnenstunden = st.number_input("Sonnenstunden", value=6.0)
        standort = st.text_input("Standort", value="Musterstadt")
        submitted = st.form_submit_button("Hinzufügen")
        if submitted:
            wd.hinzufuegen(WetterMessung(datum, temperatur, niederschlag, sonnenstunden, standort=standort))
            wd.speichern(github)
            st.success("Messung gespeichert ✅")

if __name__ == "__main__":
    main()

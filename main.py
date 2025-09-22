import base64  # zum kodieren/decodieren der Json Daten
import datetime  # Datum & Uhrzeit
import json  # Laden und Speichern
import random  # für die Zufallswerte
import traceback  # für Fehlermeldungungen im Debug Modus
import uuid  # für eindeutige ID´s
from enum import Enum  # Quelle der Wetterdaten
import matplotlib.pyplot as plt  # für Diagramme
import numpy as np  # mathematische Berechnungen
import pandas as pd  # für Tabellen und Daten
import requests  # für HTTP- Anfragen
import streamlit as st  # Web-App-Oberfläche


# Quelle der Wetterdaten (Enum für bessere Übersicht und Sicherheit)


class Quelle(Enum):
    MANUELL = "manuell"  # von Hand eingeben
    SIMULIERT = "simuliert"  # automatisch generierte zufalls Daten
    LIVE = "live"  # von der Wetter-API abrufen


# GitHub-Konfiguration aus Streamlit Secrets
# Repo-Name, Branch, Token und Pfad zur JSON-Datei mit Wetterdaten

GITHUB_REPO = st.secrets["Legacy91988"]["Wetterweiser"]
GITHUB_BRANCH = st.secrets["Legacy91988"].get("branch", "main")
GITHUB_TOKEN = st.secrets["Legacy91988"]["github_token"]
GITHUB_JSON_PATH = "wetterdaten.json"


# Klasse für einzelne Wettermessungen
# Klasse für einzelne Wettermessungen
class WetterMessung:
    def __init__(
        self,
        datum,
        temperatur=None,  # Durchschnitt, optional
        niederschlag=0,
        sonnenstunden=None,
        id=None,
        quelle=Quelle.MANUELL,
        standort="Musterstadt",
        temp_min=None,  # NEU
        temp_max=None,  # NEU
    ):
        self.id = id or str(uuid.uuid4())  # eindeutige ID
        self.datum = pd.to_datetime(datum)
        self.temperatur = temperatur  # Durchschnitt optional
        self.niederschlag = niederschlag
        self.sonnenstunden = (
            sonnenstunden
            if sonnenstunden is not None
            else round(random.uniform(0, 12), 1)
        )
        self.quelle = quelle.value if isinstance(quelle, Quelle) else quelle
        self.standort = standort

        # NEU: min/max Temperaturen speichern
        self.temp_min = temp_min
        self.temp_max = temp_max

    def als_dict(self):
        # Falls Temperatur None ist, Mittelwert aus Temp_min und Temp_max berechnen
        if self.temperatur is None:
            temp_min = self.temp_min
            temp_max = self.temp_max
            if temp_min is not None and temp_max is not None:
                temperatur = round((float(temp_min) + float(temp_max)) / 2, 1)
            else:
                temperatur = 0  # Fallback, falls keine Werte vorhanden
        else:
            temperatur = self.temperatur

        return {
            "ID": self.id,
            "Datum": self.datum.strftime("%Y-%m-%d %H:%M:%S") if self.datum else "",
            "Temperatur": temperatur,
            "Niederschlag": self.niederschlag if self.niederschlag is not None else 0,
            "Sonnenstunden": (
                self.sonnenstunden if self.sonnenstunden is not None else 0
            ),
            "Quelle": self.quelle,
            "Standort": self.standort,
            "Temp_min": self.temp_min,
            "Temp_max": self.temp_max,
        }


# Klasse zum Verwalten mehrerer Wettermessung
class WetterDaten:
    def __init__(self):
        self.messungen = []  # Liste aller Messung

    def hinzufuegen(self, messung: WetterMessung):
        self.messungen.append(messung)

    # prüfen ob für einen Ort oder Datum ein Eintrag existiert
    def existiert_eintrag(self, datum, standort):
        for m in self.messungen:
            if m.standort == standort and m.datum.date() == datum.date():
                return True
        return False

    # ersetzt eine bestehende Messung
    def ersetze_eintrag(self, datum, standort, neue_messung):
        # alte Messung entfernen
        self.messungen = [
            m
            for m in self.messungen
            if not (m.standort == standort and m.datum.date() == datum.date())
        ]
        # neue Messung hinzufügen
        self.hinzufuegen(neue_messung)

    # Wandelt alle Messung in ein pandas DataFrame um
    def als_dataframe(self):
        # Liste aller Dicts in DataFrame
        df = pd.DataFrame([m.als_dict() for m in self.messungen])
        if not df.empty:
            df["Datum"] = pd.to_datetime(df["Datum"])
            df = df.sort_values("Datum")  # nach Datum sortieren
        return df

    # löscht eine Messung anhand ihrer ID
    def loeschen(self, messung_id):
        self.messungen = [m for m in self.messungen if m.id != messung_id]

    def import_github_json(self):
        # Importiert Messdaten von GitHub aus der JSON-Datei#
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_JSON_PATH}?ref={GITHUB_BRANCH}"
        headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
        # Daten von GitHub abrufen
        try:
            response = requests.get(url, headers=headers, timeout=5)
            response.raise_for_status()
            data_json = response.json()
        except requests.RequestException as e:
            st.error(f"Fehler beim Zugriff auf GitHub: {e}")
            return
        # Prüfen ob Inhalt vorhanden
        if "content" not in data_json:
            msg = data_json.get("message", "Unbekannter Fehler beim Laden der Daten.")
            st.warning(f"GitHub-API meldet: {msg}")
            return
        # Inhalt dekodieren und JSON laden
        try:
            content = base64.b64decode(data_json["content"]).decode("utf-8")
            data = json.loads(content)
        except Exception as e:
            st.error(f"Fehler beim Dekodieren der GitHub-Daten: {e}")
            return
        # neue Eintäge erstellen (wenn noch nicht vorhanden)
        hinzugefuegte = 0
        for eintrag in data:
            messung = WetterMessung(
                id=eintrag.get("ID"),
                datum=eintrag.get("Datum"),
                temperatur=eintrag.get("Temperatur"),
                niederschlag=eintrag.get("Niederschlag"),
                sonnenstunden=eintrag.get("Sonnenstunden"),
                quelle=eintrag.get("Quelle"),
                standort=eintrag.get("Standort"),
            )
            if not self.existiert_eintrag(messung.datum, messung.standort):
                self.hinzufuegen(messung)
                hinzugefuegte += 1

        st.info(f"{hinzugefuegte} Einträge von GitHub importiert.")

    @staticmethod
    def load_github_data(debug=False):
        # Lädt die Wetterdaten aus GitHub.
        def _load():
            wd = WetterAnalyse()  # Objekt erstellen
            wd.import_github_json()  # Daten von Git Hub importieren
            return wd

        if debug:
            return _load()
        else:
            # Daten mit Streamlit-Cache laden (TTL = 300 Sekunden)
            @st.cache_data(ttl=300)
            def cached_load():
                return _load()

            return cached_load()

    def export_github_json(self, debug_mode=False):
        """
        Speichert die Wetterdaten auf GitHub als JSON-Datei.

        Verwendet die GitHub-API, um die Datei zu aktualisieren. Jede Datei auf GitHub hat eine
        eindeutige SHA (Secure Hash Algorithm), die die aktuelle Version identifiziert.
        Die SHA wird benötigt, damit GitHub erkennt, welche Version der Datei überschrieben
        werden soll, und um Konflikte zu vermeiden.

        Funktionsweise:
        1. Wandelt die Wetterdaten in JSON um.
        2. Ruft die aktuelle SHA der Datei von GitHub ab.
        3. Erstellt die Payload mit Message, Content, Branch und SHA.
        4. Sendet die PUT-Anfrage an GitHub, um die Datei zu aktualisieren.
        5. Gibt Erfolg oder Fehler auf der Streamlit-Oberfläche aus.
        """

        # Daten auf GitHub speichern, als JSON
        if not GITHUB_TOKEN:
            st.warning("Kein GitHub-Token gesetzt – Daten nicht gespeichert.")
            return
        # Messungen in JSON umwandeln
        df = [m.als_dict() for m in self.messungen]
        json_data = json.dumps(df, indent=2)
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}

        # Prüfen, ob Datei schon existiert, um SHA für Update zu erhalten
        url_get = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_JSON_PATH}?ref={GITHUB_BRANCH}"
        try:
            r_get = requests.get(url_get, headers=headers)
            r_get.raise_for_status()
            sha = r_get.json().get(
                "sha"
            )  # eindeutiger Hash der Datei, nötig für ein Update auf GitHub
        except requests.RequestException:
            sha = None  # n

        # Payload für GitHub PUT-Anfrage vorbereiten
        payload = {
            "message": f"Update Wetterdaten {datetime.datetime.now()}",
            "content": base64.b64encode(json_data.encode()).decode(),
            "branch": GITHUB_BRANCH,
        }
        # nur hinzufügen, wenn Datei schon existiert, damit GitHub weiß, dass wir updaten
        if sha:
            payload["sha"] = sha

        if debug_mode:
            st.text_area("🔍 GitHub-Payload", json.dumps(payload, indent=2), height=250)

        ## Daten auf GitHub hochladen
        try:
            r_put = requests.put(
                f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_JSON_PATH}",
                headers=headers,
                data=json.dumps(payload),
            )
            r_put.raise_for_status()
            st.success("Daten erfolgreich auf GitHub gespeichert!")
        except requests.RequestException as e:
            st.error(f"Fehler beim Speichern auf GitHub: {e}")


# Analyse & Diagramme
class WetterAnalyse(WetterDaten):
    #  heißester und kältister Tag
    def extremwerte(self, ort_filter="Alle"):
        df = self.als_dataframe()
        if df.empty:
            return None, None
        if ort_filter != "Alle":
            df = df[df["Standort"] == ort_filter]
        if df.empty:
            return None, None
        # Heißester Tag: max Temp_max
        max_tag = df.loc[df["Temp_max"].idxmax()]
        # Kältester Tag: min Temp_min
        min_tag = df.loc[df["Temp_min"].idxmin()]
        return max_tag, min_tag

    # Jahresstatistik anzeigen
    def jahresstatistik(self, ort_filter="Alle"):
        st.subheader("📈 Jahresstatistik")
        df = self.als_dataframe()
        if ort_filter != "Alle":
            df = df[df["Standort"] == ort_filter]
        if df.empty:
            st.info("Keine Daten vorhanden")
            return

        # Durchschnittswerte und Summen anzeigen (nur gültige Werte)
        temp_mean = df["Temperatur"].mean()
        nied_sum = df["Niederschlag"].sum()
        sonne_sum = df["Sonnenstunden"].sum()

        st.write(f"Durchschnittstemperatur: {temp_mean:.2f} °C")
        st.write(f"Gesamtniederschlag: {nied_sum:.2f} mm")
        st.write(f"Gesamte Sonnenstunden: {sonne_sum:.2f} h")

        # Extremwerte (heißester und kältester Tag) berechnen
        df_extrem = df.dropna(
            subset=["Temperatur"]
        )  # nur Zeilen mit gültiger Temperatur
        if df_extrem.empty:
            st.info("Keine Temperaturdaten für Extremwert-Berechnung.")
            return

        max_tag_row = df_extrem.loc[df_extrem["Temperatur"].idxmax()]
        min_tag_row = df_extrem.loc[df_extrem["Temperatur"].idxmin()]

        st.success(
            f"Heißester Tag: {max_tag_row['Datum'].date()} mit {max_tag_row['Temperatur']}°C"
        )
        st.info(
            f"Kältester Tag: {min_tag_row['Datum'].date()} mit {min_tag_row['Temperatur']}°C"
        )

    # berechnet Regenwahrscheinlichkeit
    def regenwahrscheinlichkeit(self, tage=7, ort_filter="Alle"):
        df = self.als_dataframe()
        if df.empty:
            return 0
        if ort_filter != "Alle":
            df = df[df["Standort"] == ort_filter]
        letzte_tage = df.sort_values("Datum").tail(tage)
        regen_tage = letzte_tage[letzte_tage["Niederschlag"] > 0]  # Tage mit Regen
        wahrscheinlichkeit = len(regen_tage) / tage * 100  # % Regen
        return round(wahrscheinlichkeit, 1)

    #

    #  Prognose basierent auf den Mittelwert der letzten 7 Tage
    def prognose_mittelwert(self, serie, tage=3):
        mw = (
            serie.tail(7).mean() if len(serie) >= 1 else 0
        )  # Mittelwert der letzten 7 Einträge
        return [round(mw, 1)] * tage

    # Prognose basierend auf dem Trend der letzten 7 Tage
    def prognose_trend(self, serie, tage=3, is_precipitation=False):
        data = serie.tail(7).values  # letzte 7 Werte
        if len(data) >= 2:
            trend = np.poly1d(
                np.polyfit(np.arange(len(data)), data, 1)
            )  # lineare Trendlinie
            werte = [round(trend(len(data) + i), 1) for i in range(1, tage + 1)]
            # Niederschlag darf nicht negativ sein
            if is_precipitation:
                werte = [max(0, w) for w in werte]
            return werte
        return self.prognose_mittelwert(serie, tage)

    # Prognose mit zufälliger Abweichung
    def prognose_ueberraschung(self, serie, tage=3, is_precipitation=False):
        mw = (
            serie.tail(7).mean() if len(serie) >= 1 else 0
        )  # Mittelwert der letzten 7 Werte
        werte = [
            round(mw + random.uniform(-3, 3), 1) for _ in range(tage)
        ]  # kleine Zufallsschwankung
        if is_precipitation:
            werte = [max(0, w) for w in werte]
        return werte

    # Prognosen für Temperatur & Niederschlag (basierend auf Mittelwert)
    def prognose_temperatur(self, tage=3):
        df = self.als_dataframe()
        if df.empty:
            return []
        return self.prognose_trend(df["Temperatur"], tage)

    def prognose_niederschlag(self, tage=3):
        df = self.als_dataframe()
        if df.empty:
            return []
        return self.prognose_trend(df["Niederschlag"], tage, is_precipitation=True)

    # Diagramme für Temperatur und Niederschlag (3 Tage)
    def plot_3tage_prognose(self, ort_filter="Alle"):
        st.subheader("🌤️ 3-Tage Prognose")
        df = self.als_dataframe()

        if df.empty:
            st.info("Keine Daten vorhanden – Prognose kann nicht erstellt werden.")
            return

        # Filter nach Ort
        if ort_filter != "Alle":
            df = df[df["Standort"] == ort_filter]
            if df.empty:
                st.info("Keine Daten für diesen Ort.")
                return

        # Filter nach Quelle
        quelle_filter = st.selectbox(
            "Quelle auswählen:", ["Alle", "manuell", "simuliert", "live"]
        )
        if quelle_filter != "Alle":
            df = df[df["Quelle"] == quelle_filter]
            if df.empty:
                st.info(f"Keine Daten für Quelle '{quelle_filter}'.")
                return

        # Prognose-Methode auswählen
        methode = st.selectbox(
            "Prognose-Methode wählen:",
            ["Mittelwert-Prognose", "Trendbasierte Prognose", "Überraschungsprognose"],
            key="prognose_methode",
        )

        tage = 3
        labels = [
            (datetime.datetime.now() + datetime.timedelta(days=i)).strftime("%d-%m")
            for i in range(1, tage + 1)
        ]

        # Prognosen erstellen
        if methode == "Mittelwert-Prognose":
            temp = self.prognose_mittelwert(df["Temperatur"], tage)
            nied = self.prognose_mittelwert(df["Niederschlag"], tage)
        elif methode == "Trendbasierte Prognose":
            temp = self.prognose_trend(df["Temperatur"], tage)
            nied = self.prognose_trend(df["Niederschlag"], tage, is_precipitation=True)
        else:  # Überraschungsprognose
            temp = self.prognose_ueberraschung(df["Temperatur"], tage)
            nied = self.prognose_ueberraschung(
                df["Niederschlag"], tage, is_precipitation=True
            )

        # Diagramm: Temperatur und Niederschlag nebeneinander
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))

        ax1.plot(labels, temp, marker="o", color="red", linewidth=2)
        ax1.set_ylabel("°C")
        ax1.set_title(f"Temperaturprognose – {methode}")

        ax2.bar(labels, nied, color="blue", alpha=0.6)
        ax2.set_ylabel("mm")
        ax2.set_title(f"Niederschlagsprognose – {methode}")

        plt.tight_layout()
        st.pyplot(fig)

    # Vergleich der letzten 7 Tage ( Niederschlag und Sonnenstunden)
    def plot_7tage_vergleich(self, ort_filter="Alle"):
        st.subheader("📊 Letzte 7 Tage – Niederschlag & Sonnenstunden")
        df = self.als_dataframe()
        if df.empty:
            st.info("Keine Daten vorhanden.")
            return

        # Filter nach Ort
        if ort_filter != "Alle":
            df = df[df["Standort"] == ort_filter]
            if df.empty:
                st.info("Keine Daten für diesen Ort.")
                return

        # Filter nach Quelle
        quelle_filter = st.selectbox(
            "Quelle auswählen:",
            ["Alle", "manuell", "simuliert", "live"],
            key="quelle_7tage",
        )
        if quelle_filter != "Alle":
            df = df[df["Quelle"] == quelle_filter]
            if df.empty:
                st.info(f"Keine Daten für Quelle '{quelle_filter}'.")
                return

        heute = pd.Timestamp(datetime.datetime.now())
        letzte7 = [heute - pd.Timedelta(days=i) for i in range(6, -1, -1)]
        nied, sonne = [], []
        for tag in letzte7:
            row = df[df["Datum"].dt.date == tag.date()]
            nied.append(row["Niederschlag"].sum() if not row.empty else 0)
            sonne.append(row["Sonnenstunden"].sum() if not row.empty else 0)

        if sum(nied) == 0 and sum(sonne) == 0:
            st.info("Keine Messwerte für die letzten 7 Tage.")
            return

        labels = [tag.strftime("%d-%m") for tag in letzte7]
        x = np.arange(len(labels))
        width = 0.35

        # Zwei nebeneinanderliegende Subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))

        ax1.bar(x, nied, width, color="blue")
        ax1.set_xticks(x)
        ax1.set_xticklabels(labels)
        ax1.set_ylabel("mm")
        ax1.set_title("Niederschlag letzte 7 Tage")

        ax2.bar(x, sonne, width, color="orange")
        ax2.set_xticks(x)
        ax2.set_xticklabels(labels)
        ax2.set_ylabel("h")
        ax2.set_title("Sonnenstunden letzte 7 Tage")

        plt.tight_layout()
        st.pyplot(fig)

    # Vergleich der Monate (Niederschlag und Sonnenstuunden)
    def plot_monatsvergleich(self, ort_filter="Alle"):
        st.subheader("📊 Monatsvergleich – Niederschlag & Sonnenstunden")
        df = self.als_dataframe()
        if df.empty:
            st.info("Keine Daten vorhanden.")
            return

        # Filter nach Ort
        if ort_filter != "Alle":
            df = df[df["Standort"] == ort_filter]
            if df.empty:
                st.info("Keine Daten für diesen Ort.")
                return

        # Filter nach Quelle
        quelle_filter = st.selectbox(
            "Quelle auswählen:",
            ["Alle", "manuell", "simuliert", "live"],
            key="quelle_monatsvergleich",
        )
        if quelle_filter != "Alle":
            df = df[df["Quelle"] == quelle_filter]
            if df.empty:
                st.info(f"Keine Daten für Quelle '{quelle_filter}'.")
                return

        # Jahr & Monat extrahieren
        df["Jahr"] = df["Datum"].dt.year
        df["Monat"] = df["Datum"].dt.month
        aktuelles_jahr = datetime.datetime.now().year
        letztes_jahr = aktuelles_jahr - 1

        # Summen für aktuelles Jahr
        nied_sum = (
            df[df["Jahr"] == aktuelles_jahr]
            .groupby("Monat")["Niederschlag"]
            .sum()
            .reindex(range(1, 13), fill_value=0)
        )
        sonne_sum = (
            df[df["Jahr"] == aktuelles_jahr]
            .groupby("Monat")["Sonnenstunden"]
            .sum()
            .reindex(range(1, 13), fill_value=0)
        )

        # Summen für letztes Jahr
        nied_letztes = (
            df[df["Jahr"] == letztes_jahr]
            .groupby("Monat")["Niederschlag"]
            .sum()
            .reindex(range(1, 13), fill_value=0)
        )
        sonne_letztes = (
            df[df["Jahr"] == letztes_jahr]
            .groupby("Monat")["Sonnenstunden"]
            .sum()
            .reindex(range(1, 13), fill_value=0)
        )

        if (
            nied_sum.sum() == 0
            and sonne_sum.sum() == 0
            and nied_letztes.sum() == 0
            and sonne_letztes.sum() == 0
        ):
            st.info("Keine Messwerte für die Monatsvergleiche.")
            return

        monate = [
            "Jan",
            "Feb",
            "Mär",
            "Apr",
            "Mai",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Okt",
            "Nov",
            "Dez",
        ]

        x = np.arange(len(monate))
        width = 0.35

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))

        # Niederschlag: aktuell vs letztes Jahr
        ax1.bar(
            x - width / 2,
            nied_sum.values,
            width=width,
            label=f"{aktuelles_jahr}",
            color="blue",
        )
        ax1.bar(
            x + width / 2,
            nied_letztes.values,
            width=width,
            label=f"{letztes_jahr}",
            color="orange",
            alpha=0.7,
        )
        ax1.set_xticks(x)
        ax1.set_xticklabels(monate)
        ax1.set_ylabel("mm")
        ax1.set_title("Monatlicher Niederschlag")
        ax1.legend()

        # Sonnenstunden: aktuell vs letztes Jahr
        ax2.bar(
            x - width / 2,
            sonne_sum.values,
            width=width,
            label=f"{aktuelles_jahr}",
            color="yellow",
        )
        ax2.bar(
            x + width / 2,
            sonne_letztes.values,
            width=width,
            label=f"{letztes_jahr}",
            color="green",
            alpha=0.7,
        )
        ax2.set_xticks(x)
        ax2.set_xticklabels(monate)
        ax2.set_ylabel("h")
        ax2.set_title("Monatliche Sonnenstunden")
        ax2.legend()

        plt.tight_layout()
        st.pyplot(fig)


# zeigt Debug - Infos an
def dev_mode_dashboard(wd, live_data=None):
    """
    Zeigt alle Debug-Infos im Dev-Mode an.
    - wd: WetterDaten/WetterAnalyse Objekt
    - live_data: optional dict mit Live-API Rohdaten
    """
    if not st.session_state.get("dev_mode", False):
        return  # Nur anzeigen, wenn Dev-Mode aktiv

    st.markdown("## 🔍 Dev-Mode Übersicht")

    # GitHub-Daten (alle geladenen)
    st.subheader("GitHub: geladene Messungen")
    st.text_area("GitHub-Daten", str([m.als_dict() for m in wd.messungen]), height=200)

    # Live-API Rohdaten + Sonnenstunden
    if live_data:
        st.subheader("Live-Daten API Rohwerte")
        st.json(live_data)

        try:
            sunrise_ts = live_data["sys"]["sunrise"]
            sunset_ts = live_data["sys"]["sunset"]
            clouds = live_data.get("clouds", {}).get("all", 100)
            sunrise = datetime.datetime.fromtimestamp(sunrise_ts)
            sunset = datetime.datetime.fromtimestamp(sunset_ts)
            tageslaenge = (sunset - sunrise).total_seconds() / 3600
            sonnenstunden = round((1 - clouds / 100) * tageslaenge, 1)

            # Ergebnisse anzeigen
            st.write(f"- Sonnenaufgang: {sunrise}")
            st.write(f"- Sonnenuntergang: {sunset}")
            st.write(f"- Tageslänge: {tageslaenge:.2f} h")
            st.write(f"- Bewölkung: {clouds}%")
            st.write(f"- Berechnete Sonnenstunden: {sonnenstunden} h")
        except Exception as e:
            st.error(f"Fehler bei Sonnenstunden-Berechnung: {e}")

    # Simulationsdaten
    st.subheader("Simulations-Daten")
    sim_data = [m.als_dict() for m in wd.messungen if m.quelle == "simuliert"]
    if sim_data:
        st.dataframe(sim_data)
    else:
        st.info("Keine Simulations-Daten vorhanden")

    # Live-Messungen Übersicht
    st.subheader("Live-Messungen")
    live_entries = [m.als_dict() for m in wd.messungen if m.quelle == "live"]
    if live_entries:
        st.dataframe(live_entries)
    else:
        st.info("Keine Live-Daten vorhanden")


# App-Funktionen
# Manuelle Eingabe mehrerer Wetterdaten (Tabelle)
def manuelle_eingabe(wd):
    st.subheader("Manuelle Wetterdaten eingeben (mehrere Tage)")

    # Vorlage für die Eingabetabelle
    df_input = pd.DataFrame(
        {
            "Datum": [datetime.datetime.now().date()],
            "Temp_min": [15.0],
            "Temp_max": [25.0],
            "Niederschlag": [0.0],
            "Sonnenstunden": [6.0],
            "Standort": [""],
        }
    )

    # Dynamische Tabelle, in der mehrere Zeilen hinzugefügt werden können
    edited_df = st.data_editor(df_input, num_rows="dynamic")

    if st.button("Speichern"):
        hinzugefuegt = 0
        uebersprungen = 0

        for _, row in edited_df.iterrows():
            try:
                datum_dt = pd.to_datetime(row["Datum"])
                temp_min = float(row["Temp_min"])
                temp_max = float(row["Temp_max"])
                niederschlag = float(row["Niederschlag"])
                sonnenstunden = float(row["Sonnenstunden"])
                standort = str(row["Standort"]).strip()

                # Prüfen, ob für diesen Tag & Standort schon ein Eintrag existiert
                if not wd.existiert_eintrag(datum_dt, standort):
                    wd.hinzufuegen(
                        WetterMessung(
                            datum=datum_dt,
                            temperatur=None,
                            niederschlag=niederschlag,
                            sonnenstunden=sonnenstunden,
                            standort=standort,
                            quelle="manuell",
                            temp_min=temp_min,
                            temp_max=temp_max,
                        )
                    )
                    hinzugefuegt += 1
                else:
                    uebersprungen += 1
            except Exception as e:
                st.warning(f"Fehler in einer Zeile: {e}")

        if hinzugefuegt > 0:
            wd.export_github_json()
            st.success(f"{hinzugefuegt} neue Einträge gespeichert ")

        if uebersprungen > 0:
            st.info(f"{uebersprungen} Einträge wurden übersprungen (bereits vorhanden)")

        # Leeren DataFrame anzeigen, um Eingabefeld zu resetten
        st.data_editor(
            pd.DataFrame(
                {
                    "Datum": [datetime.datetime.now().date()],
                    "Temp_min": [15.0],
                    "Temp_max": [25.0],
                    "Niederschlag": [0.0],
                    "Sonnenstunden": [6.0],
                    "Standort": [""],
                }
            ),
            num_rows="dynamic",
        )


def wettersimulation(wd):
    st.subheader("Simulation")
    ort = st.text_input("Ort")
    # Anzahl der Tage für die Simulation auswählen , 1-30, 7-Standart
    tage = st.number_input("Tage", 1, 30, 7)
    if st.button("Simulieren"):
        heute = datetime.datetime.now()
        # Für jeden Tag eine zufällige Messung erzeugen
        for i in range(tage):
            # Datum rückwärts berechnen
            datum = heute - datetime.timedelta(days=i)
            wd.hinzufuegen(
                WetterMessung(
                    datum,
                    round(random.uniform(15, 30), 1),  # Temperatur
                    round(random.uniform(0, 10), 1),  # Niederschlag
                    round(random.uniform(0, 12), 1),  # Sonnenstunden
                    quelle=Quelle.SIMULIERT,
                    standort=ort,
                )
            )
        # Alle simulierten Daten auf GitHub speichern
        wd.export_github_json()
        st.success(f"{tage} Tage simuliert!")


def live_wetterdaten(wd, ort):
    """
    Holt aktuelle Wetterdaten für einen Ort:
    - Temperatur, Niederschlag, Sonnenstunden
    - Speichert die Messung in wd
    - Gibt die Rohdaten der API zurück
    """

    # API-Key aus Secrets
    OWM_API_KEY = st.secrets["Legacy91988"]["OWM_API_KEY"]
    if not OWM_API_KEY:
        st.error("OpenWeatherMap API-Key ist nicht gesetzt!")
        return None
    # API-Request
    url = f"http://api.openweathermap.org/data/2.5/weather?q={ort}&appid={OWM_API_KEY}&units=metric&lang=de"
    try:
        data = requests.get(url, timeout=5).json()
    except Exception as e:
        st.error(f"Fehler beim Abrufen der Live-Daten: {e}")
        return None

    # Werte aus JSON extrahieren
    temp = data.get("main", {}).get("temp")
    niederschlag = data.get("rain", {}).get("1h", 0)

    if temp is None:
        msg = data.get("message", "Keine Temperaturdaten erhalten.")
        st.error(f"OpenWeatherMap-Fehler: {msg}")
        return data

    # Sonnenstunden berechnen
    try:
        sunrise_ts = data["sys"]["sunrise"]
        sunset_ts = data["sys"]["sunset"]
        clouds = data.get("clouds", {}).get("all", 100)  # Bewölkung in %
        sunrise = datetime.datetime.fromtimestamp(sunrise_ts)
        sunset = datetime.datetime.fromtimestamp(sunset_ts)
        tageslaenge = (sunset - sunrise).total_seconds() / 3600  # Stunden
        sonnenstunden = round((1 - clouds / 100) * tageslaenge, 1)
    except Exception as e:
        st.warning(f"Sonnenstunden konnten nicht berechnet werden: {e}")
        sonnenstunden = 0

    # Messung erstellen
    messung = WetterMessung(
        datum=datetime.datetime.now(),
        temperatur=temp,
        niederschlag=niederschlag,
        sonnenstunden=sonnenstunden,
        quelle=Quelle.LIVE,
        standort=ort,
    )
    # Prüfen, ob für heute schon ein Eintrag existiert
    if not wd.existiert_eintrag(messung.datum, ort):
        wd.hinzufuegen(messung)
        st.success(
            f"Live-Daten für {ort} hinzugefügt: {temp}°C, {niederschlag}mm, {sonnenstunden}h Sonne"
        )
    else:
        st.info(f"Für {ort} existiert bereits ein Eintrag für heute.")

    # Rohdaten für Dev-Mode zurückgeben
    return data


# Funktion zum Herunterladen aller Wetterdaten als CSV
def download_wetterdaten_csv(wd):
    st.subheader("Wetterdaten als CSV herunterladen")
    # Alle Messungen als DataFrame
    df = wd.als_dataframe()
    if df.empty:
        st.info("Keine Daten vorhanden zum Download")
        return
    # DataFrame in Csv Format umwandeln
    csv_data = df.to_csv(index=False)
    # Download-Button in Streamlit anzeigen
    st.download_button(
        label="Download als CSV",
        data=csv_data,
        file_name="wetterdaten.csv",
        mime="text/csv",
    )


# Funktion: Messungen anzeigen & (im Dev-Mode) löschen
def anzeigen_und_loeschen(wd):
    st.subheader(" Messungen anzeigen ")
    # Alle Messungen als DataFrame
    df = wd.als_dataframe()
    if df.empty:
        st.info("Keine Daten vorhanden.")
        return

    # Filter nach Ort
    orte = df["Standort"].unique()
    ort_filter = st.selectbox("Ort auswählen:", np.append("Alle", orte))
    if ort_filter != "Alle":
        df = df[df["Standort"] == ort_filter]

    # Tabelle anzeigen
    st.dataframe(
        df[
            [
                "ID",
                "Standort",
                "Datum",
                "Temperatur",
                "Niederschlag",
                "Sonnenstunden",
                "Quelle",
            ]
        ].sort_values("Datum", ascending=False)
    )

    # Dev-Mode: Einträge löschen
    if st.session_state.get("dev_mode", False):
        st.markdown("###  Einträge löschen (Dev-Mode)")
        # Liste der Einträge vorbereiten
        df_sorted = df.sort_values("Datum", ascending=False)
        eintraege = [
            f"{row['ID']} | {row['Standort']} | {row['Datum'].strftime('%d.%m.%Y')} | "
            f"{row['Temperatur']}°C | {row['Niederschlag']}mm | {row['Sonnenstunden']}h | {row['Quelle']}"
            for _, row in df_sorted.iterrows()
        ]
        # Auswahl per Multiselect
        if eintraege:
            auswahl = st.multiselect(
                "Einträge zum Löschen auswählen:",
                options=eintraege,
                key="dev_delete_multiselect",  # eindeutiger Key
            )
            # Löschen bestätigen
            if auswahl and st.button("Löschen", key="dev_delete_button"):
                for eintrag in auswahl:
                    eintrag_id = eintrag.split(" | ")[0]
                    wd.loeschen(eintrag_id)
                wd.export_github_json()
                st.success(f"{len(auswahl)} Messung(en) gelöscht!")

                # Trigger zum "Soft-Rerun"
                st.session_state["reload"] = not st.session_state.get("reload", False)


# Haupt-App
def main():
    st.title("🌤️ Wetterweiser")

    # Dev-Mode Initialisierung
    if "dev_mode" not in st.session_state:
        st.session_state.dev_mode = False
        # Soft-Rerun Flag
    if "reload" not in st.session_state:
        st.session_state["reload"] = False
    _ = st.session_state[
        "reload"
    ]  # sorgt dafür, dass die App neu ausgeführt wird, wenn reload sich ändert

    # Entwickler-Passwort abfragen
    eingabe = st.sidebar.text_input("Entwickler-Passwort", type="password")
    ist_entwickler = eingabe == st.secrets["dev"]["debug_password"]
    # Dev-Mode aktivieren, falls Passwort korrekt
    if ist_entwickler:
        st.session_state.dev_mode = st.sidebar.checkbox(
            "🔍 Debug-Modus aktiv", value=st.session_state.dev_mode
        )
        if st.session_state.dev_mode:
            st.sidebar.success("🔍 Dev-Mode aktiv")

    # Wetterdaten laden
    wd = WetterDaten.load_github_data(debug=st.session_state.dev_mode)

    # Dev-Mode Dashboard initial anzeigen
    live_data = None
    dev_mode_dashboard(wd, live_data=live_data)

    # Daten hinzufügen
    st.subheader("Daten hinzufügen")
    modus = st.radio("Modus", ("Manuelle Eingabe", "Simulation", "Live-Abfrage"))

    if modus == "Manuelle Eingabe":
        manuelle_eingabe(wd)
    elif modus == "Simulation":
        wettersimulation(wd)
    elif modus == "Live-Abfrage":
        ort = st.text_input("Ort für Live-Abfrage", "Musterstadt")
        if st.button("Live-Daten abrufen"):
            live_data = live_wetterdaten(wd, ort)
            dev_mode_dashboard(
                wd, live_data=live_data
            )  # Dev-Infos nach Live-Daten aktualisieren

        # CSV-Download
        download_wetterdaten_csv(wd)

    # Diagramme und Statistiken
    df = wd.als_dataframe()
    orte = df["Standort"].unique() if not df.empty else []
    ort_filter = st.selectbox(
        "Diagramm-Ort auswählen",
        options=np.append("Alle", orte) if len(orte) > 0 else ["Alle"],
    )

    wd.plot_3tage_prognose(ort_filter)
    regen_wahrscheinlichkeit = wd.regenwahrscheinlichkeit(tage=7, ort_filter=ort_filter)
    st.write(
        f"🌧️ Regenwahrscheinlichkeit in den letzten 7 Tagen: {regen_wahrscheinlichkeit}%"
    )
    wd.plot_7tage_vergleich(ort_filter)
    wd.plot_monatsvergleich(ort_filter)
    wd.jahresstatistik(ort_filter)

    # Messungen anzeigen & ggf. löschen
    anzeigen_und_loeschen(wd)


# Programm starten
if __name__ == "__main__":
    main()

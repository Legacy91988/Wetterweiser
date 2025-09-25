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
    """
    Enum zur Kennzeichnung der Datenquelle einer Wettermessung.

    Attribute:
        MANUELL: Daten wurden von Hand eingegeben.
        SIMULIERT: Daten wurden automatisch simuliert.
        LIVE: Daten stammen von einer Wetter-API.
    """

    MANUELL = "manuell"
    SIMULIERT = "simuliert"
    LIVE = "live"



    """
GitHub-Konfiguration für das Laden und Speichern von Wetterdaten.

Variablen:
    GITHUB_REPO: Name des GitHub-Repositories.
    GITHUB_BRANCH: Branch, aus dem die Daten geladen werden (Standard: "main").
    GITHUB_TOKEN: Persönlicher Zugriffstoken für Authentifizierung.
    GITHUB_JSON_PATH: Pfad zur JSON-Datei mit den Wetterdaten im Repository.
    """


GITHUB_REPO = st.secrets["Legacy91988"]["Wetterweiser"]
GITHUB_BRANCH = st.secrets["Legacy91988"].get("branch", "main")
GITHUB_TOKEN = st.secrets["Legacy91988"]["github_token"]
GITHUB_JSON_PATH = "wetterdaten.json"


class WetterMessung:
    """
    Repräsentiert eine einzelne Wettermessung.

    Attribute:
        id (str): Eindeutige ID der Messung
        datum (datetime): Datum der Messung
        temperatur (float|None): Durchschnittstemperatur
        temp_min (float|None): Minimale Temperatur
        temp_max (float|None): Maximale Temperatur
        niederschlag (float): Niederschlag in mm
        sonnenstunden (float): Sonnenstunden (falls None, wird zufällig erzeugt)
        quelle (str): Herkunft der Daten ("manuell", "simuliert", "live")
        standort (str): Ort der Messung
    """

    def __init__(
        self,
        datum,
        temperatur=None,  # Durchschnitt, optional
        niederschlag=0,
        sonnenstunden=None,
        id=None,
        quelle=Quelle.MANUELL,
        standort="Musterstadt",
        temp_min=None,
        temp_max=None,
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

        # min/max Temperaturen speichern
        self.temp_min = temp_min
        self.temp_max = temp_max

    def als_dict(self):
        """
        Gibt die Wettermessung als Dictionary zurück
        Berechnet die Durchschnittstemperatur, falls 'temperatur' None ist, aus Temp_min und Temp_max.
        Fallback auf 0, wenn keine Werte vorhanden.

        Returns:
            dict: Messdaten mit Feldern ID, Datum, Temperatur, Temp_min, Temp_max,
                  Niederschlag, Sonnenstunden, Quelle und Standort.
        """

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


class WetterDaten:
    """
    Verwaltung mehrerer Wettermessungen

    Speichert, fügt hinzu, ersetzt, löscht und wandelt Messungen in DataFrames um.
    """

    def __init__(self):
        self.messungen = []  # Liste aller Messung

    def hinzufuegen(self, messung: WetterMessung):
        """
        Fügt eine Wettermessung zur Liste hinzu
        """
        self.messungen.append(messung)

    # prüfen ob für einen Ort oder Datum ein Eintrag existiert
    def existiert_eintrag(self, datum, standort):
        for m in self.messungen:
            if m.standort == standort and m.datum.date() == datum.date():
                return True
        return False

    def ersetze_eintrag(self, datum, standort, neue_messung):
        """
        Prüft, ob bereits eine Wettermessung für ein bestimmtes Datum und einen bestimmten Ort existiert

        Args:
            datum (datetime-like): Das Datum der zu prüfenden Messung.
            standort (str): Der Name des Standorts.

        Returns:
            bool: True, wenn ein Eintrag existiert, sonst False.
        """

        # alte Messung entfernen
        self.messungen = [
            m
            for m in self.messungen
            if not (m.standort == standort and m.datum.date() == datum.date())
        ]
        # neue Messung hinzufügen
        self.hinzufuegen(neue_messung)

    def als_dataframe(self):
        """
        Wandelt alle gespeicherten Wettermessungen in ein pandas DataFrame um
        DataFrame mit allen Messungen, sortiert nach Datum
        Spalten: ID, Datum, Temperatur, Temp_min, Temp_max,
        Niederschlag, Sonnenstunden, Quelle, Standort
        """

        df = pd.DataFrame([m.als_dict() for m in self.messungen])
        if not df.empty:
            df["Datum"] = pd.to_datetime(df["Datum"])
            df = df.sort_values("Datum")  # nach Datum sortieren
        return df

    def loeschen(self, messung_id):
        """
        Löscht eine Wettermessung anhand ihrer eindeutigen ID.
        """
        self.messungen = [m for m in self.messungen if m.id != messung_id]

    def import_github_json(self):
        """
        Lädt Wettermessungen aus einer GitHub-JSON-Datei und fügt sie der App hinzu
        Vorgehensweise:
            1. Ruft die JSON-Datei über die GitHub-API ab.
            2. Dekodiert den Base64-Inhalt.
            3. Erstellt für jeden Eintrag ein WetterMessung-Objekt.
            4. Fügt nur Einträge hinzu, die noch nicht für Datum + Ort existieren.
            - Zeigt eine Info-Meldung an, dass die GitHub-Daten übernommen wurden.
        """

        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_JSON_PATH}?ref={GITHUB_BRANCH}"
        headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}

        try:
            response = requests.get(url, headers=headers, timeout=5)
            response.raise_for_status()
            data_json = response.json()
        except requests.RequestException as e:
            st.error(f"Fehler beim Zugriff auf GitHub: {e}")
            return

        if "content" not in data_json:
            msg = data_json.get("message", "Unbekannter Fehler beim Laden der Daten.")
            st.warning(f"GitHub-API meldet: {msg}")
            return

        try:
            content = base64.b64decode(data_json["content"]).decode("utf-8")
            data = json.loads(content)
        except Exception as e:
            st.error(f"Fehler beim Dekodieren der GitHub-Daten: {e}")
            return

        hinzugefuegte = 0
        for eintrag in data:
            temp_min = eintrag.get("Temp_min")
            temp_max = eintrag.get("Temp_max")
            temperatur = eintrag.get("Temperatur")

            # Alte Monatswerte reparieren: falls Temp_min/Temp_max None, setze auf Temperatur
            if (temp_min is None or temp_max is None) and temperatur is not None:
                temp_min = temp_min if temp_min is not None else temperatur
                temp_max = temp_max if temp_max is not None else temperatur

            messung = WetterMessung(
                id=eintrag.get("ID"),
                datum=eintrag.get("Datum"),
                temperatur=temperatur,
                niederschlag=eintrag.get("Niederschlag"),
                sonnenstunden=eintrag.get("Sonnenstunden"),
                quelle=eintrag.get("Quelle"),
                standort=eintrag.get("Standort"),
                temp_min=temp_min,
                temp_max=temp_max,
            )

            # Nur hinzufügen, wenn noch kein Eintrag für diesen Tag & Ort existiert
            if not self.existiert_eintrag(messung.datum, messung.standort):
                self.hinzufuegen(messung)

        st.info(f"GitHub-Daten wurden geladen und in die App übernommen.")

    @staticmethod
    def load_github_data(debug=False):
        """
        Lädt die Wetterdaten aus GitHub und gibt ein WetterAnalyse-Objekt zurück.

        Parameter:
            debug (bool): Wenn True, werden die Daten direkt geladen ohne Caching.
                          Wenn False, werden die Daten für 5 Minuten gecached.

        Rückgabe:
            WetterAnalyse: Objekt mit allen geladenen Messungen.

        Hinweise:
            - Verwendet intern `import_github_json`, um die Messungen zu übernehmen.
            - Durch Caching wird die GitHub-Abfrage bei wiederholtem Aufruf reduziert.
        """

        def _load_data():
            # Neues WetterAnalyse-Objekt erstellen
            wd = WetterAnalyse()
            wd.import_github_json()  # Messungen von GitHub hinzufügen
            return wd  # Korrekt: komplettes Objekt zurückgeben

        if debug:
            wd = _load_data()
        else:

            @st.cache_data(ttl=300)
            def cached_load_data():
                return _load_data()

            wd = cached_load_data()

        return wd


# Analyse & Diagramme
class WetterAnalyse(WetterDaten):
    def extremwerte(self, ort_filter="Alle"):
        """
        Berechnet die extremen Temperaturen (heißester und kältester Tag)

        Parameter:
            ort_filter (str): Optional. Filter für einen bestimmten Ort
            Standard: "Alle" (alle Standorte berücksichtigen)

        Rückgabe:
            tuple: Zwei Pandas Series:
                - max_tag: Zeile mit höchster Temp_max
                - min_tag: Zeile mit niedrigster Temp_min
            Falls keine Daten vorhanden sind, wird (None, None) zurückgegeben

        Hinweise:
            - Verwendet die gespeicherten Temp_min und Temp_max, nicht die Durchschnittstemperatur
            - DataFrame wird nach Ort gefiltert, falls ort_filter != "Alle"
        """
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
        """
        Zeigt eine Jahresübersicht für Temperatur, Niederschlag und Sonnenstunden an
        Anzeige:
            - Durchschnittstemperatur
            - Gesamtniederschlag
            - Gesamte Sonnenstunden
            - Extremwerte: heißester Tag (Maximaltemperatur) und kältester Tag (Minimaltemperatur)
        Hinweise:
            - Verwendet Temp_min und Temp_max für Extremwertberechnung.
            - Gibt nichts zurück, Daten werden direkt über Streamlit angezeigt.
        """

        st.subheader("Jahresstatistik")
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
        df_extrem = df.dropna(subset=["Temp_min", "Temp_max"])
        if df_extrem.empty:
            st.info("Keine Temperaturdaten für Extremwert-Berechnung.")
            return

        max_tag = df_extrem.loc[df_extrem["Temp_max"].idxmax()]
        min_tag = df_extrem.loc[df_extrem["Temp_min"].idxmin()]

        st.success(
            f"Heißester Tag: {max_tag['Datum'].date()} mit Max: {max_tag['Temp_max']}°C"
        )
        st.info(
            f"Kältester Tag: {min_tag['Datum'].date()} mit Min: {min_tag['Temp_min']}°C"
        )

    def regenwahrscheinlichkeit(self, tage=7, ort_filter="Alle"):
        """
        Berechnet die Regenwahrscheinlichkeit für die letzten Tage

        Parameter:
            tage (int): Anzahl der letzten Tage, die betrachtet werden. Standard: 7
            ort_filter (str): Optional. Filter für einen bestimmten Ort
                              Standard: "Alle" (alle Standorte berücksichtigen)

        Rückgabe:
            float: Regenwahrscheinlichkeit in Prozent, gerundet auf 1 Nachkommastelle.

        Hinweise:
            - Ein Tag zählt als "Regen", wenn der Niederschlag > 0 mm ist.
            - Nutzt nur die vorhandenen Wetterdaten im DataFrame.
        """

        df = self.als_dataframe()
        if df.empty:
            return 0
        if ort_filter != "Alle":
            df = df[df["Standort"] == ort_filter]
        letzte_tage = df.sort_values("Datum").tail(tage)
        regen_tage = letzte_tage[letzte_tage["Niederschlag"] > 0]  # Tage mit Regen
        wahrscheinlichkeit = len(regen_tage) / tage * 100  # % Regen
        return round(wahrscheinlichkeit, 1)

    def export_github_json(self, debug_mode=False):
        """
        Exportiert aktuelle Wetterdaten als JSON auf GitHub und lokal.

        Parameter:
            debug_mode (bool): Wenn True, zeigt die JSON-Payload in Streamlit an.

        Funktionsweise:
            - Alte GitHub-Daten werden geladen.
            - Neue Messungen + alte Messungen zusammengeführt, Duplikate per ID entfernt.
            - JSON-Datei lokal gespeichert (als Fallback).
            - Prüft, ob die Datei bereits auf GitHub existiert:
                - Wenn ja, wird die aktuelle SHA der Datei abgerufen und im Update-Payload
                  verwendet, damit GitHub die Datei korrekt überschreiben kann.
                - Wenn nein, wird ein neues File erstellt.
            - JSON wird Base64-codiert und mit einem PUT-Request auf GitHub hochgeladen.
            - Statusmeldung in Streamlit angezeigt (Erfolg oder Fehler).

        SHA (Secure Hash Algorithm):
            - GitHub speichert zu jeder Datei einen SHA-1 Hash.
            - Dieser Hash ist eine eindeutige Zeichenkette, die den aktuellen Inhalt der Datei
              repräsentiert.
            - Wenn man die Datei aktualisieren möchte, muss man GitHub die SHA der aktuellen
              Datei mitgeben.
            - GitHub prüft so, ob man wirklich die neueste Version der Datei überschreibt.
            - Ohne SHA würde ein Update fehlschlagen oder es könnte zu Konflikten kommen.
        """
        #Alte GitHub Daten laden
        #alt_wd = WetterAnalyse()
        #alt_wd.import_github_json()

        #kombi = list({m.id: m for m in (alt_wd.messungen + self.messungen)}.values())
        #daten = [m.als_dict() for m in kombi]
        
        # Nur aktuelle Messungen exportieren
        daten = [m.als_dict() for m in self.messungen]

        if debug_mode:
            st.text_area(
                "🔍 GitHub-Payload (Debug)", json.dumps(daten, indent=2), height=250
            )

        # Lokaler Fallback
        with open("wetterdaten.json", "w", encoding="utf-8") as f:
            json.dump(daten, f, ensure_ascii=False, indent=2)

        # GitHub URL & Header
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_JSON_PATH}"
        headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}

        # SHA holen (für Update)
        try:
            resp = requests.get(f"{url}?ref={GITHUB_BRANCH}", headers=headers)
            resp.raise_for_status()
            sha = resp.json().get("sha")
        except Exception:
            sha = None  # Datei existiert noch nicht

        # Content vorbereiten
        content = base64.b64encode(json.dumps(daten, indent=2).encode()).decode()

        # Payload für PUT
        payload = {
            "message": "Update Wetterdaten",
            "branch": GITHUB_BRANCH,
            "content": content,
        }
        if sha:
            payload["sha"] = sha  # SHA nur hinzufügen, wenn Datei existiert

        # PUT-Request
        resp = requests.put(url, headers=headers, data=json.dumps(payload))
        if resp.status_code in [200, 201]:
            st.success("Wetterdaten erfolgreich auf GitHub aktualisiert!")
        else:
            st.error(f"Fehler beim GitHub-Update: {resp.status_code} – {resp.text}")

    def prognose_mittelwert(self, serie, tage=3):
        """
        Berechnet eine einfache Wetterprognose auf Basis des Mittelwerts.

        Funktionsweise:
            - Nimmt die letzten 7 Werte der Serie (falls vorhanden).
            - Berechnet den Mittelwert dieser Werte.
            - Gibt eine Liste zurück, in der dieser Mittelwert für die nächsten 'tage' Tage wiederholt wird.
            - Falls keine Werte vorhanden, wird 0 zurückgegeben.
        """

        mw = (
            serie.tail(7).mean() if len(serie) >= 1 else 0
        )  # Mittelwert der letzten 7 Einträge
        return [round(mw, 1)] * tage

    # Prognose basierend auf dem Trend der letzten 7 Tage
    def prognose_trend(self, serie, tage=3, is_precipitation=False):
        """
        Erstellt eine einfache Prognose basierend auf dem Trend der letzten Werte

        Parameter:
            serie (pd.Series): Zeitreihe mit Werten (z.B. Temperaturen oder Niederschlag).
            tage (int): Anzahl der Tage, für die die Prognose erstellt werden soll.
            is_precipitation (bool): Wenn True, werden negative Prognosewerte (für Niederschlag) auf 0 gesetzt.

        Rückgabe:
            Liste von Länge 'tage' mit den prognostizierten Werten.

        Funktionsweise:
            - Nimmt die letzten 7 Werte der Serie (falls vorhanden).
            - Berechnet eine lineare Trendlinie (erste Ordnung) über diese Werte.
            - Extrapoliert die Trendlinie für die nächsten 'tage' Tage.
            - Für Niederschlag wird sichergestellt, dass keine negativen Werte entstehen.
            - Wenn nicht genügend Datenpunkte vorhanden sind, wird die Mittelwert-Prognose genutzt.
        """

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
        """
        Erstellt eine "Überraschungs"-Prognose mit kleinen zufälligen Schwankungen.

        Parameter:
            serie (pd.Series): Zeitreihe mit Werten (z.B. Temperaturen oder Niederschlag).
            tage (int): Anzahl der Tage, für die die Prognose erstellt werden soll.
            is_precipitation (bool): Wenn True, werden negative Werte für Niederschlag auf 0 gesetzt.

        Rückgabe:
            Liste von Länge 'tage' mit den prognostizierten Werten.

        Funktionsweise:
            - Berechnet den Mittelwert der letzten 7 Werte der Serie (falls vorhanden).
            - Fügt jedem prognostizierten Tag eine kleine Zufallsschwankung (-3 bis +3) hinzu.
            - Stellt sicher, dass Niederschlag nicht negativ ist.
            - Liefert so eine einfache, "spielerische" Prognose für die kommenden Tage.
        """

        mw = (
            serie.tail(7).mean() if len(serie) >= 1 else 0
        )  # Mittelwert der letzten 7 Werte
        werte = [
            round(mw + random.uniform(-3, 3), 1) for _ in range(tage)
        ]  # kleine Zufallsschwankung
        if is_precipitation:
            werte = [max(0, w) for w in werte]
        return werte

    def prognose_temperatur(self, tage=3):
        """
        Erstellt eine Temperaturprognose für die kommenden Tage.

        Parameter:
            tage (int): Anzahl der Tage, für die die Prognose erstellt werden soll.

        Rückgabe:
            Liste von Länge 'tage' mit den prognostizierten Durchschnittstemperaturen in °C.

        Funktionsweise:
            - Nutzt die gespeicherten Temperaturwerte aus allen Messungen.
            - Berechnet eine Prognose basierend auf dem linearen Trend der letzten 7 Werte.
            - Fällt die Trendberechnung aus (zu wenig Daten), wird der Mittelwert der letzten 7 Tage verwendet.
        """
        df = self.als_dataframe()
        if df.empty:
            return []
        return self.prognose_trend(df["Temperatur"], tage)

    def prognose_niederschlag(self, tage=3):
        """
        Erstellt eine Niederschlagsprognose für die kommenden Tage.

        Parameter:
            tage (int): Anzahl der Tage, für die die Prognose erstellt werden soll.

        Rückgabe:
            Liste von Länge 'tage' mit den prognostizierten Niederschlagsmengen in mm.

        Funktionsweise:
            - Nutzt die gespeicherten Niederschlagswerte aus allen Messungen.
            - Berechnet eine Prognose basierend auf dem linearen Trend der letzten 7 Werte.
            - Negative Werte werden auf 0 gesetzt, da Niederschlag nicht negativ sein kann.
            - Fällt die Trendberechnung aus (zu wenig Daten), wird der Mittelwert der letzten 7 Tage verwendet.
        """

        df = self.als_dataframe()
        if df.empty:
            return []
        return self.prognose_trend(df["Niederschlag"], tage, is_precipitation=True)

    def plot_3tage_prognose(self, ort_filter="Alle"):
        """
        Erstellt ein 3-Tage-Prognose-Diagramm für Temperatur und Niederschlag.

        Parameter:
            ort_filter (str): Optionaler Filter für einen bestimmten Ort.
                              Standard ist "Alle", dann werden alle Orte berücksichtigt.

        Funktionsweise:
            - Filtert die Daten nach Ort und optional nach Quelle (manuell, simuliert, live).
            - Der Benutzer wählt die Prognose-Methode:
              Mittelwert, Trend oder Überraschung.
            - Berechnet die Prognosen für die nächsten 3 Tage.
            - Visualisiert die Ergebnisse in einem nebeneinander liegenden Diagramm:
                - Linie für Temperatur (°C)
                - Balken für Niederschlag (mm)
            - Zeigt informative Meldungen an, falls keine Daten verfügbar sind.
        """
        st.subheader("3-Tage Prognose")
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

    def plot_7tage_vergleich(self, ort_filter="Alle"):
        """
        Visualisiert Niederschlag und Sonnenstunden der letzten 7 Tage.

        Parameter:
            ort_filter (str): Optionaler Filter für einen bestimmten Ort.
                              Standard ist "Alle", dann werden alle Orte berücksichtigt.

        Funktionsweise:
            - Filtert die Daten nach Ort und optional nach Quelle (manuell, simuliert, live).
            - Berechnet für die letzten 7 Tage die täglichen Summen von:
                - Niederschlag (mm)
                - Sonnenstunden (h)
            - Zeigt die Ergebnisse in zwei nebeneinanderliegenden Balkendiagrammen:
                - Linkes Diagramm: Niederschlag
                - Rechtes Diagramm: Sonnenstunden
            - Zeigt informative Meldungen an, falls keine Daten vorhanden sind.
        """

        st.subheader("Letzte 7 Tage – Niederschlag & Sonnenstunden")
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

        # Zwei nebeneinanderliegende plots
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
        """
        Zeigt den Monatsvergleich von Niederschlag und Sonnenstunden für aktuelles und
        letztes Jahr an.

        Parameter:
            ort_filter (str): Optionaler Filter für einen bestimmten Ort.
                              Standard ist "Alle", dann werden alle Orte berücksichtigt.

        Funktionsweise:
            - Filtert die Daten nach Ort und optional nach Quelle (manuell, simuliert, live).
            - Extrahiert Jahr und Monat aus den Datumsangaben.
            - Summiert für jeden Monat:
                - Niederschlag (mm)
                - Sonnenstunden (h)
            - Erstellt zwei nebeneinanderliegende Balkendiagramme:
                - Linkes Diagramm: Niederschlag – aktuelles Jahr vs letztes Jahr
                - Rechtes Diagramm: Sonnenstunden – aktuelles Jahr vs letztes Jahr
            - Zeigt informative Meldungen an, falls keine Daten vorhanden sind.
        """

        st.subheader("Monatsvergleich – Niederschlag & Sonnenstunden")
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

    st.markdown("Dev-Mode Übersicht")

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
def manuelle_eingabe(wd):
    """
    Stellt ein Interface für die manuelle Eingabe von Wetterdaten bereit.

    Parameter:
        wd (WetterDaten | WetterAnalyse): Objekt, in das die neuen Messungen eingefügt werden.

    Funktionsweise:
        - Zeigt einen Streamlit-Editor für Datum, Min/Max-Temperatur, Niederschlag, Sonnenstunden und Standort.
        - Berechnet optional den Durchschnitt aus Temp_min und Temp_max.
        - Prüft auf Duplikate (gleicher Tag + Ort) und ermöglicht, vorhandene Einträge zu überschreiben.
        - Speichert neue oder aktualisierte Messungen im WetterDaten-Objekt.
        - Optional: Exportiert die Daten zu GitHub (Debug-Modus, falls aktiv).
        - Setzt die Eingabefelder für die nächste Messung zurück.
    """
    st.subheader("Manuelle Eingabe der Wetterdaten")

    # Standardwerte für neue Eingabe
    if "manuelle_input_df" not in st.session_state:
        st.session_state.manuelle_input_df = pd.DataFrame(
            {
                "Datum": [datetime.datetime.now().date()],
                "Temp_min": [15.0],
                "Temp_max": [25.0],
                "Niederschlag": [0.0],
                "Sonnenstunden": [6.0],
                "Standort": [""],
            }
        )

    # Editor für Benutzereingabe
    edited_df = st.data_editor(
        st.session_state.manuelle_input_df,
        num_rows="dynamic",
        key="manuelle_editor_input",
    )

    # Speichern-Button
    if st.button("Speichern", key="btn_speichern_manuell"):
        neue_messungen = []

        for _, row in edited_df.iterrows():
            messung = WetterMessung(
                datum=row["Datum"],
                temp_min=float(row["Temp_min"]) if pd.notna(row["Temp_min"]) else None,
                temp_max=float(row["Temp_max"]) if pd.notna(row["Temp_max"]) else None,
                temperatur=(
                    (float(row["Temp_min"]) + float(row["Temp_max"])) / 2
                    if pd.notna(row["Temp_min"]) and pd.notna(row["Temp_max"])
                    else None
                ),
                niederschlag=(
                    float(row["Niederschlag"]) if pd.notna(row["Niederschlag"]) else 0
                ),
                sonnenstunden=(
                    float(row["Sonnenstunden"])
                    if pd.notna(row["Sonnenstunden"])
                    else None
                ),
                quelle=Quelle.MANUELL,
                standort=row.get("Standort", ""),
            )
            neue_messungen.append(messung)

        # Prüfen auf Duplikate (Datum + Ort)
        duplicate_entries = [
            m for m in neue_messungen if wd.existiert_eintrag(m.datum, m.standort)
        ]
        if duplicate_entries:
            st.warning(
                f"{len(duplicate_entries)} Einträge existieren bereits für das Datum/den Ort!"
            )
            overwrite = st.checkbox("Vorhandene Einträge ersetzen?")
            if overwrite:
                for m in duplicate_entries:
                    wd.ersetze_eintrag(m.datum, m.standort, m)
                # Entferne die ersetzten aus neue_messungen, um sie nicht erneut hinzuzufügen
                neue_messungen = [
                    m for m in neue_messungen if m not in duplicate_entries
                ]

        # Alle neuen (nicht-doppelten) Messungen hinzufügen
        for m in neue_messungen:
            wd.hinzufuegen(m)

        # GitHub Push: nur debug_mode=True, wenn Dev-Mode aktiv
        wd.export_github_json(debug_mode=st.session_state.get("dev_mode", False))
        st.success("Wetterdaten gespeichert!")

        # Eingabe zurücksetzen
        st.session_state.manuelle_input_df = pd.DataFrame(
            {
                "Datum": [datetime.datetime.now().date()],
                "Temp_min": [15.0],
                "Temp_max": [25.0],
                "Niederschlag": [0.0],
                "Sonnenstunden": [6.0],
                "Standort": [""],
            }
        )


def wettersimulation(wd):
    """
        Führt eine zufällige Wettersimulation durch und speichert die Ergebnisse.

        Parameter:
            wd (WetterDaten | WetterAnalyse): Objekt, in das die simulierten Messungen eingefügt werden.

        Funktionsweise:
            - Nutzer gibt Ort und Anzahl der Simulations-Tage (1–30) ein.
            - Für jeden Tag wird eine zufällige Messung erzeugt:
                - Temperatur (15–30 °C)
                - Niederschlag (0–10 mm)
                - Sonnenstunden (0–12 h)
            - Quelle der Messungen wird als 'simuliert' markiert.
            - Die erzeugten Messungen werden dem WetterDaten-Objekt hinzugefügt.
            - Optional: Alle simulierten Daten werden auf GitHub gespeichert.
            - Zeigt eine Erfolgsmeldung mit der Anzahl simulierten Tage.
            """

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


def download_wetterdaten_csv(wd):
    """
    Ermöglicht den Download aller Wetterdaten als CSV-Datei über Streamlit.

    Parameter:
        wd (WetterDaten | WetterAnalyse): Objekt, aus dem die Wetterdaten als DataFrame extrahiert werden.

    Funktionsweise:
        - Wandelt alle gespeicherten Messungen in ein pandas DataFrame um.
        - Prüft, ob Daten vorhanden sind; falls nicht, wird eine Info-Meldung angezeigt.
        - Wandelt das DataFrame in CSV-Format um.
        - Stellt einen Download-Button in Streamlit bereit, mit dem der Benutzer die CSV-Datei herunterladen kann.
    """

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
    """
    Zeigt alle Wetter-Messungen in einer Tabelle an und ermöglicht im Dev-Mode das Löschen einzelner Einträge.

    Parameter:
        wd (WetterDaten | WetterAnalyse): Objekt, das die Wetter-Messungen enthält.

    Funktionsweise:
        - Wandelt alle Messungen in ein DataFrame um und zeigt es sortiert nach Datum.
        - Ermöglicht die Filterung nach Ort.
        - Im Dev-Mode:
            - Zeigt ein Multiselect für die Auswahl von Einträgen zum Löschen.
            - Löscht ausgewählte Einträge aus dem Objekt und optional auf GitHub.
            - Aktualisiert die Tabelle nach dem Löschen automatisch.
    """
    st.subheader("Messungen anzeigen")
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
        st.markdown("### 🗑️ Einträge löschen (Dev-Mode)")

        df_sorted = df.sort_values("Datum", ascending=False)
        eintraege = [
            f"{row['ID']} | {row['Standort']} | {row['Datum'].strftime('%d.%m.%Y')} | "
            f"{row['Temperatur']}°C | {row['Niederschlag']}mm | {row['Sonnenstunden']}h | {row['Quelle']}"
            for _, row in df_sorted.iterrows()
        ]

        if eintraege:
            auswahl = st.multiselect(
                "Einträge zum Löschen auswählen:",
                options=eintraege,
                key="dev_delete_multiselect",
            )

            if auswahl and st.button("Löschen", key="dev_delete_button"):
                geloeschte_messungen = []

                for eintrag in auswahl:
                    eintrag_id = eintrag.split(" | ")[0]
                    # Vorher speichern für Debug
                    messung = next((m for m in wd.messungen if m.id == eintrag_id), None)
                    if messung:
                        geloeschte_messungen.append(messung.als_dict())
                    # Dann löschen
                    wd.loeschen(eintrag_id)

                # GitHub-Push optional, Debug anzeigen
                if st.session_state.get("dev_mode", False):
                    st.text_area(
                        "GitHub-Payload (Debug) – zu löschende Messungen",
                        json.dumps(geloeschte_messungen, indent=2),
                        height=200
                    )

                wd.export_github_json(debug_mode=st.session_state.get("dev_mode", False))
                st.success(f"{len(auswahl)} Messung(en) gelöscht!")

                # Soft-Rerun Trigger: Tabelle wird neu geladen
                st.session_state["reload"] = not st.session_state.get("reload", False)


# Haupt-App
def main():
    """
    Hauptfunktion der Wetterweiser-App (Streamlit).

    Funktionsweise:
        - Initialisiert den Dev-Mode und einen Soft-Rerun-Trigger.
        - Fragt optional ein Entwickler-Passwort ab, um den Debug-Modus zu aktivieren.
        - Lädt Wetterdaten von GitHub als WetterAnalyse-Objekt.
        - Zeigt Dev-Mode Dashboard mit Debug-Infos (falls aktiviert).
        - Bietet drei Modi zum Hinzufügen von Daten:
            1. Manuelle Eingabe
            2. Simulation zufälliger Wetterdaten
            3. Live-Abfrage von Wetterdaten über API
        - Ermöglicht den Download aller Wetterdaten als CSV.
        - Zeigt Diagramme und Statistiken:
            - 3-Tage Prognose
            - Regenwahrscheinlichkeit der letzten 7 Tage
            - Vergleich der letzten 7 Tage
            - Monatsvergleich
            - Jahresstatistik
        - Zeigt alle Messungen an und ermöglicht im Dev-Mode das Löschen von Einträgen.

    Hinweis:
        - Die Funktion steuert die gesamte App-Logik und Oberfläche in Streamlit.
    """

    st.title("🌤️ Wetterweiser")

    # Dev-Mode Initialisierung
    if "dev_mode" not in st.session_state:
        st.session_state.dev_mode = False
    if "reload" not in st.session_state:
        st.session_state["reload"] = False
    _ = st.session_state["reload"]  # Trigger für Soft-Rerun

    # Entwickler-Passwort abfragen
    eingabe = st.sidebar.text_input("Entwickler-Passwort", type="password")
    ist_entwickler = eingabe == st.secrets["dev"]["debug_password"]
    if ist_entwickler:
        st.session_state.dev_mode = st.sidebar.checkbox(
            "🔍 Debug-Modus aktiv", value=st.session_state.dev_mode
        )
        if st.session_state.dev_mode:
            st.sidebar.success("Dev-Mode aktiv")

    # Wetterdaten laden (als WetterAnalyse-Objekt)
    wd = WetterAnalyse.load_github_data(debug=st.session_state.dev_mode)

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
            dev_mode_dashboard(wd, live_data=live_data)

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
        f" Regenwahrscheinlichkeit in den letzten 7 Tagen: {regen_wahrscheinlichkeit}%"
    )
    wd.plot_7tage_vergleich(ort_filter)
    wd.plot_monatsvergleich(ort_filter)
    wd.jahresstatistik(ort_filter)

    # Messungen anzeigen & ggf. löschen
    anzeigen_und_loeschen(wd)


# Programm starten
if __name__ == "__main__":
    main()

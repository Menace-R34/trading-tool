import streamlit as st


def zeige_erklaerungen_kennzahlen():
    erklaerungen = {
        "Acc % (Genauigkeit)": "Historische Trefferquote (%) aller bisherigen Prognosen für diesen spezifischen Wert.",
        "# (Anzahl)": "Anzahl der historisch bereits ausgewerteten Prognosen für diesen Ticker.",
        "Day € / Swing €": "Erwarteter Netto-Ertrag eines Trades nach Abzug von Gebühren und Berücksichtigung der Trefferwahrscheinlichkeit.",
        "Score (D) / Score (S)": "Gesamtbewertung (0-100), wie attraktiv der Wert aktuell für Day- bzw. Swingtrading ist.",
        "Sig. (D) / Sig. (S)": "Signalstärke (Schwach, Mittel, Stark) basierend auf dem erreichten Score.",
        "Hold (D) / Hold (S)": "Historisch ermittelte optimale Haltedauer in Tagen für erfolgreiche Trades bei dieser Aktie.",
        "CRV (D) / CRV (S)": "Chance-Risiko-Verhältnis. Ein Wert von 2.0 bedeutet, dass die Gewinnchance doppelt so hoch ist wie das Risiko.",
        "ATR relativ %": "Durchschnittliche tägliche Handelsspanne im Verhältnis zum Kurs (Wichtig für die Volatilität).",
        "Hit-Rate > 2 %": "Prozentualer Anteil der Tage, an denen die Aktie eine Bewegung von mehr als 2 % vollzogen hat.",
        "RSI 14": "Relative Strength Index. Werte < 30 gelten als überverkauft, > 70 als überkauft.",
        "Saison-Score": "Bewertung basierend auf historischen Monatsmustern (Saisonalität).",
        "News-Score": "Einfluss aktueller Nachrichten auf den Kurs (von -1.0 bis +1.0).",
        "Status (Handelsfenster)": "Zeigt an, ob der Wert aktuell in seinem primären Handelszeitraum liegt (z.B. US-Börsenzeit).",
        "Abstand Hoch/Tief %": "Distanz des aktuellen Kurses zum 52-Wochen-Hoch bzw. Tief.",
        "Trend Up / Stabil": "Indikatoren für die technische Trendstruktur der Aktie.",
        "Ø Endperformance %": "Durchschnittliche Rendite aller bisherigen abgeschlossenen Prognosen dieses Tickers.",
        "Day / Swing Kauf": "Klare Entscheidungsempfehlung des Systems (JA oder NEIN)."
    }

    with st.expander("Detaillierte Erklärung der Kennzahlen", expanded=True):
        for begriff in sorted(erklaerungen.keys()):
            st.write(f"**{begriff}**: {erklaerungen[begriff]}")


def zeige_marktlage_box(marktlage):
    st.markdown("### Gesamtmarktlage")

    col_1, col_2, col_3, col_4 = st.columns(4)
    col_1.metric("Marktlage", marktlage["Marktlage"])
    col_2.metric("Trend", marktlage["Trend"])
    col_3.metric("Volatilität", marktlage["Volatilität"])
    col_4.metric("DAX 20T %", f"{marktlage['DAX Perf 20 Tage %']:.2f}")

    st.info(f"**{marktlage['Signalbias']}** — {marktlage['Kommentar']}")


def seite_hilfe():
    from modules.prognose_speicher import _zeitstempel_str
    st.subheader("Hilfe & Dokumentation")
    st.write("Hier findest du die Definitionen der im Dashboard verwendeten Kennzahlen und Abkürzungen.")
    st.caption(f"Letzte Aktualisierung der Hilfe: {_zeitstempel_str()} deutsche Zeit")
    zeige_erklaerungen_kennzahlen()

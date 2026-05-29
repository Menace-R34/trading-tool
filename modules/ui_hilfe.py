import streamlit as st


def zeige_erklaerungen_kennzahlen():
    erklaerungen = {
        "Acc %": "Historische Trefferquote aller bewerteten Day- und Swing-Signale für diesen Ticker.",
        "#": "Anzahl der bereits bewerteten Strategie-Ergebnisse für diesen Ticker. Day und Swing zählen separat; ein einziger Auswertezyklus kann deshalb bis zu zwei Ergebnisse erzeugen.",
        "Status": "Aktuelles Handelsfenster des Werts, z.B. Europa offen, US vor Open oder geschlossen.",
        "Day Kauf / Swing Kauf": "Klare Entscheidung des Systems für die jeweilige Strategie. Nur JA-Signale werden später historisch bewertet.",
        "Sig. (D) / Sig. (S)": "Signalstärke für Day bzw. Swing. Sie wird aus Score, Chance-Risiko-Profil und Filterregeln abgeleitet.",
        "Score (D) / Score (S)": "Gesamtbewertung, wie attraktiv der Wert aktuell für Day- bzw. Swingtrading ist.",
        "Day € / Swing €": "Erwarteter Netto-Ertrag eines Trades nach Gebühren und Trefferwahrscheinlichkeit.",
        "Kurs €": "Letzter geladener Kurs in Euro bzw. in Euro umgerechnet.",
        "Kaufzeit DE": "Historisch günstigste Intraday-Kaufzeit in deutscher Zeit.",
        "Verkauf DE": "Historisch günstigste Intraday-Verkaufszeit in deutscher Zeit.",
        "Opt Buy (D) / Opt Buy (S)": "Selbstoptimierte Buy-in-Zeit aus historischen Day- bzw. Swing-Prognosen. Falls zu wenig Daten vorhanden sind, bleibt die allgemeine Intraday-Zeit maßgeblich.",
        "Opt TP (D) / Opt TP (S)": "Selbstoptimierte Take-Profit- bzw. Exit-Zeit aus historischen Day- bzw. Swing-Prognosen.",
        "Opt Hit (D) / Opt Hit (S)": "Historische Trefferquote der selbstoptimierten Intraday-Zeit für Day bzw. Swing.",
        "Hold Min": "Durchschnittliche historische Intraday-Haltedauer in Minuten.",
        "Intra %": "Historisch beobachtetes durchschnittliches Intraday-Potenzial.",
        "CRV (D) / CRV (S)": "Chance-Risiko-Verhältnis. Ein Wert von 2.0 bedeutet, dass die Zielchance doppelt so groß ist wie das Risiko.",
        "Buy-in DE (D) / Buy-in DE (S)": "Geplante Buy-in-Zeit für Day bzw. Swing in deutscher Zeit.",
        "TP-Zeit DE (D) / TP-Zeit DE (S)": "Geplante Take-Profit-Zeit für Day bzw. Swing in deutscher Zeit.",
        "Hold (D) / Hold (S)": "Historisch ermittelte typische Haltedauer erfolgreicher Day- bzw. Swing-Signale.",
        "ATR relativ %": "Durchschnittliche tägliche Handelsspanne im Verhältnis zum Kurs (Wichtig für die Volatilität).",
        "Hit-Rate > 2 %": "Prozentualer Anteil der Tage, an denen die Aktie eine Bewegung von mehr als 2 % vollzogen hat.",
        "RSI 14": "Relative Strength Index. Werte < 30 gelten als überverkauft, > 70 als überkauft.",
        "Saison": "Bewertung basierend auf historischen Monatsmustern und saisonaler Stärke.",
        "News": "Einfluss aktueller Nachrichten auf den Kurs von -1.0 bis +1.0.",
        "Abstand Hoch/Tief %": "Distanz des aktuellen Kurses zum 52-Wochen-Hoch bzw. Tief.",
        "Trend Up / Stabil": "Indikatoren für die technische Trendstruktur der Aktie.",
        "Ø Endperformance %": "Durchschnittliche Rendite aller bisherigen abgeschlossenen Prognosen dieses Tickers.",
        "Day Status / Swing Status": "Bewertungsstand einer gespeicherten Prognose, z.B. abgeschlossen, Zeitablauf, nicht bewertet oder keine Daten.",
        "Day Treffer / Swing Treffer": "Historisches Ergebnis der jeweiligen Strategie. 1 steht für Treffer, 0 für Fehler, leer für nicht bewertbar oder neutral.",
        "Day Erreicht am / Swing Erreicht am": "Datum, an dem Take Profit, Stop Loss oder das Ende der Haltedauer erreicht wurde.",
        "Day Rendite % / Swing Rendite %": "Tatsächliche Rendite der bewerteten Prognose bis Treffer, Fehler oder Zeitablauf."
    }

    with st.expander("Detaillierte Erklärung der Kennzahlen", expanded=True):
        for begriff in sorted(erklaerungen.keys()):
            st.write(f"**{begriff}**: {erklaerungen[begriff]}")


def zeige_erklaerungen_auswertung():
    with st.expander("Wann gilt eine Prognose als erfüllt?", expanded=False):
        st.write("Eine Prognose wird nur bewertet, wenn für die jeweilige Strategie `Kauf = JA` gespeichert wurde.")
        st.write("Sie gilt als Treffer, sobald der Kurs innerhalb der Haltedauer das Take-Profit-Level erreicht.")
        st.write("Wird kein Take Profit und kein Stop Loss erreicht, entscheidet nach Ablauf der Haltedauer die Rendite: positiv zählt als Treffer, negativ als Fehler, neutral bleibt ohne Trefferwertung.")
        st.write("Day und Swing werden getrennt bewertet. Dadurch kann eine Aktie aus einer einzigen gespeicherten Prognose zwei historische Ergebnisse erhalten.")


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
    zeige_erklaerungen_auswertung()

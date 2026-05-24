# =========================================================
# 01_IMPORTS
# =========================================================
import streamlit as st


# =========================================================
# 02_NAVIGATION
# =========================================================
def erstelle_navigation():
    st.sidebar.title("Navigation")

    navigation_punkte = [
        "Start",
        "Marktüberblick",
        "Signale",
        "Europa Aktien",
        "USA Aktien",
        "Prognosekontrolle",
        "Einstellungen",
        "Hilfe",
    ]

    auswahl = st.sidebar.radio(
        "Bereich wählen",
        navigation_punkte,
        label_visibility="collapsed"
    )

    st.sidebar.divider()

    # --- AKTIONEN ---
    col1, col2 = st.sidebar.columns(2)
    
    if col1.button("🔄 Markt", help="Marktdaten & Cache aktualisieren", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    if col2.button("📌 Fix", help="Prognosen für heute festschreiben", use_container_width=True):
        st.session_state["fixiere_prognosen_trigger"] = True
        st.rerun()

    st.sidebar.divider()
    
    with st.sidebar.expander("🕒 Börsenzeiten & Risiken"):
        st.markdown("**🇪🇺 Europa (Frankfurt/Xetra)**")
        st.markdown("""
<div style='font-size:0.85em; line-height: 1.4;'>
<b>08:00 – 09:00</b> | Vorbörse<br>
<span style='color:#FFC000;'>Risiko: erhöht (eingeschränkt)</span><br><br>
<b>09:00 – 17:30</b> | Hauptmarkt<br>
<span style='color:#00B050;'>Risiko: gering (volle Liquidität)</span><br><br>
<b>17:30 – 19:00</b> | Nachbörse (früh)<br>
<span style='color:#FFC000;'>Risiko: erhöht (reduziert)</span><br><br>
<b>19:00 – 22:00</b> | Nachbörse (spät)<br>
<span style='color:#FF8000;'>Risiko: hoch (sehr dünn)</span><br><br>
<b>22:00 – 08:00</b> | Geschlossen<br>
<span style='color:#C00000;'>Kein Handel</span>
</div>
""", unsafe_allow_html=True)

        st.divider()
        
        st.markdown("**🇺🇸 USA (in DE-Zeit)**")
        st.markdown("""
<div style='font-size:0.85em; line-height: 1.4;'>
<b>10:00 – 15:30</b> | Vorbörse<br>
<span style='color:#FFC000;'>Risiko: erhöht (eingeschränkt)</span><br><br>
<b>15:30 – 22:00</b> | Hauptmarkt<br>
<span style='color:#00B050;'>Risiko: gering (volle Liquidität)</span><br><br>
<b>22:00 – 02:00</b> | Nachbörse<br>
<span style='color:#FFC000;'>Risiko: erhöht (eingeschränkt)</span><br><br>
<b>02:00 – 10:00</b> | Geschlossen<br>
<span style='color:#C00000;'>Kein Handel</span>
</div>
""", unsafe_allow_html=True)

    return auswahl
# =========================================================
# 01_IMPORTS
# =========================================================
import os
import math
import json
from datetime import datetime, timedelta

import requests


# =========================================================
# 02_OPTIONALE_OPENAI_ANBINDUNG
# =========================================================
try:
    from openai import OpenAI
except Exception:
    OpenAI = None


# =========================================================
# 03_KONSTANTEN
# =========================================================
NEWSAPI_URL = "https://newsapi.org/v2/everything"

MAKRO_THEMEN = {
    "krieg": {
        "keywords": ["war", "conflict", "attack", "missile", "military", "escalation"],
        "default_impact": "risk_off",
    },
    "oel_knappheit": {
        "keywords": ["oil shortage", "opec", "crude spike", "energy shock", "supply cut"],
        "default_impact": "energy_up",
    },
    "chip_knappheit": {
        "keywords": ["chip shortage", "semiconductor shortage", "foundry capacity"],
        "default_impact": "semis_up_autos_down",
    },
    "lieferkette": {
        "keywords": ["supply chain", "shipping disruption", "port congestion", "freight costs"],
        "default_impact": "mixed",
    },
    "zinsen_inflation": {
        "keywords": ["inflation", "cpi", "rate hike", "rate cut", "fed", "ecb", "bond yields"],
        "default_impact": "macro_rates",
    },
    "sanktionen_zoelle": {
        "keywords": ["sanctions", "tariffs", "trade restrictions", "export ban"],
        "default_impact": "sector_specific",
    },
    "rohstoffe": {
        "keywords": ["copper shortage", "lithium shortage", "steel prices", "commodity spike"],
        "default_impact": "commodity_sensitive",
    },
}

SEKTOR_REGELN = {
    "Technology": {
        "positiv": ["rate cut", "ai demand", "upgrade", "strong guidance", "outperform"],
        "negativ": ["rate hike", "downgrade", "export ban", "chip shortage", "lawsuit"],
    },
    "Energy": {
        "positiv": ["oil shortage", "supply cut", "opec", "energy shock", "crude spike"],
        "negativ": ["oil glut", "demand slump", "price cap"],
    },
    "Industrials": {
        "positiv": ["infrastructure", "defense demand", "order growth"],
        "negativ": ["supply chain", "tariffs", "shipping disruption", "input cost pressure"],
    },
    "Consumer Cyclical": {
        "positiv": ["consumer demand", "strong sales", "rate cut"],
        "negativ": ["inflation", "war", "recession", "weak demand", "cost pressure"],
    },
    "Healthcare": {
        "positiv": ["approval", "positive trial", "strong demand"],
        "negativ": ["lawsuit", "recall", "trial failure"],
    },
    "Financial Services": {
        "positiv": ["higher margins", "rate stability", "strong earnings"],
        "negativ": ["credit losses", "recession fears", "bank stress"],
    },
    "Basic Materials": {
        "positiv": ["commodity spike", "supply shortage", "pricing power"],
        "negativ": ["demand weakness", "oversupply"],
    },
    "Aerospace & Defense": {
        "positiv": ["war", "military spending", "defense budget", "security demand"],
        "negativ": ["budget cuts", "contract delay"],
    },
    "Automotive": {
        "positiv": ["rate cut", "demand recovery"],
        "negativ": ["chip shortage", "recall", "tariffs", "input costs"],
    },
    "Transportation": {
        "positiv": ["lower fuel prices", "strong freight demand"],
        "negativ": ["oil shortage", "war", "shipping disruption", "port congestion"],
    },
}


# =========================================================
# 04_HILFSFUNKTIONEN
# =========================================================
def _zeitstempel():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _sichere_liste(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _normalisiere_score(score, divisor=3.0):
    return max(-1.0, min(1.0, math.tanh(score / divisor)))


def _baue_newsapi_query(ticker, firmenname=None, sektor=None):
    teile = [ticker]
    if firmenname:
        teile.append(f'"{firmenname}"')

    unternehmens_query = " OR ".join(teile)

    makro_begriffe = [
        '"war" OR "conflict" OR "sanctions" OR "tariffs" OR "inflation" OR "rate cut" OR "rate hike"',
        '"oil shortage" OR "supply chain" OR "shipping disruption" OR "chip shortage"',
        '"commodity spike" OR "energy shock" OR "port congestion"'
    ]

    if sektor:
        makro_begriffe.append(f'"{sektor}"')

    makro_query = " OR ".join(makro_begriffe)

    return f"({unternehmens_query}) OR ({makro_query})"


def _lade_news_via_newsapi(query, api_key, tage=7, page_size=30, sprache="en"):
    if not api_key:
        return []

    von_datum = (datetime.utcnow() - timedelta(days=tage)).strftime("%Y-%m-%d")

    params = {
        "q": query,
        "from": von_datum,
        "language": sprache,
        "sortBy": "publishedAt",
        "pageSize": page_size,
        "apiKey": api_key,
    }

    try:
        response = requests.get(NEWSAPI_URL, params=params, timeout=20)
        response.raise_for_status()
        daten = response.json()
        return daten.get("articles", [])
    except Exception:
        return []


def _extrahiere_texte_aus_artikeln(artikel):
    texte = []

    for eintrag in artikel:
        titel = str(eintrag.get("title", "")).strip()
        beschreibung = str(eintrag.get("description", "")).strip()
        quelle = ""
        if isinstance(eintrag.get("source"), dict):
            quelle = str(eintrag["source"].get("name", "")).strip()

        text = " | ".join([teil for teil in [titel, beschreibung, quelle] if teil])
        if text:
            texte.append(text)

    return texte


def _regelbasierter_sektor_score(texte, sektor=None):
    if not texte:
        return {
            "score": 0.0,
            "treiber": [],
            "risiken": [],
            "kommentar": "Keine Texte vorhanden",
        }

    score = 0.0
    treiber = []
    risiken = []

    sektor_regeln = SEKTOR_REGELN.get(sektor, {"positiv": [], "negativ": []})

    for text in texte:
        text_klein = text.lower()

        # sektorbezogene Regeln
        for wort in sektor_regeln.get("positiv", []):
            if wort in text_klein:
                score += 1.2
                treiber.append(wort)

        for wort in sektor_regeln.get("negativ", []):
            if wort in text_klein:
                score -= 1.2
                risiken.append(wort)

        # makrothemen
        for thema, daten in MAKRO_THEMEN.items():
            for wort in daten["keywords"]:
                if wort in text_klein:
                    if daten["default_impact"] in ["energy_up", "semis_up_autos_down"]:
                        score += 0.4
                        treiber.append(f"{thema}: {wort}")
                    elif daten["default_impact"] in ["risk_off", "macro_rates", "sector_specific", "commodity_sensitive", "mixed"]:
                        score -= 0.2
                        risiken.append(f"{thema}: {wort}")

    score_norm = _normalisiere_score(score)

    return {
        "score": round(float(score_norm), 2),
        "treiber": sorted(list(set(treiber)))[:8],
        "risiken": sorted(list(set(risiken)))[:8],
        "kommentar": "Regelbasierte Makro-/Sektorbewertung",
    }


def _ki_bewertung_mit_openai(ticker, firmenname, sektor, texte):
    if OpenAI is None:
        return None

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    if not texte:
        return None

    prompt = f"""
Du bewertest Nachrichten für Aktienhandel.

Ticker: {ticker}
Firmenname: {firmenname or "unbekannt"}
Sektor: {sektor or "unbekannt"}

Analysiere die folgenden Nachrichten:
{chr(10).join(f"- {t}" for t in texte[:25])}

Bewerte:
1. unternehmensspezifischen Einfluss
2. makroökonomischen Einfluss
3. Einfluss des Weltgeschehens wie Krieg, Rohstoffknappheit, Lieferketten, Sanktionen, Zinsen
4. wahrscheinliche kurzfristige Wirkung für Daytrading
5. wahrscheinliche Wirkung für Swingtrading

Antworte ausschließlich als JSON mit diesen Feldern:
{{
  "news_score_gesamt": Zahl von -1 bis 1,
  "news_score_unternehmen": Zahl von -1 bis 1,
  "news_score_makro": Zahl von -1 bis 1,
  "label": "Stark Positiv|Positiv|Neutral|Negativ|Stark Negativ",
  "treiber": ["..."],
  "risiken": ["..."],
  "kommentar_kurz": "...",
  "bias_day": "Positiv|Neutral|Negativ",
  "bias_swing": "Positiv|Neutral|Negativ"
}}
"""

    try:
        client = OpenAI(api_key=api_key)
        response = client.responses.create(
            model="gpt-5",
            input=prompt
        )

        text = response.output_text.strip()
        daten = json.loads(text)
        return daten
    except Exception:
        return None


def _label_aus_score(score):
    if score >= 0.6:
        return "Stark Positiv"
    if score >= 0.2:
        return "Positiv"
    if score <= -0.6:
        return "Stark Negativ"
    if score <= -0.2:
        return "Negativ"
    return "Neutral"


# =========================================================
# 05_HAUPTFUNKTION
# =========================================================
def berechne_news_score(
    ticker,
    firmenname=None,
    sektor=None,
    manuelle_texte=None,
    nutze_newsapi=True,
    nutze_openai=False,
):
    """
    News-Bewertung mit:
    - Unternehmens-News
    - Makro-/Weltgeschehen
    - optionaler OpenAI-Klassifikation
    - regelbasiertem Fallback
    """

    newsapi_key = os.getenv("NEWSAPI_KEY")
    artikel = []

    if nutze_newsapi and newsapi_key:
        query = _baue_newsapi_query(ticker=ticker, firmenname=firmenname, sektor=sektor)
        artikel = _lade_news_via_newsapi(query=query, api_key=newsapi_key)

    texte_api = _extrahiere_texte_aus_artikeln(artikel)
    texte_manuell = _sichere_liste(manuelle_texte)
    alle_texte = [t for t in (texte_api + texte_manuell) if str(t).strip()]

    if not alle_texte:
        return {
            "News-Score": 0.0,
            "News-Score Unternehmen": 0.0,
            "News-Score Makro": 0.0,
            "News-Label": "Neutral",
            "News-Kommentar": "Keine News-Daten verfügbar",
            "News-Quelle": "Keine externe Quelle verbunden",
            "News-Zeitpunkt": _zeitstempel(),
            "News-Anzahl": 0,
            "Treiber": "",
            "Risiken": "",
            "Bias Day": "Neutral",
            "Bias Swing": "Neutral",
        }

    if nutze_openai:
        ki_resultat = _ki_bewertung_mit_openai(
            ticker=ticker,
            firmenname=firmenname,
            sektor=sektor,
            texte=alle_texte
        )
    else:
        ki_resultat = None

    if ki_resultat:
        return {
            "News-Score": round(float(ki_resultat.get("news_score_gesamt", 0.0)), 2),
            "News-Score Unternehmen": round(float(ki_resultat.get("news_score_unternehmen", 0.0)), 2),
            "News-Score Makro": round(float(ki_resultat.get("news_score_makro", 0.0)), 2),
            "News-Label": str(ki_resultat.get("label", "Neutral")),
            "News-Kommentar": str(ki_resultat.get("kommentar_kurz", "KI-Bewertung")),
            "News-Quelle": "NewsAPI + OpenAI",
            "News-Zeitpunkt": _zeitstempel(),
            "News-Anzahl": len(alle_texte),
            "Treiber": ", ".join(_sichere_liste(ki_resultat.get("treiber"))[:6]),
            "Risiken": ", ".join(_sichere_liste(ki_resultat.get("risiken"))[:6]),
            "Bias Day": str(ki_resultat.get("bias_day", "Neutral")),
            "Bias Swing": str(ki_resultat.get("bias_swing", "Neutral")),
        }

    regel_resultat = _regelbasierter_sektor_score(alle_texte, sektor=sektor)

    return {
        "News-Score": round(float(regel_resultat["score"]), 2),
        "News-Score Unternehmen": 0.0,
        "News-Score Makro": round(float(regel_resultat["score"]), 2),
        "News-Label": _label_aus_score(regel_resultat["score"]),
        "News-Kommentar": regel_resultat["kommentar"],
        "News-Quelle": "NewsAPI + Regelwerk" if artikel else "Regelwerk lokal",
        "News-Zeitpunkt": _zeitstempel(),
        "News-Anzahl": len(alle_texte),
        "Treiber": ", ".join(regel_resultat["treiber"]),
        "Risiken": ", ".join(regel_resultat["risiken"]),
        "Bias Day": _label_aus_score(regel_resultat["score"]).replace("Stark ", ""),
        "Bias Swing": _label_aus_score(regel_resultat["score"]).replace("Stark ", ""),
    }
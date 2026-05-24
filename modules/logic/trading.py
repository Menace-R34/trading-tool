from modules.logic.common import _wert, _begrenzt, _hole_marktlage, _signal_farbe, _signal_textfarbe
from modules.logic.scoring import berechne_daytrading_score, berechne_swingtrading_score

def berechne_erwartungswert(potenzial, risiko, trefferquote, gebuehren=2.0):
    try:
        potenzial = float(potenzial)
        risiko = float(risiko)
        trefferquote = _begrenzt(float(trefferquote), 0.0, 1.0)
        gebuehren = float(gebuehren)
    except:
        return 0.0, 0.0

    if risiko <= 0: return 0.0, -gebuehren
    erwartung = (trefferquote * potenzial) - ((1 - trefferquote) * risiko)
    return round(erwartung, 2), round(erwartung - gebuehren, 2)

def berechne_trade_parameter_day(statistik):
    kurs = _wert(statistik, "Letzter Kurs €", 0)
    atr = _wert(statistik, "ATR 14 €", 0)
    if kurs == 0 or atr == 0: return {"Stop Loss €": 0.0, "Take Profit €": 0.0, "CRV": 0.0, "Potenzial €": 0.0}
    
    stop_loss = kurs - (atr * 0.9)
    take_profit = kurs + (atr * 1.5)
    risiko = kurs - stop_loss
    chance = take_profit - kurs
    return {
        "Stop Loss €": round(stop_loss, 2),
        "Take Profit €": round(take_profit, 2),
        "CRV": round(chance / risiko if risiko > 0 else 0.0, 2),
        "Potenzial €": round(chance, 2),
    }

def berechne_trade_parameter_swing(statistik):
    kurs = _wert(statistik, "Letzter Kurs €", 0)
    atr = _wert(statistik, "ATR 14 €", 0)
    if kurs == 0 or atr == 0: return {"Stop Loss €": 0.0, "Take Profit €": 0.0, "CRV": 0.0, "Potenzial €": 0.0}
    
    stop_loss = kurs - (atr * 1.5)
    take_profit = kurs + (atr * 3.0)
    risiko = kurs - stop_loss
    chance = take_profit - kurs
    return {
        "Stop Loss €": round(stop_loss, 2),
        "Take Profit €": round(take_profit, 2),
        "CRV": round(chance / risiko if risiko > 0 else 0.0, 2),
        "Potenzial €": round(chance, 2),
    }

def bewerte_daytrading_signal(statistik, saison, news, markt=None):
    score = berechne_daytrading_score(statistik, saison, news, markt=markt)
    atr_relativ = _wert(statistik, "ATR relativ %")
    hitrate_2 = _wert(statistik, "Hit-Rate > 2 %")
    tagesrange_avg = _wert(statistik, "Ø Tagesrange %")
    rsi = _wert(statistik, "RSI 14", 0)
    news_score = _wert(news, "News-Score", 0.0)
    kurs = _wert(statistik, "Letzter Kurs €", 0.0)
    marktlage = _hole_marktlage(markt)

    trade = berechne_trade_parameter_day(statistik)
    crv = trade.get("CRV", 0.0)
    potenzial = trade.get("Potenzial €", 0.0)
    stop_loss = trade.get("Stop Loss €", 0.0)
    risiko = kurs - stop_loss if kurs > 0 and stop_loss > 0 else 0.0
    
    erwartung, netto_erwartung = berechne_erwartungswert(potenzial, risiko, hitrate_2/100.0)

    score_schwelle = 28; min_crv = 1.3; min_potenzial = 5.0; min_netto = 1.0
    if marktlage == "Risk-Off":
        score_schwelle = 31; min_crv = 1.5; min_potenzial = 6.0; min_netto = 1.5
    elif marktlage == "Risk-On":
        score_schwelle = 26; min_crv = 1.2; min_potenzial = 5.0; min_netto = 1.0

    gruende = []
    if atr_relativ >= 2.0: gruende.append("ATR ausreichend")
    if hitrate_2 >= 35: gruende.append("gute Bewegungsfrequenz")
    if tagesrange_avg >= 2.0: gruende.append("handelbare Tagesrange")
    if 25 <= rsi <= 70: gruende.append("RSI brauchbar")
    if news_score > 0.15: gruende.append("positiver News-Impuls")
    if crv >= min_crv: gruende.append("CRV ausreichend")
    if potenzial >= min_potenzial: gruende.append("Potenzial ausreichend")
    if netto_erwartung >= min_netto: gruende.append("positiver Erwartungswert")
    elif netto_erwartung < 0: gruende.append("negativer Erwartungswert")

    kauf_ja = (score >= score_schwelle and atr_relativ >= 1.8 and hitrate_2 >= 30 and tagesrange_avg >= 1.5 and 20 <= rsi <= 75 and news_score >= -0.35 and crv >= min_crv and potenzial >= min_potenzial and netto_erwartung >= min_netto)
    signal = "JA" if kauf_ja else "NEIN"
    
    if score >= score_schwelle + 8 and netto_erwartung >= min_netto: signalstaerke = "Stark"
    elif score >= score_schwelle + 2 and netto_erwartung >= 0: signalstaerke = "Mittel"
    else: signalstaerke = "Schwach"

    return {
        "Day Score": score, "Day Kauf": signal, "Day Signalstärke": signalstaerke, "Day Kommentar": ", ".join(gruende),
        "Day Farbe": _signal_farbe(signal), "Day Textfarbe": _signal_textfarbe(signal),
        "Day Stop Loss €": trade["Stop Loss €"], "Day Take Profit €": trade["Take Profit €"],
        "Day CRV": trade["CRV"], "Day Potenzial €": trade["Potenzial €"],
        "Day Erwartung €": erwartung, "Day Netto €": netto_erwartung
    }

def bewerte_swingtrading_signal(statistik, saison, news, markt=None):
    score = berechne_swingtrading_score(statistik, saison, news, markt=markt)
    trend_up = _wert(statistik, "Trend Up", False)
    trend_stabil = _wert(statistik, "Trend Stabil", False)
    perf_20 = _wert(statistik, "Perf 20 Tage %")
    rsi = _wert(statistik, "RSI 14", 0)
    saison_score = _wert(saison, "Saison-Score", 0.0)
    news_score = _wert(news, "News-Score", 0.0)
    marktlage = _hole_marktlage(markt)

    trade = berechne_trade_parameter_swing(statistik)
    crv = trade.get("CRV", 0.0)
    potenzial = trade.get("Potenzial €", 0.0)
    stop_loss = trade.get("Stop Loss €", 0.0)
    kurs = _wert(statistik, "Letzter Kurs €", 0.0)
    
    tq_swing = 0.45
    if trend_up: tq_swing += 0.10
    elif trend_stabil: tq_swing += 0.05
    
    risiko = kurs - stop_loss if kurs > 0 and stop_loss > 0 else 0.0
    erwartung_swing, netto_swing = berechne_erwartungswert(potenzial, risiko, tq_swing)

    score_schwelle = 32; min_crv = 1.5; min_potenzial = 10.0
    if marktlage == "Risk-Off":
        score_schwelle = 36; min_crv = 1.7; min_potenzial = 12.0
    elif marktlage == "Risk-On":
        score_schwelle = 30; min_crv = 1.4; min_potenzial = 9.0

    gruende = []
    if trend_up: gruende.append("klarer Aufwärtstrend")
    elif trend_stabil: gruende.append("stabile Trendstruktur")
    if perf_20 > 0: gruende.append("positives Momentum")
    if 35 <= rsi <= 70: gruende.append("RSI im brauchbaren Bereich")
    if saison_score > 0: gruende.append("saisonale Unterstützung")
    if news_score > 0: gruende.append("positive Nachrichtenlage")
    if crv >= min_crv: gruende.append("CRV ausreichend")
    if potenzial >= min_potenzial: gruende.append("Potenzial ausreichend")

    kauf_ja = (score >= score_schwelle and (trend_up or trend_stabil) and perf_20 >= -2 and 30 <= rsi <= 75 and saison_score >= -1.5 and news_score >= -0.4 and crv >= min_crv and potenzial >= min_potenzial)
    signal = "JA" if kauf_ja else "NEIN"
    
    if score >= score_schwelle + 10: signalstaerke = "Stark"
    elif score >= score_schwelle + 2: signalstaerke = "Mittel"
    else: signalstaerke = "Schwach"

    return {
        "Swing Score": score, "Swing Kauf": signal, "Swing Signalstärke": signalstaerke, "Swing Kommentar": ", ".join(gruende),
        "Swing Farbe": _signal_farbe(signal), "Swing Textfarbe": _signal_textfarbe(signal),
        "Swing Stop Loss €": trade["Stop Loss €"], "Swing Take Profit €": trade["Take Profit €"],
        "Swing CRV": trade["CRV"], "Swing Potenzial €": trade["Potenzial €"],
        "Swing Erwartung €": erwartung_swing, "Swing Netto €": netto_swing
    }

def bewerte_signale(statistik, saison, news, markt=None):
    day = bewerte_daytrading_signal(statistik, saison, news, markt=markt)
    swing = bewerte_swingtrading_signal(statistik, saison, news, markt=markt)
    return {**day, **swing}

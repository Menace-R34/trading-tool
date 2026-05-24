from modules.logic.common import _wert, _begrenzt, _hole_marktlage

def berechne_daytrading_score(statistik, saison, news, markt=None):
    score = 0.0
    tagesrange_avg = _wert(statistik, "Ø Tagesrange %")
    tagesrange_median = _wert(statistik, "Median Tagesrange %")
    volatilitaet = _wert(statistik, "Volatilität %")
    atr_relativ = _wert(statistik, "ATR relativ %")
    hitrate_2 = _wert(statistik, "Hit-Rate > 2 %")
    hitrate_3 = _wert(statistik, "Hit-Rate > 3 %")
    tagesveraenderung = abs(_wert(statistik, "Tagesveränderung %"))
    rsi = _wert(statistik, "RSI 14", 0)
    news_score = _wert(news, "News-Score", 0.0)
    bias_day = str(_wert(news, "Bias Day", "Neutral")).lower()
    marktlage = _hole_marktlage(markt)

    score += _begrenzt(tagesrange_avg, 0, 8) * 2.8
    score += _begrenzt(tagesrange_median, 0, 8) * 2.2
    score += _begrenzt(volatilitaet, 0, 80) * 0.18
    score += _begrenzt(atr_relativ, 0, 10) * 2.6
    score += _begrenzt(hitrate_2, 0, 100) * 0.10
    score += _begrenzt(hitrate_3, 0, 100) * 0.08
    score += _begrenzt(tagesveraenderung, 0, 8) * 0.9
    score += _begrenzt(news_score, -1, 1) * 4.0

    if bias_day == "positiv": score += 2.0
    elif bias_day == "negativ": score -= 2.0

    if 35 <= rsi <= 60: score += 4.0
    elif 25 <= rsi < 35: score += 2.0
    elif 60 < rsi <= 70: score += 1.5
    elif rsi > 75: score -= 3.5
    elif rsi < 20: score -= 1.5

    saison_score = _wert(saison, "Saison-Score", 0.0)
    score += _begrenzt(saison_score, -3, 3) * 0.3

    if marktlage == "Risk-On": score += 2.0
    elif marktlage == "Risk-Off": score -= 3.0

    return round(score, 2)

def berechne_swingtrading_score(statistik, saison, news, markt=None):
    score = 0.0
    trend_up = _wert(statistik, "Trend Up", False)
    trend_stabil = _wert(statistik, "Trend Stabil", False)
    perf_20 = _wert(statistik, "Perf 20 Tage %")
    abstand_hoch = _wert(statistik, "Abstand zum Hoch %")
    abstand_tief = _wert(statistik, "Abstand zum Tief %")
    volatilitaet = _wert(statistik, "Volatilität %")
    rsi = _wert(statistik, "RSI 14", 0)
    saison_score = _wert(saison, "Saison-Score", 0.0)
    saison_label = str(_wert(saison, "Saison-Label", "Neutral")).lower()
    news_score = _wert(news, "News-Score", 0.0)
    bias_swing = str(_wert(news, "Bias Swing", "Neutral")).lower()
    marktlage = _hole_marktlage(markt)

    if trend_up: score += 22
    elif trend_stabil: score += 12

    score += _begrenzt(perf_20, -10, 20) * 0.8

    if abstand_hoch <= 0:
        momentum_bonus = max(0, 10 - abs(abstand_hoch))
        score += momentum_bonus * 1.1

    if abstand_tief < 5: score -= 4
    elif 5 <= abstand_tief <= 20: score += 4
    elif 20 < abstand_tief <= 60: score += 7
    elif abstand_tief > 60: score += 4

    score += _begrenzt(volatilitaet, 0, 80) * 0.08
    score += _begrenzt(saison_score, -5, 5) * 1.6
    score += _begrenzt(news_score, -1, 1) * 3.0

    if saison_label == "positiv": score += 2.0
    elif saison_label == "negativ": score -= 2.0
    if bias_swing == "positiv": score += 2.0
    elif bias_swing == "negativ": score -= 2.0

    if 45 <= rsi <= 65: score += 6
    elif 35 <= rsi < 45: score += 3
    elif 65 < rsi <= 75: score += 2
    elif rsi > 75: score -= 6
    elif rsi < 25: score -= 4

    if marktlage == "Risk-On": score += 3.0
    elif marktlage == "Risk-Off": score -= 4.0

    return round(score, 2)

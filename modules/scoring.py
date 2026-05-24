# =========================================================
# SCORING ZENTRALE
# =========================================================

def berechne_gesamtscore(stats, news_score, saison_score):
    score_day = 0
    score_swing = 0

    # =========================
    # VOLATILITÄT → DAYTRADING
    # =========================
    if stats["volatilitaet"] > 0.4:
        score_day += 25
    elif stats["volatilitaet"] > 0.25:
        score_day += 15

    # =========================
    # INTRADAY RANGE
    # =========================
    if stats["atr_relativ"] > 0.03:
        score_day += 20

    # =========================
    # TREND → SWING
    # =========================
    if stats["trend"] == "bullish":
        score_swing += 20
    elif stats["trend"] == "bearish":
        score_swing -= 10

    # =========================
    # MOMENTUM
    # =========================
    if stats["perf_20"] > 5:
        score_swing += 15
    elif stats["perf_20"] < -5:
        score_swing -= 10

    # =========================
    # NEWS
    # =========================
    score_day += news_score * 5
    score_swing += news_score * 10

    # =========================
    # SAISONALITÄT
    # =========================
    score_swing += saison_score * 10

    return score_day, score_swing
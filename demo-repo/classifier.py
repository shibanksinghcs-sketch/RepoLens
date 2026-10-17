def classify_score(score):
    if score < 1.5:
        return "FAMILIAR"
    elif score < 2.5:
        return "BORDERLINE"
    return "UNFAMILIAR"

def normalize_score(score, maximum):
    if maximum <= 0:
        raise ValueError("maximum must be positive")
    return score / maximum

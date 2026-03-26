
def classify(text: str) -> str:
    """
    Mock AI classification function for citizen complaints.
    Returns a category based on keyword matching.
    """
    text_lower = text.lower()

    infrastructure_keywords = [
        "пат", "мост", "расвета", "улица", "тротоар", "асфалт",
        "road", "bridge", "street", "light", "pothole"
    ]
    communal_keywords = [
        "вода", "отпад", "канализација", "ѓубре", "смет",
        "water", "waste", "sewage", "garbage", "trash"
    ]
    admin_keywords = [
        "документ", "дозвола", "барање", "сертификат", "апликација",
        "document", "permit", "request", "certificate", "license"
    ]
    safety_keywords = [
        "безбедност", "опасност", "кражба", "несреќа", "пожар",
        "safety", "danger", "theft", "accident", "fire"
    ]

    scores = {
        "Инфраструктура": sum(1 for kw in infrastructure_keywords if kw in text_lower),
        "Комунални услуги": sum(1 for kw in communal_keywords if kw in text_lower),
        "Административни услуги": sum(1 for kw in admin_keywords if kw in text_lower),
        "Јавна безбедност": sum(1 for kw in safety_keywords if kw in text_lower),
    }

    best_match = max(scores, key=scores.get)

    if scores[best_match] == 0:
        return "Некласифицирано"

    return best_match


# category = classify("A car caught fire on the road near student dormitory Goce Delcev today. Tragic accident.")
# print(category)
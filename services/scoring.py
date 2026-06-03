from services.constraints import haversine_km


def preference_match_score(poi, preferences):
    """
    计算用户输入偏好与 POI 的匹配程度。

    当前主要看：
    - food 偏好是否命中 cuisine
    - tags 是否命中 POI tags
    """
    score = 0

    user_foods = preferences.get("food", [])
    user_tags = preferences.get("tags", [])

    poi_cuisines = poi.get("cuisine", [])
    poi_tags = poi.get("tags", [])

    for food in user_foods:
        if food in poi_cuisines:
            score += 25

    for tag in user_tags:
        if tag in poi_tags:
            score += 10

    return score


def calculate_poi_score(poi, preferences, user_prefs=None, option_type="hard_constraint"):
    """
    计算 POI 综合评分。

    评分由四部分组成：
    1. 用户评分 rating
    2. 偏好匹配
    3. 排队时间惩罚
    4. 价格惩罚或历史偏好加分
    """
    score = poi.get("rating", 0) * 20

    match_score = preference_match_score(poi, preferences)
    if option_type == "demand_satisfaction":
        score += match_score * 1.8
    elif option_type == "hard_constraint":
        score += match_score * 0.8
    else:
        score += match_score

    wait_time = poi.get("wait_time", 0)
    wait_penalty = {
        "demand_satisfaction": 0.25,
        "hard_constraint": 0.9,
        "preference_insight": 0.45
    }.get(option_type, 0.4)
    score -= wait_time * wait_penalty

    budget = preferences.get("budget")
    if budget:
        price_ratio = poi.get("price", 0) / max(budget, 1)
        if price_ratio > 0.5:
            price_penalty = 14 if option_type == "hard_constraint" else 8
            score -= price_ratio * price_penalty

    if option_type == "preference_insight" and user_prefs:
        explicit = user_prefs.get("explicit_preferences", {})
        history = user_prefs.get("history_behavior", {})

        preferred_tags = explicit.get("preferred_tags", [])
        disliked_tags = explicit.get("disliked_tags", [])
        frequent_tags = history.get("frequent_tags", [])
        avoid_poi_ids = history.get("avoid_poi_ids", [])
        liked_poi_types = history.get("liked_poi_types", [])
        visited_poi_ids = history.get("visited_poi_ids", [])

        for tag in set(preferred_tags + frequent_tags):
            if tag in poi.get("tags", []):
                score += 16
            for comment in poi.get("ugc_comments", []):
                if tag in comment:
                    score += 4

        for tag in disliked_tags:
            if tag in poi.get("tags", []):
                score -= 24

        if poi.get("type") in liked_poi_types:
            score += 8

        if poi.get("is_hidden_gem"):
            score += 18

        if poi.get("popularity", 0) >= 85:
            score -= 10

        if poi.get("id") in visited_poi_ids:
            score -= 25

        if poi.get("id") in avoid_poi_ids:
            score -= 50

    if option_type == "demand_satisfaction":
        score += poi.get("rating", 0) * 5
        score += poi.get("popularity", 0) * 0.12

    if option_type == "hard_constraint":
        score -= poi.get("price", 0) * 0.12

    return round(score, 2)


def choose_next_poi(current_point, candidate_pois):
    """
    贪心选择下一个 POI。

    选择逻辑：
    - 综合评分越高越好；
    - 距离当前位置越近越好；
    - 因此使用 score - distance_penalty 作为排序依据。
    """
    best_poi = None
    best_value = -999999

    for poi in candidate_pois:
        distance = haversine_km(
            current_point["lng"],
            current_point["lat"],
            poi["lng"],
            poi["lat"]
        )

        value = poi["engine_score"] - distance * 8

        if value > best_value:
            best_value = value
            best_poi = poi

    return best_poi

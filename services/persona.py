from services.constraints import haversine_km


SUPPORTED_PERSONA_TAGS = {
    "parent_child_family",
    "elder_family",
    "couple_date",
    "friends_group",
    "solo_citywalk",
}

SUPPORTED_PREFERENCE_TAGS = {
    "food",
    "photo",
    "culture",
    "nature",
    "shopping",
    "night_view",
    "niche",
    "relaxed",
}

SUPPORTED_CONSTRAINT_TAGS = {
    "less_walking",
    "low_budget",
    "avoid_queue",
    "indoor_first",
    "half_day",
    "end_before_night",
}


PERSONA_STRATEGIES = {
    "parent_child_family": {
        "label": "亲子家庭",
        "suitable_for": {"family"},
        "preferred_types": {"park", "scenic", "restaurant", "dessert", "tea_house"},
        "preferred_tags": {"亲子", "公园", "草坪", "放松", "免费", "轻松", "本地风味"},
        "avoid_tags": {"登高", "徒步", "排队久", "热闹", "夜游"},
        "poi_count_delta": -1,
        "stay_delta": 8,
        "distance_penalty": 7,
        "wait_penalty": 0.8,
        "price_penalty": 0.05,
        "score_weights": {"family": 28, "comfort": 20},
    },
    "elder_family": {
        "label": "带父母/长辈",
        "suitable_for": {"family"},
        "preferred_types": {"museum", "bookstore", "tea_house", "cafe", "restaurant", "park"},
        "preferred_tags": {"安静", "文化", "展览", "适合休息", "茶饮", "放松", "轻松"},
        "avoid_tags": {"登高", "徒步", "热闹", "夜游", "排队久"},
        "poi_count_delta": -1,
        "stay_delta": 10,
        "distance_penalty": 10,
        "wait_penalty": 1.0,
        "price_penalty": 0.03,
        "score_weights": {"comfort": 30, "family": 12},
    },
    "couple_date": {
        "label": "情侣约会",
        "suitable_for": {"couple"},
        "preferred_types": {"cafe", "dessert", "tea_house", "scenic", "park", "restaurant", "historic"},
        "preferred_tags": {"情侣", "约会", "拍照", "夜景", "甜品", "咖啡", "安静", "花园"},
        "avoid_tags": {"亲子", "快速补给"},
        "poi_count_delta": 0,
        "stay_delta": 5,
        "distance_penalty": 5,
        "wait_penalty": 0.35,
        "price_penalty": 0.02,
        "score_weights": {"romantic": 32, "comfort": 8},
    },
    "friends_group": {
        "label": "朋友出游",
        "suitable_for": {"friends"},
        "preferred_types": {"restaurant", "drink", "dessert", "mall", "historic", "scenic"},
        "preferred_tags": {"朋友聚餐", "适合聊天", "热闹", "小吃", "逛街", "商圈", "拍照"},
        "avoid_tags": set(),
        "poi_count_delta": 0,
        "stay_delta": 0,
        "distance_penalty": 4,
        "wait_penalty": 0.35,
        "price_penalty": 0.02,
        "score_weights": {"social": 34},
    },
    "solo_citywalk": {
        "label": "单人 Citywalk",
        "suitable_for": {"solo"},
        "preferred_types": {"historic", "bookstore", "cafe", "scenic", "park", "tea_house"},
        "preferred_tags": {"citywalk", "小众", "文化", "历史街区", "老街巷", "安静", "本地生活"},
        "avoid_tags": {"朋友聚餐", "热闹", "亲子"},
        "poi_count_delta": 0,
        "stay_delta": 0,
        "distance_penalty": 5,
        "wait_penalty": 0.45,
        "price_penalty": 0.04,
        "score_weights": {"comfort": 8, "intensity": 8},
    },
}


PREFERENCE_STRATEGIES = {
    "food": {
        "types": {"restaurant", "cafe", "drink", "dessert", "tea_house"},
        "tags": {"小吃", "本地风味", "朋友聚餐", "咖啡", "甜品", "茶饮", "性价比"},
    },
    "photo": {
        "types": {"scenic", "park", "historic", "cafe"},
        "tags": {"拍照", "看景", "花园", "夜景", "江景", "水边", "历史街区"},
    },
    "culture": {
        "types": {"museum", "bookstore", "historic", "tea_house"},
        "tags": {"文化", "展览", "历史", "历史街区", "老城", "历史感"},
    },
    "nature": {
        "types": {"park", "scenic"},
        "tags": {"自然", "自然景观", "公园", "草坪", "树林", "水边", "户外", "放松"},
    },
    "shopping": {
        "types": {"mall", "drink", "dessert", "restaurant"},
        "tags": {"逛街", "商圈", "现代城市", "饭后"},
    },
    "night_view": {
        "types": {"scenic", "historic", "restaurant", "cafe"},
        "tags": {"夜景", "夜游", "夜晚", "江景", "现代城市"},
    },
    "niche": {
        "types": {"bookstore", "cafe", "historic", "park", "tea_house"},
        "tags": {"小众", "本地生活", "老街巷", "安静", "本地人常去"},
    },
    "relaxed": {
        "types": {"park", "cafe", "tea_house", "bookstore", "scenic"},
        "tags": {"放松", "轻松", "安静", "适合休息", "散步", "免费"},
    },
}


INDOOR_TYPES = {"restaurant", "cafe", "drink", "dessert", "tea_house", "museum", "bookstore", "mall"}


def _normalize_tag_list(raw_tags):
    if not raw_tags:
        return []
    if isinstance(raw_tags, str):
        raw_tags = [raw_tags]
    if not isinstance(raw_tags, list):
        return []
    normalized = []
    seen = set()
    for tag in raw_tags:
        tag = str(tag).strip()
        if tag and tag not in seen:
            normalized.append(tag)
            seen.add(tag)
    return normalized


def normalize_persona_tags(preferences):
    preferences = dict(preferences or {})
    raw_persona_tags = _normalize_tag_list(preferences.get("persona_tags", []))
    raw_preference_tags = _normalize_tag_list(preferences.get("preference_tags", []))
    raw_constraint_tags = _normalize_tag_list(preferences.get("constraint_tags", []))

    persona_tags = [tag for tag in raw_persona_tags if tag in SUPPORTED_PERSONA_TAGS]
    preference_tags = [tag for tag in raw_preference_tags if tag in SUPPORTED_PREFERENCE_TAGS]
    constraint_tags = [tag for tag in raw_constraint_tags if tag in SUPPORTED_CONSTRAINT_TAGS]
    ignored_tags = _normalize_tag_list(preferences.get("ignored_tags", [])) + (
        [tag for tag in raw_persona_tags if tag not in SUPPORTED_PERSONA_TAGS]
        + [tag for tag in raw_preference_tags if tag not in SUPPORTED_PREFERENCE_TAGS]
        + [tag for tag in raw_constraint_tags if tag not in SUPPORTED_CONSTRAINT_TAGS]
    )
    ignored_tags = _normalize_tag_list(ignored_tags)

    preferences["persona_tags"] = persona_tags
    preferences["preference_tags"] = preference_tags
    preferences["constraint_tags"] = constraint_tags
    preferences["ignored_tags"] = ignored_tags

    if "half_day" in constraint_tags and "duration_minutes" not in preferences:
        preferences["duration_minutes"] = 210
    if "end_before_night" in constraint_tags:
        time_window = list(preferences.get("time_window", ["10:00", "18:00"]))
        if len(time_window) == 2 and time_window[1] > "18:00":
            preferences["time_window"] = [time_window[0], "18:00"]

    return preferences


def build_persona_context(preferences):
    preferences = normalize_persona_tags(preferences)
    return {
        "persona_tags": preferences.get("persona_tags", []),
        "preference_tags": preferences.get("preference_tags", []),
        "constraint_tags": preferences.get("constraint_tags", []),
        "ignored_tags": preferences.get("ignored_tags", []),
        "persona_labels": [
            PERSONA_STRATEGIES[tag]["label"]
            for tag in preferences.get("persona_tags", [])
            if tag in PERSONA_STRATEGIES
        ],
    }


def get_persona_poi_count_delta(preferences):
    tags = preferences.get("persona_tags", [])
    constraint_tags = set(preferences.get("constraint_tags", []))
    delta = sum(PERSONA_STRATEGIES[tag]["poi_count_delta"] for tag in tags if tag in PERSONA_STRATEGIES)
    if "less_walking" in constraint_tags:
        delta -= 1
    if "half_day" in constraint_tags:
        delta = min(delta, 0)
    return delta


def get_persona_stay_duration_delta(poi, preferences):
    tags = preferences.get("persona_tags", [])
    constraint_tags = set(preferences.get("constraint_tags", []))
    preference_tags = set(preferences.get("preference_tags", []))
    delta = sum(PERSONA_STRATEGIES[tag]["stay_delta"] for tag in tags if tag in PERSONA_STRATEGIES)

    if "relaxed" in preference_tags:
        delta += 8
    if "less_walking" in constraint_tags:
        delta += 5
    if "half_day" in constraint_tags and poi.get("type") not in {"restaurant", "museum", "park"}:
        delta -= 5

    return delta


def apply_persona_to_effective_preferences(preferences):
    preferences = normalize_persona_tags(preferences)
    constraint_tags = set(preferences.get("constraint_tags", []))

    if "low_budget" in constraint_tags:
        preferences["budget"] = min(float(preferences.get("budget", 300)), 180)
    if "avoid_queue" in constraint_tags:
        preferences["max_wait"] = min(int(preferences.get("max_wait", 30)), 15)
    if "half_day" in constraint_tags:
        preferences["duration_minutes"] = min(int(preferences.get("duration_minutes", 240)), 240)

    if "less_walking" in constraint_tags:
        preferences["persona_search_radius_multiplier"] = 0.65
    else:
        preferences["persona_search_radius_multiplier"] = 1.0

    return preferences


def persona_score_adjustment(poi, preferences, option_type="hard_constraint"):
    persona_tags = preferences.get("persona_tags", [])
    preference_tags = preferences.get("preference_tags", [])
    constraint_tags = set(preferences.get("constraint_tags", []))
    poi_tags = set(poi.get("tags", []))
    poi_type = poi.get("type")
    suitable_for = set(poi.get("suitable_for", []))
    score = 0

    for tag in persona_tags:
        strategy = PERSONA_STRATEGIES.get(tag)
        if not strategy:
            continue
        if poi_type in strategy["preferred_types"]:
            score += 10
        if suitable_for.intersection(strategy["suitable_for"]):
            score += 14
        score += len(poi_tags.intersection(strategy["preferred_tags"])) * 6
        score -= len(poi_tags.intersection(strategy["avoid_tags"])) * 10
        score -= poi.get("wait_time", 0) * strategy["wait_penalty"]
        score -= poi.get("price", 0) * strategy["price_penalty"]

    for tag in preference_tags:
        strategy = PREFERENCE_STRATEGIES.get(tag)
        if not strategy:
            continue
        if poi_type in strategy["types"]:
            score += 8
        score += len(poi_tags.intersection(strategy["tags"])) * 5

    if "niche" in preference_tags:
        score += 18 if poi.get("is_hidden_gem") else 0
        score -= max(poi.get("popularity", 0) - 75, 0) * 0.4
    if "indoor_first" in constraint_tags:
        score += 16 if poi_type in INDOOR_TYPES else -8
    if "avoid_queue" in constraint_tags:
        score -= poi.get("wait_time", 0) * 1.2
    if "low_budget" in constraint_tags:
        score -= poi.get("price", 0) * 0.15
        if poi.get("price", 0) == 0:
            score += 10
    if "end_before_night" in constraint_tags and poi_tags.intersection({"夜景", "夜游", "夜晚"}):
        score -= 18

    if option_type == "demand_satisfaction":
        score *= 1.1
    elif option_type == "hard_constraint":
        score *= 0.95

    return round(score, 2)


def persona_route_selection_adjustment(poi, distance_km, preferences):
    persona_tags = preferences.get("persona_tags", [])
    constraint_tags = set(preferences.get("constraint_tags", []))
    score = 0
    for tag in persona_tags:
        strategy = PERSONA_STRATEGIES.get(tag)
        if not strategy:
            continue
        score -= distance_km * strategy["distance_penalty"]

    if "less_walking" in constraint_tags:
        score -= distance_km * 14
    if "avoid_queue" in constraint_tags:
        score -= poi.get("wait_time", 0) * 1.1

    return score


def build_matched_reasons(route, preferences):
    context = build_persona_context(preferences)
    pois = route.get("pois", []) if route else []
    if not pois:
        return []

    reasons = []
    persona_labels = context["persona_labels"]
    if persona_labels:
        reasons.append(f"适合{ '、'.join(persona_labels) }：路线按该画像调整了点位类型、停留节奏和移动距离。")

    preference_tags = set(context["preference_tags"])
    constraint_tags = set(context["constraint_tags"])
    all_poi_tags = {tag for poi in pois for tag in poi.get("tags", [])}
    hidden_count = sum(1 for poi in pois if poi.get("is_hidden_gem"))

    preference_reason_map = {
        "food": ("餐饮偏好", {"小吃", "本地风味", "咖啡", "甜品", "茶饮", "朋友聚餐"}),
        "photo": ("拍照偏好", {"拍照", "看景", "夜景", "花园", "江景"}),
        "culture": ("文化偏好", {"文化", "展览", "历史", "历史街区", "历史感"}),
        "nature": ("自然偏好", {"自然", "自然景观", "公园", "草坪", "树林", "户外"}),
        "shopping": ("逛街偏好", {"逛街", "商圈", "现代城市"}),
        "night_view": ("夜景偏好", {"夜景", "夜游", "夜晚", "江景"}),
        "relaxed": ("放松偏好", {"放松", "轻松", "安静", "适合休息", "散步"}),
    }
    for tag, (label, match_tags) in preference_reason_map.items():
        matched = sorted(all_poi_tags.intersection(match_tags))
        if tag in preference_tags and matched:
            reasons.append(f"命中{label}：包含{ '、'.join(matched[:3]) }等路线信号。")
            break

    if "niche" in preference_tags and hidden_count:
        reasons.append(f"命中小众偏好：路线中包含 {hidden_count} 个小众宝藏点。")

    if "less_walking" in constraint_tags:
        reasons.append(f"已降低步行压力：总移动距离约 {route.get('total_distance', 0)} 公里，并优先选择近距离串联。")
    if "avoid_queue" in constraint_tags:
        reasons.append(f"已控制排队压力：总等待约 {route.get('total_wait_time', 0)} 分钟。")
    if "low_budget" in constraint_tags:
        reasons.append(f"已控制预算：路线总花费约 {route.get('total_cost', 0)} 元。")
    if "indoor_first" in constraint_tags:
        indoor_count = sum(1 for poi in pois if poi.get("type") in INDOOR_TYPES)
        reasons.append(f"优先室内点位：路线中 {indoor_count}/{len(pois)} 个点位偏室内或可休息。")
    if "end_before_night" in constraint_tags:
        reasons.append("已避开夜间收尾：路线按 18:00 前结束的约束生成。")

    return reasons[:4]


def _clamp_score(value):
    return max(0, min(100, int(round(value))))


def build_quality_scores(route, preferences):
    pois = route.get("pois", []) if route else []
    if not pois:
        return {
            "comfort_score": 0,
            "social_score": 0,
            "romantic_score": 0,
            "family_score": 0,
            "intensity_score": 0,
        }

    total_distance = route.get("total_distance", 0)
    total_wait = route.get("total_wait_time", 0)
    total_time = max(route.get("total_time", 1), 1)
    poi_count = len(pois)
    all_tags = [tag for poi in pois for tag in poi.get("tags", [])]
    tag_set = set(all_tags)
    suitable_values = [item for poi in pois for item in poi.get("suitable_for", [])]
    indoor_count = sum(1 for poi in pois if poi.get("type") in INDOOR_TYPES)
    free_or_low_cost = sum(1 for poi in pois if poi.get("price", 0) <= 60)
    hidden_count = sum(1 for poi in pois if poi.get("is_hidden_gem"))

    comfort = (
        72
        - total_distance * 5
        - total_wait * 0.5
        + indoor_count * 4
        + len(tag_set.intersection({"安静", "放松", "轻松", "适合休息", "散步"})) * 5
    )
    social = (
        35
        + suitable_values.count("friends") * 8
        + len(tag_set.intersection({"朋友聚餐", "适合聊天", "热闹", "小吃", "逛街"})) * 8
    )
    romantic = (
        30
        + suitable_values.count("couple") * 7
        + len(tag_set.intersection({"情侣", "约会", "拍照", "夜景", "甜品", "咖啡", "花园"})) * 9
    )
    family = (
        30
        + suitable_values.count("family") * 8
        + len(tag_set.intersection({"亲子", "公园", "草坪", "放松", "免费", "轻松"})) * 9
        + free_or_low_cost * 3
        - total_wait * 0.35
    )
    intensity = (
        20
        + poi_count * 12
        + total_distance * 6
        + max(0, 60 - total_time / max(poi_count, 1)) * 0.5
        - len(tag_set.intersection({"安静", "放松", "适合休息"})) * 3
    )

    if "niche" in preferences.get("preference_tags", []):
        comfort += hidden_count * 3
    if preferences.get("pace_mode") == "intensive":
        intensity += 22
        comfort -= 8

    return {
        "comfort_score": _clamp_score(comfort),
        "social_score": _clamp_score(social),
        "romantic_score": _clamp_score(romantic),
        "family_score": _clamp_score(family),
        "intensity_score": _clamp_score(intensity),
    }

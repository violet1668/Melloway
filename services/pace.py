PACE_NORMAL = "normal"
PACE_INTENSIVE = "intensive"

FAST_POI_TYPES = {"drink", "dessert", "tea_house", "mall", "historic"}
FAST_POI_TAGS = {
    "小吃", "茶饮", "饮品", "甜品", "快速补给", "打卡", "拍照", "适合拍照",
    "商圈", "逛街", "citywalk", "散步", "漫步", "街区", "历史街区", "老街巷",
    "夜景", "看景", "观景", "轻松"
}
SLOW_POI_TYPES = {"museum", "gallery", "temple", "park"}
SLOW_POI_TAGS = {"博物馆", "美术馆", "寺庙", "大型公园", "主题公园", "正式景点", "展览"}


def normalize_pace_preferences(preferences):
    """
    归一化全局路线节奏参数，保留用户原始游玩时长作为 base_duration_minutes。
    """
    preferences = dict(preferences or {})
    pace_mode = str(preferences.get("pace_mode", PACE_NORMAL) or PACE_NORMAL).strip().lower()
    if pace_mode not in {PACE_NORMAL, PACE_INTENSIVE}:
        pace_mode = PACE_NORMAL

    try:
        time_flex_minutes = int(preferences.get("time_flex_minutes", 0) or 0)
    except (TypeError, ValueError):
        time_flex_minutes = 0

    time_flex_minutes = max(0, min(time_flex_minutes, 60))
    if pace_mode == PACE_NORMAL:
        time_flex_minutes = 0

    try:
        base_duration = int(preferences.get("base_duration_minutes", preferences.get("duration_minutes", 240)))
    except (TypeError, ValueError):
        base_duration = 240

    preferences["pace_mode"] = pace_mode
    preferences["time_flex_minutes"] = time_flex_minutes
    preferences["base_duration_minutes"] = base_duration
    return preferences


def is_intensive(preferences):
    return preferences.get("pace_mode") == PACE_INTENSIVE


def get_base_duration_minutes(preferences):
    return int(preferences.get("base_duration_minutes", preferences.get("duration_minutes", 240)))


def get_effective_duration_minutes(preferences):
    base_duration = get_base_duration_minutes(preferences)
    if is_intensive(preferences):
        return base_duration + int(preferences.get("time_flex_minutes", 0))
    return int(preferences.get("duration_minutes", base_duration))


def build_pace_info(preferences):
    preferences = normalize_pace_preferences(preferences)
    if is_intensive(preferences):
        flex = preferences.get("time_flex_minutes", 0)
        return {
            "pace_mode": PACE_INTENSIVE,
            "label": "特种兵模式",
            "time_flex_minutes": flex,
            "message": f"当前为特种兵模式，系统会优先选择更紧凑、顺路的 POI，并在你允许的 {flex} 分钟弹性范围内尽可能增加游玩点。"
        }

    return {
        "pace_mode": PACE_NORMAL,
        "label": "标准模式",
        "time_flex_minutes": 0,
        "message": "当前为标准节奏，系统会平衡路线数量与停留体验。"
    }


def is_fast_turnover_poi(poi):
    poi_type = poi.get("type")
    tags = set(poi.get("tags", []))
    if poi_type in SLOW_POI_TYPES or tags.intersection(SLOW_POI_TAGS):
        return False
    return poi_type in FAST_POI_TYPES or bool(tags.intersection(FAST_POI_TAGS))


def get_adjusted_stay_duration(poi, preferences):
    stay_duration = int(poi.get("stay_duration", 0) or 0)
    if not is_intensive(preferences) or not is_fast_turnover_poi(poi):
        return stay_duration

    reduction = min(10, max(0, int(stay_duration * 0.15)))
    return max(15, stay_duration - reduction)


def get_default_poi_count(duration_minutes):
    if duration_minutes <= 150:
        return 2
    if duration_minutes <= 300:
        return 3
    return 4


def get_intensive_poi_count_bonus(preferences):
    if not is_intensive(preferences):
        return 0
    return 2 if int(preferences.get("time_flex_minutes", 0) or 0) >= 60 else 1


def pace_score_adjustment(poi, distance_km, preferences):
    if not is_intensive(preferences):
        return 0

    score = 0
    tags = set(poi.get("tags", []))
    wait_time = poi.get("wait_time", 0)
    stay_duration = poi.get("stay_duration", 0)
    price = poi.get("price", 0)

    score -= distance_km * 10
    score -= wait_time * 0.9
    score -= max(stay_duration - 45, 0) * 0.35
    score -= max(price - 60, 0) * 0.12

    if is_fast_turnover_poi(poi):
        score += 22
    if tags.intersection({"citywalk", "小吃", "茶饮", "打卡", "拍照", "历史街区", "商圈", "夜景"}):
        score += 14
    if wait_time <= 15:
        score += 8

    return score


def build_pace_relaxation_notice(route, preferences):
    if not route or not is_intensive(preferences):
        return None

    base_duration = get_base_duration_minutes(preferences)
    extra_time = max(0, route.get("total_time", 0) - base_duration)
    if extra_time <= 0:
        return None

    flex = preferences.get("time_flex_minutes", 0)
    return f"这条路线使用了特种兵模式的时间弹性，预计比原计划多 {extra_time} 分钟，未超过你允许的 {flex} 分钟。"


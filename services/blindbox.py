import json
import os
import random
from datetime import timedelta

from services.constraints import (
    estimate_travel_minutes,
    filter_pois,
    haversine_km,
    infer_search_radius_km,
    parse_start_point,
    parse_time,
)
from services.poi_service import get_pois
from services.pace import (
    build_pace_info,
    build_pace_relaxation_notice,
    get_adjusted_stay_duration,
    get_base_duration_minutes,
    get_default_poi_count,
    get_effective_duration_minutes,
    get_intensive_poi_count_bonus,
    normalize_pace_preferences,
    pace_score_adjustment,
)


def _load_user_profile():
    profile_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'user_profile.json')
    try:
        with open(profile_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


THEME_RULES = {
    "citywalk": {
        "name": "Citywalk 盲盒",
        "tags": ["citywalk", "散步", "老街巷", "历史街区", "拍照", "轻松"],
        "types": ["historic", "scenic", "park", "bookstore", "gallery"]
    },
    "foodie": {
        "name": "吃吃喝喝盲盒",
        "tags": ["小吃", "本地风味", "朋友聚餐", "咖啡", "茶饮", "甜品"],
        "types": ["restaurant", "cafe", "drink", "dessert", "tea_house"]
    },
    "culture": {
        "name": "文化之旅盲盒",
        "tags": ["文化", "展览", "艺术", "书店", "历史", "室内"],
        "types": ["museum", "gallery", "bookstore", "historic"]
    },
    "hidden_gem": {
        "name": "小众探索盲盒",
        "tags": ["小众", "安静", "本地生活", "放松", "宝藏", "本地风味"],
        "types": ["cafe", "tea_house", "bookstore", "gallery", "historic", "park", "scenic"]
    }
}

THEME_ALIASES = {
    "吃吃喝喝": "foodie",
    "美食": "foodie",
    "food": "foodie",
    "foodie": "foodie",
    "文化之旅": "culture",
    "文化": "culture",
    "culture": "culture",
    "小众": "hidden_gem",
    "隐藏宝藏": "hidden_gem",
    "hidden": "hidden_gem",
    "hidden_gem": "hidden_gem",
    "citywalk": "citywalk",
    "城市漫步": "citywalk"
}


def normalize_theme(theme):
    """
    归一化盲盒主题。
    """
    if not theme:
        return "citywalk"

    return THEME_ALIASES.get(str(theme).strip())


def score_blindbox_poi(poi, theme_key, strategy="theme_match", preferences=None, start_point=None, user_profile=None):
    """
    主题匹配、小众程度、体验质量和用户历史偏好共同决定盲盒候选分。
    """
    theme = THEME_RULES[theme_key]
    tags = set(poi.get("tags", []))
    theme_hits = len(tags.intersection(theme["tags"]))
    score = poi.get("rating", 0) * 18
    score += theme_hits * 14

    theme_types = set(theme["types"])
    poi_type = poi.get("type", "")
    if isinstance(poi_type, list):
        poi_type = ",".join(poi_type)
    poi_types = {t.strip() for t in str(poi_type).split(",") if t.strip()}
    if poi_types.intersection(theme_types):
        score += 18

    if poi.get("is_hidden_gem"):
        score += 16

    # ---- 用户历史偏好调整 ----
    if user_profile:
        history = user_profile.get("history_behavior", {})
        explicit = user_profile.get("explicit_preferences", {})

        visited_ids = set(history.get("visited_poi_ids", []))
        liked_types = set(history.get("liked_poi_types", []))
        frequent_tags = set(history.get("frequent_tags", []))
        avoid_ids = set(history.get("avoid_poi_ids", []))

        preferred_tags = set(explicit.get("preferred_tags", []))
        disliked_tags = set(explicit.get("disliked_tags", []))
        favorite_cuisines = set(explicit.get("favorite_cuisines", []))

        # 已去过：大幅降分，避免重复推荐
        if poi.get("id") in visited_ids:
            score -= 35

        # 明确避开：直接排除
        if poi.get("id") in avoid_ids:
            score -= 60

        # 喜欢的地点类型：加分
        poi_type = poi.get("type", "")
        if isinstance(poi_type, list):
            poi_type = ",".join(poi_type)
        poi_types = {t.strip() for t in str(poi_type).split(",") if t.strip()}
        if poi_types.intersection(liked_types):
            score += 12

        # 常选标签匹配：加分
        history_tag_hits = len(tags.intersection(frequent_tags))
        score += history_tag_hits * 8

        # 偏好标签匹配：加分
        pref_tag_hits = len(tags.intersection(preferred_tags))
        score += pref_tag_hits * 6

        # 不喜欢标签匹配：减分
        dislike_hits = len(tags.intersection(disliked_tags))
        score -= dislike_hits * 15

        # 偏好菜系匹配
        cuisine = poi.get("category", "") or poi.get("cuisine", "")
        if isinstance(cuisine, list):
            cuisine = ",".join(cuisine)
        cuisine_set = {c.strip() for c in str(cuisine).split(",") if c.strip()}
        if cuisine_set.intersection(favorite_cuisines):
            score += 10

    # ---- 策略调整 ----
    if strategy == "stable":
        score -= poi.get("wait_time", 0) * 1.2
        score -= poi.get("price", 0) * 0.12
        score += min(poi.get("popularity", 0), 70) * 0.08
    elif strategy == "hidden_gem":
        score += 24 if poi.get("is_hidden_gem") else 0
        score -= max(poi.get("popularity", 0) - 65, 0) * 0.45
        score -= poi.get("wait_time", 0) * 0.45
    elif theme_key == "hidden_gem":
        score -= max(poi.get("popularity", 0) - 70, 0) * 0.35
    else:
        score += theme_hits * 10
        score += min(poi.get("popularity", 0), 75) * 0.05

    if strategy != "stable":
        score -= poi.get("wait_time", 0) * 0.35

    if preferences and start_point:
        distance = haversine_km(start_point["lng"], start_point["lat"], poi["lng"], poi["lat"])
        score += pace_score_adjustment(poi, distance, preferences)

    return round(score, 2)


def select_blindbox_candidates(pois, start_point, preferences, theme_key, strategy="theme_match", user_profile=None):
    """
    先按基础约束过滤，再按主题得分 + 用户历史偏好排序。
    """
    filtered = filter_pois(pois, start_point, preferences, "blindbox")

    for poi in filtered:
        poi["blindbox_score"] = score_blindbox_poi(
            poi,
            theme_key,
            strategy=strategy,
            preferences=preferences,
            start_point=start_point,
            user_profile=user_profile
        )

    filtered = sorted(
        filtered,
        key=lambda item: item["blindbox_score"],
        reverse=True
    )

    return filtered


def build_blindbox_route(start_point, candidate_pois, preferences, theme_key, strategy="theme_match", route_index=0):
    """
    生成主题盲盒路线。
    """
    if not candidate_pois:
        return None

    duration_minutes = get_effective_duration_minutes(preferences)
    time_window = preferences.get("time_window", ["10:00", "18:00"])
    transport = preferences.get("transport", "walk")
    budget = preferences.get("budget", 300)
    requested_poi_count = preferences.get("poi_count")
    if requested_poi_count:
        poi_count = int(requested_poi_count)
    else:
        poi_count = get_default_poi_count(get_base_duration_minutes(preferences))
        poi_count += get_intensive_poi_count_bonus(preferences)
    poi_count = min(poi_count, len(candidate_pois))

    seed = f"{theme_key}:{strategy}:{route_index}:{round(start_point['lng'], 3)}:{round(start_point['lat'], 3)}:{duration_minutes}:{budget}"
    shuffled_candidates = list(candidate_pois[:12])
    random.Random(seed).shuffle(shuffled_candidates)
    candidate_pois = sorted(
        shuffled_candidates,
        key=lambda poi: (poi["blindbox_score"], poi.get("is_hidden_gem", False)),
        reverse=True
    )

    current_point = start_point
    current_time = parse_time(time_window[0])
    selected = []
    segments = []
    total_cost = 0
    total_time = 0
    total_wait_time = 0
    total_travel_time = 0
    total_distance = 0

    for poi in candidate_pois:
        if len(selected) >= poi_count:
            break

        distance_km = haversine_km(current_point["lng"], current_point["lat"], poi["lng"], poi["lat"])
        depart_time_text = current_time.strftime("%H:%M")
        travel_minutes = estimate_travel_minutes(distance_km, transport, depart_time=depart_time_text)
        stay_duration = get_adjusted_stay_duration(poi, preferences)
        projected_total_time = total_time + travel_minutes + poi.get("wait_time", 0) + stay_duration
        projected_total_cost = total_cost + poi.get("price", 0)

        if projected_total_time > duration_minutes:
            continue

        if projected_total_cost > budget:
            continue

        arrive_time = current_time + timedelta(minutes=travel_minutes)
        leave_time = arrive_time + timedelta(minutes=poi.get("wait_time", 0) + stay_duration)
        poi_detail = dict(poi)
        original_stay_duration = int(poi.get("stay_duration", 0) or 0)
        poi_detail["stay_duration"] = stay_duration
        if stay_duration != original_stay_duration:
            poi_detail["original_stay_duration"] = original_stay_duration
        poi_detail["arrive_time"] = arrive_time.strftime("%H:%M")
        poi_detail["leave_time"] = leave_time.strftime("%H:%M")

        segments.append({
            "from": "起点" if not selected else selected[-1]["name"],
            "to": poi["name"],
            "transport": transport,
            "duration": travel_minutes,
            "distance": round(distance_km, 2),
            "distance_type": "haversine_estimated",
            "time_estimation": "speed_detour_peak_factor",
            "traffic_note": "移动时间基于距离、出行方式和时段系数估算，未接入实时路况。"
        })

        selected.append(poi_detail)
        total_cost += poi.get("price", 0)
        total_time += travel_minutes + poi.get("wait_time", 0) + stay_duration
        total_wait_time += poi.get("wait_time", 0)
        total_travel_time += travel_minutes
        total_distance += distance_km
        current_time = leave_time
        current_point = {"lng": poi["lng"], "lat": poi["lat"]}

    if not selected:
        return None

    theme = THEME_RULES[theme_key]
    return {
        "start_point": start_point,
        "theme": theme_key,
        "theme_name": theme["name"],
        "pois": selected,
        "segments": segments,
        "total_cost": total_cost,
        "total_time": total_time,
        "total_wait_time": total_wait_time,
        "total_travel_time": total_travel_time,
        "total_distance": round(total_distance, 2),
        "search_radius_km": round(infer_search_radius_km(duration_minutes, transport), 2),
        "option_type": "blindbox",
        "pace_info": build_pace_info(preferences)
    }


THEME_USER_FACING = {
    "citywalk": {
        "intro": "用漫步的方式串起杭州的街巷角落，适合慢慢走、慢慢发现。",
        "tags_display": ["街巷漫步", "拍照打卡", "轻松节奏"],
    },
    "foodie": {
        "intro": "把杭州的好味道串在一起，从正餐到甜品都帮你安排好了。",
        "tags_display": ["本地风味", "咖啡茶饮", "朋友聚餐"],
    },
    "culture": {
        "intro": "带你走进杭州的文化深处，展览、书店、历史街区一次逛完。",
        "tags_display": ["文化展览", "书店艺术", "历史街区"],
    },
    "hidden_gem": {
        "intro": "避开人群，带你发现杭州那些安静又有味道的小角落。",
        "tags_display": ["小众探索", "安静放松", "本地宝藏"],
    },
}


def build_option_from_route(route, theme_key, preferences, user_profile=None):
    """
    构建盲盒揭晓后的路线详情，用产品化文案替代系统术语。
    """
    theme = THEME_RULES[theme_key]
    uf = THEME_USER_FACING.get(theme_key, THEME_USER_FACING["citywalk"])
    poi_names = [p["name"] for p in route["pois"][:3]]

    # 卡片摘要
    summary = f"{theme['name']}：{' → '.join(poi_names)}，共 {len(route['pois'])} 个地点，约 {route['total_time']} 分钟。"

    # 产品化解释：提及用户历史偏好 + 本条策略特点
    strategy = preferences.get("_strategy", "theme_match")
    strategy_descriptions = {
        "theme_match": "这条路线优先挑选了与「{theme_name}」最匹配的地点，主题感最强。",
        "stable": "这条路线选了排队少、性价比高的稳妥组合，适合不想有意外的一天。",
        "hidden_gem": "这条路线偏爱人少安静的小众地点，避开热门，体验更独特。",
    }
    intro_parts = [uf["intro"]]
    intro_parts.append(strategy_descriptions.get(strategy, "").format(theme_name=theme["name"]))
    if user_profile:
        history = user_profile.get("history_behavior", {})
        liked = history.get("liked_poi_types", [])
        if liked:
            type_names = {"restaurant": "餐厅", "cafe": "咖啡馆", "scenic": "景点", "museum": "博物馆", "bookstore": "书店", "tea_house": "茶馆", "park": "公园"}
            liked_cn = [type_names.get(t, t) for t in liked[:3]]
            intro_parts.append(f"因为你常去{'、'.join(liked_cn)}，这条路线优先推荐了同类地点。")
    explanation = "".join(intro_parts)

    # 约束说明：更自然的表达
    budget = preferences.get("budget", 300)
    duration_hours = preferences.get("duration_minutes", 240) // 60
    relaxation_notice = build_pace_relaxation_notice(route, preferences)
    if not relaxation_notice:
        relaxation_notice = f"路线总花费控制在 ¥{budget} 以内，时长约 {duration_hours} 小时，排队时间也帮你考虑过了。"

    # 路线差异原因：每条路线解释自己与其他两条的不同
    diff_map = {
        "theme_match": "这条最贴近「{theme_name}」主题，另外两条分别在稳妥性和小众探索上做了不同取舍。",
        "stable": "这条最稳妥省心，花费和排队都压得比较低；另外两条一条偏主题感、一条偏小众。",
        "hidden_gem": "这条最偏小众，选了人少安静的地方；另外两条一条偏主题、一条偏稳妥。",
    }
    differentiation_reason = diff_map.get(strategy, diff_map["theme_match"]).format(theme_name=theme["name"])

    return {
        "type": "blindbox",
        "plan_type": "blindbox",
        "name": "神秘路线盲盒",
        "plan_name": "神秘路线盲盒",
        "success": True,
        "message": "盲盒路线已揭晓",
        "route": route,
        "summary": summary,
        "explanation": explanation,
        "relaxation_notice": relaxation_notice,
        "differentiation_reason": differentiation_reason,
        "pace_info": build_pace_info(preferences),
        "pois": route["pois"],
        "segments": route["segments"],
        "total_cost": route["total_cost"],
        "total_time": route["total_time"],
        "total_wait_time": route["total_wait_time"]
    }


def route_signature(route):
    """
    用 POI 集合作为路线差异判断。
    """
    if not route:
        return tuple()

    return tuple(sorted(poi["id"] for poi in route.get("pois", [])))


def generate_three_blindbox_routes(parsed_start, preferences, theme_key, user_profile=None):
    """
    使用三种内部策略生成 3 条路线，但不把策略暴露给前端。
    用户历史偏好用于调整 POI 评分。
    """
    strategies = ["theme_match", "stable", "hidden_gem"]
    routes = []
    signatures = set()
    pois = get_pois(city=preferences.get("city", "杭州"))

    for index, strategy in enumerate(strategies):
        candidates = select_blindbox_candidates(
            pois, parsed_start, preferences, theme_key,
            strategy=strategy, user_profile=user_profile
        )
        route = build_blindbox_route(
            parsed_start,
            candidates,
            preferences,
            theme_key,
            strategy=strategy,
            route_index=index
        )

        if route and route_signature(route) in signatures and route.get("pois"):
            first_poi_id = route["pois"][0]["id"]
            candidates = [poi for poi in candidates if poi.get("id") != first_poi_id]
            route = build_blindbox_route(
                parsed_start,
                candidates,
                preferences,
                theme_key,
                strategy=strategy,
                route_index=index + 10
            )

        if route:
            signatures.add(route_signature(route))
            routes.append(route)

    return routes


def generate_blindbox_route(start_point=None, preferences=None, user_prefs=None):
    """
    盲盒路线生成。

    支持 theme / blind_box_theme，使用本地 POI 和规则评分，不接入真实 API 或 LLM。
    """
    preferences = normalize_pace_preferences(preferences or {})
    raw_start = start_point or preferences.get("start") or preferences.get("start_location")
    if not raw_start:
        return {
            "type": "blindbox",
            "success": False,
            "message": "缺少盲盒路线起点坐标。",
            "route": None,
            "summary": "缺少盲盒路线起点坐标。"
        }

    try:
        parsed_start = parse_start_point(raw_start)
    except ValueError as error:
        return {
            "type": "blindbox",
            "success": False,
            "message": str(error),
            "route": None,
            "summary": str(error)
        }

    if "duration_minutes" not in preferences and preferences.get("duration_hours"):
        preferences["duration_minutes"] = int(float(preferences["duration_hours"]) * 60)
    if "max_wait" not in preferences and preferences.get("max_wait_time") is not None:
        preferences["max_wait"] = preferences["max_wait_time"]

    preferences.setdefault("city", "杭州")
    preferences.setdefault("budget", 300)
    preferences.setdefault("max_wait", 30)
    preferences.setdefault("duration_minutes", 240)
    preferences.setdefault("transport", "walk")
    preferences.setdefault("time_window", ["10:00", "18:00"])
    preferences = normalize_pace_preferences(preferences)

    theme_key = normalize_theme(preferences.get("theme") or preferences.get("blind_box_theme"))
    if not theme_key:
        message = "暂不支持该盲盒主题，请选择 citywalk、吃吃喝喝、文化之旅或小众探索。"
        return {
            "type": "blindbox",
            "success": False,
            "message": message,
            "route": None,
            "summary": message
        }

    routes = generate_three_blindbox_routes(parsed_start, preferences, theme_key, user_profile=_load_user_profile())
    if len(routes) < 3:
        message = "当前盲盒主题和约束下无可用路线，请更换主题或放宽预算、时间、排队限制。"
        return {
            "type": "blindbox",
            "success": False,
            "message": message,
            "route": None,
            "summary": message,
            "theme": theme_key,
            "theme_name": THEME_RULES[theme_key]["name"]
        }

    shuffle_seed = f"boxes:{theme_key}:{round(parsed_start['lng'], 3)}:{round(parsed_start['lat'], 3)}:{preferences['budget']}:{preferences['duration_minutes']}"
    random.Random(shuffle_seed).shuffle(routes)

    user_profile = _load_user_profile()
    strategies = ["theme_match", "stable", "hidden_gem"]
    blind_boxes = []
    for index, route in enumerate(routes, start=1):
        prefs_with_strategy = dict(preferences)
        prefs_with_strategy["_strategy"] = strategies[(index - 1) % 3]
        option = build_option_from_route(route, theme_key, prefs_with_strategy, user_profile=user_profile)
        route["summary"] = option["summary"]
        blind_boxes.append({
            "box_id": f"box_{index}",
            "display_name": "神秘路线盲盒",
            "is_revealed": False,
            "option": option
        })

    blind_box_info = {
        "theme": theme_key,
        "theme_name": THEME_RULES[theme_key]["name"],
        "message": "系统已为你准备 3 个神秘路线盲盒，点击任意一个揭晓路线。"
    }

    return {
        "type": "blindbox",
        "plan_type": "blindbox",
        "success": True,
        "message": "盲盒路线生成成功",
        "theme": theme_key,
        "theme_name": THEME_RULES[theme_key]["name"],
        "blind_box_info": blind_box_info,
        "pace_info": build_pace_info(preferences),
        "blind_boxes": blind_boxes
    }

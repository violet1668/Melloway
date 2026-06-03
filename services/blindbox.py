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


def score_blindbox_poi(poi, theme_key, strategy="theme_match"):
    """
    主题匹配、小众程度和体验质量共同决定盲盒候选分。
    """
    theme = THEME_RULES[theme_key]
    tags = set(poi.get("tags", []))
    theme_hits = len(tags.intersection(theme["tags"]))
    score = poi.get("rating", 0) * 18
    score += theme_hits * 14

    if poi.get("type") in theme["types"]:
        score += 18

    if poi.get("is_hidden_gem"):
        score += 16

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

    return round(score, 2)


def select_blindbox_candidates(pois, start_point, preferences, theme_key, strategy="theme_match"):
    """
    先按基础约束过滤，再按主题得分排序。
    """
    filtered = filter_pois(pois, start_point, preferences, "blindbox")

    for poi in filtered:
        poi["blindbox_score"] = score_blindbox_poi(poi, theme_key, strategy=strategy)

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

    duration_minutes = preferences.get("duration_minutes", 240)
    time_window = preferences.get("time_window", ["10:00", "18:00"])
    transport = preferences.get("transport", "walk")
    budget = preferences.get("budget", 300)
    poi_count = min(int(preferences.get("poi_count", 3) or 3), len(candidate_pois))

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
        travel_minutes = estimate_travel_minutes(distance_km, transport)
        projected_total_time = total_time + travel_minutes + poi.get("wait_time", 0) + poi.get("stay_duration", 0)
        projected_total_cost = total_cost + poi.get("price", 0)

        if projected_total_time > duration_minutes:
            continue

        if projected_total_cost > budget:
            continue

        arrive_time = current_time + timedelta(minutes=travel_minutes)
        leave_time = arrive_time + timedelta(minutes=poi.get("wait_time", 0) + poi.get("stay_duration", 0))
        poi_detail = dict(poi)
        poi_detail["arrive_time"] = arrive_time.strftime("%H:%M")
        poi_detail["leave_time"] = leave_time.strftime("%H:%M")

        segments.append({
            "from": "起点" if not selected else selected[-1]["name"],
            "to": poi["name"],
            "transport": transport,
            "duration": travel_minutes,
            "distance": round(distance_km, 2)
        })

        selected.append(poi_detail)
        total_cost += poi.get("price", 0)
        total_time += travel_minutes + poi.get("wait_time", 0) + poi.get("stay_duration", 0)
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
        "option_type": "blindbox"
    }


def build_option_from_route(route, theme_key):
    """
    构建盲盒揭晓后的路线详情。内容不暴露内部生成策略。
    """
    theme = THEME_RULES[theme_key]
    summary = (
        f"{theme['name']}路线已揭晓：围绕{ '、'.join(theme['tags'][:3]) }安排，"
        f"共 {len(route['pois'])} 个地点，预计 {route['total_time']} 分钟。"
    )
    explanation = "这条路线由系统在主题匹配、时间预算和探索体验之间综合生成。"
    relaxation_notice = "该盲盒路线遵守你的预算、排队和时间限制。"
    differentiation_reason = "该路线围绕所选盲盒主题生成，并与其他盲盒路线保持地点组合差异。"

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


def generate_three_blindbox_routes(parsed_start, preferences, theme_key):
    """
    使用三种内部策略生成 3 条路线，但不把策略暴露给前端。
    """
    strategies = ["theme_match", "stable", "hidden_gem"]
    routes = []
    signatures = set()
    pois = get_pois(city=preferences.get("city", "杭州"))

    for index, strategy in enumerate(strategies):
        candidates = select_blindbox_candidates(pois, parsed_start, preferences, theme_key, strategy=strategy)
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
    preferences = dict(preferences or {})
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

    routes = generate_three_blindbox_routes(parsed_start, preferences, theme_key)
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

    blind_boxes = []
    for index, route in enumerate(routes, start=1):
        option = build_option_from_route(route, theme_key)
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
        "blind_boxes": blind_boxes
    }

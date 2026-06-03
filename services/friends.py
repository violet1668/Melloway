from services.constraints import (
    estimate_travel_minutes,
    haversine_km,
    infer_search_radius_km,
    is_open_during_visit,
    is_valid_coordinate,
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


FRIENDS_TAGS = {"朋友聚餐", "朋友聚会", "适合聊天", "轻松", "安静", "本地风味", "商圈"}


def validate_friend_locations(friend_locations):
    """
    校验朋友位置列表。
    """
    if not isinstance(friend_locations, list) or len(friend_locations) < 2:
        raise ValueError("请至少提供 2 个朋友位置。")

    normalized_locations = []
    for index, location in enumerate(friend_locations, start=1):
        if not isinstance(location, dict):
            raise ValueError("朋友位置格式错误，请使用包含 lng 和 lat 的对象。")

        if not is_valid_coordinate(location.get("lng"), location.get("lat")):
            raise ValueError(f"第 {index} 个朋友位置坐标无效。")

        normalized_locations.append({
            "name": location.get("name") or f"朋友{index}",
            "lng": float(location["lng"]),
            "lat": float(location["lat"])
        })

    return normalized_locations


def calculate_center_point(friend_locations):
    """
    使用经纬度均值计算 MVP 阶段集合中心点。
    """
    normalized_locations = validate_friend_locations(friend_locations)
    center_lng = sum(location["lng"] for location in normalized_locations) / len(normalized_locations)
    center_lat = sum(location["lat"] for location in normalized_locations) / len(normalized_locations)

    return {
        "lng": round(center_lng, 6),
        "lat": round(center_lat, 6),
        "name": "推荐集合点",
        "source_count": len(normalized_locations)
    }


def calculate_friend_fairness_score(poi, friend_locations):
    """
    计算 POI 到所有朋友位置的距离公平性。
    """
    distances = [
        haversine_km(location["lng"], location["lat"], poi["lng"], poi["lat"])
        for location in friend_locations
    ]
    return {
        "avg_distance_km": round(sum(distances) / len(distances), 2),
        "max_distance_km": round(max(distances), 2),
        "distance_spread_km": round(max(distances) - min(distances), 2)
    }


def score_friend_poi(poi, center_point, preferences, friend_locations):
    """
    朋友中心选址评分：距离公平、适合聊天聚会、等待和价格可控。
    """
    distance_to_center = haversine_km(center_point["lng"], center_point["lat"], poi["lng"], poi["lat"])
    fairness = calculate_friend_fairness_score(poi, friend_locations)
    poi_tags = set(poi.get("tags", []))

    score = poi.get("rating", 0) * 18
    score += len(FRIENDS_TAGS.intersection(poi_tags)) * 12
    score += poi.get("popularity", 0) * 0.08
    score -= distance_to_center * 10
    score -= fairness["distance_spread_km"] * 6
    score -= poi.get("wait_time", 0) * 0.5

    budget = preferences.get("budget")
    if budget:
        score -= (poi.get("price", 0) / max(budget, 1)) * 8

    score += pace_score_adjustment(poi, distance_to_center, preferences)

    return round(score, 2)


def filter_friend_pois(pois, center_point, preferences):
    """
    按朋友中心路线的基础约束过滤 POI。
    """
    duration_minutes = get_effective_duration_minutes(preferences)
    transport = preferences.get("transport", "walk")
    budget = preferences.get("budget", 300)
    max_wait = preferences.get("max_wait", 30)
    time_window = preferences.get("time_window", ["10:00", "18:00"])
    search_radius_km = infer_search_radius_km(duration_minutes, transport)

    filtered = []
    for poi in pois:
        distance_to_center = haversine_km(center_point["lng"], center_point["lat"], poi["lng"], poi["lat"])
        if distance_to_center > search_radius_km:
            continue

        if poi.get("price", 0) > budget:
            continue

        if poi.get("wait_time", 0) > max_wait:
            continue

        if not is_open_during_visit(poi, time_window[0]):
            continue

        poi_detail = dict(poi)
        poi_detail["distance_to_center_km"] = round(distance_to_center, 2)
        filtered.append(poi_detail)

    return filtered


def build_friends_route(center_point, candidate_pois, preferences, friend_locations):
    """
    生成朋友集合点附近的轻量路线。
    """
    if not candidate_pois:
        return None

    duration_minutes = get_effective_duration_minutes(preferences)
    transport = preferences.get("transport", "walk")
    requested_poi_count = preferences.get("poi_count")
    if requested_poi_count:
        poi_count = int(requested_poi_count)
    else:
        poi_count = get_default_poi_count(get_base_duration_minutes(preferences))
        poi_count += get_intensive_poi_count_bonus(preferences)
    poi_count = min(poi_count, len(candidate_pois))

    selected = []
    segments = []
    current_point = center_point
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
        stay_duration = get_adjusted_stay_duration(poi, preferences)
        projected_total_time = total_time + travel_minutes + poi.get("wait_time", 0) + stay_duration

        if projected_total_time > duration_minutes:
            continue

        poi_detail = dict(poi)
        original_stay_duration = int(poi.get("stay_duration", 0) or 0)
        poi_detail["stay_duration"] = stay_duration
        if stay_duration != original_stay_duration:
            poi_detail["original_stay_duration"] = original_stay_duration
        poi_detail["friend_fairness"] = calculate_friend_fairness_score(poi, friend_locations)
        selected.append(poi_detail)

        segments.append({
            "from": "推荐集合点" if len(selected) == 1 else selected[-2]["name"],
            "to": poi["name"],
            "transport": transport,
            "duration": travel_minutes,
            "distance": round(distance_km, 2)
        })

        total_cost += poi.get("price", 0)
        total_time += travel_minutes + poi.get("wait_time", 0) + stay_duration
        total_wait_time += poi.get("wait_time", 0)
        total_travel_time += travel_minutes
        total_distance += distance_km
        current_point = {"lng": poi["lng"], "lat": poi["lat"]}

    if not selected:
        return None

    return {
        "center": center_point,
        "pois": selected,
        "segments": segments,
        "total_cost": total_cost,
        "total_time": total_time,
        "total_wait_time": total_wait_time,
        "total_travel_time": total_travel_time,
        "total_distance": round(total_distance, 2),
        "option_type": "friends",
        "pace_info": build_pace_info(preferences)
    }


def find_friends_route(start_point=None, preferences=None, user_prefs=None):
    """
    朋友中心选址路线生成。

    preferences 需要包含 friends_locations:
    [
        {"name": "A", "lng": 120.1630, "lat": 30.2768},
        {"name": "B", "lng": 120.2105, "lat": 30.2082}
    ]
    """
    preferences = normalize_pace_preferences(preferences or {})
    friend_locations = validate_friend_locations(preferences.get("friends_locations", []))
    center_point = calculate_center_point(friend_locations)

    pois = get_pois(city=preferences.get("city", "杭州"))
    candidate_pois = filter_friend_pois(pois, center_point, preferences)

    for poi in candidate_pois:
        poi["friend_score"] = score_friend_poi(poi, center_point, preferences, friend_locations)

    candidate_pois = sorted(
        candidate_pois,
        key=lambda item: item["friend_score"],
        reverse=True
    )

    route = build_friends_route(center_point, candidate_pois, preferences, friend_locations)
    if not route:
        return {
            "type": "friends",
            "success": False,
            "message": "当前朋友位置和约束下无法生成合适路线，请放宽预算、时间或排队限制。",
            "center": center_point,
            "route": None,
            "pace_info": build_pace_info(preferences),
            "summary": "当前朋友位置和约束下无法生成合适路线，请放宽预算、时间或排队限制。"
        }

    summary = (
        f"已根据 {len(friend_locations)} 位朋友的位置计算推荐集合点，"
        f"优先选择距离公平、适合聊天聚会的地点："
        f"{' → '.join(poi['name'] for poi in route['pois'])}。"
    )

    relaxation_notice = (
        build_pace_relaxation_notice(route, preferences)
        or "该朋友中心路线遵守你的预算、排队和时间限制。"
    )

    return {
        "type": "friends",
        "success": True,
        "message": "朋友中心路线生成成功",
        "center": center_point,
        "route": route,
        "summary": summary,
        "relaxation_notice": relaxation_notice,
        "pace_info": build_pace_info(preferences),
        "pois": route["pois"],
        "segments": route["segments"],
        "total_cost": route["total_cost"],
        "total_time": route["total_time"],
        "total_wait_time": route["total_wait_time"]
    }

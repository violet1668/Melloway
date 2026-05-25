import math
from datetime import datetime, timedelta

from services.poi_service import get_pois
from services.llm_service import (
    load_mock_user_prefs,
    infer_user_preferences,
    generate_route_summary,
    validate_explanation,
)


def parse_start_point(start):
    """
    解析用户输入的起点坐标。

    输入格式：
    "120.1551,30.2741"

    返回：
    {"lng": 120.1551, "lat": 30.2741}
    """
    try:
        lng_text, lat_text = start.split(",")
        return {
            "lng": float(lng_text.strip()),
            "lat": float(lat_text.strip())
        }
    except Exception:
        raise ValueError("起点坐标格式错误，请使用 lng,lat 格式，例如 120.1551,30.2741")


def parse_time(time_text):
    """
    将 HH:MM 格式的时间转换为 datetime 对象。
    日期不重要，只用于比较当天时间。
    """
    return datetime.strptime(time_text, "%H:%M")


def minutes_between(start_time, end_time):
    """
    计算两个 HH:MM 时间之间的分钟差。
    """
    start_dt = parse_time(start_time)
    end_dt = parse_time(end_time)
    return int((end_dt - start_dt).total_seconds() / 60)


def haversine_km(lng1, lat1, lng2, lat2):
    """
    使用 Haversine 公式计算两个经纬度点之间的直线距离，单位为公里。

    这里不是精确导航距离，但足够用于 MVP 阶段的路线排序和范围过滤。
    """
    radius = 6371

    lng1, lat1, lng2, lat2 = map(math.radians, [lng1, lat1, lng2, lat2])

    d_lng = lng2 - lng1
    d_lat = lat2 - lat1

    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(d_lng / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))

    return radius * c


def estimate_travel_minutes(distance_km, transport):
    """
    根据距离和出行方式估算交通时间。

    walk：约 4.5 km/h
    bike：约 12 km/h
    drive：约 25 km/h
    """
    speed_map = {
        "walk": 4.5,
        "bike": 12,
        "drive": 25
    }

    speed = speed_map.get(transport, 4.5)
    return max(1, int(distance_km / speed * 60))


def infer_search_radius_km(duration_minutes, transport):
    """
    根据预计游玩时长和出行方式，动态推导地点搜索范围。

    逻辑：
    - 时间越短，范围越小；
    - 步行范围最小；
    - 骑行和驾车范围更大；
    - 避免固定写死 8 公里。
    """
    if duration_minutes <= 120:
        base_radius = 2.5
    elif duration_minutes <= 240:
        base_radius = 4.5
    elif duration_minutes <= 360:
        base_radius = 7
    else:
        base_radius = 10

    multiplier = {
        "walk": 1.0,
        "bike": 1.8,
        "drive": 3.0
    }.get(transport, 1.0)

    return base_radius * multiplier


def is_open_during_visit(poi, arrive_time_text):
    """
    判断 POI 在预计到达时间是否营业。
    """
    arrive = parse_time(arrive_time_text)
    open_time = parse_time(poi["open_time"])
    close_time = parse_time(poi["close_time"])

    return open_time <= arrive <= close_time


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

    score += preference_match_score(poi, preferences)

    wait_time = poi.get("wait_time", 0)
    score -= wait_time * 0.4

    budget = preferences.get("budget")
    if budget:
        price_ratio = poi.get("price", 0) / max(budget, 1)
        if price_ratio > 0.5:
            score -= price_ratio * 8

    if option_type == "preference_insight" and user_prefs:
        explicit = user_prefs.get("explicit_preferences", {})
        history = user_prefs.get("history_behavior", {})

        preferred_tags = explicit.get("preferred_tags", [])
        frequent_tags = history.get("frequent_tags", [])
        avoid_poi_ids = history.get("avoid_poi_ids", [])

        for tag in set(preferred_tags + frequent_tags):
            if tag in poi.get("tags", []):
                score += 12

        if poi.get("id") in avoid_poi_ids:
            score -= 50

    if option_type == "demand_satisfaction":
        # 需求满足方案更重视体验质量，因此给高评分 POI 额外加权。
        score += poi.get("rating", 0) * 5

    return round(score, 2)


def filter_pois(pois, start_point, preferences, option_type):
    """
    根据不同方案过滤 POI。

    hard_constraint：
    - 严格满足预算、排队、营业时间、距离范围。

    demand_satisfaction：
    - 更重视用户输入需求和体验，可以适度放宽预算和排队条件。

    preference_insight：
    - 在硬约束基础上结合历史偏好。
    """
    budget = preferences.get("budget", 300)
    max_wait = preferences.get("max_wait", 30)
    time_window = preferences.get("time_window", ["10:00", "18:00"])
    duration_minutes = preferences.get("duration_minutes", 240)
    transport = preferences.get("transport", "walk")

    search_radius_km = infer_search_radius_km(duration_minutes, transport)
    start_time = time_window[0]

    filtered = []

    for poi in pois:
        distance_from_start = haversine_km(
            start_point["lng"],
            start_point["lat"],
            poi["lng"],
            poi["lat"]
        )

        poi = dict(poi)
        poi["distance_from_start_km"] = round(distance_from_start, 2)

        if distance_from_start > search_radius_km:
            continue

        if not is_open_during_visit(poi, start_time):
            continue

        if option_type == "hard_constraint" or option_type == "preference_insight":
            if poi.get("price", 0) > budget:
                continue

            if poi.get("wait_time", 0) > max_wait:
                continue

        if option_type == "demand_satisfaction":
            relaxed_budget = budget * 1.25
            relaxed_wait = max_wait + 15

            if poi.get("price", 0) > relaxed_budget:
                continue

            if poi.get("wait_time", 0) > relaxed_wait:
                continue

        filtered.append(poi)

    return filtered


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


def build_route(start_point, candidate_pois, preferences, option_type, user_prefs=None):
    """
    根据候选 POI 生成路线。

    输出包括：
    - pois：访问顺序
    - segments：每段交通信息
    - total_cost：总花费
    - total_time：总时间
    """
    if not candidate_pois:
        return None

    poi_count = preferences.get("poi_count")
    duration_minutes = preferences.get("duration_minutes", 240)
    time_window = preferences.get("time_window", ["10:00", "18:00"])
    transport = preferences.get("transport", "walk")

    user_specified_poi_count = poi_count is not None and int(poi_count) > 0

    if not poi_count:
        if duration_minutes <= 150:
            poi_count = 2
        elif duration_minutes <= 300:
            poi_count = 3
        else:
            poi_count = 4

    poi_count = int(poi_count)

    # 如果用户明确指定 POI 数量，则该数量作为硬约束。
    # 候选 POI 数量不足时，直接判定当前方案无法满足需求。
    if user_specified_poi_count and len(candidate_pois) < poi_count:
        return None

    # 如果用户未指定 POI 数量，则系统可以根据候选数量动态减少。
    if not user_specified_poi_count:
        poi_count = min(poi_count, len(candidate_pois))

    current_point = start_point
    remaining = list(candidate_pois)
    selected = []
    segments = []

    current_time = parse_time(time_window[0])
    total_cost = 0
    total_time = 0
    total_travel_time = 0
    total_distance = 0

    for index in range(poi_count):
        next_poi = choose_next_poi(current_point, remaining)

        if not next_poi:
            break

        distance = haversine_km(
            current_point["lng"],
            current_point["lat"],
            next_poi["lng"],
            next_poi["lat"]
        )
        travel_minutes = estimate_travel_minutes(distance, transport)

        arrive_time = current_time + timedelta(minutes=travel_minutes)
        leave_time = arrive_time + timedelta(
            minutes=next_poi.get("wait_time", 0) + next_poi.get("stay_duration", 0)
        )

        projected_total_time = total_time + travel_minutes + next_poi.get("wait_time", 0) + next_poi.get("stay_duration", 0)

        if projected_total_time > duration_minutes:
            remaining.remove(next_poi)
            continue

        poi_detail = dict(next_poi)
        poi_detail["arrive_time"] = arrive_time.strftime("%H:%M")
        poi_detail["leave_time"] = leave_time.strftime("%H:%M")

        from_name = "起点" if not selected else selected[-1]["name"]

        segments.append({
            "from": from_name,
            "to": next_poi["name"],
            "transport": transport,
            "duration": travel_minutes,
            "distance": round(distance, 2)
        })

        selected.append(poi_detail)

        total_cost += next_poi.get("price", 0)
        total_time += travel_minutes + next_poi.get("wait_time", 0) + next_poi.get("stay_duration", 0)
        total_travel_time += travel_minutes
        total_distance += distance

        current_time = leave_time
        current_point = {
            "lng": next_poi["lng"],
            "lat": next_poi["lat"]
        }

        remaining.remove(next_poi)

    if not selected:
        return None

    # 如果用户明确指定 POI 数量，但受时间、距离或其他约束影响，
    # 最终没有凑够指定数量，则该方案不应被视为成功。
    if user_specified_poi_count and len(selected) < poi_count:
        return None

    return {
        "start_point": start_point,
        "pois": selected,
        "segments": segments,
        "total_cost": total_cost,
        "total_time": total_time,
        "total_travel_time": total_travel_time,
        "total_distance": round(total_distance, 2),
        "search_radius_km": round(infer_search_radius_km(duration_minutes, transport), 2),
        "option_type": option_type
    }


def generate_one_option(option_type, start_point, preferences, pois, user_prefs):
    """
    生成单个方案。
    """
    filtered_pois = filter_pois(pois, start_point, preferences, option_type)

    for poi in filtered_pois:
        poi["engine_score"] = calculate_poi_score(
            poi,
            preferences,
            user_prefs=user_prefs,
            option_type=option_type
        )

    filtered_pois = sorted(
        filtered_pois,
        key=lambda item: item["engine_score"],
        reverse=True
    )

    route = build_route(
        start_point=start_point,
        candidate_pois=filtered_pois,
        preferences=preferences,
        option_type=option_type,
        user_prefs=user_prefs
    )

    if not route:
        requested_poi_count = preferences.get("poi_count")
        if requested_poi_count:
            fail_message = "当前条件下无法满足指定 POI 数量，请放宽预算、时间或排队限制，或减少 POI 数量。"
        else:
            fail_message = "当前条件下无可用路线，请调整预算、时间或排队限制。"

        return {
            "type": option_type,
            "success": False,
            "message": fail_message,
            "route": None,
            "summary": fail_message
        }

    summary = generate_route_summary(option_type, route, user_prefs)
    is_valid_summary = validate_explanation(summary, route)

    route["summary"] = summary

    return {
        "type": option_type,
        "success": True,
        "message": "路线生成成功",
        "route": route,
        "summary": summary,
        "summary_valid": is_valid_summary
    }


def generate_route_plan(user_request):
    """
    核心入口函数。

    app.py 后续会调用这个函数生成路线。

    user_request 示例：
    {
        "start": "120.1551,30.2741",
        "preferences": {
            "food": ["杭帮菜"],
            "budget": 300,
            "time_window": ["10:00", "18:00"],
            "max_wait": 30,
            "duration_minutes": 240,
            "transport": "walk",
            "poi_count": 3
        }
    }
    """
    start = user_request.get("start")
    preferences = user_request.get("preferences", {})

    if not start:
        return {
            "success": False,
            "message": "缺少起点坐标。",
            "options": []
        }

    try:
        start_point = parse_start_point(start)
    except ValueError as error:
        return {
            "success": False,
            "message": str(error),
            "options": []
        }

    pois = get_pois(city=preferences.get("city", "杭州"))
    user_prefs = load_mock_user_prefs()

    user_input = user_request.get("user_input", "")
    preference_insight = infer_user_preferences(user_input, user_prefs)

    option_types = [
        "demand_satisfaction",
        "hard_constraint",
        "preference_insight"
    ]

    options = []

    for option_type in option_types:
        option = generate_one_option(
            option_type=option_type,
            start_point=start_point,
            preferences=preferences,
            pois=pois,
            user_prefs=user_prefs
        )
        options.append(option)

    has_success_option = any(option.get("success") for option in options)

    return {
        "success": has_success_option,
        "message": "三方案路线生成完成。" if has_success_option else "当前条件下无法生成可用路线，请调整预算、时间、排队限制或 POI 数量。",
        "city": preferences.get("city", "杭州"),
        "start_point": start_point,
        "preference_insight": preference_insight,
        "options": options
    }


if __name__ == "__main__":
    demo_request = {
        "start": "120.1551,30.2741",
        "user_input": "周末想在杭州轻松逛逛，吃点本地特色",
        "preferences": {
            "city": "杭州",
            "food": ["杭帮菜"],
            "tags": ["本地风味", "放松"],
            "budget": 300,
            "time_window": ["10:00", "18:00"],
            "max_wait": 30,
            "duration_minutes": 240,
            "transport": "walk",
            "poi_count": 3
        }
    }

    import json

    result = generate_route_plan(demo_request)
    print(json.dumps(result, ensure_ascii=False, indent=2))

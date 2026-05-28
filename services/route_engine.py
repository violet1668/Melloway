from datetime import timedelta

from services.poi_service import get_pois
from services.user_service import load_user_profile, infer_user_preferences
from services.constraints import (
    parse_start_point,
    parse_time,
    estimate_travel_minutes,
    infer_search_radius_km,
    filter_pois,
    haversine_km,
)
from services.scoring import calculate_poi_score, choose_next_poi
from services.explanation import generate_route_summary, validate_explanation


def build_route(start_point, candidate_pois, preferences, option_type, user_prefs=None):
    """
    根据候选 POI 生成路线。

    输出包括：
    - pois：访问顺序
    - segments：每段交通信息
    - total_cost：总花费
    - total_time：总时间
    - total_wait_time：总排队等待时间
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

    if user_specified_poi_count and len(candidate_pois) < poi_count:
        return None

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
    total_wait_time = 0
    total_distance = 0

    for index in range(poi_count):
        next_poi = choose_next_poi(current_point, remaining)

        if not next_poi:
            break

        distance_km = haversine_km(
            current_point["lng"],
            current_point["lat"],
            next_poi["lng"],
            next_poi["lat"],
        )
        travel_minutes = estimate_travel_minutes(distance_km, transport)

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
            "distance": round(distance_km, 2)
        })

        selected.append(poi_detail)

        total_cost += next_poi.get("price", 0)
        total_time += travel_minutes + next_poi.get("wait_time", 0) + next_poi.get("stay_duration", 0)
        total_travel_time += travel_minutes
        total_wait_time += next_poi.get("wait_time", 0)
        total_distance += distance_km

        current_time = leave_time
        current_point = {
            "lng": next_poi["lng"],
            "lat": next_poi["lat"]
        }

        remaining.remove(next_poi)

    if not selected:
        return None

    if user_specified_poi_count and len(selected) < poi_count:
        return None

    return {
        "start_point": start_point,
        "pois": selected,
        "segments": segments,
        "total_cost": total_cost,
        "total_time": total_time,
        "total_wait_time": total_wait_time,
        "total_travel_time": total_travel_time,
        "total_distance": round(total_distance, 2),
        "search_radius_km": round(infer_search_radius_km(duration_minutes, transport), 2),
        "option_type": option_type
    }


def get_option_name(option_type):
    """
    将方案类型转换为前端展示用的中文名称。
    """
    option_names = {
        "demand_satisfaction": "需求满足方案",
        "hard_constraint": "硬约束方案",
        "preference_insight": "历史偏好洞察方案"
    }
    return option_names.get(option_type, option_type)


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
            "name": get_option_name(option_type),
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
        "name": get_option_name(option_type),
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
    user_prefs = load_user_profile()

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

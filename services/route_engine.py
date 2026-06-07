from datetime import timedelta

from services.poi_service import get_pois
from services.friends import calculate_center_point
from services.user_service import (
    DEFAULT_BUDGET,
    DEFAULT_DURATION_MINUTES,
    DEFAULT_MAX_WAIT,
    extract_preferences_from_text,
    load_user_profile,
    infer_user_preferences,
    unique_keep_order,
)
from services.constraints import (
    parse_start_point,
    parse_time,
    estimate_travel_minutes,
    infer_search_radius_km,
    filter_pois,
    haversine_km,
)
from services.scoring import calculate_poi_score, preference_match_score
from services.explanation import generate_route_summary, validate_explanation
from services.pace import (
    build_pace_info,
    build_pace_relaxation_notice,
    get_adjusted_stay_duration,
    get_base_duration_minutes,
    get_default_poi_count,
    get_effective_duration_minutes,
    get_intensive_poi_count_bonus,
    is_intensive,
    normalize_pace_preferences,
    pace_score_adjustment,
)
from services.persona import (
    apply_persona_to_effective_preferences,
    build_matched_reasons,
    build_persona_context,
    build_quality_scores,
    get_persona_poi_count_delta,
    get_persona_stay_duration_delta,
    normalize_persona_tags,
    persona_route_selection_adjustment,
)


OPTION_CONSTRAINT_POLICIES = {
    "hard_constraint": {
        "budget_relax_ratio": 0,
        "wait_relax_minutes": 0,
        "duration_relax_minutes": 0,
        "duration_relax_ratio": 0,
        "strategy": "严格遵守预算、排队时间和总游玩时间，优先选择低价格、低等待、短距离的稳定路线。"
    },
    "demand_satisfaction": {
        "budget_relax_ratio": 0.15,
        "wait_relax_minutes": 10,
        "duration_relax_minutes": 30,
        "duration_relax_ratio": 0.15,
        "strategy": "优先满足当前显式输入的菜系、标签和兴趣点，允许在明确提示下适度放宽约束。"
    },
    "preference_insight": {
        "budget_relax_ratio": 0.10,
        "wait_relax_minutes": 8,
        "duration_relax_minutes": 20,
        "duration_relax_ratio": 0.10,
        "strategy": "结合用户画像、长期偏好、UGC、小众宝藏点和本地特色，允许在明确提示下小幅放宽约束。"
    }
}

DEFAULT_ASSUMPTION_MESSAGES = {
    "budget": "300元预算",
    "duration_minutes": "4小时",
    "max_wait": "最多排队30分钟"
}

ASSUMPTION_FIELD_LABELS = {
    "budget": "预算",
    "duration_minutes": "游玩时长",
    "max_wait": "排队限制"
}


def build_assumptions(missing_fields):
    """
    说明哪些约束由系统默认补齐。
    """
    if not missing_fields:
        return {
            "has_missing_constraints": False,
            "missing_fields": [],
            "message": "预算、游玩时长和排队限制均已明确。"
        }

    field_labels = [ASSUMPTION_FIELD_LABELS[field] for field in missing_fields]
    labels = [DEFAULT_ASSUMPTION_MESSAGES[field] for field in missing_fields]
    return {
        "has_missing_constraints": True,
        "missing_fields": missing_fields,
        "message": f"你没有填写{ '、'.join(field_labels) }，系统已默认按{ '、'.join(labels) }规划。"
    }


def validate_route_constraints(preferences):
    """
    校验路线生成的基础数值约束。
    """
    try:
        budget = float(preferences.get("budget", DEFAULT_BUDGET))
    except (TypeError, ValueError):
        return "请输入有效预算，预算必须是大于 0 的数字。"

    try:
        duration_minutes = int(preferences.get("duration_minutes", DEFAULT_DURATION_MINUTES))
    except (TypeError, ValueError):
        return "请输入有效游玩时长，游玩时长必须是大于 0 的数字。"

    try:
        max_wait = int(preferences.get("max_wait", DEFAULT_MAX_WAIT))
    except (TypeError, ValueError):
        return "请输入有效排队限制，排队时间不能为负数。"

    if budget <= 0:
        return "请输入有效预算，预算必须大于 0。"

    if duration_minutes <= 0:
        return "请输入有效游玩时长，游玩时长必须大于 0 分钟。"

    if max_wait < 0:
        return "请输入有效排队限制，排队时间不能为负数。"

    preferences["budget"] = budget
    preferences["duration_minutes"] = duration_minutes
    preferences["max_wait"] = max_wait
    return None


def build_option_constraints(option_type, preferences):
    """
    计算某个方案的生效约束和可解释的放宽策略。
    """
    policy = OPTION_CONSTRAINT_POLICIES[option_type]
    budget = float(preferences.get("budget", 300))
    max_wait = int(preferences.get("max_wait", 30))
    preferences = normalize_pace_preferences(preferences)
    base_duration_minutes = get_base_duration_minutes(preferences)

    budget_extra = round(budget * policy["budget_relax_ratio"], 2)
    wait_extra = policy["wait_relax_minutes"]
    if is_intensive(preferences):
        duration_extra = int(preferences.get("time_flex_minutes", 0) or 0)
    else:
        duration_extra = min(
            policy["duration_relax_minutes"],
            int(base_duration_minutes * policy["duration_relax_ratio"])
        )

    effective_preferences = dict(preferences)
    effective_preferences["budget"] = budget + budget_extra
    effective_preferences["max_wait"] = max_wait + wait_extra
    effective_preferences["duration_minutes"] = base_duration_minutes + duration_extra
    effective_preferences["base_duration_minutes"] = base_duration_minutes
    effective_preferences = apply_persona_to_effective_preferences(effective_preferences)

    constraint_policy = {
        "mode": option_type,
        "strategy": policy["strategy"],
        "budget_limit": round(effective_preferences["budget"], 2),
        "max_wait_limit": effective_preferences["max_wait"],
        "duration_minutes_limit": effective_preferences["duration_minutes"],
        "allows_relaxation": option_type != "hard_constraint"
    }

    relaxed_constraints = {
        "budget_extra": round(budget_extra, 2),
        "max_wait_extra": wait_extra,
        "duration_minutes_extra": duration_extra,
        "original_budget": round(budget, 2),
        "original_max_wait": max_wait,
        "original_duration_minutes": base_duration_minutes
    }

    return effective_preferences, constraint_policy, relaxed_constraints


def build_relaxation_notice(route, relaxed_constraints):
    """
    根据路线实际结果说明是否用到了放宽额度。
    """
    if not route:
        return "该方案严格遵守你的预算、排队和时间限制。"

    extra_cost = max(0, round(route.get("total_cost", 0) - relaxed_constraints["original_budget"], 2))
    extra_time = max(0, route.get("total_time", 0) - relaxed_constraints["original_duration_minutes"])
    max_wait = max((poi.get("wait_time", 0) for poi in route.get("pois", [])), default=0)
    extra_wait = max(0, max_wait - relaxed_constraints["original_max_wait"])

    if extra_cost == 0 and extra_time == 0 and extra_wait == 0:
        return "该方案严格遵守你的预算、排队和时间限制。"

    parts = []
    if extra_time > 0:
        parts.append(f"预计比原计划多 {extra_time} 分钟")
    if extra_cost > 0:
        parts.append(f"预算多 {extra_cost:g} 元")
    if extra_wait > 0:
        parts.append(f"单点最高排队时间多 {extra_wait} 分钟")

    return f"这条路线为了更好满足你的偏好，{ '，'.join(parts) }。"


def build_must_visit_summary(route):
    """
    提取 DIY 必去点纳入情况。
    """
    if not route:
        return [], []

    included = route.get("must_visit_pois_included", [])
    missing = route.get("must_visit_pois_missing", [])
    return included, missing


def format_must_visit_reason(included, missing):
    """
    生成 DIY POI 纳入说明。
    """
    parts = []
    if included:
        included_names = "、".join(poi["name"] for poi in included)
        parts.append(f"已纳入你手动添加的 {included_names}")
    if missing:
        missing_names = "、".join(poi["name"] for poi in missing)
        parts.append(f"未纳入 {missing_names}")

    return "；".join(parts)


def build_differentiation_reason(option_type, route, preferences, user_prefs):
    """
    解释当前方案的真实取舍，不使用通用空话。
    """
    pois = route.get("pois", []) if route else []
    if not pois:
        return "当前约束下没有足够 POI 形成该方案。"

    included, missing = build_must_visit_summary(route)
    must_visit_text = format_must_visit_reason(included, missing)

    if option_type == "hard_constraint":
        avg_wait = round(sum(poi.get("wait_time", 0) for poi in pois) / len(pois), 1)
        reason = f"该方案优先控制预算、排队和移动距离，路线总花费 {route['total_cost']} 元，单点平均排队约 {avg_wait} 分钟。"
        if must_visit_text:
            reason += f"DIY POI 处理结果：{must_visit_text}。"
        return reason

    if option_type == "demand_satisfaction":
        matched = [
            poi["name"]
            for poi in pois
            if preference_match_score(poi, preferences) > 0
        ]
        matched_text = "、".join(matched[:3]) if matched else "高评分和热门地点"
        reason = f"该方案优先满足你本次输入的 food/tags 偏好，重点选择了 {matched_text}，并接受有限放宽来提高匹配度。"
        if must_visit_text:
            reason += f"DIY POI 处理结果：{must_visit_text}。"
        return reason

    explicit = user_prefs.get("explicit_preferences", {})
    history = user_prefs.get("history_behavior", {})
    preferred_tags = set(explicit.get("preferred_tags", []) + history.get("frequent_tags", []))
    hidden_names = [poi["name"] for poi in pois if poi.get("is_hidden_gem")]
    tag_hits = sorted({tag for poi in pois for tag in poi.get("tags", []) if tag in preferred_tags})
    ugc_hits = [
        poi["name"]
        for poi in pois
        if any(tag in comment for tag in preferred_tags for comment in poi.get("ugc_comments", []))
    ]
    signals = []
    if hidden_names:
        signals.append(f"小众点 { '、'.join(hidden_names[:2]) }")
    if tag_hits:
        signals.append(f"长期偏好标签 { '、'.join(tag_hits[:3]) }")
    if ugc_hits:
        signals.append(f"UGC 中被反复提到的 { '、'.join(ugc_hits[:2]) }")

    reason = "该方案结合用户画像选择" + "，".join(signals or ["安静、本地风味和适合聊天的地点"]) + "，并降低已去过或不喜欢标签的权重。"
    if must_visit_text:
        reason += f"DIY POI 处理结果：{must_visit_text}。"
    return reason


def normalize_must_visit_poi_ids(raw_must_visit_pois):
    """
    兼容 must_visit_pois 的字符串 id 列表和对象列表格式。
    """
    if not raw_must_visit_pois:
        return []

    normalized_ids = []
    seen_ids = set()

    for item in raw_must_visit_pois:
        if isinstance(item, str):
            poi_id = item
        elif isinstance(item, dict):
            poi_id = item.get("id")
        else:
            poi_id = None

        if poi_id and poi_id not in seen_ids:
            normalized_ids.append(poi_id)
            seen_ids.add(poi_id)

    return normalized_ids


def resolve_must_visit_pois(raw_must_visit_pois, pois):
    """
    根据 id 从现有 POI 数据中解析 DIY 必去点。
    """
    must_visit_ids = normalize_must_visit_poi_ids(raw_must_visit_pois)
    poi_by_id = {poi.get("id"): poi for poi in pois}
    missing_ids = [poi_id for poi_id in must_visit_ids if poi_id not in poi_by_id]

    if missing_ids:
        return [], missing_ids

    return [dict(poi_by_id[poi_id]) for poi_id in must_visit_ids], []


def normalize_route_request(user_request):
    """
    将前端现有格式和 PRD 格式统一为路线引擎内部格式。
    """
    if not isinstance(user_request, dict):
        return {
            "start": None,
            "preferences": {},
            "user_input": "",
            "must_visit_pois": [],
            "preference_insight": {
                "raw_input": "",
                "extracted_food": [],
                "extracted_tags": [],
                "extracted_constraints": {},
                "assumptions": build_assumptions(["budget", "duration_minutes", "max_wait"]),
                "parser_source": "rules"
            }
        }

    raw_preferences = user_request.get("preferences", {})

    if isinstance(raw_preferences, dict):
        preferences = dict(raw_preferences)
        start = user_request.get("start") or user_request.get("start_location")
        user_input = user_request.get("user_input", "")
        must_visit_pois = user_request.get("must_visit_pois", preferences.get("must_visit_pois", []))

        if "budget" not in preferences and "budget" in user_request:
            preferences["budget"] = user_request.get("budget")
        if "max_wait" not in preferences and "max_wait_time" in user_request:
            preferences["max_wait"] = user_request.get("max_wait_time")
        if "max_wait" not in preferences and "max_wait" in user_request:
            preferences["max_wait"] = user_request.get("max_wait")
        if "duration_minutes" not in preferences and "duration_minutes" in user_request:
            preferences["duration_minutes"] = user_request.get("duration_minutes")
        if "duration_minutes" not in preferences and "duration_hours" in user_request:
            preferences["duration_minutes"] = int(float(user_request.get("duration_hours")) * 60)
    else:
        preference_items = raw_preferences if isinstance(raw_preferences, list) else []
        preferences = {
            "city": user_request.get("city", "杭州"),
            "food": preference_items,
            "tags": preference_items,
            "transport": user_request.get("transport", "walk")
        }
        start = user_request.get("start") or user_request.get("start_location")
        user_input = user_request.get("user_input") or "、".join(preference_items)
        must_visit_pois = user_request.get("must_visit_pois", [])

        if "budget" in user_request:
            preferences["budget"] = user_request.get("budget")
        if "max_wait_time" in user_request:
            preferences["max_wait"] = user_request.get("max_wait_time")
        if "duration_hours" in user_request:
            preferences["duration_minutes"] = int(float(user_request.get("duration_hours")) * 60)

        if user_request.get("time_window"):
            preferences["time_window"] = user_request.get("time_window")
        else:
            preferences["time_window"] = [
                user_request.get("start_time", "10:00"),
                user_request.get("end_time", "18:00")
            ]

        if user_request.get("poi_count") is not None:
            preferences["poi_count"] = user_request.get("poi_count")

    for field in ["pace_mode", "time_flex_minutes"]:
        if field in user_request and field not in preferences:
            preferences[field] = user_request.get(field)

    for field in ["persona_tags", "preference_tags", "constraint_tags"]:
        if field in user_request and field not in preferences:
            preferences[field] = user_request.get(field)

    preferences.setdefault("city", user_request.get("city", "杭州"))
    preferences.setdefault("transport", user_request.get("transport", "walk"))
    preferences.setdefault("time_window", user_request.get("time_window", ["10:00", "18:00"]))

    if "food" not in preferences:
        preferences["food"] = []
    if "tags" not in preferences:
        preferences["tags"] = []

    extracted_preferences = extract_preferences_from_text(user_input)
    preferences["food"] = unique_keep_order(
        list(preferences.get("food", [])) + extracted_preferences["food"]
    )
    preferences["tags"] = unique_keep_order(
        list(preferences.get("tags", [])) + extracted_preferences["tags"]
    )

    preferences = normalize_persona_tags(preferences)

    missing_fields = []
    defaults = {
        "budget": DEFAULT_BUDGET,
        "duration_minutes": DEFAULT_DURATION_MINUTES,
        "max_wait": DEFAULT_MAX_WAIT
    }

    for field, default_value in defaults.items():
        if field in preferences:
            continue

        if field in extracted_preferences["constraints"]:
            preferences[field] = extracted_preferences["constraints"][field]
            continue

        preferences[field] = default_value
        missing_fields.append(field)

    preferences = normalize_pace_preferences(preferences)

    assumptions = build_assumptions(missing_fields)
    preference_insight = {
        "raw_input": user_input,
        "extracted_food": extracted_preferences["food"],
        "extracted_tags": extracted_preferences["tags"],
        "extracted_constraints": extracted_preferences["constraints"],
        "assumptions": assumptions,
        "parser_source": "rules"
    }

    return {
        "start": start,
        "preferences": preferences,
        "user_input": user_input,
        "must_visit_pois": must_visit_pois,
        "preference_insight": preference_insight
    }


def choose_next_poi_for_option(current_point, candidate_pois, option_type, preferences, user_prefs=None, avoid_poi_ids=None):
    """
    按方案目标选择下一站，让三种方案在路线层面产生真实差异。
    """
    best_poi = None
    best_value = -999999

    explicit = (user_prefs or {}).get("explicit_preferences", {})
    history = (user_prefs or {}).get("history_behavior", {})
    preferred_tags = set(explicit.get("preferred_tags", []) + history.get("frequent_tags", []))
    disliked_tags = set(explicit.get("disliked_tags", []))
    visited_poi_ids = set(history.get("visited_poi_ids", []))
    avoid_poi_ids = set(avoid_poi_ids or [])

    for poi in candidate_pois:
        distance = haversine_km(
            current_point["lng"],
            current_point["lat"],
            poi["lng"],
            poi["lat"]
        )

        if option_type == "demand_satisfaction":
            value = (
                poi["engine_score"]
                + preference_match_score(poi, preferences) * 0.9
                + poi.get("popularity", 0) * 0.08
                - distance * 5
            )
        elif option_type == "hard_constraint":
            value = (
                poi["engine_score"]
                - distance * 12
                - poi.get("wait_time", 0) * 1.2
                - poi.get("price", 0) * 0.2
            )
        elif option_type == "preference_insight":
            matched_history_tags = len(preferred_tags.intersection(poi.get("tags", [])))
            disliked_hits = len(disliked_tags.intersection(poi.get("tags", [])))
            ugc_hits = sum(
                1 for tag in preferred_tags
                for comment in poi.get("ugc_comments", [])
                if tag in comment
            )
            value = (
                poi["engine_score"]
                + matched_history_tags * 10
                + ugc_hits * 6
                + (16 if poi.get("is_hidden_gem") else 0)
                - max(poi.get("popularity", 0) - 75, 0) * 0.25
                - disliked_hits * 20
                - (30 if poi.get("id") in visited_poi_ids else 0)
                - distance * 7
            )
        else:
            value = poi["engine_score"] - distance * 8

        value += pace_score_adjustment(poi, distance, preferences)
        value += persona_route_selection_adjustment(poi, distance, preferences)

        if poi.get("id") in avoid_poi_ids:
            value -= 18

        if value > best_value:
            best_value = value
            best_poi = poi

    return best_poi


def build_route(start_point, candidate_pois, preferences, option_type, user_prefs=None, avoid_poi_ids=None, must_visit_pois=None):
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

    must_visit_pois = [dict(poi) for poi in (must_visit_pois or [])]
    must_visit_ids = {poi["id"] for poi in must_visit_pois}

    poi_count = preferences.get("poi_count")
    duration_minutes = get_effective_duration_minutes(preferences)
    time_window = preferences.get("time_window", ["10:00", "18:00"])
    transport = preferences.get("transport", "walk")
    budget = preferences.get("budget", 300)

    user_specified_poi_count = poi_count is not None and int(poi_count) > 0

    if not poi_count:
        poi_count = get_default_poi_count(get_base_duration_minutes(preferences))
        poi_count += get_persona_poi_count_delta(preferences)
        poi_count += get_intensive_poi_count_bonus(preferences)

    poi_count = int(poi_count)
    poi_count = max(1, poi_count)
    poi_count = max(poi_count, len(must_visit_pois))

    if user_specified_poi_count and len(candidate_pois) < poi_count and not must_visit_pois:
        return None

    if not user_specified_poi_count:
        poi_count = min(poi_count, len(candidate_pois))

    current_point = start_point
    candidate_by_id = {poi.get("id"): dict(poi) for poi in candidate_pois}
    remaining = list(candidate_by_id.values())
    pending_must_visit_ids = set(must_visit_ids)
    missing_must_visit = []
    selected = []
    segments = []

    current_time = parse_time(time_window[0])
    total_cost = 0
    total_time = 0
    total_travel_time = 0
    total_wait_time = 0
    total_distance = 0

    for index in range(poi_count):
        must_visit_candidates = [
            poi for poi in remaining
            if poi.get("id") in pending_must_visit_ids
        ]
        candidates_for_step = must_visit_candidates or remaining

        next_poi = choose_next_poi_for_option(
            current_point=current_point,
            candidate_pois=candidates_for_step,
            option_type=option_type,
            preferences=preferences,
            user_prefs=user_prefs,
            avoid_poi_ids=avoid_poi_ids
        )

        if not next_poi:
            break

        distance_km = haversine_km(
            current_point["lng"],
            current_point["lat"],
            next_poi["lng"],
            next_poi["lat"],
        )
        depart_time_text = current_time.strftime("%H:%M")
        travel_minutes = estimate_travel_minutes(distance_km, transport, depart_time=depart_time_text)

        arrive_time = current_time + timedelta(minutes=travel_minutes)
        stay_duration = get_adjusted_stay_duration(next_poi, preferences)
        stay_duration = max(15, stay_duration + get_persona_stay_duration_delta(next_poi, preferences))

        leave_time = arrive_time + timedelta(
            minutes=next_poi.get("wait_time", 0) + stay_duration
        )

        projected_total_time = total_time + travel_minutes + next_poi.get("wait_time", 0) + stay_duration
        projected_total_cost = total_cost + next_poi.get("price", 0)
        is_must_visit = next_poi.get("id") in pending_must_visit_ids

        if projected_total_time > duration_minutes:
            remaining.remove(next_poi)
            if is_must_visit:
                missing_must_visit.append(dict(next_poi))
                pending_must_visit_ids.remove(next_poi["id"])
            continue

        if projected_total_cost > budget:
            remaining.remove(next_poi)
            if is_must_visit:
                missing_must_visit.append(dict(next_poi))
                pending_must_visit_ids.remove(next_poi["id"])
            continue

        poi_detail = dict(next_poi)
        original_stay_duration = int(next_poi.get("stay_duration", 0) or 0)
        poi_detail["stay_duration"] = stay_duration
        if stay_duration != original_stay_duration:
            poi_detail["original_stay_duration"] = original_stay_duration
        poi_detail["arrive_time"] = arrive_time.strftime("%H:%M")
        poi_detail["leave_time"] = leave_time.strftime("%H:%M")

        from_name = "起点" if not selected else selected[-1]["name"]

        segments.append({
            "from": from_name,
            "to": next_poi["name"],
            "transport": transport,
            "duration": travel_minutes,
            "distance": round(distance_km, 2),
            "distance_type": "haversine_estimated",
            "time_estimation": "speed_detour_peak_factor",
            "traffic_note": "移动时间基于距离、出行方式和时段系数估算，未接入实时路况。"
        })

        selected.append(poi_detail)
        if is_must_visit:
            pending_must_visit_ids.remove(next_poi["id"])

        total_cost += next_poi.get("price", 0)
        total_time += travel_minutes + next_poi.get("wait_time", 0) + stay_duration
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

    included_must_visit = [
        poi for poi in selected
        if poi.get("id") in must_visit_ids
    ]
    selected_ids = {poi.get("id") for poi in selected}
    missing_must_visit_ids = pending_must_visit_ids.union(
        poi.get("id") for poi in missing_must_visit
    )
    missing_must_visit_by_id = {poi.get("id"): poi for poi in missing_must_visit}
    for poi in must_visit_pois:
        if poi.get("id") in missing_must_visit_ids and poi.get("id") not in selected_ids:
            missing_must_visit_by_id.setdefault(poi.get("id"), poi)

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
        "option_type": option_type,
        "pace_info": build_pace_info(preferences),
        "must_visit_pois_included": included_must_visit,
        "must_visit_pois_missing": list(missing_must_visit_by_id.values())
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


def generate_one_option(option_type, start_point, preferences, pois, user_prefs, avoid_poi_ids=None, must_visit_pois=None):
    """
    生成单个方案。
    """
    effective_preferences, constraint_policy, relaxed_constraints = build_option_constraints(option_type, preferences)
    pace_info = build_pace_info(effective_preferences)

    filtered_pois = filter_pois(pois, start_point, effective_preferences, option_type)

    for poi in filtered_pois:
        poi["engine_score"] = calculate_poi_score(
            poi,
            effective_preferences,
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
        preferences=effective_preferences,
        option_type=option_type,
        user_prefs=user_prefs,
        avoid_poi_ids=avoid_poi_ids,
        must_visit_pois=must_visit_pois
    )

    if not route:
        persona_context = build_persona_context(effective_preferences)
        requested_poi_count = preferences.get("poi_count")
        if requested_poi_count:
            fail_message = "当前条件下无法满足指定 POI 数量，请放宽预算、时间或排队限制，或减少 POI 数量。"
        else:
            fail_message = "当前条件下无可用路线，请调整预算、时间或排队限制。"

        return {
            "type": option_type,
            "name": get_option_name(option_type),
            "plan_type": option_type,
            "plan_name": get_option_name(option_type),
            "success": False,
            "message": fail_message,
            "route": None,
            "summary": fail_message,
            "total_cost": 0,
            "total_time": 0,
            "total_wait_time": 0,
            "pois": [],
            "segments": [],
            "explanation": fail_message,
            "constraint_policy": constraint_policy,
            "relaxed_constraints": relaxed_constraints,
            "relaxation_notice": build_relaxation_notice(None, relaxed_constraints),
            "differentiation_reason": "当前约束下没有足够 POI 形成该方案。",
            "pace_info": pace_info,
            "persona_context": persona_context,
            "matched_reasons": [],
            "quality_scores": build_quality_scores(None, effective_preferences),
            "must_visit_pois_included": [],
            "must_visit_pois_missing": must_visit_pois or []
        }

    differentiation_reason = build_differentiation_reason(option_type, route, preferences, user_prefs)
    relaxation_notice = build_relaxation_notice(route, relaxed_constraints)
    pace_notice = build_pace_relaxation_notice(route, effective_preferences)
    if pace_notice:
        relaxation_notice = pace_notice
    route["constraint_policy"] = constraint_policy
    route["relaxed_constraints"] = relaxed_constraints
    route["relaxation_notice"] = relaxation_notice
    route["differentiation_reason"] = differentiation_reason
    route["pace_info"] = pace_info
    persona_context = build_persona_context(effective_preferences)
    matched_reasons = build_matched_reasons(route, effective_preferences)
    quality_scores = build_quality_scores(route, effective_preferences)
    route["persona_context"] = persona_context
    route["matched_reasons"] = matched_reasons
    route["quality_scores"] = quality_scores

    summary = generate_route_summary(option_type, route, user_prefs)
    is_valid_summary = validate_explanation(summary, route)

    route["summary"] = summary

    return {
        "type": option_type,
        "name": get_option_name(option_type),
        "plan_type": option_type,
        "plan_name": get_option_name(option_type),
        "success": True,
        "message": "路线生成成功",
        "route": route,
        "summary": summary,
        "total_cost": route["total_cost"],
        "total_time": route["total_time"],
        "total_wait_time": route["total_wait_time"],
        "pois": route["pois"],
        "segments": route["segments"],
        "explanation": summary,
        "constraint_policy": constraint_policy,
        "relaxed_constraints": relaxed_constraints,
        "relaxation_notice": relaxation_notice,
        "differentiation_reason": differentiation_reason,
        "pace_info": pace_info,
        "persona_context": persona_context,
        "matched_reasons": matched_reasons,
        "quality_scores": quality_scores,
        "must_visit_pois_included": route["must_visit_pois_included"],
        "must_visit_pois_missing": route["must_visit_pois_missing"],
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
    normalized_request = normalize_route_request(user_request)
    start = normalized_request.get("start")
    preferences = normalized_request.get("preferences", {})
    mode = user_request.get("mode") if isinstance(user_request, dict) else None
    friends_center = None

    constraint_error = validate_route_constraints(preferences)
    if constraint_error:
        return {
            "success": False,
            "message": constraint_error,
            "options": []
        }

    if mode == "friends":
        try:
            friends_center = calculate_center_point(user_request.get("friends_locations", []))
        except ValueError as error:
            return {
                "success": False,
                "message": str(error),
                "options": []
            }

        start = friends_center

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
    must_visit_pois, missing_must_visit_ids = resolve_must_visit_pois(
        normalized_request.get("must_visit_pois", []),
        pois
    )
    if missing_must_visit_ids:
        return {
            "success": False,
            "message": f"未找到手动添加的 POI：{ '、'.join(missing_must_visit_ids) }，请从现有 POI 数据中选择。",
            "options": []
        }

    user_prefs = load_user_profile()

    user_input = normalized_request.get("user_input", "")
    preference_insight = {
        **infer_user_preferences(user_input, user_prefs),
        **normalized_request.get("preference_insight", {})
    }

    option_types = [
        "demand_satisfaction",
        "hard_constraint",
        "preference_insight"
    ]

    options = []
    used_poi_ids = set()

    for option_type in option_types:
        option = generate_one_option(
            option_type=option_type,
            start_point=start_point,
            preferences=preferences,
            pois=pois,
            user_prefs=user_prefs,
            avoid_poi_ids=used_poi_ids,
            must_visit_pois=must_visit_pois
        )
        options.append(option)
        if option.get("success"):
            used_poi_ids.update(poi.get("id") for poi in option.get("pois", []))

    has_success_option = any(option.get("success") for option in options)
    pace_info = build_pace_info(preferences)
    persona_context = build_persona_context(preferences)

    return {
        "success": has_success_option,
        "message": "三方案路线生成完成。" if has_success_option else "当前条件下无法生成可用路线，请调整预算、时间、排队限制或 POI 数量。",
        "city": preferences.get("city", "杭州"),
        "start_point": start_point,
        "friends_center": friends_center,
        "preference_insight": preference_insight,
        "pace_info": pace_info,
        "persona_context": persona_context,
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

def generate_route_summary(option_type, route, user_prefs):
    """
    规则版路线简介生成。

    当前版本：
    - 不调用真实 LLM；
    - 根据路线里的真实 POI、总花费、总时间生成简介；
    - 不允许编造不存在的 POI。
    """
    pois = route.get("pois", [])
    poi_names = [poi.get("name", "未知地点") for poi in pois]
    total_cost = route.get("total_cost", 0)
    total_time = route.get("total_time", 0)

    if not pois:
        return "当前条件下暂未生成可用路线，请适当放宽预算、时间或排队限制。"

    route_text = " → ".join(poi_names)
    differentiation_reason = route.get("differentiation_reason", "")
    relaxation_notice = route.get("relaxation_notice", "")
    detail_text = ""
    if differentiation_reason:
        detail_text += f"{differentiation_reason}"
    if relaxation_notice:
        detail_text += f"{relaxation_notice}"

    if option_type == "demand_satisfaction":
        return f"这条路线优先满足你的输入需求，安排为：{route_text}，预计花费约 {total_cost} 元，总耗时约 {total_time} 分钟。{detail_text}"

    if option_type == "hard_constraint":
        return f"这条路线严格控制预算、排队和时间约束，安排为：{route_text}，预计花费约 {total_cost} 元，总耗时约 {total_time} 分钟。{detail_text}"

    if option_type == "preference_insight":
        explicit = user_prefs.get("explicit_preferences", {})
        preferred_tags = explicit.get("preferred_tags", [])
        tag_text = "、".join(preferred_tags[:3]) if preferred_tags else "轻松体验"
        return f"结合你偏好的{tag_text}，系统推荐：{route_text}，更适合轻松探索杭州本地体验。{detail_text}"

    return f"系统为你生成路线：{route_text}，预计花费约 {total_cost} 元，总耗时约 {total_time} 分钟。{detail_text}"


def validate_explanation(summary, route):
    """
    校验推荐解释是否虚构 POI。

    简化规则：
    - 如果简介中出现了路线外的 POI 名称，后续可以在这里拦截；
    - 当前版本主要保留安全校验入口。
    """
    pois = route.get("pois", [])
    poi_names = [poi.get("name", "") for poi in pois]

    if not poi_names:
        return False

    return any(name in summary for name in poi_names)

import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
MOCK_USER_PREFS_PATH = BASE_DIR / "data" / "mock_user_prefs.json"


def load_mock_user_prefs():
    """
    读取本地 Mock 用户历史偏好。

    当前版本：
    - 使用 mock_user_prefs.json 模拟用户历史偏好。

    后续版本：
    - 可以替换为真实用户画像数据库；
    - 也可以把这些偏好作为 LLM 的输入。
    """
    with open(MOCK_USER_PREFS_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def infer_user_preferences(user_input, user_prefs):
    """
    规则版“偏好洞察”。

    当前版本不调用真实 LLM，只根据用户输入和历史偏好做简单推断。
    后续如果接入真实 LLM，可以替换这个函数内部逻辑，但保持输出格式不变。
    """
    explicit = user_prefs.get("explicit_preferences", {})
    history = user_prefs.get("history_behavior", {})

    favorite_cuisines = explicit.get("favorite_cuisines", [])
    preferred_tags = explicit.get("preferred_tags", [])
    frequent_tags = history.get("frequent_tags", [])

    discovered_preferences = list(set(preferred_tags + frequent_tags))

    inferred_intent = "根据历史偏好，用户更可能偏好轻松、不排队、适合朋友聊天的本地路线。"

    if user_input:
        if "放松" in user_input or "随便" in user_input or "逛逛" in user_input:
            inferred_intent = "用户可能希望进行低压力、轻松探索型出游。"
        elif "吃" in user_input or "聚餐" in user_input:
            inferred_intent = "用户可能更关注餐饮体验和朋友聚餐氛围。"
        elif "西湖" in user_input or "景点" in user_input:
            inferred_intent = "用户可能希望结合杭州城市景观与轻量休闲体验。"

    return {
        "inferred_intent": inferred_intent,
        "favorite_cuisines": favorite_cuisines,
        "discovered_preferences": discovered_preferences
    }


def generate_route_summary(option_type, route, user_prefs):
    """
    规则版路线简介生成。

    当前版本：
    - 不调用真实 LLM；
    - 根据路线里的真实 POI、总花费、总时间生成简介；
    - 不允许编造不存在的 POI。

    参数：
    - option_type: 方案类型，例如 demand_satisfaction / hard_constraint / preference_insight
    - route: route_engine.py 生成的路线结果
    - user_prefs: 用户偏好数据
    """
    pois = route.get("pois", [])
    poi_names = [poi.get("name", "未知地点") for poi in pois]
    total_cost = route.get("total_cost", 0)
    total_time = route.get("total_time", 0)

    if not pois:
        return "当前条件下暂未生成可用路线，请适当放宽预算、时间或排队限制。"

    route_text = " → ".join(poi_names)

    if option_type == "demand_satisfaction":
        return f"这条路线优先满足你的输入需求，安排为：{route_text}，预计花费约 {total_cost} 元，总耗时约 {total_time} 分钟。"

    if option_type == "hard_constraint":
        return f"这条路线严格控制预算、排队和时间约束，安排为：{route_text}，预计花费约 {total_cost} 元，总耗时约 {total_time} 分钟。"

    if option_type == "preference_insight":
        explicit = user_prefs.get("explicit_preferences", {})
        preferred_tags = explicit.get("preferred_tags", [])
        tag_text = "、".join(preferred_tags[:3]) if preferred_tags else "轻松体验"
        return f"结合你偏好的{tag_text}，系统推荐：{route_text}，更适合轻松探索杭州本地体验。"

    return f"系统为你生成路线：{route_text}，预计花费约 {total_cost} 元，总耗时约 {total_time} 分钟。"


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

    # 当前规则：至少要包含一个真实 POI 名称，避免生成完全空泛的解释。
    return any(name in summary for name in poi_names)


def call_real_llm_api(prompt):
    """
    真实 LLM API 预留入口。

    当前版本不启用。
    后续可以在这里接入 OpenAI、Claude、Qwen、Kimi 等模型 API。

    注意：
    - API Key 不要写死在代码里；
    - 应放在 .env 文件中；
    - .env 已经被 .gitignore 忽略，不会上传 GitHub。
    """
    raise NotImplementedError("真实 LLM API 尚未接入，当前版本使用规则模拟。")

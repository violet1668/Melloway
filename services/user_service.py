import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
USER_PROFILE_PATH = BASE_DIR / "data" / "user_profile.json"


def load_user_profile():
    """
    读取本地用户画像数据。

    当前版本：
    - 使用 user_profile.json 模拟用户历史偏好。

    后续版本：
    - 可以替换为真实用户画像数据库；
    - 也可以把这些偏好作为 LLM 的输入。
    """
    with open(USER_PROFILE_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def infer_user_preferences(user_input, user_prefs):
    """
    规则版"偏好洞察"。

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

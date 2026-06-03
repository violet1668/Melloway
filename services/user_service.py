import json
import re
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
USER_PROFILE_PATH = BASE_DIR / "data" / "user_profile.json"

DEFAULT_BUDGET = 300
DEFAULT_DURATION_MINUTES = 240
DEFAULT_MAX_WAIT = 30

FOOD_KEYWORDS = {
    "川菜": ["川菜", "辣", "麻辣", "重口味"],
    "杭帮菜": ["杭帮菜", "杭州菜", "本地菜", "本帮菜"],
    "咖啡": ["咖啡", "咖啡馆", "拿铁", "美式"],
    "甜品": ["甜品", "蛋糕", "下午茶"],
    "小吃": ["小吃", "夜市", "边走边吃"],
    "茶馆": ["茶馆", "喝茶", "龙井茶", "茶室"]
}

TAG_KEYWORDS = {
    "安静": ["安静", "清净", "不吵", "适合聊天"],
    "适合拍照": ["拍照", "出片", "打卡", "好看", "网红"],
    "citywalk": ["citywalk", "散步", "逛逛", "走走", "漫步"],
    "小众": ["小众", "人少", "隐藏", "宝藏", "不想太网红"],
    "本地风味": ["本地", "杭州特色", "地道", "老杭州"],
    "适合朋友聚会": ["朋友", "聚会", "聊天", "一起"],
    "文化感": ["文化", "展览", "博物馆", "书店", "艺术"],
    "夜景": ["夜景", "晚上", "夜晚", "灯光"],
    "亲子友好": ["亲子", "孩子", "家庭", "带娃"],
    "放松": ["放松", "轻松", "慢节奏", "不赶"]
}


def unique_keep_order(items):
    """
    去重并保留原顺序。
    """
    result = []
    seen = set()
    for item in items:
        if item not in seen:
            result.append(item)
            seen.add(item)
    return result


def match_keywords(text, keyword_map):
    """
    使用规则词典从文本中提取标准化偏好。
    """
    matched = []
    for normalized_value, keywords in keyword_map.items():
        if any(keyword in text for keyword in keywords):
            matched.append(normalized_value)
    return matched


def extract_budget(text):
    """
    提取预算表达。
    """
    patterns = [
        r"预算\s*(\d+)",
        r"(\d+)\s*以内",
        r"人均\s*(\d+)\s*左右"
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return int(match.group(1))

    if "便宜一点" in text:
        return 150

    if "别太贵" in text:
        return 200

    return None


def extract_duration_minutes(text):
    """
    提取游玩时长表达。
    """
    match = re.search(r"玩\s*(\d+)\s*小时", text)
    if match:
        return int(match.group(1)) * 60

    match = re.search(r"(\d+)\s*小时", text)
    if match:
        return int(match.group(1)) * 60

    if "一整天" in text:
        return 480

    if "半天" in text or "下午" in text:
        return 240

    return None


def extract_max_wait(text):
    """
    提取排队倾向。
    """
    if "不想排队" in text:
        return 15

    if "少排队" in text:
        return 20

    if "可以排队" in text:
        return 40

    return None


def extract_preferences_from_text(user_input):
    """
    从自然语言中提取结构化偏好。

    当前版本完全基于规则词典，不调用真实 LLM。
    """
    text = user_input or ""
    constraints = {}

    budget = extract_budget(text)
    duration_minutes = extract_duration_minutes(text)
    max_wait = extract_max_wait(text)

    if budget is not None:
        constraints["budget"] = budget
    if duration_minutes is not None:
        constraints["duration_minutes"] = duration_minutes
    if max_wait is not None:
        constraints["max_wait"] = max_wait

    return {
        "raw_input": text,
        "food": unique_keep_order(match_keywords(text, FOOD_KEYWORDS)),
        "tags": unique_keep_order(match_keywords(text, TAG_KEYWORDS)),
        "constraints": constraints,
        "parser_source": "rules"
    }


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

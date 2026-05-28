"""
LLM 服务模块（兼容层）。

本文件保留为向后兼容。
核心逻辑已迁移至：
- services/explanation.py  → generate_route_summary, validate_explanation
- services/user_service.py → load_user_profile, infer_user_preferences
"""

from services.explanation import (
    generate_route_summary,
    validate_explanation,
)
from services.user_service import (
    load_user_profile,
    infer_user_preferences,
)


# 兼容旧名称
def load_mock_user_prefs():
    """兼容旧接口，实际调用 load_user_profile。"""
    return load_user_profile()


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

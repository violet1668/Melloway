"""
POI 数据服务模块。

当前版本：
- 只读取本地 data/poi_hangzhou.json；
- 不再依赖旧版 data/mock_pois.json；
- 后续接入真实 POI API 时，只需要替换本模块的数据读取逻辑，
  route_engine.py 不需要关心数据来自 Mock 文件还是真实 API。
"""

import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
POI_HANGZHOU_PATH = BASE_DIR / "data" / "poi_hangzhou.json"


def load_pois_from_file(path):
    """
    从指定 JSON 文件读取 POI 列表。

    支持两种 JSON 结构：
    1. 直接是 POI 列表：[{...}, {...}]
    2. 包含 pois 字段：{"pois": [{...}, {...}]}
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        return data.get("pois", [])

    return []


def load_mock_pois():
    """
    从新版杭州 POI 数据文件读取 Mock POI 数据。
    """
    if not POI_HANGZHOU_PATH.exists():
        raise FileNotFoundError(f"POI 数据文件不存在：{POI_HANGZHOU_PATH}")

    return load_pois_from_file(POI_HANGZHOU_PATH)


def get_pois(city=None):
    """
    获取 POI 数据的统一入口。

    参数：
    - city: 城市名称。当前 Mock 版本主要使用杭州数据。

    返回：
    - pois: POI 列表
    """
    pois = load_mock_pois()

    if city:
        pois = [
            poi for poi in pois
            if poi.get("city") == city or city == "杭州"
        ]

    return pois


def fetch_pois_from_real_api(city, keyword=None):
    """
    真实 POI API 预留入口。

    当前版本不启用。
    后续接入真实 API 时，可以在这里实现：
    - 请求真实 POI 数据；
    - 将外部 API 字段转换为本项目统一 POI 字段；
    - 返回统一格式的 POI 列表。
    """
    raise NotImplementedError("真实 POI API 尚未接入，当前版本使用本地 Mock 数据。")

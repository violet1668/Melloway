import json
from pathlib import Path


# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent

# Mock POI 数据文件路径
MOCK_POI_PATH = BASE_DIR / "data" / "mock_pois.json"


def load_mock_pois():
    """
    从本地 mock_pois.json 读取 POI 数据。

    当前版本：
    - 使用本地 Mock 数据，方便开发和演示。

    后续版本：
    - 可以替换为真实 POI API，例如美团、高德、Google Places 等。
    - 但返回的数据结构仍然建议保持为统一的 pois 列表。
    """
    with open(MOCK_POI_PATH, "r", encoding="utf-8") as file:
        data = json.load(file)

    return data.get("pois", [])


def get_pois(city=None):
    """
    获取 POI 数据的统一入口。

    参数：
    - city: 城市名称，当前 Mock 版本暂时不根据 city 过滤。

    返回：
    - pois: POI 列表

    设计目的：
    route_engine.py 后续只调用 get_pois()，
    不直接关心数据来自 Mock 文件还是真实 API。
    """
    pois = load_mock_pois()

    # 当前 mock_pois.json 已经是杭州数据，因此这里暂时直接返回全部 POI。
    # 后续如果 mock 数据包含多个城市，可以在这里按 city 过滤。
    return pois


def fetch_pois_from_real_api(city, keyword=None):
    """
    真实 POI API 预留入口。

    当前版本不启用。
    后续接入真实 API 时，可以在这里实现：
    - 请求真实 POI 数据；
    - 将外部 API 字段转换为本项目统一 POI 字段；
    - 返回统一格式的 pois 列表。
    """
    raise NotImplementedError("真实 POI API 尚未接入，当前版本使用 Mock 数据。")

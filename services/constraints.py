import math
from datetime import datetime


def is_valid_coordinate(lng, lat):
    """
    校验经纬度是否合法。
    """
    try:
        lng = float(lng)
        lat = float(lat)
    except (TypeError, ValueError):
        return False

    return -180 <= lng <= 180 and -90 <= lat <= 90


def parse_start_point(start):
    """
    解析用户输入的起点坐标。

    兼容两种格式：

    旧格式：
    "120.1551,30.2741"

    新格式：
    {
        "type": "coordinate",
        "lng": 120.1551,
        "lat": 30.2741,
        "name": "武林广场"
    }

    返回：
    {
        "lng": 120.1551,
        "lat": 30.2741,
        "name": "武林广场"  # 如果有 name 就保留
    }
    """
    # 新接口格式：start 是一个对象
    if isinstance(start, dict):
        try:
            if not is_valid_coordinate(start.get("lng"), start.get("lat")):
                raise ValueError

            result = {
                "lng": float(start.get("lng")),
                "lat": float(start.get("lat"))
            }

            # name 是可选字段，用于前端展示和地图 popup
            if start.get("name"):
                result["name"] = start.get("name")

            return result
        except Exception:
            raise ValueError("起点坐标格式错误，请检查 start.lng 和 start.lat 是否为数字。")

    # 旧接口格式：start 是 "lng,lat" 字符串
    if isinstance(start, str):
        try:
            lng_text, lat_text = start.split(",")
            if not is_valid_coordinate(lng_text.strip(), lat_text.strip()):
                raise ValueError

            return {
                "lng": float(lng_text.strip()),
                "lat": float(lat_text.strip())
            }
        except Exception:
            raise ValueError("起点坐标格式错误，请使用 lng,lat 格式，例如 120.1551,30.2741")

    raise ValueError("起点格式错误，请使用坐标字符串或 start 对象。")



def _is_time_in_window(time_text, start_text, end_text):
    try:
        current = parse_time(time_text).time()
        start = parse_time(start_text).time()
        end = parse_time(end_text).time()
    except (TypeError, ValueError):
        return False

    return start <= current <= end


def get_peak_factor(transport, depart_time=None):
    """
    根据出发时间返回轻量高峰时段系数。
    """
    if transport not in {"bike", "drive"} or not depart_time:
        return 1.0

    if _is_time_in_window(depart_time, "07:30", "09:30"):
        return 1.4 if transport == "drive" else 1.1

    if _is_time_in_window(depart_time, "17:00", "19:00"):
        return 1.5 if transport == "drive" else 1.1

    return 1.0


def estimate_travel_minutes(distance_km, transport, depart_time=None):
    """
    根据距离和出行方式估算交通时间。

    walk：约 4.5 km/h
    bike：约 12 km/h
    drive：约 25 km/h

    基于直线距离进行轻量估算：
    - 先乘以不同出行方式的道路绕行系数；
    - 再按出发时间叠加简单高峰时段系数；
    - 不接入实时路况或外部地图 API。
    """
    speed_map = {
        "walk": 4.5,
        "bike": 12,
        "drive": 25
    }
    detour_factor_map = {
        "walk": 1.15,
        "bike": 1.25,
        "drive": 1.35
    }

    speed = speed_map.get(transport, 4.5)
    detour_factor = detour_factor_map.get(transport, 1.15)
    peak_factor = get_peak_factor(transport, depart_time)
    estimated_distance = distance_km * detour_factor
    return max(1, int(estimated_distance / speed * 60 * peak_factor))


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


def parse_time(time_text):
    """
    将 HH:MM 格式的时间转换为 datetime 对象。
    日期不重要，只用于比较当天时间。
    """
    return datetime.strptime(time_text, "%H:%M")


def is_open_during_visit(poi, arrive_time_text):
    """
    判断 POI 在预计到达时间是否营业。
    """
    arrive = parse_time(arrive_time_text)
    open_time = parse_time(poi["open_time"])
    close_time = parse_time(poi["close_time"])

    return open_time <= arrive <= close_time


def filter_pois(pois, start_point, preferences, option_type):
    """
    根据当前方案的生效约束过滤 POI。

    不同方案的放宽规则由 route_engine 先计算到 preferences 中，
    这里统一按传入的预算、排队、营业时间、距离范围执行。
    """
    budget = preferences.get("budget", 300)
    max_wait = preferences.get("max_wait", 30)
    time_window = preferences.get("time_window", ["10:00", "18:00"])
    duration_minutes = preferences.get("duration_minutes", 240)
    transport = preferences.get("transport", "walk")

    search_radius_km = infer_search_radius_km(duration_minutes, transport)
    search_radius_km *= float(preferences.get("persona_search_radius_multiplier", 1.0) or 1.0)
    start_time = time_window[0]

    filtered = []

    for poi in pois:
        if not is_valid_coordinate(poi.get("lng"), poi.get("lat")):
            continue

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

        if poi.get("price", 0) > budget:
            continue

        if poi.get("wait_time", 0) > max_wait:
            continue

        filtered.append(poi)

    return filtered

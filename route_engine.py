"""
兼容性 shim：将根目录 route_engine.py 的调用转发到 services/route_engine.py。

保留此文件是为了向后兼容，任何直接 `import route_engine` 的代码仍能工作。
"""

from services.route_engine import generate_route_plan  # noqa: F401

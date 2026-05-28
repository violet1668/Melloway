from flask import Flask, render_template, request, jsonify

from services.route_engine import generate_route_plan


app = Flask(__name__)


@app.route("/")
def index():
    """
    首页路由。

    用户访问 http://127.0.0.1:5000/ 时，
    返回前端页面 templates/index.html。
    """
    return render_template("index.html")


@app.route("/api/generate_route", methods=["POST"])
def api_generate_route():
    """
    路线生成 API（旧接口，保留向后兼容）。

    前端会把用户输入的起点、预算、时间、偏好等信息发到这里。
    这个接口再调用 route_engine 中的 generate_route_plan()，
    最后把三方案路线结果以 JSON 格式返回给前端。
    """
    return _handle_route_generation(request)


@app.route("/api/routes/generate", methods=["POST"])
def api_routes_generate():
    """
    路线生成 API（新接口）。

    与旧接口 /api/generate_route 功能相同，
    但路径更规范，响应格式统一。
    """
    return _handle_route_generation(request)


def _handle_route_generation(flask_request):
    """处理路线生成的公共逻辑。"""
    try:
        user_request = flask_request.get_json()

        if not user_request:
            return jsonify({
                "success": False,
                "message": "请求体为空，请提交 JSON 数据。",
                "options": []
            }), 400

        result = generate_route_plan(user_request)
        status_code = 200 if result.get("success") else 400

        return jsonify(result), status_code

    except Exception as error:
        return jsonify({
            "success": False,
            "message": f"服务器处理失败：{str(error)}",
            "options": []
        }), 500


if __name__ == "__main__":
    app.run(debug=True)

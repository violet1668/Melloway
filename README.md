# AI 本地路线智能规划系统 MVP

这是一个基于 **Flask + Leaflet** 的本地路线智能规划系统 MVP。项目目标是模拟一个“AI 本地路线助手”：用户输入起点、预算、时间、排队限制、偏好标签、出行方式等信息后，系统基于杭州 Mock POI 数据生成三种路线方案，并在网页中展示方案卡片和地图路线。

当前版本重点完成了 P0 主流程：

~~~text
用户输入需求
→ 后端生成路线
→ 前端展示三方案
→ 地图显示 POI 与路线连线
~~~

项目已经完成基础工程化拆分，适合两人继续进行前后端分工开发。

---

## 1. 项目简介

本项目面向本地生活路线规划场景，当前以杭州为示例城市，使用本地 Mock POI、地标和用户画像数据，模拟 AI 根据用户需求生成本地出行路线的过程。

当前版本不是完整商业化产品，而是一个可运行、可演示、可继续扩展的 MVP。它主要验证以下能力：

- 能否从用户输入中获得路线约束；
- 能否根据预算、排队、营业时间、距离等条件筛选 POI；
- 能否生成不同策略下的三种路线方案；
- 能否在前端展示方案卡片；
- 能否在 Leaflet 地图中展示起点、POI 标记和路线连线；
- 能否为后续真实 POI API、真实 LLM、朋友选址和盲盒路线预留接口。

---

## 2. 当前版本状态

当前版本已经完成：

- Flask 后端服务；
- 首页输入表单；
- 杭州 Mock POI 数据读取；
- Mock 用户画像读取；
- 杭州地标数据预留；
- 起点坐标解析；
- 预算、排队时间、营业时间、距离范围等约束过滤；
- POI 综合评分；
- 三种路线方案生成；
- 推荐解释生成；
- 三方案卡片展示；
- Leaflet 地图展示；
- 前后端文件结构拆分；
- API、数据、模块、演示文档占位；
- 测试目录占位；
- 旧版文件清理。

当前版本仍然是 MVP，不代表真实线上产品，也不接入真实美团、高德、Google Places 或 LLM API。

---

## 3. 已完成功能

### 3.1 路线生成核心能力

当前后端已经支持：

- 读取杭州 POI 数据；
- 读取用户画像数据；
- 解析起点坐标；
- 根据用户游玩时长推导推荐 POI 数量和搜索范围；
- 根据预算、排队时间、营业时间过滤 POI；
- 根据评分、偏好标签、价格、等待时间和用户画像对 POI 打分；
- 生成三种路线方案；
- 返回统一 JSON 响应。

### 3.2 三种路线方案

当前系统固定生成三类方案：

~~~text
demand_satisfaction    # 需求满足方案
hard_constraint        # 硬约束方案
preference_insight     # 历史偏好洞察方案
~~~

三种方案分别用于模拟不同推荐策略：

- **需求满足方案**：优先满足用户输入需求，侧重体验完整性；
- **硬约束方案**：更严格控制预算、排队、营业时间和距离；
- **历史偏好洞察方案**：结合 Mock 用户画像和历史偏好生成推荐。

### 3.3 前端展示能力

当前前端已经支持：

- 表单输入；
- 点击按钮请求后端 API；
- 渲染三种方案卡片；
- 展示方案名称、简介、总价、总时长、总等待时间和 POI 数量；
- 点击方案后在地图中展示路线；
- Leaflet 地图展示起点、POI 标记和路线连线。

---

## 4. 当前未完成 / 占位功能

当前项目中有一些模块已经创建，但还只是占位或简化版本：

- `services/friends.py`：朋友中心选址占位模块；
- `services/blindbox.py`：盲盒路线占位模块；
- `PRD.md`：产品需求文档占位版；
- `EXECUTION_PLAN.md`：执行计划占位版；
- `docs/api.md`：API 文档占位版；
- `docs/data_contract.md`：数据契约占位版；
- `docs/module_contract.md`：模块契约占位版；
- `docs/demo_script.md`：演示脚本占位版；
- `tests/`：当前为基础占位测试，后续需要补充真实测试。

---

## 5. 项目结构

~~~text
ai-local-route-engine/
├── app.py                              # Flask 主入口：页面路由和 API 路由
├── requirements.txt                    # Python 依赖
├── README.md                           # GitHub 首页说明
├── PRD.md                              # 产品需求文档
├── EXECUTION_PLAN.md                   # 开发执行计划与分工说明
├── .gitignore                          # Git 忽略规则
│
├── data/
│   ├── poi_hangzhou.json               # 杭州 Mock POI 数据
│   ├── landmarks_hangzhou.json         # 杭州地标数据
│   └── user_profile.json               # Mock 用户画像与历史偏好
│
├── services/
│   ├── __init__.py                     # Python 包标识
│   ├── route_engine.py                 # 路线生成核心入口
│   ├── constraints.py                  # 约束过滤与起点解析
│   ├── scoring.py                      # POI 评分逻辑
│   ├── explanation.py                  # 推荐解释生成
│   ├── poi_service.py                  # POI 数据读取入口
│   ├── user_service.py                 # 用户画像读取入口
│   ├── friends.py                      # 朋友中心选址占位模块
│   └── blindbox.py                     # 盲盒路线占位模块
│
├── templates/
│   └── index.html                      # 页面骨架
│
├── static/
│   ├── css/
│   │   └── style.css                   # 页面样式
│   └── js/
│       ├── config.js                   # 前端接口地址和方案名称配置
│       ├── main.js                     # 表单读取、请求后端、渲染方案卡片
│       └── map.js                      # Leaflet 地图初始化和路线展示
│
├── docs/
│   ├── DECISIONS.md                    # 开发决策记录
│   ├── api.md                          # API 接口契约
│   ├── data_contract.md                # 数据字段契约
│   ├── module_contract.md              # 模块职责契约
│   ├── demo_script.md                  # 演示脚本
│   └── screenshots/
│       └── .gitkeep                    # 保留截图目录
│
└── tests/
    ├── test_api.py                     # Flask API 测试
    ├── test_constraints.py             # 约束模块测试
    └── test_route_engine.py            # 路线引擎测试
~~~

---

## 6. 技术栈

后端：

- Python 3
- Flask
- 本地 JSON Mock 数据

前端：

- HTML
- CSS
- JavaScript
- Leaflet
- OpenStreetMap 地图底图

协作工具：

- Git
- GitHub
- Feature Branch
- Pull Request

---

## 7. 本地运行方式

### 7.1 克隆项目

如果是第一次下载项目：

~~~bash
cd ~/Desktop
git clone https://github.com/violet1668/ai-local-route-engine.git
cd ai-local-route-engine
~~~

如果已经下载过项目：

~~~bash
cd ~/Desktop/ai-local-route-engine
git checkout main
git pull origin main
~~~

### 7.2 创建并激活虚拟环境

第一次运行时：

~~~bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
~~~

之后再次运行时，只需要激活虚拟环境：

~~~bash
source .venv/bin/activate
~~~

### 7.3 启动项目

~~~bash
python3 app.py
~~~

启动成功后，终端会显示类似：

~~~text
Running on http://127.0.0.1:5000
~~~

浏览器打开：

~~~text
http://127.0.0.1:5000
~~~

### 7.4 停止项目

在运行 Flask 的终端中按：

~~~text
Control + C
~~~

---

## 8. 页面使用方式

打开首页后，可以输入或调整：

- 起点信息；
- 用户自然语言需求；
- 菜系偏好；
- 偏好标签；
- 预算上限；
- 最大排队时间；
- 开始时间与结束时间；
- 预计游玩时长；
- 出行方式；
- 期望 POI 数量。

点击生成按钮后，系统会返回三种路线方案：

1. **需求满足方案**  
   优先满足用户输入需求，侧重体验完整性。

2. **硬约束方案**  
   更严格控制预算、排队时间、营业时间和路线范围。

3. **历史偏好洞察方案**  
   结合 Mock 用户画像和历史偏好生成路线推荐。

每个方案会展示：

- 方案名称；
- 推荐简介；
- POI 数量；
- 总耗时；
- 总花费；
- 总等待时间；
- 路线详情；
- 地图查看按钮。

点击地图查看后，页面会展示对应路线的起点、POI 标记和路线连线。

---

## 9. API 接口说明

### 9.1 路线生成接口

正式接口：

~~~text
POST /api/routes/generate
~~~

兼容旧接口：

~~~text
POST /api/generate_route
~~~

两个接口均调用同一套路由生成逻辑。后续前端开发统一使用正式接口：

~~~text
/api/routes/generate
~~~

### 9.2 请求示例

~~~json
{
  "mode": "standard",
  "start": {
    "type": "coordinate",
    "lng": 120.1551,
    "lat": 30.2741,
    "name": "武林广场"
  },
  "user_input": "周末想在杭州轻松逛逛，吃点本地特色",
  "preferences": {
    "city": "杭州",
    "food": ["杭帮菜"],
    "tags": ["本地风味", "放松"],
    "budget": 300,
    "time_window": ["10:00", "18:00"],
    "duration_minutes": 240,
    "max_wait": 30,
    "transport": "walk",
    "companion": "friends",
    "poi_count": null
  }
}
~~~

### 9.3 响应核心字段

后端响应包含：

~~~text
success
message
city
options
options[].type
options[].name
options[].success
options[].summary
options[].route
route.start_point
route.pois
route.segments
route.total_cost
route.total_time
route.total_wait_time
route.total_distance
route.search_radius_km
~~~

### 9.4 三种方案类型

~~~text
demand_satisfaction    # 需求满足方案
hard_constraint        # 硬约束方案
preference_insight     # 历史偏好洞察方案
~~~

---

## 10. 数据文件说明

当前数据文件位于 `data/` 目录：

~~~text
data/poi_hangzhou.json
data/landmarks_hangzhou.json
data/user_profile.json
~~~

### 10.1 POI 数据

文件：

~~~text
data/poi_hangzhou.json
~~~

用途：

- 提供杭州 Mock POI 数据；
- 支持路线生成、评分、预算过滤、排队过滤和地图展示。

主要字段包括：

- `id`
- `name`
- `type`
- `category`
- `cuisine`
- `lng`
- `lat`
- `rating`
- `price`
- `wait_time`
- `stay_duration`
- `open_time`
- `close_time`
- `tags`
- `suitable_for`
- `popularity`

### 10.2 地标数据

文件：

~~~text
data/landmarks_hangzhou.json
~~~

用途：

- 起点选择；
- 朋友中心选址预留；
- 默认测试点位。

主要字段包括：

- `id`
- `name`
- `lng`
- `lat`
- `district`
- `tags`

### 10.3 用户画像数据

文件：

~~~text
data/user_profile.json
~~~

用途：

- 模拟用户历史偏好；
- 支持历史偏好洞察方案；
- 后续可替换为真实用户系统或数据库。

主要字段包括：

- `user_id`
- `city`
- `profile`
- `explicit_preferences`
- `history_behavior`

---

## 11. 后端模块说明

### 11.1 `app.py`

Flask 主入口，负责：

- 注册首页路由；
- 注册 API 路由；
- 接收前端请求；
- 调用路线生成服务；
- 返回 JSON 响应。

主要接口：

~~~text
GET /
POST /api/routes/generate
POST /api/generate_route
~~~

### 11.2 `services/route_engine.py`

路线生成核心入口，负责：

- 接收用户请求；
- 解析用户偏好；
- 读取 POI 数据；
- 读取用户画像；
- 生成三种路线方案；
- 返回统一结构的路线结果。

### 11.3 `services/constraints.py`

约束过滤模块，负责：

- 起点解析；
- 动态搜索范围推导；
- 预算过滤；
- 排队时间过滤；
- 营业时间过滤；
- 出行时间估算；
- 距离计算。

### 11.4 `services/scoring.py`

POI 评分模块，负责：

- 基础评分计算；
- 偏好标签匹配；
- 菜系偏好匹配；
- 用户画像加权；
- 排队惩罚；
- 价格惩罚。

### 11.5 `services/explanation.py`

推荐解释模块，负责：

- 根据方案类型生成推荐理由；
- 根据预算、等待时间、偏好标签生成路线简介；
- 当前为规则模板版；
- 后续可替换为真实 LLM。

### 11.6 `services/poi_service.py`

POI 数据服务，负责：

- 读取 `data/poi_hangzhou.json`；
- 返回统一 POI 列表；
- 预留真实 POI API 接入口。

### 11.7 `services/user_service.py`

用户画像服务，负责：

- 读取 `data/user_profile.json`；
- 返回 Mock 用户画像；
- 后续可替换为真实用户数据库。

### 11.8 `services/friends.py`

朋友中心选址占位模块。当前只作为后续功能入口保留，未来可实现：

- 多人位置输入；
- 中心点计算；
- 地标匹配；
- 朋友聚会路线生成。

### 11.9 `services/blindbox.py`

盲盒路线占位模块。当前只作为后续功能入口保留，未来可实现：

- Citywalk 盲盒路线；
- 吃喝主题路线；
- 文化探索路线；
- 随机 POI 组合。

---

## 12. 前端模块说明

### 12.1 `templates/index.html`

页面骨架，负责：

- 页面结构；
- 表单区域；
- 方案卡片区域；
- 地图容器；
- 引入 CSS 和 JS 文件。

### 12.2 `static/css/style.css`

页面样式文件，负责：

- 页面布局；
- 表单样式；
- 按钮样式；
- 三方案卡片样式；
- 地图区域样式；
- 错误提示样式。

### 12.3 `static/js/config.js`

前端配置文件，负责：

- API 地址配置；
- 方案类型与中文名称映射；
- 后续可扩展统一配置项。

### 12.4 `static/js/main.js`

前端主逻辑，负责：

- 读取表单输入；
- 组装请求 JSON；
- 请求后端 API；
- 渲染三方案卡片；
- 展示错误提示；
- 调用地图展示函数。

### 12.5 `static/js/map.js`

地图逻辑，负责：

- 初始化 Leaflet 地图；
- 添加起点 Marker；
- 添加 POI Marker；
- 绘制路线 Polyline；
- 点击不同方案时切换地图路线。

---

## 13. 测试方式

运行基础测试：

~~~bash
python3 -m unittest discover -s tests
~~~

运行 Python 语法检查：

~~~bash
python3 -m py_compile app.py services/*.py
~~~

当前 `tests/` 目录已经创建，但部分测试仍为占位版本。后续应逐步补充真实测试，例如：

- 正常输入是否返回三方案；
- 坐标格式错误是否返回错误提示；
- 预算过低是否触发失败方案；
- 指定 POI 数量是否生效；
- `/api/routes/generate` 是否返回统一字段；
- 地图所需字段是否完整返回。

---

## 14. GitHub 协作流程

本项目采用 GitHub 分支协作模式：

~~~text
main：稳定版本
feature/xxx：功能开发分支
Pull Request：功能完成后申请合并
~~~

### 14.1 后端开发流程

~~~bash
git checkout main
git pull origin main
git checkout -b feature/backend-core-optimization
~~~

开发完成后：

~~~bash
git add .
git commit -m "Update backend route engine"
git push -u origin feature/backend-core-optimization
~~~

然后在 GitHub 创建 Pull Request。

### 14.2 前端开发流程

~~~bash
git checkout main
git pull origin main
git checkout -b feature/frontend-ui-optimization
~~~

开发完成后：

~~~bash
git add .
git commit -m "Update frontend route cards and map view"
git push -u origin feature/frontend-ui-optimization
~~~

然后在 GitHub 创建 Pull Request。

### 14.3 合并规则

合并前必须确认：

- 没有未提交文件；
- 本地测试通过；
- 页面主流程可运行；
- PR 无冲突；
- 合并后所有人重新 `git pull origin main`。

---

## 15. 前后端分工建议

### 15.1 后端主要负责

~~~text
app.py
services/
data/
docs/api.md
docs/data_contract.md
docs/module_contract.md
tests/
~~~

重点任务：

- 路线生成；
- 约束过滤；
- POI 评分；
- 推荐解释；
- 用户画像读取；
- API 返回字段；
- 数据字段规范；
- 测试用例。

### 15.2 前端主要负责

~~~text
templates/index.html
static/css/style.css
static/js/config.js
static/js/main.js
static/js/map.js
docs/demo_script.md
docs/screenshots/
~~~

重点任务：

- 输入表单；
- 三方案卡片；
- 详情展示；
- Leaflet 地图；
- 页面视觉；
- 错误提示；
- 演示截图。

---

## 16. 联调检查清单

每次前后端合并后，应共同检查：

- 页面能否正常打开；
- 点击生成路线后是否出现三张方案卡片；
- 三张卡片名称是否正常；
- 是否展示总价、总时长、总等待时间；
- 点击地图查看后是否显示 POI 标记；
- 地图路线连线是否显示；
- `/api/routes/generate` 是否返回 200；
- 异常输入是否有提示；
- `python3 -m py_compile app.py services/*.py` 是否通过；
- `python3 -m unittest discover -s tests` 是否通过。

---

## 17. 当前版本边界

当前版本仍然是本地 MVP，不包含：

- 真实 POI API；
- 真实 LLM API；
- 用户登录；
- 用户画像数据库；
- 真实导航路径规划；
- 实时排队数据；
- 真实交通时间；
- 完整朋友中心选址；
- 完整盲盒路线；
- 线上生产部署。

当前路线距离和交通时间主要基于简化估算，不代表真实导航结果。

---

## 18. 后续开发路线

### 18.1 完善真实测试

将 `tests/` 中的占位测试逐步替换为真实测试。

重点测试：

- 路线生成；
- 约束过滤；
- POI 评分；
- API 响应字段；
- 异常输入；
- 约束过严场景。

### 18.2 完善 API 文档

补充：

- 请求字段表；
- 响应字段表；
- 错误码；
- 示例输入；
- 示例输出。

### 18.3 扩展 POI 数据

将杭州 POI 数据扩展到 40–60 个，覆盖：

- 餐厅；
- 咖啡；
- 景点；
- 文化空间；
- 商圈；
- Citywalk 点位。

### 18.4 朋友中心选址

后续在 `services/friends.py` 中实现：

- 多人起点输入；
- 中心点计算；
- 推荐集合地点；
- 朋友聚会路线生成。

### 18.5 盲盒路线

后续在 `services/blindbox.py` 中实现：

- 主题路线；
- 随机路线；
- 小众探索路线；
- 吃喝路线；
- 文化路线。

### 18.6 接入真实 POI API

后续可在 `services/poi_service.py` 中接入：

- 高德地图；
- Google Places；
- 美团相关数据源；
- 其他开放 POI 数据接口。

### 18.7 接入真实 LLM

后续可在 `services/explanation.py` 或新增 LLM 服务中接入真实模型，用于：

- 用户意图理解；
- 偏好补全；
- 路线解释生成；
- 个性化推荐理由。

---

## 19. 常见问题

### 19.1 为什么有 `services/__init__.py`？

它用于告诉 Python：`services/` 是一个可以被 import 的包。这样代码可以稳定使用：

~~~python
from services.route_engine import generate_route_plan
~~~

### 19.2 为什么 `docs/screenshots/` 里有 `.gitkeep`？

Git 不会上传空文件夹。`.gitkeep` 是占位文件，用来让 GitHub 保留这个截图目录。以后放入真实截图后，可以保留或删除 `.gitkeep`。

### 19.3 为什么 `friends.py` 和 `blindbox.py` 现在没有完整功能？

这两个模块属于后续扩展功能。当前版本先保留入口，避免后续再大规模调整项目结构。

### 19.4 为什么当前使用 Mock 数据？

因为 MVP 阶段重点验证核心路线引擎、页面展示和地图展示逻辑。真实 POI API 和真实 LLM 接入留到后续版本。

---

## 20. 项目状态总结

当前版本已经完成：

~~~text
核心 MVP 主流程
最终项目结构整理
旧文件清理
前后端模块拆分
基础文档目录
基础测试目录
GitHub 分支协作准备
~~~

当前最重要的下一步是：

~~~text
1. 完善 PRD.md、EXECUTION_PLAN.md 和 docs 文档
2. 完善 tests 中的真实测试
3. 前后端分别基于 feature 分支继续优化
4. 完成在线 Demo 部署
~~~

# AI 本地路线智能规划系统 MVP

这是一个基于 **Flask + Leaflet** 的本地路线智能规划系统 MVP。项目目标是模拟一个“AI 本地路线助手”：用户输入起点、预算、时间、排队限制、偏好标签、出行方式等信息后，系统基于杭州 Mock POI 数据生成三种路线方案，并在网页中展示方案卡片和地图路线。

当前版本重点完成了 P0/P1 可演示主流程：

~~~text
用户输入需求
→ 后端解析结构化偏好
→ 生成差异化三方案 / DIY 重生成 / 朋友中心 / 盲盒路线
→ 前端展示路线结果
→ 地图显示 POI 与路线连线
~~~

项目已经完成基础工程化拆分和核心后端能力补齐，适合继续进入前后端联调、体验优化和演示打磨阶段。

---

## 1. 项目简介

本项目面向本地生活路线规划场景，当前以杭州为示例城市，使用本地 Mock POI、地标和用户画像数据，模拟 AI 根据用户需求生成本地出行路线的过程。

当前版本不是完整商业化产品，而是一个可运行、可演示、可继续扩展的 MVP。它主要验证以下能力：

- 能否从用户输入中获得路线约束；
- 能否从自然语言中提取餐饮偏好、场景标签、预算、时长和排队限制；
- 能否根据预算、排队、营业时间、距离等条件筛选 POI；
- 能否生成不同策略下的三种路线方案；
- 能否支持用户手动添加必去 POI 后重新生成路线；
- 能否支持朋友中心选址路线；
- 能否支持主题盲盒路线；
- 能否支持全局“特种兵模式”路线节奏；
- 能否在前端展示方案卡片；
- 能否在 Leaflet 地图中展示起点、POI 标记和路线连线；
- 能否为后续真实 POI API、真实 LLM、数据库和登录系统预留扩展空间。

---

## 2. 当前版本状态

当前版本已经完成：

- Flask 后端服务；
- 首页输入表单；
- 杭州 Mock POI 数据读取，当前 POI 已扩充并包含 UGC 评论和小众标识；
- Mock 用户画像读取；
- 杭州地标数据预留；
- 起点坐标解析；
- 预算、排队时间、营业时间、距离范围等约束过滤；
- POI 综合评分；
- 三种差异化路线方案生成；
- 当前前端格式与 PRD 格式请求兼容；
- 自然语言偏好规则解析；
- DIY 添加必去 POI 并重新生成路线；
- 朋友中心选址路线；
- 主题盲盒路线；
- 全局 normal / intensive 路线节奏参数；
- 推荐解释生成；
- 三方案卡片展示；
- Leaflet 地图展示；
- 前后端文件结构拆分；
- API、数据、模块、演示文档基础目录；
- 后端真实测试覆盖；
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
- 生成三种真实差异化路线方案；
- 返回约束策略、放宽说明和差异化理由；
- 返回统一 JSON 响应。

### 3.2 三种路线方案

当前系统固定生成三类方案：

~~~text
demand_satisfaction    # 需求满足方案
hard_constraint        # 硬约束方案
preference_insight     # 历史偏好洞察方案
~~~

三种方案分别用于模拟不同推荐策略：

- **需求满足方案**：优先满足用户显式输入的 food/tags 和本次偏好，必要时在规则允许范围内放宽预算、排队和总时长，并明确提示；
- **硬约束方案**：严格控制预算、排队和总游玩时间，优先低价格、低等待、短距离和稳定路线；
- **历史偏好洞察方案**：结合 Mock 用户画像、preferred_tags、UGC 评论、hidden gem 标识、长期偏好和已访问记录生成推荐。

### 3.3 自然语言偏好解析

当前后端支持用户只输入 `user_input`，系统自动提取结构化偏好：

- 餐饮偏好：川菜、杭帮菜、咖啡、甜品、小吃、茶馆；
- 场景标签：安静、适合拍照、citywalk、小众、本地风味、朋友聚会、文化感、夜景、亲子友好、放松；
- 预算表达：如“预算200”“200以内”“人均100左右”“别太贵”“便宜一点”；
- 时间表达：如“玩3小时”“4小时”“半天”“下午”“一整天”；
- 排队倾向：如“不想排队”“少排队”“可以排队”。

如果用户没有填写预算、游玩时长或最大排队时间，系统会默认使用：

~~~text
budget = 300
duration_minutes = 240
max_wait = 30
~~~

返回结果会包含 `preference_insight` 和 `assumptions`，说明哪些字段来自规则解析，哪些字段由系统默认假设补齐。

### 3.4 DIY 添加 POI 并重新生成路线

路线生成接口支持新增 `must_visit_pois` 字段。用户可以从现有 `data/poi_hangzhou.json` 中选择一个或多个 POI 作为必去点，然后重新生成三方案。

支持格式：

~~~json
["poi_001", "poi_008"]
~~~

或：

~~~json
[{"id": "poi_001", "name": "西湖断桥"}]
~~~

返回结果中每个 option 会包含：

- `must_visit_pois_included`
- `must_visit_pois_missing`

如果传入不存在的 POI id，后端返回 `success:false` 和中文提示。

### 3.5 朋友中心选址路线

当前后端已实现朋友中心选址能力：

- 支持至少两个朋友位置；
- 使用经纬度均值计算推荐集合点；
- 基于集合点筛选附近适合聊天、聚会、轻松活动的 POI；
- 返回朋友集合点、路线详情和公平性距离信息；
- 少于两个朋友地点时返回 `success:false` 和中文提示。

可通过两种路径使用：

~~~text
POST /api/routes/generate  # mode = friends
POST /api/friends/center
~~~

### 3.6 盲盒主题路线

当前后端已实现主题盲盒路线：

- 支持 `citywalk`、`foodie`、`culture`、`hidden_gem` 等主题及中文别名；
- 每次返回 3 个外观一致的盲盒；
- 盲盒初始可见字段不暴露“稳妥”“小众”“主题直觉”等策略提示；
- 盲盒内部 option 保留完整路线详情；
- 三条路线内部使用不同策略保证 POI 组合差异；
- 返回前随机打乱盲盒顺序。

接口：

~~~text
POST /api/routes/blind-box
~~~

### 3.7 全局特种兵模式

当前后端已实现全局路线节奏参数：

~~~text
pace_mode = normal | intensive
time_flex_minutes = 0 | 30 | 60
~~~

其中：

- `normal` 为标准模式，平衡路线数量与停留体验；
- `intensive` 为特种兵模式，优先选择更紧凑、更顺路、等待更短、适合快进快出的 POI；
- `time_flex_minutes` 表示用户允许额外增加的总游览时间，最大不超过 60 分钟。

特种兵模式不会简单压缩所有 POI 停留时间。系统只会对小吃、茶饮、打卡点、商圈、街区、城市观景点等适合快进快出的 POI 轻微压缩停留时间；不会明显压缩正式景点、博物馆、美术馆、寺庙、大型公园、正式餐厅和深度文化空间。

每次路线结果会返回 `pace_info`：

~~~json
{
  "pace_mode": "intensive",
  "label": "特种兵模式",
  "time_flex_minutes": 60,
  "message": "当前为特种兵模式，系统会优先选择更紧凑、顺路的 POI，并在你允许的 60 分钟弹性范围内尽可能增加游玩点。"
}
~~~

### 3.8 前端展示能力

当前前端已经支持：

- 表单输入；
- 点击按钮请求后端 API；
- 渲染三种方案卡片；
- 展示方案名称、简介、总价、总时长、总等待时间和 POI 数量；
- 点击方案后在地图中展示路线；
- Leaflet 地图展示起点、POI 标记和路线连线。

---

## 4. 当前阶段说明

当前阶段已经完成 P0/P1 后端核心可演示目标，重点能力包括标准路线、PRD 格式兼容、自然语言解析、DIY 必去点、朋友中心、盲盒路线和全局特种兵模式。

当前仍然保持 MVP 边界：

- 使用本地 Mock POI 数据；
- 使用规则词典解析自然语言；
- 使用简化距离和交通时间估算；
- 不接入真实地图路线 API；
- 不接入真实 LLM；
- 不接入数据库、登录系统或线上部署能力。

下一阶段重点不应继续堆后端新功能，而应优先做：

- 前后端联调，确认当前前端是否完整展示新增字段；
- 更新 `docs/api.md`、`docs/data_contract.md` 和演示脚本；
- 针对真实演示路径补充端到端手工检查清单；
- 优化前端对盲盒揭晓、DIY 添加 POI、自然语言解析结果和特种兵模式的展示体验。

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
│   ├── user_service.py                 # 用户画像读取与自然语言规则解析
│   ├── pace.py                         # normal / intensive 全局节奏逻辑
│   ├── friends.py                      # 朋友中心选址路线
│   └── blindbox.py                     # 盲盒主题路线
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
    ├── test_blindbox.py                # 盲盒路线测试
    ├── test_constraints.py             # 约束模块测试
    ├── test_friends.py                 # 朋友中心路线测试
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

当前接口同时兼容前端现有格式和 PRD 格式。

前端现有格式示例：

~~~json
{
  "start": "120.1646,30.2552",
  "user_input": "周末想在杭州轻松逛逛，吃点本地特色",
  "must_visit_pois": ["poi_008"],
  "preferences": {
    "city": "杭州",
    "food": ["杭帮菜"],
    "tags": ["本地风味", "放松"],
    "budget": 300,
    "time_window": ["10:00", "18:00"],
    "duration_minutes": 240,
    "max_wait": 30,
    "transport": "walk",
    "poi_count": null,
    "pace_mode": "intensive",
    "time_flex_minutes": 60
  }
}
~~~

PRD 格式示例：

~~~json
{
  "mode": "standard",
  "start_location": {
    "name": "湖滨银泰",
    "lng": 120.1646,
    "lat": 30.2552
  },
  "duration_hours": 4,
  "budget": 200,
  "max_wait_time": 20,
  "preferences": ["川菜", "咖啡"],
  "transport": "walk",
  "pace_mode": "normal",
  "time_flex_minutes": 0
}
~~~

### 9.3 响应核心字段

后端响应包含：

~~~text
success
message
city
start_point
friends_center
preference_insight
pace_info
options
options[].type
options[].name
options[].success
options[].summary
options[].route
options[].constraint_policy
options[].relaxed_constraints
options[].relaxation_notice
options[].differentiation_reason
options[].must_visit_pois_included
options[].must_visit_pois_missing
options[].pace_info
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

### 9.5 朋友中心接口

~~~text
POST /api/friends/center
~~~

请求核心字段：

~~~json
{
  "friends_locations": [
    {"name": "A", "lng": 120.1600, "lat": 30.2600},
    {"name": "B", "lng": 120.1800, "lat": 30.2400}
  ],
  "budget": 260,
  "max_wait": 30,
  "duration_minutes": 240,
  "transport": "walk",
  "pace_mode": "normal",
  "time_flex_minutes": 0
}
~~~

### 9.6 盲盒路线接口

~~~text
POST /api/routes/blind-box
~~~

请求核心字段：

~~~json
{
  "theme": "citywalk",
  "start_location": {
    "name": "湖滨银泰",
    "lng": 120.1646,
    "lat": 30.2552
  },
  "duration_hours": 4,
  "budget": 220,
  "max_wait_time": 30,
  "transport": "walk",
  "pace_mode": "intensive",
  "time_flex_minutes": 60
}
~~~

响应包含 `blind_box_info` 和 `blind_boxes`。每个盲盒初始只暴露通用名称 `神秘路线盲盒`，不暴露内部生成策略。

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
- `ugc_comments`
- `is_hidden_gem`

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
- 兼容当前前端格式和 PRD 格式；
- 解析用户偏好；
- 合并自然语言解析结果和显式 preferences；
- 解析 DIY 必去 POI；
- 读取 POI 数据；
- 读取用户画像；
- 生成三种路线方案；
- 处理朋友模式下的中心点起点；
- 返回 `constraint_policy`、`relaxed_constraints`、`relaxation_notice`、`differentiation_reason`、`pace_info` 等字段；
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
- 使用规则词典从自然语言中提取 food、tags、budget、duration_minutes 和 max_wait；
- 生成偏好解析洞察和默认假设说明；
- 后续可替换为真实用户数据库。

### 11.8 `services/friends.py`

朋友中心选址模块，负责：

- 多人位置输入；
- 中心点计算；
- 距离公平性计算；
- 适合朋友聊天和聚会的 POI 筛选；
- 朋友聚会路线生成；
- 少于两个朋友位置时返回中文错误提示。

### 11.9 `services/blindbox.py`

盲盒路线模块，负责：

- 主题归一化；
- Citywalk、吃吃喝喝、文化、小众探索主题路线；
- 生成 3 个无提示盲盒；
- 保留内部策略差异，但不向前端暴露策略名称；
- 返回盲盒整体信息和揭晓后的 option 路线详情。

### 11.10 `services/pace.py`

全局路线节奏模块，负责：

- 归一化 `pace_mode` 和 `time_flex_minutes`；
- 生成 `pace_info`；
- 计算 normal / intensive 下的有效总时长；
- 判断可轻微压缩停留时长的快进快出 POI；
- 为特种兵模式提供距离、等待、停留时长、价格和标签相关的评分调整；
- 生成特种兵模式下的时间弹性提示。

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

运行全量测试：

~~~bash
python -m pytest tests
~~~

当前阶段最近一次验证结果：

~~~text
40 passed
~~~

运行 Python 语法检查：

~~~bash
python3 -m py_compile app.py services/*.py
~~~

当前 `tests/` 已包含真实后端测试，覆盖：

- 正常输入是否返回三方案；
- PRD 格式是否兼容；
- 自然语言偏好解析；
- DIY 必去 POI；
- 朋友中心选址；
- 盲盒路线；
- 特种兵模式；
- 坐标格式错误是否返回错误提示；
- 预算非法、朋友地点不足、盲盒主题未知等异常输入；
- `/api/routes/generate` 是否返回统一字段；
- Flask API 基础返回结构。

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
- `python -m pytest tests` 是否通过。

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
- 任意真实地址 POI 搜索；
- 真实多人登录协同；
- 线上生产部署。

当前路线距离和交通时间主要基于简化估算，不代表真实导航结果。

---

## 18. 后续开发路线

### 18.1 前后端联调与展示补齐

优先确认前端是否完整展示后端新增能力：

- `preference_insight` 和 `assumptions`；
- `must_visit_pois_included` 和 `must_visit_pois_missing`；
- `constraint_policy`、`relaxed_constraints`、`relaxation_notice`；
- 朋友中心集合点和路线；
- 盲盒点击揭晓体验；
- `pace_info` 和特种兵模式提示。

### 18.2 完善 API 文档

补充：

- 请求字段表；
- 响应字段表；
- 错误码；
- 示例输入；
- 示例输出。

### 18.3 完善演示脚本

围绕当前可演示能力补充固定 demo path：

- 只输入自然语言；
- DIY 添加必去 POI；
- 朋友中心选址；
- 盲盒主题路线；
- 特种兵模式对比 normal 模式。

### 18.4 数据继续扩展

后续可继续扩展杭州 POI 数据，重点补齐：

- 更密集的地理聚类；
- 更真实的营业时间；
- 更细分的 POI 类型；
- 更丰富的 UGC 评论；
- 更适合盲盒和特种兵模式的点位。

### 18.5 真实 POI API 预留

后续可在 `services/poi_service.py` 中接入：

- 高德地图；
- Google Places；
- 美团相关数据源；
- 其他开放 POI 数据接口。

### 18.6 真实 LLM 预留

后续可在 `services/explanation.py` 或新增 LLM 服务中接入真实模型，用于：

- 用户意图理解；
- 偏好补全；
- 路线解释生成；
- 个性化推荐理由。

当前阶段不建议立即接入真实 API 或 LLM。先完成本地 MVP 演示闭环更符合项目目标。

---

## 19. 常见问题

### 19.1 为什么有 `services/__init__.py`？

它用于告诉 Python：`services/` 是一个可以被 import 的包。这样代码可以稳定使用：

~~~python
from services.route_engine import generate_route_plan
~~~

### 19.2 为什么 `docs/screenshots/` 里有 `.gitkeep`？

Git 不会上传空文件夹。`.gitkeep` 是占位文件，用来让 GitHub 保留这个截图目录。以后放入真实截图后，可以保留或删除 `.gitkeep`。

### 19.3 为什么盲盒不展示三条路线的策略差异？

当前产品逻辑是：用户先看到 3 个外观相同的神秘盲盒，点击后再揭晓路线。因此后端不会在 `display_name`、`teaser` 或其他初始可见字段中暴露“稳妥”“小众”“主题直觉”等策略提示。三条路线内部仍会使用不同策略生成，以保证路线差异。

### 19.4 为什么当前使用 Mock 数据？

因为 MVP 阶段重点验证核心路线引擎、页面展示和地图展示逻辑。真实 POI API 和真实 LLM 接入留到后续版本。

### 19.5 特种兵模式是不是压缩所有 POI 停留时间？

不是。特种兵模式的核心是更紧凑的空间组合、更顺路的路线、更低等待和更适合快速串联的 POI。只有小吃、茶饮、打卡点、商圈、街区、城市观景点等快进快出类型会被轻微压缩停留时间；正式景点、博物馆、美术馆、寺庙、大型公园、正式餐厅和深度文化空间不会被明显压缩。

---

## 20. 项目状态总结

当前阶段已经完成：

~~~text
P0/P1 后端核心功能补齐
杭州 POI 数据扩充与 UGC 字段补充
当前前端格式与 PRD 格式兼容
自然语言偏好解析
三方案真实差异化生成
DIY 添加 POI 路线重生成
朋友中心选址路线
盲盒主题路线
全局特种兵模式
后端真实测试覆盖
~~~

当前阶段结论：

~~~text
后端已经具备可演示闭环。
系统仍是本地 Mock MVP，不依赖真实 API、真实 LLM、数据库或登录系统。
下一阶段应优先做前后端联调、文档同步和演示路径打磨。
~~~

当前最重要的下一步建议：

~~~text
1. 更新 docs/api.md 和 docs/data_contract.md，使其与当前后端字段一致
2. 前端补充自然语言解析、DIY、朋友中心、盲盒和特种兵模式的展示入口
3. 按 demo_script 固定 4-5 条演示路径
4. 再做一次前后端联调和异常输入检查
~~~

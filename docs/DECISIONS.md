# 开发决策记录

本文档用于记录 AI 本地路线智能规划系统 MVP 开发过程中的关键决策，方便后续复盘、交接、扩展和撰写 README。

## 1. 开发范围决策

本次开发不沿用旧项目，而是根据 PRD 从零重新开发。

本轮优先完成核心引擎模块，目标是形成一个可本地运行、可演示、后续可上传 GitHub 的 MVP 产品。

本轮重点实现：

- 用户输入起点与偏好
- 使用 Mock POI 数据
- POI 过滤
- POI 评分
- 贪心路线生成
- 三方案输出
- 最小 Web 展示

暂不开发：

- 真实美团 API 接入
- 真实 LLM 接入
- 用户登录
- 数据持久化
- 朋友中心选址
- 盲盒路线
- 真实导航路径规划

## 2. 技术路线决策

本项目采用 Flask + HTML/CSS + Leaflet 的方式实现。

原因：

- Flask 适合构建后端接口和最小 Web 产品；
- Leaflet 适合展示地图、POI 标记和路线连线；
- 相比 Streamlit，该结构更接近真实 Web 产品，也更方便后续接入真实前端或 API。

## 3. 数据策略决策

本轮使用杭州 Mock POI 数据，不接入真实 API。

Mock 数据用于验证核心路线引擎逻辑，包括：

- 预算过滤
- 排队时间过滤
- 营业时间过滤
- 偏好匹配
- 距离与路线连贯性
- 三方案生成

后续真实 POI 数据接入时，优先修改 services/poi_service.py，不直接改 route_engine.py。

## 4. 历史偏好洞察决策

本轮使用规则模拟版历史偏好洞察，不接真实 LLM。

原因：

- 保证 MVP 稳定可运行；
- 避免 API Key、模型费用、响应稳定性影响核心功能开发；
- 同时保留 LLM 服务入口，方便后续扩展。

后续真实 LLM 接入时，优先修改 services/llm_service.py。

## 5. 地点范围约束决策

地点范围约束不采用固定距离，而是根据用户输入的预计游玩时长和出行方式动态推导。

因此，本轮新增输入字段：

- duration_minutes：预计游玩时长
- transport：出行方式，例如 walk / bike / drive

核心逻辑：

- 用户游玩时间越短，系统推荐范围越小；
- 步行模式下范围更小；
- 骑行或驾车模式下范围可以适当扩大；
- 生成路线时还需要检查 POI 之间的交通时间和总路线时间。

## 6. 项目结构决策

项目采用服务化结构：

```text
ai-local-route-engine/
├── app.py                         # Flask 后端入口
├── route_engine.py                 # 核心路线引擎
├── services/
│   ├── poi_service.py              # POI 数据入口：当前读 Mock，后续接真实 API
│   └── llm_service.py              # LLM 入口：当前规则模拟，后续接真实 LLM
├── data/
│   ├── mock_pois.json              # 杭州 Mock POI 数据
│   └── mock_user_prefs.json        # Mock 用户历史偏好
├── templates/
│   └── index.html                  # 前端页面
├── static/
│   └── style.css                   # 页面样式
├── docs/
│   └── DECISIONS.md                # 开发决策记录
├── requirements.txt                # Python 依赖
└── .gitignore                      # Git 忽略规则


## 7. 地图展示决策

本轮使用 Leaflet 实现地图展示，并采用 CDN 在线引入方式。

原因：

- 当前阶段优先完成 MVP 闭环；
- CDN 引入开发速度更快，不需要额外下载和管理 Leaflet 文件；
- 后续如果要提高演示稳定性，可以再将 Leaflet 本地化到 static/vendor/leaflet/ 目录。

地图展示方式采用：

- 页面下方设置一个公共地图区域；
- 三张方案卡片中分别提供“在地图中查看”按钮；
- 点击不同方案后，地图切换显示对应路线；
- 地图展示内容包括起点、POI 标记和路线连线。

## 8. POI 数量约束决策

POI 数量字段设置为可选输入。

具体规则：

- 用户不填写 POI 数量时，系统根据预计游玩时长 duration_minutes 动态计算推荐 POI 数量；
- 用户填写 POI 数量时，该数量作为硬约束；
- 如果当前预算、时间、排队、距离等条件无法满足用户指定的 POI 数量，则对应方案返回失败提示；
- 如果三种方案均无法满足条件，则整体 success=false，并返回明确错误提示。

该设计用于同时满足“用户可指定 POI 数量”和“无指定时动态计算”的需求。

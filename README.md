# Melloway — AI 本地路线智能规划系统

> 少想一点，马上出发。

**在线体验**：[https://ai-local-route-engine.onrender.com](https://ai-local-route-engine.onrender.com)

Melloway 是一个面向本地生活路线规划场景的 Web Demo。用户输入出行想法后，系统结合 POI 数据、UGC 评价与用户偏好，同时生成三条可比较的路线方案，并在交互式地图中展示。项目以杭州为示例城市，使用 Mock 数据模拟完整 AI 路线规划流程。

---

## 产品演示

当前版本完成以下主流程：

```
用户输入出行想法
  → AI 解析偏好与约束（预算、排队、时长、口味、同行人）
  → 同时生成三条差异化路线方案
  → 三方案卡片对比（翻转查看路线预览）
  → 查看完整路线 → 地图展示 POI 与路线连线
```

### 核心功能

**三方案对比**
系统一次生成三种策略路线，不做单一推荐，让用户自己比较选择：
- **体验优先方案** — 优先满足偏好，预算和时间可略微放宽
- **精打细算方案** — 严格遵守预算、排队和时长限制
- **个性化方案** — 基于用户画像、历史偏好与小众洞察

**路线盲盒**
不想思考时，选择一个主题（Citywalk / 吃吃喝喝 / 文化之旅 / 小众探索），系统随机生成三条神秘路线。卡片点击展开揭晓内容，再次点击折叠——自己决定什么时候看、看哪条。

**DIY 必去点**
路线生成后，可以添加 1-3 个必去地点，系统据此重新规划路线。已加入的显示确认标记，暂未加入的会说明原因。

**行程条件全局控制**
- 出发地、时长（2h/4h/6h/8h）、预算（¥100-800）、排队容忍度
- 出行方式（步行/骑行/驾车）、出发时间
- 游玩节奏（标准 / 特种兵）+ 弹性加时（+0/+30m/+60m）

**个性化**
- 同行画像：亲子家庭、带父母、情侣约会、朋友出游、单人 Citywalk
- 体验偏好：餐饮、拍照、文化、自然、逛街、夜景、小众、放松
- 路线约束：少走路、低预算、避开排队、室内优先、半日、天黑前结束

**路线详情 & 地图**
- 每个 POI 显示到达/离开时间、人均消费、排队时间
- 隐藏宝藏标签标记小众地点
- UGC 评论：「去过的人这样说」
- Leaflet 交互地图：POI 标记 + 路线连线 + 自动缩放

**自然语言解析**
支持用户只输入自然语言描述，系统自动提取餐饮偏好、场景标签、预算、时长和排队倾向。未填写的字段由系统默认假设补齐，并在结果中透明展示。

**体验评分**
每条路线展示五维评分（舒适 / 社交 / 浪漫 / 家庭 / 强度），帮助用户快速判断路线调性。

---

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | Python / Flask |
| 前端 | 原生 HTML + CSS + JavaScript |
| 地图 | Leaflet + OpenStreetMap |
| 数据 | 杭州 Mock POI（30+ 地点）、Mock 用户画像、模拟 UGC 评论 |
| 无外部 API 依赖 | 不使用真实 LLM、地图 API 或 POI 服务 |

---

## 项目结构

```
├── app.py                  # Flask 入口，路由定义
├── services/               # 后端核心模块
│   ├── route_engine.py     # 三方案路线生成引擎
│   ├── blindbox.py         # 盲盒路线生成
│   ├── constraints.py      # 预算/排队/营业时间约束过滤
│   ├── scoring.py          # POI 多维度评分
│   ├── persona.py          # 用户画像匹配
│   ├── explanation.py      # 方案解释生成
│   ├── pace.py             # 节奏模式与弹性时间
│   ├── poi_service.py      # POI 数据读取
│   └── user_service.py     # 用户画像读取与自然语言解析
├── data/                   # Mock 数据
│   ├── poi_hangzhou.json   # 杭州 POI 数据
│   ├── landmarks_hangzhou.json
│   └── user_profile.json   # 模拟用户画像
├── templates/
│   └── index.html          # SPA 页面
├── static/
│   ├── js/
│   │   ├── config.js       # API 配置、POI 数据、图表映射
│   │   ├── main.js         # 前端主逻辑
│   │   └── map.js          # Leaflet 地图封装
│   └── css/
│       └── style.css       # 全局样式
├── docs/                   # 接口契约与演示脚本
└── tests/                  # 后端测试
```

---

## 本地运行

```bash
# 1. 克隆仓库
git clone https://github.com/violet1668/Melloway.git
cd Melloway

# 2. 创建虚拟环境并安装依赖
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. 启动服务
python app.py

# 4. 浏览器打开
open http://127.0.0.1:5000
```

---

## API 接口

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/` | 首页 |
| POST | `/api/routes/generate` | 标准路线生成（含 DIY） |
| POST | `/api/routes/blind-box` | 盲盒路线 |

---

## 开发说明

- 本项目为 MVP / 学习型项目，优先保证功能可运行、可展示
- 使用杭州 Mock 数据，不接入真实 API
- 当前 MVP 阶段仅开放标准路线和盲盒路线两种模式

---

## License

MIT

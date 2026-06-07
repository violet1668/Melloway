# API Contract

## POST /api/routes/generate

生成三种路线方案：

- `demand_satisfaction`：需求满足方案
- `hard_constraint`：硬约束方案
- `preference_insight`：历史偏好洞察方案

兼容旧接口：

- `POST /api/generate_route`

### Request

画像 tag 可以放在顶层，也可以放在 `preferences` 内。后端会统一归一化到 `preferences`。

```json
{
  "start": "120.1551,30.2741",
  "user_input": "周末带孩子轻松玩半天，别排队太久",
  "persona_tags": ["parent_child_family"],
  "preference_tags": ["food", "nature", "relaxed"],
  "constraint_tags": ["less_walking", "avoid_queue", "half_day"],
  "preferences": {
    "city": "杭州",
    "budget": 300,
    "duration_minutes": 240,
    "max_wait": 20,
    "transport": "walk",
    "pace_mode": "normal",
    "time_flex_minutes": 0
  }
}
```

也支持对象格式起点：

```json
{
  "start": {
    "type": "coordinate",
    "lng": 120.1551,
    "lat": 30.2741,
    "name": "武林广场"
  },
  "preferences": {
    "persona_tags": ["solo_citywalk"],
    "preference_tags": ["culture", "niche", "photo"],
    "constraint_tags": ["low_budget"]
  }
}
```

### Supported Tags

`persona_tags`：

| tag | 含义 |
|---|---|
| `parent_child_family` | 亲子家庭 |
| `elder_family` | 带父母/长辈 |
| `couple_date` | 情侣约会 |
| `friends_group` | 朋友出游 |
| `solo_citywalk` | 单人 Citywalk |

`special_forces` 不再作为 persona tag。特种兵能力使用全局节奏参数：

```json
{
  "pace_mode": "intensive",
  "time_flex_minutes": 60
}
```

`preference_tags`：

| tag | 含义 |
|---|---|
| `food` | 餐饮 |
| `photo` | 拍照 |
| `culture` | 文化 |
| `nature` | 自然 |
| `shopping` | 购物/逛街 |
| `night_view` | 夜景 |
| `niche` | 小众 |
| `relaxed` | 放松 |

`constraint_tags`：

| tag | 含义 |
|---|---|
| `less_walking` | 少走路 |
| `low_budget` | 低预算 |
| `avoid_queue` | 避免排队 |
| `indoor_first` | 室内优先 |
| `half_day` | 半日路线 |
| `end_before_night` | 天黑前结束 |

非法 tag 不会导致接口失败，会出现在 `persona_context.ignored_tags`。

### Response Fields

顶层新增：

```json
{
  "persona_context": {
    "persona_tags": ["parent_child_family"],
    "preference_tags": ["food", "nature", "relaxed"],
    "constraint_tags": ["less_walking", "avoid_queue", "half_day"],
    "ignored_tags": [],
    "persona_labels": ["亲子家庭"]
  }
}
```

每个 `option` 新增：

```json
{
  "matched_reasons": [
    "适合亲子家庭：路线按该画像调整了点位类型、停留节奏和移动距离。",
    "命中自然偏好：包含公园、放松等路线信号。",
    "已降低步行压力：总移动距离约 1.8 公里，并优先选择近距离串联。"
  ],
  "quality_scores": {
    "comfort_score": 86,
    "social_score": 52,
    "romantic_score": 30,
    "family_score": 91,
    "intensity_score": 28
  },
  "persona_context": {
    "persona_tags": ["parent_child_family"],
    "preference_tags": ["food", "nature", "relaxed"],
    "constraint_tags": ["less_walking", "avoid_queue", "half_day"],
    "ignored_tags": [],
    "persona_labels": ["亲子家庭"]
  }
}
```

前端建议展示：

| 字段 | 展示位置 |
|---|---|
| `persona_context.persona_labels` | 方案卡片顶部画像标签 |
| `persona_context.preference_tags` | 方案卡片顶部偏好标签 |
| `persona_context.constraint_tags` | 方案卡片顶部约束标签 |
| `matched_reasons` | 方案卡片中部，展示 2-3 条 |
| `quality_scores.comfort_score` | 质量分 Badge 或进度条 |
| `quality_scores.social_score` | 质量分 Badge 或进度条 |
| `quality_scores.romantic_score` | 质量分 Badge 或进度条 |
| `quality_scores.family_score` | 质量分 Badge 或进度条 |
| `quality_scores.intensity_score` | 质量分 Badge 或进度条 |
| `pace_info.label` | 方案卡片节奏标签 |
| `relaxation_notice` | 路线详情中的约束说明 |
| `differentiation_reason` | 路线详情中的方案差异说明 |

## Demo Requests

### 1. 亲子家庭轻松半日

```json
{
  "start": "120.1646,30.2552",
  "user_input": "周末带孩子轻松玩半天，别排队太久",
  "persona_tags": ["parent_child_family"],
  "preference_tags": ["food", "nature", "relaxed"],
  "constraint_tags": ["less_walking", "avoid_queue", "half_day"],
  "budget": 320,
  "transport": "walk"
}
```

### 2. 带父母低强度文化路线

```json
{
  "start": "120.1646,30.2552",
  "user_input": "带爸妈在杭州慢慢逛，最好室内多一点，天黑前结束",
  "preferences": {
    "persona_tags": ["elder_family"],
    "preference_tags": ["culture", "relaxed", "food"],
    "constraint_tags": ["less_walking", "indoor_first", "end_before_night"],
    "budget": 360,
    "duration_minutes": 240,
    "max_wait": 20,
    "transport": "walk"
  }
}
```

### 3. 情侣约会拍照夜景

```json
{
  "start": "120.1646,30.2552",
  "user_input": "晚上情侣约会，想拍照和吃点甜品",
  "preferences": {
    "persona_tags": ["couple_date"],
    "preference_tags": ["photo", "night_view", "food"],
    "constraint_tags": [],
    "budget": 420,
    "duration_minutes": 300,
    "max_wait": 30,
    "transport": "walk",
    "time_window": ["14:00", "21:00"]
  }
}
```

### 4. 朋友出游吃喝逛街

```json
{
  "start": "120.1646,30.2552",
  "user_input": "朋友一起出门，想吃吃喝喝逛一逛",
  "preferences": {
    "persona_tags": ["friends_group"],
    "preference_tags": ["food", "shopping", "photo"],
    "constraint_tags": ["avoid_queue"],
    "budget": 400,
    "duration_minutes": 300,
    "max_wait": 25,
    "transport": "walk"
  }
}
```

### 5. 单人小众 Citywalk

```json
{
  "start": "120.1646,30.2552",
  "user_input": "一个人 citywalk，想找小众文化感路线",
  "preferences": {
    "persona_tags": ["solo_citywalk"],
    "preference_tags": ["culture", "niche", "photo"],
    "constraint_tags": ["low_budget"],
    "budget": 220,
    "duration_minutes": 240,
    "max_wait": 25,
    "transport": "walk"
  }
}
```

### 6. 单人 Citywalk + 全局特种兵模式

```json
{
  "start": "120.1646,30.2552",
  "user_input": "今天想多打卡几个点，路线紧凑一点",
  "preferences": {
    "persona_tags": ["solo_citywalk"],
    "preference_tags": ["food", "photo", "culture"],
    "constraint_tags": ["avoid_queue"],
    "budget": 500,
    "duration_minutes": 240,
    "max_wait": 30,
    "transport": "walk",
    "pace_mode": "intensive",
    "time_flex_minutes": 60
  }
}
```

## Acceptance Criteria

1. `persona_tags`、`preference_tags`、`constraint_tags` 支持顶层和 `preferences` 内传入。
2. 非法 tag 不导致接口失败，并返回到 `persona_context.ignored_tags`。
3. `special_forces` 不作为 persona tag；特种兵模式只由 `pace_mode=intensive` 控制。
4. 6 个 demo 请求均能返回至少一个成功 option。
5. 每个成功 option 返回 `matched_reasons`，且至少包含画像、偏好或约束中的一类解释。
6. 每个成功 option 返回 `quality_scores`，包含 `comfort_score`、`social_score`、`romantic_score`、`family_score`、`intensity_score`。
7. `parent_child_family` 和 `elder_family` 路线应更偏舒适，`family_score` 或 `comfort_score` 不应明显低于 `intensity_score`。
8. `couple_date` 路线应提升 `romantic_score`。
9. `friends_group` 路线应提升 `social_score`。
10. `solo_citywalk + niche` 应更倾向小众、文化、citywalk 相关 POI。
11. `less_walking` 应降低搜索半径并增强距离惩罚。
12. `avoid_queue` 应收紧等待时间或增强等待惩罚。
13. `low_budget` 应增强价格惩罚。
14. `indoor_first` 应提升室内或可休息类型 POI。
15. `end_before_night` 应将结束时间约束到 18:00 前。

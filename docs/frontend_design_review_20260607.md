# 前端设计审查报告

> 审查日期：2026-06-07
> 审查范围：templates/index.html、static/css/style.css、static/js/main.js、static/js/config.js、static/js/map.js
> 原则：不改后端 API、不破坏现有功能闭环、保留黄色暖金色主色调

---

## 一、当前最有 AI 味的 5 个问题（按影响排序）

### 问题 1（最严重）：.chip 样式到处同款——功能性元素无区分度

**症状**：`.chip` 这一套样式（`border-radius: 20px`、`border: 1.5px`、`padding: 8px 16px`）同时用于：

- 快捷偏好选择（「本地风味」「放松」）
- 同行画像（「亲子家庭」「带父母」）
- 体验偏好（「餐饮」「拍照」）
- 路线约束（「少走路」「半日」）
- 游玩时长选择
- 预算范围选择
- 排队接受度选择

七种不同功能的交互，视觉完全一样。这是典型的 AI 训练语料平均化的结果——选了最安全的组件，套到所有地方。

**影响**：用户看不出哪些是情感偏好、哪些是硬约束、哪些是数值选择。所有东西都是「点一下变色的圆角框」。

### 问题 2：表单区 = 后台配置面板

当前 bento 网格有 **7 个卡片** + **4 组 chip 群** + **生成按钮**。对于一个「输入想法→生成路线」的产品而言，信息密度过高。`tag-control` 里用三层卡片（同行画像/体验偏好/路线约束），看起来像算法参数配置，不像用户选择。

### 问题 3：三方案卡片底部提示没对齐

因为三张卡片的 `plan-diff-tag` 数量可能不同（1个或2个）、`quality-mini` 高度不同（有的 3 条进度条、有的 2 条），导致 `card-short-notice` 的 Y 位置不一致。当前用自然流布局（`flex-direction: column`），notice 跟着上面内容走，没法固定在底部。

### 问题 4：卡片背面文字溢出不完整

`.back-summary` 设置 `-webkit-line-clamp: 2`，但部分后端返回的 summary 超过两行。同时卡片高度 440px 中 `back-header` + `back-canvas` + `back-stops` + `back-actions` 分摊空间，summary 区如果内容长会挤掉 stop list 显示。

### 问题 5：详细页文案残留字段名

虽然已经加了一层 `sanitizeUserText()` 清洗，但当前代码中存在两套同名函数（`getPlanExplanation` 在 218 和 445 行各定义了一次，`renderQualityScores` 在 384 和 463 行各定义了一次——后者会覆盖前者）。这意味着 sanitize 清洗逻辑可能没生效。此外当前的清洗只是简单字符串替换，没有处理「UGC」「权重」「画像」等术语。

---

## 二、表单区优化建议

### 2.1 哪些应该默认露出，哪些应该弱化

| 元素 | 建议 |
|------|------|
| 主输入框（textarea） | **保留**，且加大高度，让它成为页面的唯一视觉焦点 |
| 快捷偏好 chips | **保留**，但控制在 **5-8 个**，一行显示完，超过收进「更多偏好」下拉 |
| 同行画像 | **轻度显示**：改成 4 个小头像 / 图标选择（单人/情侣/亲子/朋友），不要做成4个一样的圆角 chip |
| 体验偏好 | **默认隐藏**，放进「高级设置」折叠区，或用 3 个小 emoji 快速选 |
| 路线约束 | **默认隐藏**，放进「高级设置」折叠区 |
| 出发地选择 | **保留**，但改成一个带地图图钉图标的简洁下拉，不占独立卡片 |
| 游玩时长 / 预算 / 排队 | **保留**，但三者合并成一个「行程条件」卡片，用 3 行轻量滑块或小型分段选择器 |
| AI 路线引擎说明卡片 | **删除或极度缩小**，目前的 bullet list 是说明文档不是产品 UI——考虑改成主输入框下方的 1 行 subtitle |
| DIY 必去点 | **保留**，但从独立卡片移到结果区附近（用户在看到路线后更可能加地点），或放在主输入区下方作为可折叠区域 |

### 2.2 推荐的用户操作路径

```
输入想法（大文本框）
    ↓
选择 5-8 个快捷偏好（一行 chips）
    ↓
选出发地 + 时长/预算/排队（一行 3-4 个小控件）
    ↓
[可选] 展开高级设置（同行画像 + 更多约束）
    ↓
「生成我的路线」
```

### 2.3 表单区可以合并的卡片

当前 bento grid 7 个卡片可以合并为 **4 个**：

1. **主输入卡**（textarea + 快捷偏好 + 生成按钮）
2. **条件卡**（出发地 + 时长 + 预算 + 排队——一行 4 个轻量 select）
3. **DIY 地点卡**（保留在结果区附近，或在主输入卡下方折叠）
4. **高级设置**（默认折叠，含 同行画像 + 体验偏好 + 路线约束）

---

## 三、三方案卡片优化建议

### 3.1 正面布局重排

建议正面采用**固定 5 行 grid 布局**，解决对齐问题：

```
┌──────────────────────────┐
│ 方案名称 (h3)             │  ← grid-row: 1
│                           │
│ 推荐理由标签 (≤2)         │  ← grid-row: 2, min-height: 28px
│                           │
│ 属性进度条 (≤3)           │  ← grid-row: 3
│                           │
│ 关键指标 (4 项)           │  ← grid-row: 4
│                           │
│ 约束提示 (可选，固定高度)  │  ← grid-row: 5, max-height: 40px
└──────────────────────────┘
```

关键改动：

- 正面 `flex-direction: column` 改为 `display: grid; grid-template-rows: auto auto 1fr auto auto`
- tag 区固定 `min-height: 28px`，确保无标签时也占位
- 指标区和 footer 使用 `align-self: end` 或 `grid-row` 固定到底部
- 短提示 footer 固定高度 32px，无内容时用 `visibility: hidden` 保留占位

对应 CSS：

```css
.flip-card-front {
  display: grid;
  grid-template-rows: auto auto 1fr auto auto;
}

.card-tags-area {
  min-height: 28px;
}

.card-footer-notice {
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.card-footer-notice:empty {
  visibility: hidden;
}
```

### 3.2 背面布局调整

建议背面采用 `flex-column` 加固定空间分配：

```
┌──────────────────────────┐
│ back-header (方案名)      │  ← flex: 0 0 auto
│ back-summary (1-2行)      │  ← flex: 0 0 auto (max-height: 40px)
├──────────────────────────┤
│ back-canvas (mini-route)  │  ← flex: 1 (自动伸缩)
├──────────────────────────┤
│ back-stops                │  ← flex: 0 0 auto (min-height: 24px)
│ back-actions (按钮)       │  ← flex: 0 0 auto
└──────────────────────────┘
```

关键改动：

- 移除 `back-metrics`（背面不需要再显示时长/花费——在正面已经看到了）
- summary 固定 `max-height: 2.5em`（≈两行），超过显示省略号
- `back-canvas` 使用 `flex: 1; min-height: 0;` 让它在中间自动伸缩

### 3.3 降低卡片 AI 味的具体做法

- **tag 不再用大圆角胶囊**：用 `border-radius: 4px` + `padding: 2px 6px` 的小型文本标签，类似 GitHub issue labels 的紧凑版
- **进度条去掉圆角**：`border-radius: 1px`，让它们更像数据 bar 而不是装饰
- **指标区用文字排列代替 pill 堆积**：`4 个地点 · 约 240 分钟 · 约 ¥300 · 排队 30 分钟`，一行文字比分开放置更干净
- **阴影从 `0 4px 18px` 降低到 `0 1px 4px`**：实产品不需要那么多投影

---

## 四、卡片底部提示对齐的具体方案

### 推荐方案：CSS Grid + 固定 footer 区域

```css
.flip-card-front {
  display: grid;
  grid-template-rows: auto auto 1fr auto auto;
}
```

tag 区：

```css
.card-tags-area {
  min-height: 28px;  /* 固定最小高度 */
}
```

短提示 footer：

```css
.card-footer-notice {
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.card-footer-notice:empty {
  visibility: hidden;  /* 保留占位，保证对齐 */
}
```

三张卡片统一高度：

```css
.flip-card {
  height: 420px;  /* 统一高度，由 grid 内部分配 */
}
```

这样即使一张卡没有 tag、另一张有2个 tag，由于 `min-height` 占位和 footer 固定位置，三张卡片的视觉重心一致。

---

## 五、按钮 / Chip 如何更高级、更真实产品化

### 5.1 主按钮（生成路线 / 查看完整路线）

当前问题：厚重阴影（`0 4px 18px`）+ 大圆角（`14px`）+ 渐变色——三者叠加产生「AI demo 页」感。

建议方向：

- 阴影降低到 `0 1px 3px rgba(200,139,42,0.18)`
- 圆角降到 `10px`（不是 4px 那么直角，也不是 14px 那么圆）
- 渐变更克制：`linear-gradient(135deg, #d4972b, #c8861e)`，两个色值更接近
- hover 态用 `translateY(-1px)` + 阴影微增，不要大幅跳跃

### 5.2 次级按钮

当前 `.chip` 既是选择器，又扮演「小按钮」角色——太统一。

建议：

- **数值选择 chip**（时长/预算/排队）：改成小型分段按钮组，类似 iOS 的 segmented control——更紧凑，更像「做选择」而非「加标签」
- **情感标签 chip**（本地风味/放松）：保留圆角 tag 风格，但缩小尺寸
- **功能 chip**（同行画像/约束）：改成更克制的 ghost 样式——浅底 + 细边框 + 小字

### 5.3 Chip 分级方案

| 类型 | 建议样式 |
|------|---------|
| 快捷偏好 | 保持圆角 tag，但圆角降到 `10px`，去掉阴影，默认态更轻 |
| 数值选择（时长/预算/排队） | 改为分段控件：`display: flex; gap: 0`，相邻项共享边框，选中项用暖金色底 |
| 同行画像 | 改为 4 个 emoji 按钮，不用文字 chip |
| 体验偏好 / 路线约束 | 默认折叠，展开后用轻量 ghost chip |
| 三方案卡片 tag | 改为小型文本标签：`border-radius: 4px; padding: 2px 6px; font-size: 11px` |

### 5.4 「查看完整路线」按钮

当前背面只有这一个按钮，它是用户从卡片到详情的唯一路径。

建议：

- 做成底部固定位置的全宽按钮
- 样式上减少圆角，更像列表底部的 CTA 行
- 可以加一个右箭头 `→` 暗示「展开详情」

### 5.5 选中态表达

当前选中 = 填充色切换：灰底→暖金底（快捷偏好）或灰底→深灰底（约束/画像）。

建议：

- 快捷偏好选中态：保留暖金色填充（这是品牌色，不冲突）
- 其他 chip 选中态：可以改成左侧细边框（`border-left: 2px solid var(--gold)`）+ 文字变重，不一定要填充变色
- 数值 select：选中态用底部 2px 下划线 + 文字变色，像 Apple 的分段控件

---

## 六、详细路线页文案产品化

### 6.1 当前仍存在的问题

1. 代码中存在两套 `getPlanExplanation` 和 `renderQualityScores`（重复定义），后定义的覆盖了前面的，可能导致 sanitize 清洗逻辑不生效。
2. `sanitizeUserText` 也重复定义了两次。
3. 当前清洗只做了正则替换，没有处理如「UGC」「权重」「画像」「命中」等出现在文案中的术语。

### 6.2 需要替换的术语和替换方向

| 当前可能出现 | 问题 | 替换方向 |
|------------|------|---------|
| 「满足你本次输入的偏好」 | 像配置说明 | 「更贴近你这次的想法」 |
| 「命中 XXX 偏好」 | 算法术语 | 「路线安排里体现了 XXX」 |
| 「长期偏好标签」 | 数据库术语 | 「你常选的方向」 |
| 「降低已去过或不喜欢的权重」 | 权重是算法词 | 「减少重复，多推荐你没试过的」 |
| 「UGC 中被反复提到」 | 字段名 | 「很多去过的人推荐这里」 |
| 「画像匹配」 | 后台术语 | 「适合你的风格」 |
| 「包含了 matched_reasons」 | 直接暴露字段名 | 「推荐理由如下」 |
| 「quality_scores 评分」 | 直接暴露字段名 | 「路线体验评分」 |

### 6.3 推荐做法

1. **先修重复定义问题**：删除 384-462 行之间的重复函数，只保留 sanitize 版本的。
2. **扩充 sanitize 词表**：增加 `UGC`、`权重`、`画像`、`命中` 的替换。
3. **在 showFullRoute 的 detailSummary 区增加产品化文案包装**：比如在每个方案详情顶部加一句自然的摘要句。

---

## 七、建议的最小修改清单

### Round 1：关键修复（P0）

1. 删除 `main.js` 中的 4 个重复函数定义（`sanitizeUserText` 第二份、`getPlanExplanation` 第二份、`renderMatchedReasons` 第二份、`renderQualityScores` 第二份）
2. 扩充 `sanitizeUserText` 词表：增加「UGC」「权重」「画像」「命中」的替换

### Round 2：卡片对齐（P1）

3. 正面改为 CSS Grid 5 行固定布局，解决 notice 不对齐问题
4. 正面 footer 保留占位（`visibility: hidden` + `height: 32px`）
5. 三张卡片统一高度 420px
6. 背面改为 flex-column 弹性空间分配

### Round 3：去 AI 味（P2）

7. tag 样式从大胶囊改为小文本标签（`border-radius: 4px`）
8. 进度条改为细矩形（`height: 3px; border-radius: 1px`）
9. 指标区改为文字排列（`·` 分隔，代替 pill）
10. 按钮阴影降低到 `0 1px 3px`
11. 减少卡片正面的胶囊元素总量（目标：每张卡 <6 个圆角元素）

### Round 4：表单区精简（P3）

12. AI 路线引擎卡片改为一行 subtitle
13. 同行画像 / 体验偏好 / 路线约束折叠合并
14. 时长/预算/排队改为分段选择器
15. DIY 必去点移到结果区附近

---

## 八、执行优先级

```
第一步（1-2h）：修重复函数 + 扩充 sanitize 词表 → 保证文案干净
第二步（2-3h）：正面 5 行 Grid + 背面 flex-column → 解决对齐和溢出
第三步（2-3h）：tag/chip/进度条/按钮/指标 去 AI 味 → 视觉升级
第四步（3-4h）：表单区精简合并 → 产品更像真实产品
```

每一步都可独立验收，不影响后端的正常运行。

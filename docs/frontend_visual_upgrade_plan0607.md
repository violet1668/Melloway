# S1 前端视觉优化计划

## 当前前端现状简述

当前前端已完成 P0 MVP 基础架构，具备以下能力：
- 简单的 Hero 区域（深色渐变背景 + 标题 + 副标题）
- 完整的输入表单（起点、偏好、预算、时间等字段）
- 三方案卡片展示（普通白色卡片，显示方案名称、summary、POI 数量、总时长、总花费）
- Leaflet 地图展示（POI 标记 + 路线连线）
- 基础响应式布局

页面功能完整可用，但视觉呈现较为朴素，交互较为基础。

---

## 本次优化目标

本次不是重构，而是在 P0 主流程完整可用的基础上，增强视觉呈现和交互体验：
- 保持 P0 主流程功能：输入表单、API 调用、三方案展示、地图联动、错误提示全部保留
- 不引入新框架，继续使用 Flask + 原生 HTML/CSS/JavaScript + Leaflet
- 不修改后端 API、不修改 services/、不修改数据层
- 通过 CSS 3D 变换、SVG 动画、流动渐变背景等原生技术实现视觉增强

---

## 页面结构方案

页面保持原有的垂直流式布局，自上而下：

```
┌─────────────────────────────────┐
│     Hero 区域（新增流动渐变）    │
├─────────────────────────────────┤
│     输入表单区（保持不变）        │
├─────────────────────────────────┤
│   三方案卡片区（改为 3D 翻转）   │
├─────────────────────────────────┤
│   路线详情区（展开显示）          │
├─────────────────────────────────┤
│   主地图区（保持唯一 Leaflet）   │
└─────────────────────────────────┘
```

- Hero 区域：吸引用户注意，传达产品价值
- 输入区：保持原表单结构，不修改字段
- 卡片区：三方案从普通卡片升级为 3D 翻转卡片
- 详情区：点击卡片后展开 POI 详情（保持功能）
- 地图区：单个主地图，不在卡片背面嵌入地图

---

## Hero 区域设计

### 文案层级

```
H1: AI 本地路线智能规划系统
P:  输入起点与偏好，自动生成三种杭州本地路线方案。
```

### 流动渐变背景

使用 CSS `background-size` + `@keyframes` 实现多色缓慢流动：

```css
background: linear-gradient(
  45deg,
  #f97316,  /* 橙色 */
  #ec4899,  /* 粉色 */
  #8b5cf6,  /* 紫色 */
  #06b6d4   /* 青色 */
);
background-size: 400% 400%;
animation: gradient-flow 15s ease infinite;

@keyframes gradient-flow {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}
```

色调柔和过渡，类似 Apple 官网风格，但不复制任何 Apple 资源。

---

## 三方案 3D 翻转卡片设计

### 卡片结构

```html
<div class="flip-card">
  <div class="flip-card-inner">
    <!-- 正面 -->
    <div class="flip-card-front">
      <h3>需求满足方案</h3>
      <p class="summary">更优先满足你想吃川菜和朋友聚会的需求。</p>
      <div class="meta">
        <span>3 个 POI</span>
        <span>约 235 分钟</span>
        <span>约 ¥218</span>
      </div>
      <button>查看完整路线</button>
    </div>
    <!-- 背面 -->
    <div class="flip-card-back">
      <div class="svg-icons-container">
        <!-- SVG 图标依次绘制 -->
      </div>
    </div>
  </div>
</div>
```

### 正面内容

- 方案名称（h3）
- summary（推荐理由）
- 元数据标签（POI 数量、总时长、总花费、总等待时间）
- "查看完整路线" 按钮

### 背面内容

- **不放真实 Leaflet 地图**（避免性能和布局问题）
- SVG 场景图标描边动画
- 店铺名依次浮现
- 路线顺序感（通过动画延迟实现）

### 选中态与点击行为

- 鼠标悬停时卡片轻微上浮
- 点击按钮或卡片正面时：
  - 卡片翻转显示背面 SVG 动画
  - 同时触发主地图更新
  - 详情区展开显示完整 POI 列表
- 再次点击可翻回正面

---

## SVG 场景图标描边动画设计

### 图标类型

根据 POI 类型映射对应的 SVG 图标：

| POI 类型 | SVG 图标 | 说明 |
|---------|---------|------|
| 餐厅/美食 | 餐盘图标 | fork + knife |
| 咖啡店 | 咖啡杯图标 | 带热气 |
| 文具店 | 笔记本图标 | 简化版 |
| 书店 | 书籍图标 | 两本书叠放 |
| 景点 | 相机/山景图标 | 可选 |
| 商圈 | 购物袋图标 | 简化版 |

### 动画机制

使用 `stroke-dasharray` + `stroke-dashoffset` 实现描边绘制：

```css
.svg-icon {
  stroke: currentColor;
  stroke-width: 2;
  fill: none;
  stroke-dasharray: 100;
  stroke-dashoffset: 100;
  animation: draw-icon 1.5s ease forwards;
}

@keyframes draw-icon {
  to { stroke-dashoffset: 0; }
}
```

### 店铺名浮现

```css
.poi-name {
  opacity: 0;
  transform: translateY(10px);
  animation: fade-in 0.5s ease forwards;
}

@keyframes fade-in {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
```

### 路线顺序感

通过 `animation-delay` 实现依次绘制：

```javascript
const delay = index * 300; // 每个 POI 延迟 300ms
icon.style.animationDelay = `${delay}ms`;
name.style.animationDelay = `${delay + 1}s`;
```

整体效果：图标像 AI 正在一步步生成路线一样依次出现。

---

## 主地图与详情区联动

### 设计原则

- 页面只保留一个主 Leaflet 地图（位于页面底部）
- 不在卡片背面嵌入真实地图（避免性能问题和复杂度）
- 点击卡片后，主地图和详情区同步更新

### 联动逻辑

```
用户点击卡片/按钮
    ↓
1. 卡片翻转（可选，或保持正面）
    ↓
2. 调用 showRouteOnMap(index) 更新主地图
    ↓
3. 详情区展开（或已有详情区更新内容）
    ↓
4. 页面平滑滚动到地图区（可选）
```

主地图展示：
- 起点 Marker
- POI 数字 Marker（1、2、3...）
- 路线 Polyline 连线
- 自动 fitBounds 显示完整路线

---

## 需要修改的文件

| 文件 | 修改内容 |
|-----|---------|
| `templates/index.html` | Hero 区域文案调整；卡片 HTML 结构改造为 3D 翻转结构；添加 SVG 图标容器 |
| `static/css/style.css` | Hero 流动渐变背景样式；3D 翻转卡片样式；SVG 描边动画；选中态样式；响应式适配 |
| `static/js/main.js` | 卡片渲染函数改造（renderOption）；翻转动画触发逻辑；SVG 图标动态生成逻辑 |
| `static/js/map.js` | 可能需要微调地图高度或样式，保持联动逻辑不变 |
| `static/js/config.js` | 可能添加图标类型映射配置，保持 API 配置不变 |

---

## 不修改的内容

- 不修改 `app.py`（后端路由不变）
- 不修改 `services/` 目录（路线引擎逻辑不变）
- 不修改 `data/` 目录（POI 数据不变）
- 不引入新框架（继续使用原生 HTML/CSS/JS）
- 不接真实地图 API（继续使用 OpenStreetMap）
- 不改变后端返回字段（前端适配现有 API 响应）

---

## 验收标准

完成优化后，请检查以下事项：

1. **P0 主流程保持可用**
   - 输入表单可正常提交
   - `/api/routes/generate` 调用成功
   - 三方案正常展示
   - 详情区可展开
   - 主地图显示 POI 和连线
   - 错误提示正常显示

2. **Hero 区域效果**
   - 流动渐变背景正常动画
   - 文案层级清晰
   - 无明显性能问题

3. **3D 翻转卡片效果**
   - 三张卡片可正常翻转
   - 正面信息完整显示
   - 背面 SVG 动画流畅
   - 选中态视觉反馈明显

4. **SVG 描边动画**
   - 图标依次绘制
   - 店铺名依次浮现
   - 整体路线顺序感清晰

5. **主地图联动**
   - 点击卡片后地图正常更新
   - POI 标记和连线显示正确
   - 自动缩放到完整路线范围

6. **兼容性**
   - Chrome 浏览器正常展示
   - Safari 浏览器正常展示
   - 移动端基础可用（至少不破坏布局）

7. **无障碍与体验**
   - 支持 `prefers-reduced-motion` 用户关闭动画
   - 加载状态有提示
   - 颜色对比度足够

---

## 风险控制

### 避免破坏 P0 主流程


执行前先确认 git status clean；如修改失败，用 git restore 回滚前端文件。

### 处理字段缺失

- 后端返回字段可能不完整，前端做好降级处理
- SVG 图标类型映射不匹配时使用默认图标
- 部分字段为空时不显示对应 UI 元素

### 移动端适配

- 3D 翻转卡片在移动端可能体验不佳
- 选项：移动端改用普通卡片或禁用翻转
- 添加 `@media` 查询，小屏下简化效果

### prefers-reduced-motion

```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation: none !important;
    transition: none !important;
  }
}
```

### 性能控制

- SVG 图标使用内联 SVG 或少量文件
- 动画时长控制在合理范围（1-2 秒）
- 避免 DOM 操作过多
- 使用 `requestAnimationFrame` 优化（如需要）

---

## 待我确认的问题

1. **卡片翻转触发方式**：鼠标悬停翻转

2. **移动端翻转效果**：保留成点击翻转

3. **图标设计来源**：图标不要完全自绘，使用 Lucide / Tabler Icons 的静态 inline SVG 方案即可。
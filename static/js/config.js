// API 配置
const API_CONFIG = {
  generateUrl: "/api/routes/generate",
  fallbackUrl: "/api/generate_route"
};

// 方案名称映射
const OPTION_NAMES = {
  demand_satisfaction: "体验优先方案",
  hard_constraint: "精打细算方案",
  preference_insight: "个性化方案"
};

function optionName(type) {
  return OPTION_NAMES[type] || type;
}

// 方案对应的背面主题 class
const PLAN_THEMES = {
  demand_satisfaction: "theme-warm",
  hard_constraint: "theme-cool",
  preference_insight: "theme-rose"
};

// POI 类型到 SVG 图标的映射（使用 Lucide 风格的内联 SVG）
const POI_ICONS = {
  restaurant: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 2v7c0 1.1.9 2 2 2h4a2 2 0 0 0 2-2V2"/><path d="M7 2v20"/><path d="M21 15V2v0a5 5 0 0 0-5 5v6c0 1.1.9 2 2 2h3Zm0 0v7"/></svg>`,
  coffee: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M17 8h1a4 4 0 1 1 0 8h-1"/><path d="M3 8h14v9a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4Z"/><line x1="6" x2="6" y1="2" y2="4"/><line x1="10" x2="10" y1="2" y2="4"/><line x1="14" x2="14" y1="2" y2="4"/></svg>`,
  cafe: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M17 8h1a4 4 0 1 1 0 8h-1"/><path d="M3 8h14v9a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4Z"/><line x1="6" x2="6" y1="2" y2="4"/><line x1="10" x2="10" y1="2" y2="4"/><line x1="14" x2="14" y1="2" y2="4"/></svg>`,
  stationery: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/></svg>`,
  book: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/><line x1="8" x2="8" y1="2" y2="22"/><line x1="12" x2="12" y1="2" y2="22"/><line x1="16" x2="16" y1="2" y2="22"/></svg>`,
  bookstore: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/><line x1="8" x2="8" y1="2" y2="22"/><line x1="12" x2="12" y1="2" y2="22"/><line x1="16" x2="16" y1="2" y2="22"/></svg>`,
  attraction: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M15 4V2M15 16v-2"/><path d="M8 9h2"/><path d="M20 9h2"/><path d="M17.8 11.8A6 6 0 0 1 12 18a6 6 0 0 1-5.8-4.2l-1.6-5.3A6 6 0 0 1 6 8.8c0-2.3 1.3-4.3 3.2-5.3a6 6 0 0 1 5.6 0c1.9 1 3.2 3 3.2 5.3 0 1.1-.3 2.1-1.1 3z"/></svg>`,
  scenic: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M8 3v2"/><path d="M16 3v2"/><path d="M12 5v2"/><path d="M3 12h18"/><path d="M6 12v8"/><path d="M12 12v8"/><path d="M18 12v8"/><path d="M5 21h14"/></svg>`,
  shopping: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4Z"/><path d="M3 6h18"/><path d="M16 10a4 4 0 0 1-8 0"/></svg>`,
  mall: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4Z"/><path d="M3 6h18"/><path d="M16 10a4 4 0 0 1-8 0"/></svg>`,
  default: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>`
};

function getPoiIcon(type) {
  if (!type) return POI_ICONS.default;
  const lowerType = type.toLowerCase();
  for (const [key, icon] of Object.entries(POI_ICONS)) {
    if (lowerType.includes(key) && key !== 'default') {
      return icon;
    }
  }
  return POI_ICONS.default;
}

// 杭州地标数据
const HANGZHOU_LANDMARKS = [
  { name: "湖滨银泰", lng: 120.1646, lat: 30.2552 },
  { name: "西湖断桥", lng: 120.1499, lat: 30.2617 },
  { name: "武林广场", lng: 120.1630, lat: 30.2768 },
  { name: "杭州东站", lng: 120.2120, lat: 30.2917 },
  { name: "龙翔桥", lng: 120.1666, lat: 30.2586 },
  { name: "西溪湿地", lng: 120.0648, lat: 30.2702 },
  { name: "钱江新城", lng: 120.2099, lat: 30.2460 },
  { name: "滨江宝龙城", lng: 120.2105, lat: 30.2082 },
  { name: "拱宸桥", lng: 120.1428, lat: 30.3205 },
  { name: "浙大玉泉校区", lng: 120.1244, lat: 30.2659 }
];
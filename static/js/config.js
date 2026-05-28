// API 配置
const API_CONFIG = {
  generateUrl: "/api/routes/generate",
  fallbackUrl: "/api/generate_route"
};

// 方案名称映射
const OPTION_NAMES = {
  demand_satisfaction: "需求满足方案",
  hard_constraint: "硬约束方案",
  preference_insight: "历史偏好洞察方案"
};

function optionName(type) {
  return OPTION_NAMES[type] || type;
}

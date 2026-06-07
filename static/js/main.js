// ========== 结果显示 ==========

// ========== Chips 初始化 ==========

function initChipGroup(chipContainer, hiddenInput) {
  if (!chipContainer || !hiddenInput) return;

  const chips = chipContainer.querySelectorAll('.chip');
  chips.forEach(chip => {
    chip.addEventListener('click', () => {
      chipContainer.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      hiddenInput.value = chip.dataset.value;
    });
  });
}

function initPreferenceChips() {
  const container = document.querySelector('.preference-chips');
  if (!container) return;

  const chips = container.querySelectorAll('.chip');
  const selectedValues = new Set();
  const tagsInput = document.getElementById('tags');

  chips.forEach(chip => {
    if (chip.classList.contains('active')) {
      selectedValues.add(chip.dataset.value);
    }
  });

  if (tagsInput) tagsInput.value = Array.from(selectedValues).join(',');

  chips.forEach(chip => {
    chip.addEventListener('click', () => {
      chip.classList.toggle('active');
      const value = chip.dataset.value;

      if (chip.classList.contains('active')) {
        selectedValues.add(value);
      } else {
        selectedValues.delete(value);
      }

      if (tagsInput) tagsInput.value = Array.from(selectedValues).join(',');
    });
  });
}

function initMultiSelectChips(chipContainer, hiddenInput) {
  if (!chipContainer || !hiddenInput) return;

  const chips = chipContainer.querySelectorAll('.chip');

  const syncValue = () => {
    const values = Array.from(chips)
      .filter(chip => chip.classList.contains('active'))
      .map(chip => chip.dataset.value);
    hiddenInput.value = values.join(',');
  };

  chips.forEach(chip => {
    chip.addEventListener('click', () => {
      chip.classList.toggle('active');
      syncValue();
    });
  });

  syncValue();
}

function splitInput(value) {
  if (!value) return [];
  return value.split(",").map(s => s.trim()).filter(s => s.length > 0);
}

window.selectedMustVisitPois = window.selectedMustVisitPois || [];
window.availablePoiOptions = window.availablePoiOptions || [...POI_OPTIONS];

function normalizePoiOption(poi) {
  if (!poi || !poi.id || !poi.name) return null;
  return {
    id: poi.id,
    name: poi.name,
    type: poi.type || '',
    category: poi.category || poi.cuisine || '',
    area: poi.area || ''
  };
}

function mergePoiOptions(options = []) {
  const merged = new Map();
  [...window.availablePoiOptions, ...options]
    .map(normalizePoiOption)
    .filter(Boolean)
    .forEach(poi => {
      if (!merged.has(poi.id)) {
        merged.set(poi.id, poi);
      }
    });

  window.availablePoiOptions = Array.from(merged.values());
  refreshPoiSelectOptions();
}

function refreshPoiSelectOptions() {
  const select = document.getElementById('mustVisitPoiSelect');
  if (!select) return;

  const currentValue = select.value;
  const selectedIds = new Set(window.selectedMustVisitPois.map(poi => poi.id));
  const options = window.availablePoiOptions
    .filter(poi => !selectedIds.has(poi.id))
    .sort((a, b) => a.name.localeCompare(b.name, 'zh-CN'));

  select.innerHTML = `
    <option value="">选择一个想去地点</option>
    ${options.map(poi => `<option value="${poi.id}">${poi.name}${poi.area ? ` · ${poi.area}` : ''}${poi.category ? ` · ${poi.category}` : ''}</option>`).join('')}
  `;

  if (options.some(poi => poi.id === currentValue)) {
    select.value = currentValue;
  }
}

function renderSelectedPoiChips() {
  const container = document.getElementById('selectedPoiChips');
  const hiddenInput = document.getElementById('must_visit_pois');
  if (!container || !hiddenInput) return;

  hiddenInput.value = window.selectedMustVisitPois.map(poi => poi.id).join(',');

  if (!window.selectedMustVisitPois.length) {
    container.innerHTML = '<span class="poi-chip poi-chip-placeholder">暂未添加想去地点</span>';
    refreshPoiSelectOptions();
    return;
  }

  container.innerHTML = window.selectedMustVisitPois.map((poi, index) => `
    <span class="poi-chip">
      <span>${poi.name}</span>
      <button type="button" class="poi-chip-remove" aria-label="移除 ${poi.name}" onclick="removeMustVisitPoi(${index})">×</button>
    </span>
  `).join('');

  refreshPoiSelectOptions();
}

function addMustVisitPoi() {
  const select = document.getElementById('mustVisitPoiSelect');
  if (!select || !select.value) return;
  if (window.selectedMustVisitPois.length >= 3) return;

  const poi = window.availablePoiOptions.find(item => item.id === select.value);
  if (!poi || window.selectedMustVisitPois.some(item => item.id === poi.id)) return;

  window.selectedMustVisitPois.push(poi);
  renderSelectedPoiChips();
  select.value = '';
}

function removeMustVisitPoi(index) {
  window.selectedMustVisitPois.splice(index, 1);
  renderSelectedPoiChips();
}

function collectResultPois(options = []) {
  return options.flatMap(option => getRoutePois(option).map(normalizePoiOption).filter(Boolean));
}

function getRoutePois(option) {
  return option?.route?.pois || option?.pois || [];
}

function getPlanType(option) {
  return normalizePlanType(option);
}

function getPlanLabels(option) {
  return PLAN_DIFF_LABELS[getPlanType(option)] || [];
}

function renderPlanDiffTags(option, limit = 2) {
  const labels = getPlanLabels(option).slice(0, limit);
  if (!labels.length) return '';
  return `<div class="plan-diff-tags">${labels.map(label => `<span class="plan-diff-tag">${label}</span>`).join('')}</div>`;
}

function getPlanSummary(option) {
  return option.summary || option.explanation || PLAN_EXPLANATION_FALLBACK[getPlanType(option)] || '暂无方案说明';
}

function hasRelaxationDetails(relaxedConstraints) {
  if (!relaxedConstraints) return false;
  return ['budget_extra', 'duration_minutes_extra', 'max_wait_extra'].some(key => Number(relaxedConstraints[key]) > 0);
}

function formatRelaxationItems(relaxedConstraints) {
  if (!hasRelaxationDetails(relaxedConstraints)) return [];
  const items = ['为满足偏好，系统略微放宽了部分约束'];

  if (Number(relaxedConstraints.duration_minutes_extra) > 0) {
    items.push(`预计多花 ${relaxedConstraints.duration_minutes_extra} 分钟`);
  }
  if (Number(relaxedConstraints.budget_extra) > 0) {
    items.push('预算可能略高于原设定');
  }
  if (Number(relaxedConstraints.max_wait_extra) > 0) {
    items.push(`排队时间可能增加约 ${relaxedConstraints.max_wait_extra} 分钟`);
  }

  return items;
}

function renderRelaxationNotice(option, className = '') {
  if (!option.relaxation_notice) return '';
  return `<div class="soft-notice ${className}">${escapeHtml(option.relaxation_notice)}</div>`;
}

function renderRelaxationDetails(option) {
  const items = formatRelaxationItems(option.relaxed_constraints);
  if (!items.length) return '';
  return `
    <div class="soft-notice detail-notice">
      <strong>约束提醒</strong>
      <ul>${items.map(item => `<li>${item}</li>`).join('')}</ul>
    </div>
  `;
}

function formatPoiRef(item) {
  if (typeof item === 'string') {
    return item.trim() || '未知地点';
  }

  if (!item || typeof item !== 'object') {
    return '未知地点';
  }

  const name = item.name || item.poi_name || item.title || item.id || '未知地点';
  const reason = typeof item.reason === 'string' ? item.reason.trim() : '';

  return reason ? `${name}（${reason}）` : name;
}

function getMustVisitPoiFeedback(option, key) {
  const optionItems = Array.isArray(option?.[key]) ? option[key] : [];
  if (optionItems.length) return optionItems;

  const routeItems = Array.isArray(option?.route?.[key]) ? option.route[key] : [];
  return routeItems;
}

function renderMustVisitFeedbackItems(items, itemClassName = '') {
  return `
    <div class="must-visit-feedback-items">
      ${items.map(item => `<span class="must-visit-feedback-chip ${itemClassName}">${escapeHtml(formatPoiRef(item))}</span>`).join('')}
    </div>
  `;
}

function renderMustVisitFeedback(option) {
  const included = getMustVisitPoiFeedback(option, 'must_visit_pois_included');
  const missing = getMustVisitPoiFeedback(option, 'must_visit_pois_missing');

  if (!included.length && !missing.length) return '';

  return `
    <div class="must-visit-feedback detail-notice">
      <div class="must-visit-feedback-title">DIY 地点处理结果</div>
      ${included.length ? `
        <div class="must-visit-feedback-section must-visit-feedback-section-success">
          <div class="must-visit-feedback-heading">已加入路线</div>
          ${renderMustVisitFeedbackItems(included, 'is-success')}
        </div>
      ` : ''}
      ${missing.length ? `
        <div class="must-visit-feedback-section must-visit-feedback-section-warning">
          <div class="must-visit-feedback-heading">暂未加入路线</div>
          <p class="must-visit-feedback-note">部分地点可能因时间、预算、距离或排队约束暂未纳入。</p>
          ${renderMustVisitFeedbackItems(missing, 'is-warning')}
        </div>
      ` : ''}
    </div>
  `;
}

function renderPreferenceInsight(preferenceInsight) {
  if (!preferenceInsight) return '';

  const insightGroups = [
    { label: '识别菜系', values: preferenceInsight.extracted_food || [] },
    { label: '识别偏好', values: preferenceInsight.extracted_tags || [] },
    { label: '识别约束', values: preferenceInsight.extracted_constraints || [] }
  ].filter(group => group.values.length);

  const intent = preferenceInsight.inferred_intent ? `<p class="insight-intent">${escapeHtml(preferenceInsight.inferred_intent)}</p>` : '';

  if (!insightGroups.length && !intent) return '';

  return `
    <div class="insight-header">AI 已理解你的需求</div>
    ${intent}
    <div class="insight-groups">
      ${insightGroups.map(group => `
        <div class="insight-group">
          <span class="insight-label">${escapeHtml(group.label)}</span>
          <div class="insight-tags">
            ${group.values.map(value => `<span>${escapeHtml(value)}</span>`).join('')}
          </div>
        </div>
      `).join('')}
    </div>
  `;
}

function escapeHtml(text) {
  return String(text)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

function renderPoiComments(poi) {
  const comments = (poi.ugc_comments || []).filter(Boolean).slice(0, 2);
  if (!comments.length) return '';
  return `
    <div class="ugc-comment-block">
      <div class="ugc-comment-title">体验评论</div>
      ${comments.map(comment => `<p class="ugc-comment">“${escapeHtml(comment)}”</p>`).join('')}
    </div>
  `;
}

function renderPersonaTags(personaContext) {
  if (!personaContext) return '';
  const labels = personaContext.persona_labels || [];
  const constraintTags = personaContext.constraint_tags || [];
  const tagLabelMap = {
    less_walking: '少走路',
    low_budget: '低预算',
    avoid_queue: '避开排队',
    indoor_first: '室内优先',
    half_day: '半日',
    end_before_night: '天黑前结束'
  };
  const tags = labels.concat(constraintTags.map(tag => tagLabelMap[tag] || tag)).slice(0, 4);
  if (!tags.length) return '';
  return `<div class="persona-tags">${tags.map(tag => `<span>${tag}</span>`).join('')}</div>`;
}

function renderQualityScores(scores, compact = true) {
  if (!scores) return '';
  const scoreItems = [
    ['舒适', scores.comfort_score],
    ['社交', scores.social_score],
    ['浪漫', scores.romantic_score],
    ['家庭', scores.family_score],
    ['强度', scores.intensity_score]
  ];
  const displayItems = compact
    ? scoreItems.sort((a, b) => (b[1] || 0) - (a[1] || 0)).slice(0, 3)
    : scoreItems;

  return `
    <div class="${compact ? 'quality-mini' : 'quality-list'}">
      <div class="quality-title">路线体验评分</div>
      ${displayItems.map(([label, value]) => `
        <div class="quality-item">
          <span class="quality-label">${label}</span>
          <span class="quality-bar"><i style="width: ${Math.max(0, Math.min(100, value || 0))}%"></i></span>
          <span class="quality-value">${value || 0}</span>
        </div>
      `).join('')}
    </div>
  `;
}

function sanitizeUserText(text) {
  if (!text || typeof text !== 'string') return '';

  let sanitized = text;

  const replacements = [
    { regex: /food\/tags/gi, replacement: '饮食偏好' },
    { regex: /food|tags|preferences/gi, replacement: '偏好' },
    { regex: /user_input/gi, replacement: '你的需求' },
    { regex: /plan_type/gi, replacement: '方案类型' },
    { regex: /matched_reasons/gi, replacement: '推荐理由' },
    { regex: /quality_scores/gi, replacement: '体验评分' },
    { regex: /demand_satisfaction/gi, replacement: '体验优先方案' },
    { regex: /hard_constraint/gi, replacement: '精打细算方案' },
    { regex: /preference_insight/gi, replacement: '个性化方案' },
    { regex: /budget\/max_wait\/duration/gi, replacement: '花费、排队和时间' },
    { regex: /budget|max_wait|duration/gi, replacement: (match) => {
      if (match === 'budget') return '花费';
      if (match === 'max_wait') return '排队';
      if (match === 'duration') return '时长';
      return match;
    }},
  ];

  replacements.forEach(({ regex, replacement }) => {
    if (typeof replacement === 'function') {
      sanitized = sanitized.replace(regex, replacement);
    } else {
      sanitized = sanitized.replace(regex, replacement);
    }
  });

  return sanitized;
}

function getPlanExplanation(option) {
  const rawExplanation = option.explanation || option.summary || PLAN_EXPLANATION_FALLBACK[getPlanType(option)] || '系统正在补充该方案解释。';
  return sanitizeUserText(rawExplanation);
}

function renderDifferentiationReason(option) {
  const reason = option?.differentiation_reason || option?.route?.differentiation_reason || '';
  if (!reason) return '';
  return `
    <div class="plan-diff-reason detail-notice">
      <strong>方案差异原因</strong>
      <p>${escapeHtml(sanitizeUserText(reason))}</p>
    </div>
  `;
}

function renderMatchedReasons(reasons, limit = 2) {
  if (!reasons || !reasons.length) return '';
  const sanitizedReasons = reasons.map(reason => sanitizeUserText(reason));
  return `
    <div class="matched-reasons-section">
      <div class="matched-reasons-title">推荐理由</div>
      <ul class="matched-reasons">
        ${sanitizedReasons.slice(0, limit).map(reason => `<li>${reason}</li>`).join('')}
      </ul>
    </div>
  `;
}

function transportName(transport) {
  const names = {
    walk: '步行',
    bike: '骑行',
    drive: '驾车'
  };
  return names[transport] || transport || '步行';
}

function renderRouteSegments(segments) {
  if (!segments || !segments.length) return '';

  const trafficNote = segments.find(segment => segment.traffic_note)?.traffic_note;
  const segmentItems = segments.map(segment => `
    <li>
      <strong>${segment.from} → ${segment.to}</strong>
      <span>${transportName(segment.transport)}约 ${segment.duration} 分钟，约 ${segment.distance} km</span>
    </li>
  `).join('');

  return `
    <div class="segment-section">
      <h4>路段移动时间</h4>
      <ul class="segment-list">${segmentItems}</ul>
      ${trafficNote ? `<p class="traffic-note">${trafficNote}</p>` : ''}
    </div>
  `;
}

function parseCoordinateValue(value, fallbackName) {
  const [lng, lat] = String(value || '').split(',').map(Number);
  return {
    name: fallbackName,
    lng,
    lat
  };
}

function getSelectedOptionText(selectId) {
  const select = document.getElementById(selectId);
  if (!select || !select.selectedOptions.length) return '';
  return select.selectedOptions[0].textContent.split('：').pop().trim();
}

function collectFriendLocations() {
  return [
    parseCoordinateValue(
      document.getElementById('friendLocationA')?.value,
      getSelectedOptionText('friendLocationA') || '朋友 A'
    ),
    parseCoordinateValue(
      document.getElementById('friendLocationB')?.value,
      getSelectedOptionText('friendLocationB') || '朋友 B'
    )
  ];
}

function updateFriendCommutePreview() {
  const preview = document.getElementById('friendCommutePreview');
  if (!preview) return;

  const friends = collectFriendLocations();
  preview.innerHTML = `
    <div class="commute-preview-track">
      <span class="commute-dot dot-a"></span>
      <span class="commute-center-dot"></span>
      <span class="commute-dot dot-b"></span>
    </div>
    <div class="commute-preview-labels">
      <span>${friends[0].name}</span>
      <strong>推荐集合点</strong>
      <span>${friends[1].name}</span>
    </div>
  `;
}

function renderAssumptionsPanel(preferenceInsight) {
  const container = document.getElementById('assumptionsPanel');
  if (!container) return;

  const assumptions = preferenceInsight && preferenceInsight.assumptions;
  if (!assumptions || !assumptions.has_missing_constraints) {
    container.innerHTML = '';
    return;
  }

  container.innerHTML = `
    <div class="assumptions-panel">
      <strong>默认假设</strong>
      <span>${assumptions.message}</span>
    </div>
  `;
}

function renderFriendCenterBanner(data) {
  const container = document.getElementById('friendCenterBanner');
  if (!container) return;

  if (!data || !data.friends_center) {
    container.innerHTML = '';
    return;
  }

  container.innerHTML = `
    <div class="friend-center-banner">
      <strong>推荐集合点</strong>
      <span>${data.friends_center.name || '推荐集合点'}，已综合 ${data.friends_center.source_count || 0} 位朋友的位置。</span>
    </div>
  `;
}

function renderBlindBoxResults(data) {
  const section = document.getElementById('blindBoxSection');
  const container = document.getElementById('blindBoxResults');
  if (!section || !container) return;

  if (!data.success) {
    section.style.display = 'block';
    container.innerHTML = `<div class="blindbox-message">${data.message || '盲盒路线生成失败'}</div>`;
    return;
  }

  window.latestBlindBoxes = data.blind_boxes || [];
  window.latestBlindBoxOptions = window.latestBlindBoxes.map(box => box.option);

  container.innerHTML = `
    <div class="blindbox-info">${data.blind_box_info?.message || data.message || ''}</div>
    <div class="blindbox-grid">
      ${window.latestBlindBoxes.map((box, index) => `
        <button class="blindbox-card" type="button" onclick="revealBlindBox(${index})" id="blindbox-${index}">
          <span class="blindbox-title">${box.display_name || '神秘路线盲盒'}</span>
          <span class="blindbox-theme">${data.theme_name || '主题路线'}</span>
          <span class="blindbox-action">点击揭晓</span>
        </button>
      `).join('')}
    </div>
  `;
  section.style.display = 'block';
  setTimeout(() => section.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100);
}

function revealBlindBox(index) {
  const box = window.latestBlindBoxes && window.latestBlindBoxes[index];
  if (!box || !box.option) return;

  const card = document.getElementById(`blindbox-${index}`);
  if (card) {
    card.classList.add('revealed');
    card.innerHTML = `
      <span class="blindbox-title">路线已揭晓</span>
      <span class="blindbox-summary">${box.option.summary || box.option.message || '盲盒路线'}</span>
      <span class="blindbox-action">查看完整路线</span>
    `;
  }

  window.latestOptions = window.latestBlindBoxOptions || [box.option];
  showFullRoute(index);
}

function setupPlanTypeTabs() {
  const tabs = document.querySelectorAll('.plan-type-tab');
  const modeInput = document.getElementById('route_mode');
  const generateBtnText = document.querySelector('#generateBtn .btn-text');

  const activateMode = (mode) => {
    if (modeInput) modeInput.value = mode;
    tabs.forEach(tab => tab.classList.toggle('active', tab.dataset.value === mode));
    document.querySelectorAll('[data-mode-panel]').forEach(panel => {
      panel.classList.toggle('active', panel.dataset.modePanel === mode);
    });

    if (generateBtnText) {
      generateBtnText.textContent = mode === 'blindbox' ? '生成盲盒路线' : '生成路线';
    }

    if (mode === 'standard' && document.getElementById('startSelect')) {
      document.getElementById('start').value = document.getElementById('startSelect').value;
    }
    if (mode === 'blindbox' && document.getElementById('blindBoxStartSelect')) {
      document.getElementById('start').value = document.getElementById('blindBoxStartSelect').value;
    }
    if (mode === 'friends') {
      updateFriendCommutePreview();
    }
  };

  tabs.forEach(tab => {
    tab.addEventListener('click', () => activateMode(tab.dataset.value));
  });

  activateMode(modeInput?.value || 'standard');
}

function setupPaceModeControls() {
  initChipGroup(
    document.getElementById('paceModeChips'),
    document.getElementById('pace_mode')
  );
  initChipGroup(
    document.getElementById('timeFlexChips'),
    document.getElementById('time_flex_minutes')
  );
  initChipGroup(
    document.getElementById('blindBoxThemeChips'),
    document.getElementById('blind_box_theme')
  );
}

// ========== SVG 路线预览生成 ==========

function generateMiniRouteSVG(planType, pois) {
  if (!pois || pois.length === 0) {
    return '<div class="back-canvas-empty">暂无路线信息</div>';
  }

  const displayPois = pois.slice(0, 4);
  const hasMore = pois.length > 4;
  const nodeCount = displayPois.length; // 只包含 POI，不包含额外起点和终点

  const W = 290, H = 160;
  const padX = 28, endX = W - 28;
  const baseY = H / 2;

  // 节点分布：x 均匀推进，y 交错但幅度克制
  const pts = [];
  for (let i = 0; i < nodeCount; i++) {
    const t = nodeCount <= 1 ? 0.5 : i / (nodeCount - 1);
    const x = padX + t * (endX - padX);
    // 幅度控制在 ±16px，形成自然城市路线感
    const offsets = [0, -16, 14, -12, 16];
    const y = baseY + (offsets[i] || 0);
    pts.push({ x, y });
  }

  const routeColor = planType === 'hard_constraint' ? '#64748b' :
                     planType === 'preference_insight' ? '#c88b2a' : '#ca8a04';

  // Catmull-Rom → Cubic Bézier：整体连续平滑曲线，无独立拱桥
  let pathD = `M${pts[0].x} ${pts[0].y}`;

  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[Math.max(0, i - 1)];
    const p1 = pts[i];
    const p2 = pts[i + 1];
    const p3 = pts[Math.min(pts.length - 1, i + 2)];

    let cp1x, cp1y, cp2x, cp2y;

    if (i === 0) {
      // 首段：单侧切线
      cp1x = p1.x + (p2.x - p1.x) / 3;
      cp1y = p1.y + (p2.y - p1.y) / 3;
      cp2x = p2.x - (p3.x - p1.x) / 6;
      cp2y = p2.y - (p3.y - p1.y) / 6;
    } else if (i === pts.length - 2) {
      // 末段：单侧切线
      cp1x = p1.x + (p2.x - p0.x) / 6;
      cp1y = p1.y + (p2.y - p0.y) / 6;
      cp2x = p2.x - (p2.x - p1.x) / 3;
      cp2y = p2.y - (p2.y - p1.y) / 3;
    } else {
      // 中间段：标准 Catmull-Rom
      cp1x = p1.x + (p2.x - p0.x) / 6;
      cp1y = p1.y + (p2.y - p0.y) / 6;
      cp2x = p2.x - (p3.x - p1.x) / 6;
      cp2y = p2.y - (p3.y - p1.y) / 6;
    }

    pathD += ` C${cp1x} ${cp1y} ${cp2x} ${cp2y} ${p2.x} ${p2.y}`;
  }

  let svgParts = '';

  // 主路径
  svgParts += `<path d="${pathD}" class="rb-path-main" stroke="${routeColor}" stroke-width="2"
    stroke-linecap="round" fill="none" pathLength="100"/>`;

  // 只显示 POI 节点，编号与 stop list 一致
  const textColor = '#ffffff';

  displayPois.forEach((poi, idx) => {
    const p = pts[idx];
    const delay = 0.4 + idx * 0.4;
    const num = idx + 1; // 从 1 开始编号

    svgParts += `
      <g class="rb-node-group" style="animation-delay: ${delay}s;">
        <circle cx="${p.x}" cy="${p.y}" r="9" fill="${routeColor}"/>
        <text x="${p.x}" y="${p.y}" text-anchor="middle" dominant-baseline="central" font-size="10" font-weight="700" fill="${textColor}">${num}</text>
      </g>
    `;
  });

  // 完整编号列表 (与路线图编号对应)
  const stopListHtml = displayPois.map((poi, i) => {
    const num = i + 1; // 从 1 开始编号
    return `
      <span class="back-stop-item" style="animation-delay: ${1.6 + i * 0.12}s;">
        <span class="back-stop-num">${num}</span>${poi.name}
      </span>
    `;
  }).join('');

  return `
    <div class="back-canvas">
      <svg class="back-route-svg" viewBox="0 0 ${W} ${H}" fill="none" xmlns="http://www.w3.org/2000/svg">
        ${svgParts}
      </svg>
    </div>
    <div class="back-stops">${stopListHtml}</div>
    ${hasMore ? '<div class="back-more">+ ' + (pois.length - 4) + ' 个更多地点</div>' : ''}
  `;
}

// ========== 卡片渲染 ==========

function getCardShortNotice(option, planType) {
  if (planType === 'hard_constraint' || planType === 'hard_constraints') {
    return option.relaxation_notice && option.relaxation_notice.includes('放宽')
      ? '预算、排队和时间限制更稳'
      : '严格遵守预算、排队和时间限制';
  }

  if (planType === 'demand_satisfaction') {
    if (option.relaxation_notice) {
      return option.relaxation_notice.length > 15
        ? '为满足偏好，部分约束可能略有放宽'
        : option.relaxation_notice;
    }
    return '';
  }

  if (planType === 'preference_insight') {
    if (option.relaxation_notice) {
      return option.relaxation_notice.length > 15
        ? '参考历史偏好与小众洞察'
        : option.relaxation_notice;
    }
    return '';
  }

  return '';
}

function getShortSummary(option) {
  const summary = option.summary || '';
  if (!summary) return '';

  const maxLength = 35;
  return summary.length > maxLength ? summary.slice(0, maxLength) + '…' : summary;
}

function renderOption(option, index) {
  const cardId = `card-${index}`;
  const planType = getPlanType(option);
  const themeClass = PLAN_THEMES[planType] || 'theme-warm';

  if (!option.success || !option.route) {
    return `
      <div class="flip-card" data-index="${index}" id="${cardId}">
        <div class="flip-card-inner">
          <div class="flip-card-front">
            <h3>${optionName(planType)}</h3>
            <p class="summary">${getPlanSummary(option)}</p>
            <div class="meta"><span>不可用</span></div>
          </div>
          <div class="flip-card-back ${themeClass}"><div class="back-empty">该方案不可用</div></div>
        </div>
      </div>
    `;
  }

  const route = option.route;
  const planName = optionName(planType);
  const totalWait = route.total_wait_time || 0;
  const personaContext = option.persona_context || route.persona_context;
  const qualityScores = option.quality_scores || route.quality_scores;
  const routeTransport = route.segments && route.segments.length
    ? route.segments[0].transport
    : 'walk';

  const shortNotice = getCardShortNotice(option, planType);
  const routeSvgHtml = generateMiniRouteSVG(planType, route.pois);

  return `
    <div class="flip-card" data-index="${index}" id="${cardId}">
      <div class="flip-card-inner">
        <!-- 正面：快速判断信息 -->
        <div class="flip-card-front">
          <h3>${planName}</h3>
          ${renderPersonaTags(personaContext)}
          ${renderPlanDiffTags(option, 2)}
          ${renderQualityScores(qualityScores, true)}
          <div class="meta">
            <span>${route.pois.length} 个地点</span>
            <span>约 ${route.total_time} 分钟</span>
            <span>约 ¥${route.total_cost}</span>
            <span>${transportName(routeTransport)}</span>
            ${totalWait > 0 ? `<span>排队约 ${totalWait} 分钟</span>` : ''}
          </div>
          ${shortNotice ? `<div class="card-short-notice">${escapeHtml(shortNotice)}</div>` : ''}
          <button class="btn-mobile-full-route" onclick="showFullRoute(${index}, event)">查看完整路线</button>
        </div>

        <!-- 背面：路线预览 + 简短解释 -->
        <div class="flip-card-back ${themeClass}">
          <div class="back-header">
            <span class="back-badge">${planName}</span>
            ${getShortSummary(option) ? `<p class="back-summary">${escapeHtml(getShortSummary(option))}</p>` : ''}
          </div>

          ${routeSvgHtml}

          <div class="back-actions">
            <button class="btn-full-route" onclick="showFullRoute(${index}, event)">查看完整路线</button>
          </div>
        </div>
      </div>
    </div>
  `;
}

// ========== 完整路线详情 ==========

function showFullRoute(index, event) {
  if (event) event.stopPropagation();

  const option = window.latestOptions && window.latestOptions[index];
  if (!option || !option.success || !option.route) {
    alert('该方案暂无详细路线信息');
    return;
  }

  const route = option.route;
  const detailSection = document.getElementById('detailSection');
  const matchedReasons = option.matched_reasons || route.matched_reasons || [];
  const qualityScores = option.quality_scores || route.quality_scores;
  const personaContext = option.persona_context || route.persona_context;

  document.getElementById('detailTitle').textContent = optionName(getPlanType(option));
  document.getElementById('detailSummary').innerHTML = `
    ${renderPersonaTags(personaContext)}
    ${renderPlanDiffTags(option)}
    <p>${getPlanExplanation(option)}</p>
    ${renderDifferentiationReason(option)}
    ${renderRelaxationNotice(option, 'detail-notice')}
    ${renderRelaxationDetails(option)}
    ${renderMustVisitFeedback(option)}
    ${renderMatchedReasons(matchedReasons, 4)}
    ${renderQualityScores(qualityScores, false)}
  `;

  const metrics = [
    { label: '途经地点', value: route.pois.length },
    { label: '总时长', value: `${route.total_time} 分钟` },
    { label: '总花费', value: `¥${route.total_cost}` }
  ];
  if (route.total_wait_time) metrics.push({ label: '预计排队', value: `${route.total_wait_time} 分钟` });

  document.getElementById('detailMetrics').innerHTML = metrics.map(m =>
    `<div class="metric-badge">${m.label}: ${m.value}</div>`
  ).join('');

  const poiListHtml = route.pois.map((poi, i) => `
    <li>
      <strong>
        ${i + 1}. ${poi.name}
        ${poi.is_hidden_gem ? '<span class="hidden-gem-tag">隐藏宝藏</span>' : ''}
      </strong>
      <span>到达: ${poi.arrive_time} | 离开: ${poi.leave_time} | 人均: ¥${poi.price}${poi.wait_time ? ` | 等待: ${poi.wait_time}分钟` : ''}</span>
      ${renderPoiComments(poi)}
    </li>
  `).join('');

  document.getElementById('detailPois').innerHTML = `
    <h4>路线详情</h4>
    <ul class="poi-list">${poiListHtml}</ul>
    ${renderRouteSegments(route.segments)}
  `;

  detailSection.style.display = 'block';
  RouteMap.init();
  RouteMap.showRoute(index);

  setTimeout(() => {
    detailSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, 100);
}

function closeDetail() {
  document.getElementById('detailSection').style.display = 'none';
}

// ========== 结果显示 ==========

function displayResults(data) {
  const status = document.getElementById("status");
  const results = document.getElementById("results");
  const resultsSection = document.getElementById("resultsSection");
  const preferenceInsightPanel = document.getElementById('preferenceInsightPanel');

  if (!data.success) {
    status.textContent = data.message || "路线生成失败，请检查输入条件或稍后重试。";
    return;
  }

  window.latestOptions = data.options;
  mergePoiOptions(collectResultPois(data.options));
  status.textContent = data.message;
  renderAssumptionsPanel(data.preference_insight);
  renderFriendCenterBanner(data);
  results.innerHTML = data.options.map(renderOption).join("");

  const preferenceInsightHtml = renderPreferenceInsight(data.preference_insight);
  if (preferenceInsightPanel) {
    preferenceInsightPanel.innerHTML = preferenceInsightHtml;
    preferenceInsightPanel.style.display = preferenceInsightHtml ? 'block' : 'none';
  }

  resultsSection.style.display = "block";

  setTimeout(() => {
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, 100);
}

// ========== 表单数据收集 ==========

function collectFormPayload() {
  const startValue = document.getElementById("start").value || "120.1646,30.2552";
  const startSelect = document.getElementById('startSelect');
  const durationMinutes = Number(document.getElementById("duration_minutes").value) || 240;
  const budget = Number(document.getElementById("budget").value) || 300;
  const maxWait = Number(document.getElementById("max_wait").value) || 30;
  const transport = document.getElementById("transport").value || "walk";
  const personaTags = splitInput(document.getElementById("persona_tags").value);
  const mustVisitPois = window.selectedMustVisitPois
    .map(poi => poi?.id)
    .filter(Boolean);

  const payload = {
    mode: 'standard',
    start: startValue,
    start_location: startSelect?.selectedOptions?.[0]?.textContent?.trim() || '',
    user_input: document.getElementById("user_input").value || "周末想在杭州轻松逛逛",
    duration_hours: Number((durationMinutes / 60).toFixed(1)),
    budget,
    max_wait_time: maxWait,
    companions: personaTags.includes('friends_group')
      ? 'friends'
      : personaTags.includes('couple_date')
        ? 'couple'
        : personaTags.some(tag => ['parent_child_family', 'elder_family'].includes(tag))
          ? 'family'
          : 'solo',
    transport,
    must_visit_pois: mustVisitPois,
    preferences: {
      city: "杭州",
      food: splitInput(document.getElementById("food").value || "杭帮菜"),
      tags: splitInput(document.getElementById("tags").value || "本地风味,放松"),
      budget,
      time_window: [
        document.getElementById("start_time").value || "10:00",
        document.getElementById("end_time").value || "18:00"
      ],
      max_wait: maxWait,
      duration_minutes: durationMinutes,
      transport,
      persona_tags: personaTags,
      preference_tags: splitInput(document.getElementById("preference_tags").value),
      constraint_tags: splitInput(document.getElementById("constraint_tags").value)
    }
  };

  const poiCount = document.getElementById("poi_count").value;
  if (poiCount && poiCount.trim() !== "") {
    payload.preferences.poi_count = Number(poiCount);
  }

  payload.preferences.pace_mode = document.getElementById("pace_mode").value || "normal";
  payload.preferences.time_flex_minutes = Number(document.getElementById("time_flex_minutes").value) || 0;

  const routeMode = document.getElementById("route_mode").value || "standard";
  if (routeMode === "friends") {
    payload.mode = "friends";
    payload.friends_locations = collectFriendLocations();
  }

  return payload;
}

// ========== 生成路线 ==========

async function generateRoute() {
  const status = document.getElementById("status");
  const results = document.getElementById("results");
  const resultsSection = document.getElementById("resultsSection");
  const detailSection = document.getElementById("detailSection");
  const btn = document.getElementById("generateBtn");
  const btnText = btn.querySelector('.btn-text');
  const btnLoading = btn.querySelector('.btn-loading');

  status.textContent = "";
  results.innerHTML = "";
  resultsSection.style.display = "none";
  detailSection.style.display = "none";

  btn.disabled = true;
  btnText.style.display = "none";
  btnLoading.style.display = "inline";

  if ((document.getElementById("route_mode").value || "standard") === "blindbox") {
    await generateBlindBoxRoute();
    btn.disabled = false;
    btnText.style.display = "inline";
    btnLoading.style.display = "none";
    return;
  }

  const payload = collectFormPayload();

  try {
    const response = await fetch(API_CONFIG.generateUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const contentType = response.headers.get('content-type') || '';
    const rawText = await response.text();
    let data = null;

    if (contentType.includes('application/json') && rawText) {
      try {
        data = JSON.parse(rawText);
      } catch (parseError) {
        console.error('JSON 解析失败', parseError, rawText);
      }
    }

    if (!response.ok) {
      status.textContent = data?.message || '路线生成失败，请检查输入条件或稍后重试。';
      if (!data && rawText) console.error('非 JSON 错误响应', rawText);
      return;
    }

    if (!data) {
      status.textContent = '路线生成失败，请检查输入条件或稍后重试。';
      if (rawText) console.error('无法解析成功响应', rawText);
      return;
    }

    displayResults(data);
  } catch (error) {
    console.error('请求失败', error);
    status.textContent = '路线生成失败，请检查输入条件或稍后重试。';
  } finally {
    btn.disabled = false;
    btnText.style.display = "inline";
    btnLoading.style.display = "none";
  }
}

async function generateBlindBoxRoute() {
  const status = document.getElementById("status");
  const section = document.getElementById("blindBoxSection");
  const container = document.getElementById("blindBoxResults");
  const resultsSection = document.getElementById("resultsSection");
  const detailSection = document.getElementById("detailSection");
  const btn = document.getElementById("blindBoxBtn");

  if (section) section.style.display = "none";
  if (container) container.innerHTML = "";
  if (resultsSection) resultsSection.style.display = "none";
  if (detailSection) detailSection.style.display = "none";
  status.textContent = "";
  if (btn) btn.disabled = true;

  const payload = collectFormPayload();
  payload.preferences.theme = document.getElementById("blind_box_theme").value || "citywalk";
  payload.preferences.start = payload.start;

  try {
    const response = await fetch(API_CONFIG.blindBoxUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const data = await response.json();
    if (!response.ok) {
      status.textContent = data.message || "盲盒路线生成失败";
      renderBlindBoxResults(data);
      return;
    }

    status.textContent = data.message || "盲盒路线生成成功";
    renderBlindBoxResults(data);
  } catch (error) {
    status.textContent = "请求失败：" + error.message;
  } finally {
    if (btn) btn.disabled = false;
  }
}

// ========== 初始化 ==========

document.addEventListener('DOMContentLoaded', () => {
  // 初始化时长 chips
  initChipGroup(
    document.getElementById('durationChips'),
    document.getElementById('duration_minutes')
  );

  initChipGroup(
    document.getElementById('startTimeChips'),
    document.getElementById('start_time')
  );

  initChipGroup(
    document.getElementById('transportChips'),
    document.getElementById('transport')
  );

  // 初始化预算 chips
  initChipGroup(
    document.getElementById('budgetChips'),
    document.getElementById('budget')
  );

  // 初始化排队 chips
  initChipGroup(
    document.getElementById('waitChips'),
    document.getElementById('max_wait')
  );

  // 初始化偏好 chips
  initPreferenceChips();

  initMultiSelectChips(
    document.getElementById('personaTagChips'),
    document.getElementById('persona_tags')
  );

  initMultiSelectChips(
    document.getElementById('preferenceTagChips'),
    document.getElementById('preference_tags')
  );

  initMultiSelectChips(
    document.getElementById('constraintTagChips'),
    document.getElementById('constraint_tags')
  );

  setupPaceModeControls();
  setupPlanTypeTabs();
  updateFriendCommutePreview();
  mergePoiOptions(POI_OPTIONS);
  renderSelectedPoiChips();

  const addPoiBtn = document.getElementById('addPoiBtn');
  if (addPoiBtn) {
    addPoiBtn.addEventListener('click', addMustVisitPoi);
  }
});

// 暴露到 window
window.generateRoute = generateRoute;
window.generateBlindBoxRoute = generateBlindBoxRoute;
window.revealBlindBox = revealBlindBox;
window.updateFriendCommutePreview = updateFriendCommutePreview;
window.showFullRoute = showFullRoute;
window.closeDetail = closeDetail;
window.removeMustVisitPoi = removeMustVisitPoi;

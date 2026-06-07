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

function renderMatchedReasons(reasons, limit = 2) {
  if (!reasons || !reasons.length) return '';
  return `
    <ul class="matched-reasons">
      ${reasons.slice(0, limit).map(reason => `<li>${reason}</li>`).join('')}
    </ul>
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

function renderOption(option, index) {
  const cardId = `card-${index}`;
  const themeClass = PLAN_THEMES[option.type] || 'theme-warm';

  if (!option.success || !option.route) {
    return `
      <div class="flip-card" data-index="${index}" id="${cardId}">
        <div class="flip-card-inner">
          <div class="flip-card-front">
            <h3>${optionName(option.type)}</h3>
            <p class="summary">${option.summary || option.message || '暂无方案'}</p>
            <div class="meta"><span>不可用</span></div>
          </div>
          <div class="flip-card-back ${themeClass}"><div class="back-empty">该方案不可用</div></div>
        </div>
      </div>
    `;
  }

  const route = option.route;
  const planName = optionName(option.type);
  const totalWait = route.total_wait_time || 0;
  const shortSummary = option.summary.length > 20 ? option.summary.slice(0, 20) + '…' : option.summary;
  const personaContext = option.persona_context || route.persona_context;
  const matchedReasons = option.matched_reasons || route.matched_reasons || [];
  const qualityScores = option.quality_scores || route.quality_scores;
  const routeTransport = route.segments && route.segments.length
    ? route.segments[0].transport
    : 'walk';

  const routeSvgHtml = generateMiniRouteSVG(option.type, route.pois);

  return `
    <div class="flip-card" data-index="${index}" id="${cardId}">
      <div class="flip-card-inner">
        <!-- 正面 -->
        <div class="flip-card-front">
          <h3>${planName}</h3>
          ${renderPersonaTags(personaContext)}
          <p class="summary">${option.summary}</p>
          ${renderMatchedReasons(matchedReasons, 2)}
          ${renderQualityScores(qualityScores, true)}
          <div class="meta">
            <span>${route.pois.length} 个地点</span>
            <span>约 ${route.total_time} 分钟</span>
            <span>约 ¥${route.total_cost}</span>
            <span>${transportName(routeTransport)}</span>
            ${totalWait > 0 ? `<span>排队约 ${totalWait} 分钟</span>` : ''}
          </div>
          <button class="btn-mobile-full-route" onclick="showFullRoute(${index}, event)">查看完整路线</button>
        </div>

        <!-- 背面：三段式结构 -->
        <div class="flip-card-back ${themeClass}">
          <!-- 1. 顶部信息头 -->
          <div class="back-header">
            <span class="back-badge">${planName}</span>
            ${renderPersonaTags(personaContext)}
            <p class="back-summary">${shortSummary}</p>
            <div class="back-metrics">
              <span>${route.total_time} 分钟</span>
              <span>¥${route.total_cost}</span>
              <span>${transportName(routeTransport)}</span>
              ${totalWait > 0 ? `<span>排队 ${totalWait} 分钟</span>` : ''}
            </div>
          </div>

          <!-- 2. 中间路线画布 -->
          ${routeSvgHtml}

          <!-- 3. 底部操作区 -->
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

  document.getElementById('detailTitle').textContent = optionName(option.type);
  document.getElementById('detailSummary').innerHTML = `
    ${renderPersonaTags(personaContext)}
    <p>${option.summary || ''}</p>
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
      <strong>${i + 1}. ${poi.name}</strong>
      <span>到达: ${poi.arrive_time} | 离开: ${poi.leave_time} | 人均: ¥${poi.price}${poi.wait_time ? ` | 等待: ${poi.wait_time}分钟` : ''}</span>
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

  if (!data.success) {
    status.textContent = data.message || "路线生成失败";
    return;
  }

  window.latestOptions = data.options;
  status.textContent = data.message;
  renderAssumptionsPanel(data.preference_insight);
  renderFriendCenterBanner(data);
  results.innerHTML = data.options.map(renderOption).join("");
  resultsSection.style.display = "block";

  setTimeout(() => {
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, 100);
}

// ========== 表单数据收集 ==========

function collectFormPayload() {
  const payload = {
    start: document.getElementById("start").value || "120.1646,30.2552",
    user_input: document.getElementById("user_input").value || "周末想在杭州轻松逛逛",
    preferences: {
      city: "杭州",
      food: splitInput(document.getElementById("food").value || "杭帮菜"),
      tags: splitInput(document.getElementById("tags").value || "本地风味,放松"),
      budget: Number(document.getElementById("budget").value) || 300,
      time_window: [
        document.getElementById("start_time").value || "10:00",
        document.getElementById("end_time").value || "18:00"
      ],
      max_wait: Number(document.getElementById("max_wait").value) || 30,
      duration_minutes: Number(document.getElementById("duration_minutes").value) || 240,
      transport: document.getElementById("transport").value || "walk",
      persona_tags: splitInput(document.getElementById("persona_tags").value),
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

    if (!response.ok) {
      const errorData = await response.json();
      status.textContent = errorData.message || "路线生成失败";
      return;
    }

    const data = await response.json();
    displayResults(data);
  } catch (error) {
    status.textContent = "请求失败：" + error.message;
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
});

// 暴露到 window
window.generateRoute = generateRoute;
window.generateBlindBoxRoute = generateBlindBoxRoute;
window.revealBlindBox = revealBlindBox;
window.updateFriendCommutePreview = updateFriendCommutePreview;
window.showFullRoute = showFullRoute;
window.closeDetail = closeDetail;

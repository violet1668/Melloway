// 全局状态
let map = null;
let mapLayers = [];

function splitInput(value) {
  return value
    .split(",")
    .map(item => item.trim())
    .filter(item => item.length > 0);
}

function renderOption(option, index) {
  if (!option.success || !option.route) {
    return `
      <article class="card">
        <h3>${optionName(option.type)}</h3>
        <p>${option.summary || option.message}</p>
      </article>
    `;
  }

  const route = option.route;

  const poiList = route.pois.map(poi => `
    <li>
      <strong>${poi.name}</strong>
      <span>${poi.arrive_time} 到达，${poi.leave_time} 离开，人均 ¥${poi.price}</span>
    </li>
  `).join("");

  const segmentList = route.segments.map(seg => `
    <li>${seg.from} → ${seg.to}：${seg.transport}，约 ${seg.duration} 分钟，${seg.distance} km</li>
  `).join("");

  return `
    <article class="card">
      <h3>${optionName(option.type)}</h3>
      <p class="summary">${option.summary}</p>

      <div class="meta">
        <span>${route.pois.length} 个 POI</span>
        <span>约 ${route.total_time} 分钟</span>
        <span>约 ¥${route.total_cost}</span>
      </div>

      <button class="map-button" onclick="showRouteOnMap(${index})">在地图中查看</button>

      <details>
        <summary>查看详情</summary>
        <h4>POI 顺序</h4>
        <ol>${poiList}</ol>

        <h4>交通段</h4>
        <ul>${segmentList}</ul>
      </details>
    </article>
  `;
}

function displayResults(data) {
  const status = document.getElementById("status");
  const results = document.getElementById("results");

  if (!data.success) {
    status.textContent = data.message || "路线生成失败";
    return;
  }

  window.latestOptions = data.options;
  status.textContent = data.message;
  results.innerHTML = data.options.map(renderOption).join("");

  const firstSuccessIndex = data.options.findIndex(option => option.success);
  if (firstSuccessIndex >= 0) {
    showRouteOnMap(firstSuccessIndex);
  }
}

function collectFormPayload() {
  const payload = {
    start: document.getElementById("start").value,
    user_input: document.getElementById("user_input").value,
    preferences: {
      city: "杭州",
      food: splitInput(document.getElementById("food").value),
      tags: splitInput(document.getElementById("tags").value),
      budget: Number(document.getElementById("budget").value),
      time_window: [
        document.getElementById("start_time").value,
        document.getElementById("end_time").value
      ],
      max_wait: Number(document.getElementById("max_wait").value),
      duration_minutes: Number(document.getElementById("duration_minutes").value),
      transport: document.getElementById("transport").value
    }
  };

  const poiCountValue = document.getElementById("poi_count").value;
  if (poiCountValue.trim() !== "") {
    payload.preferences.poi_count = Number(poiCountValue);
  }

  return payload;
}

async function generateRoute() {
  const status = document.getElementById("status");
  const results = document.getElementById("results");

  status.textContent = "正在生成路线...";
  results.innerHTML = "";

  const payload = collectFormPayload();

  try {
    const response = await fetch(API_CONFIG.generateUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
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
  }
}

document.getElementById("generateBtn").addEventListener("click", generateRoute);

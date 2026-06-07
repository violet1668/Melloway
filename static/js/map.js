const RouteMap = {
  map: null,
  layers: [],

  // 初始化地图（只执行一次）
  init() {
    if (this.map) {
      return;
    }

    this.map = L.map("map").setView([30.2741, 120.1551], 13);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: "&copy; OpenStreetMap contributors"
    }).addTo(this.map);
  },

  escapeHtml(text) {
    return String(text)
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#39;');
  },

  buildPoiPopup(poi, index) {
    const hiddenGem = poi.is_hidden_gem
      ? '<div class="map-popup-tag">隐藏宝藏</div>'
      : '';
    const firstComment = Array.isArray(poi.ugc_comments) && poi.ugc_comments.length
      ? `<div class="map-popup-comment">“${this.escapeHtml(poi.ugc_comments[0])}”</div>`
      : '';

    return `
      <div class="map-popup">
        <strong>${index + 1}. ${this.escapeHtml(poi.name || '未命名地点')}</strong>
        ${hiddenGem}
        <div>到达：${this.escapeHtml(poi.arrive_time || '--')}</div>
        <div>离开：${this.escapeHtml(poi.leave_time || '--')}</div>
        <div>人均：¥${Number(poi.price || 0)}</div>
        ${firstComment}
      </div>
    `;
  },

  // 清除地图图层
  clearLayers() {
    if (!this.map) return;

    this.layers.forEach(layer => {
      this.map.removeLayer(layer);
    });
    this.layers = [];
  },

  // 在地图上显示路线
  showRoute(optionIndex) {
    const option = window.latestOptions && window.latestOptions[optionIndex];

    if (!option || !option.success || !option.route) {
      return;
    }

    // 确保地图已初始化
    this.init();

    // 清除之前的图层
    this.clearLayers();

    const route = option.route;
    const points = [];

    // 起点
    const startLatLng = [route.start_point?.lat || 30.2741, route.start_point?.lng || 120.1551];
    points.push(startLatLng);

    const startMarker = L.marker(startLatLng)
      .addTo(this.map)
      .bindPopup("起点");

    this.layers.push(startMarker);

    // POI 点
    route.pois.forEach((poi, index) => {
      const latLng = [poi.lat || 30.2741, poi.lng || 120.1551];
      points.push(latLng);

      const marker = L.marker(latLng)
        .addTo(this.map)
        .bindPopup(this.buildPoiPopup(poi, index));

      this.layers.push(marker);
    });

    // 路线连线
    if (points.length > 1) {
      const polyline = L.polyline(points, {
        weight: 4,
        color: '#d97706',
        opacity: 0.8
      }).addTo(this.map);

      this.layers.push(polyline);

      // 自动缩放显示完整路线
      this.map.fitBounds(polyline.getBounds(), {
        padding: [40, 40]
      });
    } else {
      // 只有一个点时缩放到该点
      this.map.setView(points[0], 13);
    }
  }
};

// 向后兼容的函数
function initMap() {
  RouteMap.init();
}

function clearMapLayers() {
  RouteMap.clearLayers();
}

function showRouteOnMap(optionIndex) {
  RouteMap.showRoute(optionIndex);
}
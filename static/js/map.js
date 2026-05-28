function initMap() {
  if (map) {
    return;
  }

  map = L.map("map").setView([30.2741, 120.1551], 13);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap contributors"
  }).addTo(map);
}

function clearMapLayers() {
  mapLayers.forEach(layer => {
    map.removeLayer(layer);
  });
  mapLayers = [];
}

function showRouteOnMap(optionIndex) {
  const option = window.latestOptions[optionIndex];

  if (!option || !option.success || !option.route) {
    alert("该方案没有可展示的路线。");
    return;
  }

  initMap();
  clearMapLayers();

  const route = option.route;
  const points = [];

  const startLatLng = [route.start_point.lat, route.start_point.lng];
  points.push(startLatLng);

  const startMarker = L.marker(startLatLng)
    .addTo(map)
    .bindPopup("起点");

  mapLayers.push(startMarker);

  route.pois.forEach((poi, index) => {
    const latLng = [poi.lat, poi.lng];
    points.push(latLng);

    const marker = L.marker(latLng)
      .addTo(map)
      .bindPopup(`${index + 1}. ${poi.name}<br>到达：${poi.arrive_time}<br>离开：${poi.leave_time}<br>人均：¥${poi.price}`);

    mapLayers.push(marker);
  });

  const polyline = L.polyline(points, {
    weight: 4
  }).addTo(map);

  mapLayers.push(polyline);

  map.fitBounds(polyline.getBounds(), {
    padding: [40, 40]
  });
}

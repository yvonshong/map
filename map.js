// map.js

// 1. 初始化地图
// 将地图中心设置为一个大概的世界中心点，缩放级别设为2，可以看到全世界
const map = L.map('map').setView([20, 0], 2);

// 2. 添加地图瓦片图层
// 我们使用 OpenStreetMap 的免费瓦片服务
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);

// 3. 创建一个自定义图钉图标
const customPin = L.icon({
    iconUrl: 'pin.png', // 我们自己的图钉图片路径
    iconSize:     [14, 14], // 图标的尺寸 [宽, 高] - 我们把它改小了一点
    iconAnchor:   [7, 14], // 锚点也需要相应调整 (宽度的一半, 高度)
    popupAnchor:  [0, -28]  // 弹出窗口的位置也需要调整
});


// 4. 遍历已经包含坐标的地点，并在地图上标记
myPlaces.forEach(place => {
    // 检查地点数据是否包含纬度和经度
    if (place.lat && place.lon) {
        // 直接使用已有的坐标创建标记
        // 如果 place.description 不存在，则使用空字符串，避免在弹窗中显示 "undefined"
        const description = place.description || '';
        L.marker([place.lat, place.lon], {icon: customPin})
            .addTo(map)
            .bindPopup(`<b>${place.city}, ${place.country}</b><br>${description}`);
    } else {
        console.warn(`地点 ${place.city}, ${place.country} 缺少坐标信息，已跳过。`);
    }
});
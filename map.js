// 1. 初始化 Cesium Viewer
// 设置 Cesium 基础路径，防止资源加载失败
window.CESIUM_BASE_URL = "https://cesium.com/downloads/cesiumjs/releases/1.130/Build/Cesium/";

// 设置 Cesium Ion Token (来自用户提供的参考代码)
Cesium.Ion.defaultAccessToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiIzOTRjMWZjNi04ZDViLTRkMzktYTU0Yy03YTg2YzhhMWI0NzAiLCJpZCI6Mzc3ODEzLCJpYXQiOjE3NjgyNTg0NjF9.w7XetoHHL8bzAWk5bIemKLlfpsRdWUcviM6xji1s5sE';

// 使用默认的 Viewer 配置，它会自动加载 Bing Maps (需要 Token)
const viewer = new Cesium.Viewer('map', {
    baseLayerPicker: false,
    geocoder: false,
    homeButton: false,
    infoBox: false, // 参考代码禁用了 infoBox，我们暂时禁用，或者保留 true 如果需要点击查看详情
    navigationHelpButton: false,
    sceneModePicker: false,
    selectionIndicator: false,
    timeline: false,
    animation: false,
    fullscreenButton: false,
    vrButton: false,
    skyAtmosphere: new Cesium.SkyAtmosphere()
});

viewer.scene.globe.enableLighting = true; // 开启光照，更有立体感

// 2. 遍历已经包含坐标的地点，并在地图上添加 Entity (Pin)
myPlaces.forEach(place => {
    // 检查地点数据是否包含纬度和经度
    if (place.lat && place.lon) {
        // Cesium 使用笛卡尔坐标 (Cartesian3)
        // lon, lat, height
        const position = Cesium.Cartesian3.fromDegrees(place.lon, place.lat);

        // description 处理
        const description = place.description || '';

        // 添加 Entity
        viewer.entities.add({
            name: `${place.city}, ${place.country}`,
            position: position,
            point: {
                pixelSize: 10,
                color: Cesium.Color.RED,
                outlineColor: Cesium.Color.WHITE,
                outlineWidth: 2
            },
            // 如果想要用 billboard (图片图标) 可以解开下面注释并替换 iconUrl
            /*
            billboard: {
                image: 'pin.png', // 确保 pin.png 路径正确
                width: 32,
                height: 32,
                verticalOrigin: Cesium.VerticalOrigin.BOTTOM
            },
            */
            description: `
                <div style="padding: 10px;">
                    <h3>${place.city}, ${place.country}</h3>
                    <p>${description}</p>
                    <p>Lat: ${place.lat}, Lon: ${place.lon}</p>
                </div>
            `
        });
    } else {
        console.warn(`地点 ${place.city}, ${place.country} 缺少坐标信息，已跳过。`);
    }
});

// 3. 设置地图中心在上海
// 上海坐标: 31.2304° N, 121.4737° E
const shanghaiLon = 121.4691024;
const shanghaiLat = 31.2323437;
const shanghaiHeight = 10000000; // 视点高度，单位米，调整这个值来决定初始缩放级别

viewer.camera.flyTo({
    destination: Cesium.Cartesian3.fromDegrees(shanghaiLon, shanghaiLat, shanghaiHeight),
    orientation: {
        heading: Cesium.Math.toRadians(0.0), // 北向
        pitch: Cesium.Math.toRadians(-90.0), // 俯视
        roll: 0.0
    },
    duration: 3 // 飞行持续时间 3秒
});
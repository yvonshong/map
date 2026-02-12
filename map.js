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

// 禁用双击实体时的自动追踪/缩放
viewer.cesiumWidget.screenSpaceEventHandler.removeInputAction(Cesium.ScreenSpaceEventType.LEFT_DOUBLE_CLICK);

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
            name: place.city, // 使用完整的地名 (locations.js 中的 city 字段包含国家省份城市)
            position: position,
            point: {
                pixelSize: 10,
                color: Cesium.Color.RED,
                outlineColor: Cesium.Color.WHITE,
                outlineWidth: 2
            },
            label: {
                text: place.city, // 显示完整的地名
                show: false,      // 默认隐藏，点击后显示
                font: '14px sans-serif',
                style: Cesium.LabelStyle.FILL_AND_OUTLINE,
                fillColor: Cesium.Color.WHITE,
                outlineColor: Cesium.Color.BLACK,
                outlineWidth: 2,
                horizontalOrigin: Cesium.HorizontalOrigin.LEFT,
                pixelOffset: new Cesium.Cartesian2(15, 0), // 向右偏移，避免遮挡点
                scaleByDistance: new Cesium.NearFarScalar(1.5e2, 1.0, 1.5e7, 0.5) // 远距离缩小
            },
            description: `
                <div style="padding: 10px;">
                    <h3>${place.city}</h3>
                    <p>${description}</p>
                    <p>Lat: ${place.lat}, Lon: ${place.lon}</p>
                </div>
            `
        });
    } else {
        console.warn(`地点 ${place.city} 缺少坐标信息，已跳过。`);
    }
});

// 5. 监听选中实体改变事件，实现"点击显示标签"
let prevSelectedEntity = null;
viewer.selectedEntityChanged.addEventListener(function (selectedEntity) {
    // 隐藏上一个选中的实体的标签
    if (Cesium.defined(prevSelectedEntity) && Cesium.defined(prevSelectedEntity.label)) {
        prevSelectedEntity.label.show = false;
    }

    // 显示当前选中的实体的标签
    if (Cesium.defined(selectedEntity) && Cesium.defined(selectedEntity.label)) {
        selectedEntity.label.show = true;
        prevSelectedEntity = selectedEntity;
    } else {
        prevSelectedEntity = null;
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

// 6. 航班轨迹功能
// 创建一个 EntityCollection 或者数组来管理航班实体，方便显示/隐藏
const flightEntities = [];

/**
 * 计算两点之间的曲线路径 (二次贝塞尔曲线差值)
 * @param {Cesium.Cartesian3} startPoint - 起点
 * @param {Cesium.Cartesian3} endPoint - 终点
 * @param {Number} curvature - 曲率 (0 为直线，正值向左弯曲，负值向右)
 * @returns {Cesium.Cartesian3[]} - 曲线上的点集
 */
function getCurvedLine(startPoint, endPoint, curvature) {
    // 1. 计算中点
    const midPoint = Cesium.Cartesian3.add(startPoint, endPoint, new Cesium.Cartesian3());
    Cesium.Cartesian3.multiplyByScalar(midPoint, 0.5, midPoint);

    // 2. 计算中点在地球表面的法向量 (从地心指向中点)
    const midPointNormal = Cesium.Cartesian3.normalize(midPoint, new Cesium.Cartesian3());

    // 3. 计算从起点到终点的向量
    const startToEnd = Cesium.Cartesian3.subtract(endPoint, startPoint, new Cesium.Cartesian3());

    // 4. 计算垂直于 [起终点向量] 和 [地表法向量] 的向量 (即切向偏移方向)
    // 叉乘顺序: midPointNormal x startToEnd 得到的向量指向"左侧" (相对于前进方向)
    const offsetDirection = Cesium.Cartesian3.cross(midPointNormal, startToEnd, new Cesium.Cartesian3());
    Cesium.Cartesian3.normalize(offsetDirection, offsetDirection);

    // 5. 计算控制点
    // 基础高度偏移 (让曲线稍微隆起，避免穿地)
    const distance = Cesium.Cartesian3.distance(startPoint, endPoint);
    const heightOffset = distance * 0.2; // 高度为距离的 20%

    // 侧向偏移距离
    const lateralOffset = distance * curvature;

    // 控制点 = 中点 + 高度偏移 + 侧向偏移
    const controlPoint = Cesium.Cartesian3.clone(midPoint);

    // 添加高度
    const heightVector = Cesium.Cartesian3.multiplyByScalar(midPointNormal, heightOffset, new Cesium.Cartesian3());
    Cesium.Cartesian3.add(controlPoint, heightVector, controlPoint);

    // 添加侧向偏移
    const lateralVector = Cesium.Cartesian3.multiplyByScalar(offsetDirection, lateralOffset, new Cesium.Cartesian3());
    Cesium.Cartesian3.add(controlPoint, lateralVector, controlPoint);

    // 6. 生成插值点 (二次贝塞尔)
    // B(t) = (1-t)^2 * P0 + 2(1-t)t * P1 + t^2 * P2
    const points = [];
    const steps = 50;
    for (let i = 0; i <= steps; i++) {
        const t = i / steps;

        const p0 = Cesium.Cartesian3.multiplyByScalar(startPoint, Math.pow(1 - t, 2), new Cesium.Cartesian3());
        const p1 = Cesium.Cartesian3.multiplyByScalar(controlPoint, 2 * (1 - t) * t, new Cesium.Cartesian3());
        const p2 = Cesium.Cartesian3.multiplyByScalar(endPoint, Math.pow(t, 2), new Cesium.Cartesian3());

        let point = Cesium.Cartesian3.add(p0, p1, new Cesium.Cartesian3());
        point = Cesium.Cartesian3.add(point, p2, point);

        points.push(point);
    }
    return points;
}

if (typeof myFlights !== 'undefined') {
    // 记录每条航线 (O-D pair) 的航班数量，用于计算偏移量和颜色区分
    const routeCounts = {};

    myFlights.forEach(flight => {
        const startCity = flight.dep_city;
        const endCity = flight.arr_city;
        const routeKey = `${startCity}->${endCity}`;

        if (!routeCounts[routeKey]) {
            routeCounts[routeKey] = 0;
        }
        routeCounts[routeKey]++;
        const count = routeCounts[routeKey];

        // 动态计算曲率
        // 减小曲率增量，防止航线过于分散占用屏幕
        const curvature = 0.05 + (count * 0.005);

        const start = Cesium.Cartesian3.fromDegrees(flight.from_lon, flight.from_lat);
        const end = Cesium.Cartesian3.fromDegrees(flight.to_lon, flight.to_lat);

        const positions = getCurvedLine(start, end, curvature);

        const flightEntity = viewer.entities.add({
            name: `Flight ${flight.flight_no}`,
            polyline: {
                positions: positions,
                width: 2,
                material: new Cesium.PolylineGlowMaterialProperty({
                    glowPower: 0.2,
                    color: Cesium.Color.GOLD
                }),
            },
            // 将航班信息存储在自定义属性中，供点击事件使用
            properties: {
                infoText: `${flight.date}\n${flight.flight_no}\n${flight.dep_city} -> ${flight.arr_city}`
            },
            // 自定义属性，用于弹窗 (虽然我们禁用了 infoBox，保留此数据是个好习惯)
            description: `
                <div style="padding: 10px;">
                    <h3>${flight.airline} ${flight.flight_no}</h3>
                    <p><strong>Date:</strong> ${flight.date}</p>
                    <p><strong>From:</strong> ${flight.dep_city} (${flight.dep_time})</p>
                    <p><strong>To:</strong> ${flight.arr_city} (${flight.arr_time})</p>
                </div>
            `
        });

        // 默认隐藏
        flightEntity.show = false;
        flightEntities.push(flightEntity);
    });
}

// 7. 动态标签 (点击轨迹时显示在点击位置)
const dynamicLabelEntity = viewer.entities.add({
    label: {
        show: false,
        showBackground: true,
        font: '12px sans-serif',
        horizontalOrigin: Cesium.HorizontalOrigin.LEFT,
        verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
        pixelOffset: new Cesium.Cartesian2(10, -10),
        backgroundColor: new Cesium.Color(0, 0, 0, 0.7),
        style: Cesium.LabelStyle.FILL,
        fillColor: Cesium.Color.WHITE,
        disableDepthTestDistance: Number.POSITIVE_INFINITY
    }
});

// 处理点击事件
const handler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas);
handler.setInputAction(function (movement) {
    const pickedObject = viewer.scene.pick(movement.position);

    // 如果点击了实体，并且该实体有我们存的 flight infoText
    if (Cesium.defined(pickedObject) &&
        Cesium.defined(pickedObject.id) &&
        Cesium.defined(pickedObject.id.properties) &&
        pickedObject.id.properties.hasProperty('infoText')) {

        // 获取点击在地球表面的位置
        // viewer.scene.pickPosition 适用于模型和地形，但在某些 2D 视图或无地形时可能不稳定
        // 对于 Polyline，我们可以尝试用 ray intersection 或者简单的 camera pickEllipsoid
        let cartesian = viewer.scene.pickPosition(movement.position);

        if (!Cesium.defined(cartesian)) {
            const ray = viewer.camera.getPickRay(movement.position);
            cartesian = viewer.scene.globe.pick(ray, viewer.scene);
        }

        if (Cesium.defined(cartesian)) {
            dynamicLabelEntity.position = cartesian;
            dynamicLabelEntity.label.text = pickedObject.id.properties.infoText.getValue();
            dynamicLabelEntity.label.show = true;
            return;
        }
    }

    // 如果没点到航班轨迹，或者点到了空处，隐藏标签
    dynamicLabelEntity.label.show = false;

}, Cesium.ScreenSpaceEventType.LEFT_CLICK);

// 7. 添加 UI 开关
// 创建一个简单的 HTML 按钮覆盖在地图上
const toolbar = document.createElement('div');
toolbar.style.position = 'absolute';
toolbar.style.top = '20px';
toolbar.style.left = '20px';
toolbar.style.zIndex = '100';
toolbar.style.backgroundColor = 'rgba(0, 0, 0, 0.7)';
toolbar.style.padding = '10px';
toolbar.style.borderRadius = '5px';
toolbar.style.color = 'white';
toolbar.style.fontFamily = 'sans-serif';

const checkbox = document.createElement('input');
checkbox.type = 'checkbox';
checkbox.id = 'toggle-flights';
checkbox.onchange = function () {
    const isChecked = this.checked;
    flightEntities.forEach(entity => {
        entity.show = isChecked;
    });
};

const label = document.createElement('label');
label.htmlFor = 'toggle-flights';
label.innerText = ' Show Flights';
label.style.marginLeft = '5px';
label.style.cursor = 'pointer';

toolbar.appendChild(checkbox);
toolbar.appendChild(label);
document.body.appendChild(toolbar);
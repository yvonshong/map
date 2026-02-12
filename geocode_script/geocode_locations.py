# geocode_script/geocode_locations.py

import requests
import time
import json
import os
from multiprocessing import Pool

# --- 代理设置 (如果需要) ---
# 如果你处于需要代理才能访问外部网络的环境 (例如公司网络或特定地区)
# 请取消下面一行的注释，并填入你的代理服务器地址和端口。
# 常见的本地代理地址是 'http://127.0.0.1:7890' (Clash) 或 'http://127.0.0.1:10809' (V2RayN) 等。
# PROXIES = {
#    'http': 'http://127.0.0.1:7890',
#    'https': 'http://127.0.0.1:7890',
# }
PROXIES = None # 如果不需要代理，请保持为 None

# 定义输入和输出文件的路径
INPUT_FILE = os.path.join(os.path.dirname(__file__), 'places.txt')
CACHE_FILE = os.path.join(os.path.dirname(__file__), 'city_gps.json')
# os.path.join 会自动处理路径分隔符，让代码在 Windows/Mac/Linux 上都能运行
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'locations.js')

def geocode_single_location(address_line):
    """
    Geocodes a single address string. This function is designed to be run
    in a separate process.
    """
    query = address_line
    # parts = [p.strip() for p in address_line.split(',')]
    # if len(parts) < 2:
    #     # 返回一个元组表示失败，以便于主进程记录
    #     return (address_line, "格式错误，应为 '城市, 国家'")

    # city, country = parts[0], parts[1]
    # query = f"{country}{city}"
    url = "https://nominatim.openstreetmap.org/search"
    params = {'q': query, 'format': 'json', 'limit': 1}
    # 提供一个更具体的 User-Agent 是一个好习惯
    headers = {'User-Agent': 'MyTravelMap/1.0 (yvonshong/map-project)'}

    try:
        response = requests.get(url, params=params, headers=headers, proxies=PROXIES, timeout=10)
        response.raise_for_status()  # 如果请求失败 (例如 404, 500), 会抛出异常
        data = response.json()

        # 重要：为了遵守 Nominatim 的使用策略（每秒最多1次请求），每个进程必须等待。
        # 多进程会提高总体请求频率，这是一种缓解措施，但不能完全保证不超限。
        time.sleep(1.1)

        if data:
            place_data = {
                'city': query,
                'lat': float(data[0]['lat']),
                'lon': float(data[0]['lon'])
            }
            return place_data
        else:
            return (address_line, "未找到坐标")

    except requests.exceptions.RequestException as e:
        return (address_line, f"网络错误: {e}")

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_cache(cache):
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)

def process_locations_in_parallel():
    """
    从文本文件中读取地点，优先使用缓存，缺失的地点使用进程池并行进行地理编码。
    """
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            all_places = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"错误: 输入文件未找到: {INPUT_FILE}")
        print("请确保 geocode_script 文件夹中存在 places.txt 文件。")
        return

    # 1. 加载缓存
    cache = load_cache()
    print(f"已加载缓存，共 {len(cache)} 条记录。")

    # 2. 区分已缓存和未缓存的地点
    places_to_geocode = []
    final_results = []

    for place in all_places:
        if place in cache:
            # 直接从缓存构建结果对象
            final_results.append({
                'city': place,
                'lat': cache[place]['lat'],
                'lon': cache[place]['lon']
            })
        else:
            places_to_geocode.append(place)

    print(f"需要地理编码的新地点: {len(places_to_geocode)} 个")

    if places_to_geocode:
        PROCESS_COUNT = 4
        print(f"开始使用 {PROCESS_COUNT} 个进程处理 {len(places_to_geocode)} 个地点...")
        print("="*60)
        print("警告: 并行处理会以更高频率请求API。脚本中的延时(time.sleep)")
        print("      可以降低风险，但请勿过于频繁运行，以免IP被封禁。")
        print("="*60)

        successful_places = []
        failed_places = []

        # 创建一个工作进程池
        with Pool(processes=PROCESS_COUNT) as pool:
            # 使用 tqdm 显示一个漂亮的进度条
            from tqdm import tqdm
            results_iterator = pool.imap_unordered(geocode_single_location, places_to_geocode)
            
            for result in tqdm(results_iterator, total=len(places_to_geocode), desc="地理编码进度"):
                if isinstance(result, dict):
                    successful_places.append(result)
                    # 更新缓存字典 (注意：这里只是内存更新，最后统一保存)
                    cache[result['city']] = {
                        'lat': result['lat'],
                        'lon': result['lon']
                    }
                elif isinstance(result, tuple):
                    failed_places.append(result)

        # 合并新结果
        final_results.extend(successful_places)
        
        # 保存更新后的缓存
        save_cache(cache)
        print(f"缓存已更新，新增 {len(successful_places)} 条记录。")

        if failed_places:
            print(f"\n{len(failed_places)} 个地点处理失败:")
            for place, reason in failed_places:
                print(f"  - {place}: {reason}")

    # 对结果进行排序以获得一致的输出
    final_results.sort(key=lambda p: (p['city']))

    # 3. 统一命名原则：将 "台湾" 标记为 "台湾省, 中国"
    for p in final_results:
        if "台湾" in p['city'] and "中国" not in p['city']:
             p['city'] = p['city'].replace("台湾", "台湾省, 中国")
        elif "Taiwan" in p['city'] and "China" not in p['city']:
             p['city'] = p['city'].replace("Taiwan", "Taiwan Province, China")

    # --- 写入文件 ---
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    json_string = json.dumps(final_results, indent=2, ensure_ascii=False)
    file_content = f"// 此文件由 geocode_locations.py 脚本自动生成\n// 请勿手动编辑\n\nconst myPlaces = {json_string};"

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(file_content)

    print(f"\n处理完成！共 {len(final_results)} 个地点 (来自缓存+新查询) 已写入到: {OUTPUT_FILE}")

# 运行主函数
if __name__ == "__main__":
    process_locations_in_parallel()
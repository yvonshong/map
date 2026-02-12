import json

with open('geocode_script/city_gps.json', 'r', encoding='utf-8') as f:
    cache = json.load(f)

AMBIGUOUS_NAMES = [
    "Yulin", "榆林", "玉林",
    "Suzhou", "苏州", "宿州",
    "Taizhou", "泰州", "台州",
    "Fuzhou", "福州", "抚州",
    "Yichun", "宜春", "伊春",
    "Chaoyang", "朝阳",
    "Jining", "济宁", "集宁",
    "Ji'an", "吉安", "集安",
    "Datong", "大同", "大通",
    "Dongying", "东营",
    "Fukuoka", "福岡",
    "Matsuyama", "松山",
    "Komatsu", "小松"
]

print("--- Ambiguity Check ---")
for name, data in cache.items():
    for amb in AMBIGUOUS_NAMES:
        if amb in name:
            print(f"[CHECK] {name}: {data['lat']}, {data['lon']}")

print("--- End Check ---")

import json
import os

# Load cache
with open('geocode_script/city_gps.json', 'r', encoding='utf-8') as f:
    cache = json.load(f)

# Define rough bounding boxes (Min Lat, Max Lat, Min Lon, Max Lon)
REGIONS = {
    'Japan': (24, 46, 122, 154),
    '日本': (24, 46, 122, 154),
    'China': (18, 54, 73, 135),
    '中国': (18, 54, 73, 135),
    'Taiwan': (21, 26, 119, 123),
    '台湾': (21, 26, 119, 123),
    'Germany': (47, 55, 5, 16),
    'United Kingdom': (49, 61, -9, 2),
    'United States': (24, 50, -125, -66), # Mainland rough
    'Vietnam': (8, 24, 102, 110),
    'Thailand': (5, 21, 97, 106),
    'Norway': (57, 72, 4, 32),
    'Sweden': (55, 69, 10, 25),
    'Switzerland': (45, 48, 5, 11),
    'Italy': (36, 48, 6, 19),
    'France': (41, 52, -5, 10),
    'Spain': (35, 44, -10, 5),
    'Cambodia': (10, 15, 102, 108),
    'Indonesia': (-11, 6, 95, 141),
    'Malaysia': (0, 8, 99, 120),
    'Philippines': (4, 22, 116, 127),
    'South Korea': (33, 39, 124, 131),
    'United Arab Emirates': (22, 27, 51, 57),
    'Greece': (34, 42, 19, 29)
}

# Refined checks
PROVINCES = {
    'Sichuan': (26, 34.5, 97, 109),
    '四川': (26, 34.5, 97, 109),
    'Guangdong': (20, 25.5, 109, 117.5),
    '广东': (20, 25.5, 109, 117.5),
    'Fujian': (23.5, 28.5, 115, 120.5),
    '福建': (23.5, 28.5, 115, 120.5),
    'Zhejiang': (27, 31.5, 118, 123),
    '浙江': (27, 31.5, 118, 123),
    'Jiangsu': (30.5, 35.5, 116, 122),
    '江苏': (30.5, 35.5, 116, 122),
    'Hokkaido': (41, 46, 139, 146),
    '北海道': (41, 46, 139, 146),
    'Okinawa': (24, 28, 122, 132),
    '沖縄': (24, 28, 122, 132)
}

print("--- Refined Analysis Report ---")

# 1. Check for duplicates
coords_seen = {}
for name, data in cache.items():
    key = (round(data['lat'], 3), round(data['lon'], 3)) # Slightly less precision to catch near-dupes
    if key in coords_seen:
        print(f"[DUPLICATE] {name} ~ {coords_seen[key]}: {data['lat']}, {data['lon']}")
    else:
        coords_seen[key] = name

# 2. Check region bounds
for name, data in cache.items():
    lat = data['lat']
    lon = data['lon']
    
    # Check both Countries and Provinces/Regions
    for region_name, bounds in {**REGIONS, **PROVINCES}.items():
        if region_name in name:
            min_lat, max_lat, min_lon, max_lon = bounds
            if not (min_lat <= lat <= max_lat and min_lon <= lon <= max_lon):
                print(f"[SUSPICIOUS] {name} ({lat:.4f}, {lon:.4f}) outside {region_name} {bounds}")

    # Specific known tricky places
    if "Shangri-La" in name or "香格里拉" in name or "Diqing" in name or "迪庆" in name:
        if lat < 27: print(f"[CHECK] {name}: {lat}, {lon} (Too south?)")

print("--- End Report ---")

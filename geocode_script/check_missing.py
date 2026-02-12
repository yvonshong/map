import pandas as pd
import json
import os

INPUT_FILE = os.path.join(os.path.dirname(__file__), '【航旅纵横】 行程导出.xls')
CACHE_FILE = os.path.join(os.path.dirname(__file__), 'airport_gps.json')

def main():
    # Load Cache
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            cache = json.load(f)
    else:
        cache = {}
        print("Cache file not found.")

    # Read Excel
    try:
        all_sheets = pd.read_excel(INPUT_FILE, sheet_name=None)
        all_cities = set()
        for sheet_name, sheet_df in all_sheets.items():
            if '出发城市' in sheet_df.columns:
                all_cities.update(sheet_df['出发城市'].dropna().unique())
            if '到达城市' in sheet_df.columns:
                all_cities.update(sheet_df['到达城市'].dropna().unique())
    except Exception as e:
        print(f"Error reading Excel: {e}")
        return

    missing = []
    for city in all_cities:
        if city not in cache:
            missing.append(city)
    
    print(f"Total Unique Cities: {len(all_cities)}")
    print(f"Cached Cities: {len(cache)}")
    print(f"Missing Cities ({len(missing)}):")
    for city in missing:
        print(f"- {city}")

if __name__ == "__main__":
    main()

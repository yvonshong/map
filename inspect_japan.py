import json

with open('data/japan.geojson', 'r') as f:
    data = json.load(f)

print(f"Type: {data.get('type')}")
print(f"Feature count: {len(data.get('features', []))}")
for f in data.get('features', [])[:5]:
    props = f.get('properties', {})
    # 'nam' or 'name' or 'nam_ja' etc.
    name = props.get('nam', props.get('name', 'Unknown'))
    print(f"Name: {name}, Type: {f['geometry']['type']}")
